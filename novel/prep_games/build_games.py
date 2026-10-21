"""Parse every game box score -> games_long.csv (one row per player-game line) + games_qa.csv. Offline (uses caches)."""
import os, re, csv, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pgparse import *
from pgfetch import wb, HERE
from fetch_wiki import wiki
from fetch_texts import REG
RAW = {k: (u, ts, kind) for k, u, ts, kind in REG}

def text_of(key):
    p = os.path.join(HERE, "raw", "text", key + ".txt")
    return open(p).read() if os.path.exists(p) else None
def ocr_of(key):
    p = os.path.join(HERE, "raw", "ocr", key + ".txt")
    return open(p).read() if os.path.exists(p) else None

# ---------------------------------------------------------------- wikitables
def wiki_blocks(title):
    r = wiki(title)
    if not r: return [], None
    t = r["text"]; blocks = []
    # tables with the heading that precedes them
    for m in re.finditer(r"(?ms)^(={2,5})\s*([^=\n]+?)\s*\1\s*\n(.*?)(?=^={2,5}[^=]|\Z)", t):
        head, body = m.group(2), m.group(3)
        for tm in re.finditer(r"(?s)\{\|.*?\n\|\}", body):
            tb = tm.group(0); rows = []; cur = None
            for ln in tb.split("\n"):
                s = ln.rstrip()
                if s.startswith("|-"):
                    if cur is not None: rows.append(cur)
                    cur = []
                elif s.startswith("!"):
                    if cur is None: cur = []
                    cur.extend([c.strip() for c in re.split(r"!!|\n", s[1:])])
                elif s.startswith("|") and not s.startswith("|}") and not s.startswith("|+") and cur is not None:
                    cur.extend([c.strip() for c in s[1:].split("||")])
            if cur: rows.append(cur)
            rows = [[re.sub(r"^[^|]*\|(?=[^|]*$)", "", c) if "colspan" in c else c for c in r] for r in rows]
            rows = [r for r in rows if not any("colspan" in c or "Did not play" in c for c in r)]
            # normalise header names
            rows = [[("FGM/A" if c.upper().startswith("FGM") else "3PM/A" if c.upper().startswith("3PM") else "FTM/A" if c.upper().startswith("FTM") else
                      {"POINTS": "PTS", "OFF REB": "OFF", "DEF REB": "DEF", "TOT REB": "TOT", "POINT": "PTS", "TOT": "TOT"}.get(c.upper(), c)) if i == 0 or True else c for c in r] for i, r in enumerate(rows)]
            bl = parse_grid([[head]] + rows)
            for b in bl: b["team"] = head
            blocks += bl
    return blocks, r

# ---------------------------------------------------------------- generic dispatchers
def first_two(blocks, n=2):
    return [b for b in blocks if b["rows"]][:n]
def is_girls(txt): return bool(re.search(r"(?i)\bgirls\b|women", txt[:900]))

def src_official_text(key, n=2, fmt="auto"):
    t = text_of(key)
    if not t: return None
    lines = t.split("\n")
    for f in ([fmt] if fmt != "auto" else ["A", "D", "E"]):
        bl = {"A": parse_lines, "D": parse_format_d, "E": parse_format_e}[f](lines)
        bl = [b for b in bl if b["rows"]]
        if bl: return first_two(bl, n), f
    return None
def src_ocr(key, n=2):
    t = ocr_of(key)
    if not t: return None
    return ocr_shooting(t.split("\n"), n)

ROW_O = re.compile(r"^\s*(?P<num>\d{1,2})?\s*[•\*]?\s*(?P<name>[A-Za-z][A-Za-z'\.\-]*(?:[, ]+[A-Za-z'\.\-]+){0,3}?)\s+(?:[fgcFGC]\s+)?(?:\*\s+)?(?:\d{1,2}:\d{2}\s+)?(?P<fg>\d{1,2}\s*-\s*\d{1,2})\s+(?P<tp>\d{1,2}\s*-\s*\d{1,2})\s+(?P<ft>\d{1,2}\s*-\s*\d{1,2})(?P<tail>.*)$")
def ocr_shooting(lines, n=2):
    blocks = []; cur = None
    for ln in lines:
        if re.match(r"^\s*(team\s+)?totals?\b", ln, re.I): cur = None; continue
        m = ROW_O.match(ln)
        if not m: continue
        nm = m.group("name").strip(" ,.")
        if re.match(r"(?i)^(team|total|ft|fg|3fg)", nm): continue
        fg, tp, ft = [tuple(int(x) for x in re.split(r"\s*-\s*", m.group(k))) for k in ("fg", "tp", "ft")]
        if not (fg[0] <= fg[1] and tp[0] <= tp[1] and ft[0] <= ft[1] and tp[0] <= fg[0] and tp[1] <= fg[1] and fg[1] <= 40 and ft[1] <= 25): continue
        if cur is None: cur = {"team": None, "rows": [], "cols": "OCR"}; blocks.append(cur)
        cur["rows"].append(dict(name=nm, num=m.group("num"), fgm=fg[0], fga=fg[1], tpm=tp[0], tpa=tp[1], ftm=ft[0], fta=ft[1],
                                pts=2 * fg[0] + tp[0] + ft[0], pts_ok=1, ocr=1))
    return first_two([b for b in blocks if b["rows"]], n), "OCR"

def usab_blocks(year):
    L = [l.split()[:2] for l in open(os.path.join(HERE, "usab_cdx.txt")) if l[:2] == "20"]
    c = [x for x in L if re.search(r"annual-nike-hoop-summit-%d\.aspx" % year, x[1])]
    if not c: return None
    ts, u = c[0]
    h = wb(u, ts)
    if not h: return None
    rows = html_to_grid(h)
    k = [i for i, r in enumerate(rows) if any(re.search(r"Box Score", c) for c in r)]
    rows = rows[k[0]:] if k else rows
    bl = parse_grid(rows)
    return [b for b in bl if b["rows"]][:2], (u, ts)

# ---------------------------------------------------------------- game registry
def games():
    out = []   # (game, year, loader) ; loader returns (blocks, fmt, source_desc)
    def W(y): 
        def f():
            b, r = wiki_blocks("%d McDonald's All-American Boys Game" % y)
            b = [x for x in b if x["rows"]]
            # keep the two blocks following a box score heading (boys): first two tables with >=10 rows
            b = first_two(b)
            if not b: return None
            return b, "wiki", "en.wikipedia.org oldid=%s (%s)" % (r["revid"], r["ts"])
        return f
    def O(key, n=2, fmt="auto", girls_ok=False):
        def f():
            t = text_of(key)
            if t is None: return None
            if not girls_ok and is_girls(t): return None
            r = src_official_text(key, n, fmt)
            if not r: return None
            u, ts, k = RAW[key]
            return r[0], "official_" + r[1], "web.archive.org/web/%s/%s" % (ts, u)
        return f
    def C(key):
        def f():
            r = src_ocr(key)
            if not r or not r[0]: return None
            u, ts, k = RAW[key]
            return r[0], "ocr_shooting", "web.archive.org/web/%s/%s (OCR)" % (ts, u)
        return f
    def H(y):
        def f():
            r = usab_blocks(y)
            if not r or not r[0]: return None
            return r[0], "usab_html", "web.archive.org/web/%s/%s" % (r[1][1], r[1][0])
        return f
    def alt(*fs):
        def f():
            for g in fs:
                r = g()
                if r: return r
            return None
        return f
    for y in (2006, 2007, 2008, 2009, 2010): out.append(("mcd", y, alt(W(y), O("mcd%d_off" % y))))
    out.append(("mcd", 2011, alt(O("mcd2011_off_b"), O("mcd2011_off"))))
    out.append(("mcd", 2012, C("mcd2012_off")))
    out.append(("mcd", 2013, O("mcd2013_off")))
    out.append(("mcd", 2014, O("mcd2014_off")))
    for y in (2015, 2016, 2017, 2018, 2019): out.append(("mcd", y, O("mcd%d_off" % y)))
    out.append(("mcd", 2022, O("mcd2022_off_b")))
    out.append(("mcd", 2023, alt(O("mcd2023_off_a"), O("mcd2023_off_b"))))
    out.append(("mcd", 2024, C("mcd2024_off")))
    out.append(("mcd", 2025, alt(O("mcd2025_off_a"), O("mcd2025_off_b"))))
    out.append(("jbc", 2008, O("jbc2008_off")))
    out.append(("jbc", 2011, O("jbc2011_off")))
    out.append(("jbc", 2012, C("jbc2012_off")))
    out.append(("jbc", 2013, alt(O("jbc2013_off"), O("jbc2013_off_b"))))
    out.append(("jbc", 2014, O("jbc2014_off")))
    for y in (2015, 2016, 2017, 2018, 2019): out.append(("jbc", y, O("jbc%d_off" % y)))
    out.append(("jbc", 2022, C("jbc2022_off")))
    for y in list(range(2006, 2020)) + [2022]: out.append(("hs", y, H(y)))
    return out

FIELDS = ["game", "year", "block", "team", "name", "num", "starter", "min", "pts", "reb", "ast", "stl", "blk", "tov", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "pf", "pts_ok", "ocr", "fmt", "source"]
def run():
    rows = []; qa = []
    for g, y, loader in games():
        r = loader()
        if not r:
            qa.append(dict(game=g, year=y, status="NO_SOURCE")); continue
        blocks, fmt, src = r
        n = 0
        for bi, b in enumerate(blocks):
            for d in b["rows"]:
                rr = {k: d.get(k) for k in FIELDS if k in d}
                rr.update(game=g, year=y, block=bi, team=b.get("team"), fmt=fmt, source=src); rr["ocr"] = d.get("ocr", 0)
                rows.append(rr); n += 1
        qa.append(dict(game=g, year=y, status="ok", fmt=fmt, blocks=len(blocks), rows=n,
                       rows_pts_ok=sum(d["pts_ok"] for b in blocks for d in b["rows"]),
                       block_sizes="/".join(str(len(b["rows"])) for b in blocks),
                       team_pts="/".join(str(sum(d.get("pts", 0) for d in b["rows"])) for b in blocks), source=src))
    with open(os.path.join(HERE, "games_long.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS); w.writeheader(); w.writerows(rows)
    keys = ["game", "year", "status", "fmt", "blocks", "rows", "rows_pts_ok", "block_sizes", "team_pts", "source"]
    with open(os.path.join(HERE, "games_qa.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(qa)
    return qa
if __name__ == "__main__":
    for q in run(): print(q.get("game"), q.get("year"), q.get("status"), q.get("fmt"), q.get("block_sizes"), q.get("team_pts"), q.get("rows"), q.get("rows_pts_ok"))

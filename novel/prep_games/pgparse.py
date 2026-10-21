"""Rule-based box-score text parsing (Stat Crew style text, HTML <pre>, pdfminer text)."""
import re, html

COLMAP = {"OF":"oreb","OFF":"oreb","OR":"oreb","OREB":"oreb","DE":"dreb","DEF":"dreb","DR":"dreb","DREB":"dreb",
          "TOT":"reb","REB":"reb","TR":"reb","RB":"reb","PF":"pf","TP":"pts","PTS":"pts","PT":"pts","POINTS":"pts",
          "A":"ast","AST":"ast","AS":"ast","TO":"tov","TOV":"tov","BLK":"blk","BS":"blk","BK":"blk","S":"stl","ST":"stl",
          "STL":"stl","MIN":"min"}
DEFAULT_COLS10 = ["oreb","dreb","reb","pf","pts","ast","tov","blk","stl","min"]

def html_to_text(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", "", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</(p|div|tr|li|h\d|pre)>", "\n", h)
    h = re.sub(r"(?i)</t[dh]>", " | ", h)
    h = re.sub(r"<[^>]+>", "", h)
    return html.unescape(h).replace("\xa0", " ")

def _mins(s):
    if ":" in s:
        a, b = s.split(":")[:2]
        return int(a) + int(b) / 60.0
    return float(s)

ROW = re.compile(
    r"^\s*(?P<num>\d{1,2}\b)?\s*(?P<name>[A-Za-z][A-Za-z'\.\-, ]*?)[\s\.]*(?:\*\s*)?"
    r"(?:\s(?P<pos>[fgcFGC]|[FGC]/[FGC]|PG|SG|SF|PF|C|G|F))?\s+"
    r"(?P<fg>\d+\s*[-/]\s*\d+)\s+(?P<tp>\d+\s*[-/]\s*\d+)\s+(?P<ft>\d+\s*[-/]\s*\d+)\s+(?P<rest>[\d:\s]+?)\s*$")

def _pair(s):
    a, b = re.split(r"\s*[-/]\s*", s.strip())
    return int(a), int(b)

def header_cols(line):
    toks = re.findall(r"[A-Za-z]+", line.upper())
    cols = [COLMAP[t] for t in toks if t in COLMAP]
    return cols

def parse_lines(lines, default_cols=DEFAULT_COLS10):
    """Return list of blocks; each block = dict(cols, rows[list of dict]). A new block starts at every header line
    (contains 'Player' or 'FG' and 'TP'/'PTS')."""
    blocks = []; cur = None; cols = None
    for ln in lines:
        u = ln.upper()
        if ("PLAYER" in u or "NAME" in u) and re.search(r"\b(TP|PTS|POINTS)\b", u) and re.search(r"\b(MIN|A|AST)\b", u):
            cols = header_cols(ln) or default_cols
            cur = {"cols": cols, "rows": [], "hdr": ln.strip()}; blocks.append(cur); continue
        if re.match(r"(?i)^\s*(team\s+)?totals?\b", ln): cur = None; continue
        m = ROW.match(ln)
        if not m: continue
        name = m.group("name").strip(" .,*")
        if re.match(r"(?i)^(totals?|team totals?)\b", name): cur = None; continue
        if re.match(r"(?i)^(team|deadball)\b", name): continue
        rest = m.group("rest").split()
        c = cols or default_cols
        if cur is None:
            cur = {"cols": c, "rows": [], "hdr": ""}; blocks.append(cur)
        if len(rest) != len(c):
            cur.setdefault("bad", []).append(ln.strip()); continue
        d = dict(zip(c, rest))
        r = {"name": name, "num": m.group("num")}
        r["fgm"], r["fga"] = _pair(m.group("fg")); r["tpm"], r["tpa"] = _pair(m.group("tp")); r["ftm"], r["fta"] = _pair(m.group("ft"))
        for k, v in d.items():
            r[k] = _mins(v) if k == "min" else int(v)
        if "reb" not in r and "oreb" in r and "dreb" in r: r["reb"] = r["oreb"] + r["dreb"]
        r["pts_ok"] = int(r.get("pts") == 2 * r["fgm"] + r["tpm"] + r["ftm"])
        cur["rows"].append(r)
    return blocks

# ---------------------------------------------------------------- grid (table) parser
HMAP = {"FG":"fgm","NO":"num","#":"num","##":"num","NUM":"num","NAME":"name","PLAYER":"name","P":"pos","POS":"pos",
        "FGM":"fgm","FGA":"fga","FGM/A":"fg2","FG-FGA":"fg2","FGM-A":"fg2","3PM":"tpm","3PA":"tpa","3P":"tpm","3PT":"tpm","3PTM":"tpm","3-PT":"tpm",
        "3PM/A":"tp2","3PM-A":"tp2","FTM":"ftm","FTA":"fta","FT":"ftm","FTM/A":"ft2","FTM-A":"ft2","FT-FTA":"ft2",
        "OFF":"oreb","OF":"oreb","OR":"oreb","OREB":"oreb","DEF":"dreb","DE":"dreb","DR":"dreb","DREB":"dreb","TOT":"reb","REB":"reb","TR":"reb",
        "PF":"pf","TP":"pts","PTS":"pts","POINTS":"pts","A":"ast","AST":"ast","AS":"ast","TO":"tov","TOV":"tov","BLK":"blk","BS":"blk","BK":"blk",
        "S":"stl","ST":"stl","STL":"stl","MIN":"min","MINS":"min","3P-3PA":"tp2"}
def _hdr_map(cells):
    cols = []
    up = [re.sub(r"\s+", "", c.upper()) for c in cells]
    for i, h in enumerate(up):
        k = HMAP.get(h)
        if k in ("fgm", "tpm", "ftm"):   # separate M / A columns only if the next header is the A column
            nxt = up[i + 1] if i + 1 < len(up) else ""
            if h in ("FG",) and nxt != "FGA": k = "fg2"
            elif h in ("FT",) and nxt != "FTA": k = "ft2"
            elif h in ("3P", "3PT", "3-PT") and nxt not in ("3PA", "3PTA"): k = "tp2"
        cols.append(k)
    # positional fix: repeated "FG-FGA"/"FG-FGA"/"FT-FTA" headers -> FG, 3P, FT pairs
    seen = 0
    for i, h in enumerate(up):
        if h in ("FG-FGA", "FGM-A", "FGM/A") and cols[i] == "fg2":
            seen += 1
            if seen == 2: cols[i] = "tp2"
    return cols
def _num(s):
    s = s.strip().replace("\xa0", "")
    if s in ("", "-", "--"): return None
    if ":" in s: return _mins(s)
    s = s.rstrip("+-") if re.fullmatch(r"\d+[+-]", s) else s
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None
def _clean_name(s):
    s = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", s)
    s = s.replace("'''", "").replace("''", "")
    s = re.sub(r"^\s*\*+\s*|\s*\*+\s*$", "", s)
    return re.sub(r"\s+", " ", s).strip(" .")
def parse_grid(rows, team_hint=None):
    """rows: list of list[str]. Returns blocks (dicts with team label, rows)."""
    blocks = []; cols = None; cur = None; team = team_hint
    for r in rows:
        cells = [c.strip() for c in r]
        nonempty = [c for c in cells if c]
        if not nonempty: continue
        joined = " ".join(nonempty)
        mbs = re.search(r"(?i)box score\s*(.*)$", joined)
        if mbs:
            team = mbs.group(1).strip() or team; continue
        if len(nonempty) <= 2 and re.search(r"(?i)team|usa|world|east|west|visitor|home|white|black|red|gray|blue|silver|national|select", joined) and not re.search(r"(?i)totals?", joined) and not re.search(r"\d{2,}", joined):
            team = joined; continue
        up = [re.sub(r"\s+", "", c.upper()) for c in cells]
        if ("NAME" in up or "PLAYER" in up) and any(x in up for x in ("PTS", "TP", "POINTS")):
            cols = _hdr_map(cells); cur = {"team": team, "rows": [], "cols": cols}; blocks.append(cur); continue
        if cols is None or cur is None: continue
        q0 = nonempty[0].replace("'", "").replace("*", "")
        if re.match(r"(?i)^(totals?|team|percentages?|dead)", q0) or re.match(r"(?i)^totals?", joined.replace("'", "")):
            if re.match(r"(?i)^totals?", joined.replace("'", "")): cur = None
            continue
        if len(cells) < len(cols) - 3: continue
        d = {}; ok = True
        for k, v in zip(cols, cells):
            if k is None: continue
            if k == "name": d["name"] = _clean_name(v); d["starter"] = int("*" in v)
            elif k == "num": d["num"] = v
            elif k == "pos": pass
            elif k in ("fg2", "tp2", "ft2"):
                m = re.fullmatch(r"\s*(\d+)\s*[-/]\s*(\d+)\s*", v)
                if not m: ok = False; break
                a = {"fg2": ("fgm", "fga"), "tp2": ("tpm", "tpa"), "ft2": ("ftm", "fta")}[k]
                d[a[0]], d[a[1]] = int(m.group(1)), int(m.group(2))
            else:
                n = _num(v)
                if n is None: continue
                d[k] = int(n) if k != "min" else n
        if not ok or not d.get("name") or "pts" not in d or "fgm" not in d: continue
        if "reb" not in d and "oreb" in d and "dreb" in d: d["reb"] = d["oreb"] + d["dreb"]
        d["pts_ok"] = int(d["pts"] == 2 * d["fgm"] + d.get("tpm", 0) + d.get("ftm", 0))
        cur["rows"].append(d)
    return blocks

# ---------------------------------------------------------------- 2022+ format (NO. Name Min FG 3P FT OR DR TOT PF FD TP AS TO ST BS BA +/-)
ROW_D = re.compile(r"^\s*(?P<num>\d{1,2})\s+(?P<name>[A-Za-z][A-Za-z'\.\-, ]+?)\s+(?P<min>\d{1,2}:\d{2})\s+(?P<fg>\d+-\d+)\s+(?P<tp>\d+-\d+)\s+(?P<ft>\d+-\d+)\s+(?P<rest>(?:-?\d+\s*){10,12})$")
def parse_format_d(lines):
    blocks = []; cur = None
    for ln in lines:
        if re.match(r"^\s*(East|West|[A-Z][A-Za-z]+)\s*-\s*\d+\s*$", ln) and re.search(r"-\s*\d{2,3}", ln): cur = {"team": ln.strip(), "rows": [], "cols": "D"}; blocks.append(cur); continue
        m = ROW_D.match(ln)
        if not m: continue
        v = [int(x) for x in m.group("rest").split()]
        # OR DR TOT PF FD TP AS TO ST BS BA [+/-]
        if len(v) < 10: continue
        if cur is None: cur = {"team": None, "rows": [], "cols": "D"}; blocks.append(cur)
        r = {"name": m.group("name").strip(), "num": m.group("num"), "min": _mins(m.group("min"))}
        r["fgm"], r["fga"] = _pair(m.group("fg")); r["tpm"], r["tpa"] = _pair(m.group("tp")); r["ftm"], r["fta"] = _pair(m.group("ft"))
        r["oreb"], r["dreb"], r["reb"], r["pf"], _fd, r["pts"], r["ast"], r["tov"], r["stl"], r["blk"] = v[:10]
        r["pts_ok"] = int(r["pts"] == 2 * r["fgm"] + r["tpm"] + r["ftm"])
        cur["rows"].append(r)
    return blocks

# ---------------------------------------------------------------- JBC 2008 style: NO PLAYER P FGM FGA 3M 3A FTM FTA OFF DEF TOT PF TP A TO BK S MIN
ROW_E = re.compile(r"^\s*(?P<num>\d{1,2})\s+(?P<name>[A-Za-z][A-Za-z'\.\-]*(?:[ ,]+[A-Za-z'\.\-]+)*?)\s+(?:(?P<pos>[FGC*])\s+)?(?P<rest>(?:\d+\s+){14,16}\d+[+-]?)\s*$")
def parse_format_e(lines):
    blocks = []; cur = None
    for ln in lines:
        if re.match(r"^\s*(VISITOR|HOME)", ln, re.I): cur = {"team": ln.strip(), "rows": [], "cols": "E"}; blocks.append(cur); continue
        m = ROW_E.match(ln)
        if not m: continue
        v = [int(x.rstrip("+-")) for x in m.group("rest").split()]
        if len(v) != 17 - 0 and len(v) not in (16, 17): continue
        # fgm fga tpm tpa ftm fta oreb dreb reb pf pts ast tov blk stl min
        if len(v) == 16:
            fgm, fga, tpm, tpa, ftm, fta, oreb, dreb, reb, pf, pts, ast, tov, blk, stl, mn = v
        else: continue
        if cur is None: cur = {"team": None, "rows": [], "cols": "E"}; blocks.append(cur)
        r = dict(name=m.group("name").strip(" ,"), num=m.group("num"), fgm=fgm, fga=fga, tpm=tpm, tpa=tpa, ftm=ftm, fta=fta, oreb=oreb, dreb=dreb, reb=reb,
                 pf=pf, pts=pts, ast=ast, tov=tov, blk=blk, stl=stl, min=mn)
        r["pts_ok"] = int(pts == 2 * fgm + tpm + ftm)
        cur["rows"].append(r)
    return blocks


def html_to_grid(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", "", h)
    h = re.sub(r"(?i)</t[dh]\s*>", "\x01", h)
    h = re.sub(r"(?i)</tr\s*>", "\x02", h)
    h = re.sub(r"(?i)</table\s*>", "\x02", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h).replace("\xa0", " ")
    rows = []
    for r in h.split("\x02"):
        cells = [re.sub(r"\s+", " ", c).strip() for c in r.split("\x01")]
        if any(cells): rows.append(cells)
    return rows

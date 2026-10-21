#!/usr/bin/env python3
"""Pathway block builder (Task 2). Offline: reads only files on disk (plus novel/pathway/raw/predraft from fetch_prerev.py).
Inputs : coverage_audit.csv (targets), wiki_raw/prerev_*.json + raw/predraft/*.json (pre-draft revisions), wiki_raw/attn_*.json (career_rows of the
         CURRENT article, post-draft fetch), raw/E{y}_trad|adv.json, raw/U{y}_trad|adv.json (EuroLeague / EuroCup exports), gl_test.json (G League 2019-20),
         age_verified_wiki.csv, identity/tabular_names.csv, novel/euroleague/features.csv (cross-check only).
Outputs: features.csv, provenance.csv, unmatched.csv, build_stats.json (all pid-keyed; names never leave the identity join)."""
import os, re, json, glob, math, unicodedata, datetime as dt, collections, sys
import pandas as pd
D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
P = os.path.join(D, "novel/pathway")
sys.path.insert(0, P)
import pwparse

CUT = {2007:"2007-06-28",2008:"2008-06-26",2009:"2009-06-25",2010:"2010-06-24",2011:"2011-06-23",2012:"2012-06-28",2013:"2013-06-27",2014:"2014-06-26",2015:"2015-06-25",2016:"2016-06-23",2017:"2017-06-22",2018:"2018-06-21",2019:"2019-06-20",2020:"2020-11-18",2021:"2021-07-29",2022:"2022-06-23",2023:"2023-06-22",2024:"2024-06-26",2025:"2025-06-25"}
LEAGUE_NAMES = {1:"EuroLeague",2:"EuroCup",3:"ACB",4:"LNB Pro A",5:"NBL Australia",6:"G League",7:"OTE",8:"other top European",9:"other"}

def norm_name(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().replace(".", "")
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# ---------------------------------------------------------------- targets
aud = pd.read_csv(f"{P}/coverage_audit.csv")
aud["underfilled"] = (~((aud.has_impact == 1) & (aud.has_usg == 1) & (aud.has_ts == 1) & (aud.has_gp == 1) & (aud.has_minutes == 1))).astype(int)
names = pd.read_csv(f"{D}/identity/tabular_names.csv").set_index("pid").player_name.to_dict()
bd_ver = {r.pid: dt.date.fromisoformat(r.birth_date) for r in pd.read_csv(f"{D}/age_verified_wiki.csv").itertuples()}

# ---------------------------------------------------------------- wiki helpers
FRENCH = re.compile(r"asvel|villeurbanne|metropolitans|levallois|limoges|nanterre|strasbourg|\bsig\b|monaco|cholet|gravelines|le mans|dijon|j\.?d\.?a|pau|orthez|chalon|roanne|orl[eé]ans|boulogne|bourg|paris|antibes|fos|rouen|poitiers|nancy|vichy|le portel|ch[aâ]lons|hy[eè]res|[eé]vreux|lyon|bordeaux|saint-quentin|angers|aix|champagne|saint-vallier|hermine|nantes|brest|blois|lorient|quimper|denain|vitr|toulouse|clermont|lille|saint-chamond|souffelweyersheim|charleville|bourgoin|besan|rueil|la rochelle|illkirch|gries|pontarlier", re.I)
AUS = re.compile(r"adelaide|illawarra|perth|sydney|melbourne|cairns|brisbane|new zealand|breakers|tasmania|wollongong|townsville|hawks|36ers|wildcats|taipans|bullets|jackjumpers|south east", re.I)
CZECH = re.compile(r"praha|nymburk|d[eě][cč][ií]n|opava|pardubice|brno|ostrava|kol[ií]n|olomouc|svitavy|\bcez\b|ussk", re.I)
EXC_NATL = re.compile(r"national team|youth|\bu ?1\d\b|\bu ?2\d\b|under-?\d\d|junior|eurobasket|world cup|olympic|americup|afrobasket|universiade|international career|showcase|hoop summit|all-star|academy|qualif", re.I)
COLLEGE = re.compile(r"college|ncaa|collegiate|universit|junior college|\bjuco\b|naia|prep|high school", re.I)
GENERIC = {"regular season", "statistics", "career statistics", "domestic leagues", "domestic leagues stats", "domestic leagues and other leagues", "stats", "europe", "european domestic club competitions", "pan european club competitions", "career"}
LEAGUE_RULES = [  # (code, regex on label)   first match wins
    (1, r"euro ?league|euroleague"),
    (2, r"euro ?cup"),
    (3, r"\bacb\b|liga acb"),
    (4, r"^(lnb )?pro ?a$|lnb pro a|lnb [eé]lite|betclic|pro a statistics|^pro a"),
    (6, r"g league|d-league|nbdl|ignite|developmental"),
    (7, r"overtime elite|\bote\b"),
    (8, r"^lba$|lega basket|serie a$|legabasket|heba|\bgbl\b|^a-?1|tbsl|^bsl|^bbl|basketball bundesliga|bundesliga|\baba\b|adriatic|\bkls\b|premijer|ligat|ibpl|\bipl\b|vtb|rpbl|superleague|^lkl|\bblb\b|1\. ?skl|liga bih|yuba|serbian league|\bkml\b|baltic|basketball champions|fiba champions|champions league|europe cup|euro ?challenge|korisliiga|bnxt"),
]
def league_code(label, team):
    lab = label.lower().strip().strip("|[] ").strip()
    tm = team or ""
    if lab == "lnb" or lab == "lnb-s":   # Argentine LNB vs French LNB: resolve by club
        return 4 if FRENCH.search(tm) else 9
    if lab == "nbl":
        if AUS.search(tm): return 5
        if CZECH.search(tm): return 8
        return 5  # bare 'NBL' section heading in Wikipedia player articles = Australian NBL
    if lab in ("pro a", "proa", "pro a statistics") and not FRENCH.search(tm) and lab == "proa": return 9  # German second tier 'ProA'
    for code, rx in LEAGUE_RULES:
        if re.search(rx, lab):
            if code == 4 and lab.startswith("pro a") and not FRENCH.search(tm) and not re.search(r"lnb", lab): return 4  # 'Pro A' (with space) is the French top flight in these tables
            return code
    if re.search(r"ignite|g league", tm.lower()): return 6
    if re.search(r"overtime elite|city reapers|cold hearts|yrv|team elite|\bote\b", tm.lower()): return 7
    return 9

def classify_wiki(r):
    """-> (keep: bool, reason_or_code, label)"""
    sec = r.get("section", "") or ""; lg = r.get("league", "") or ""; tm = r.get("team", "") or ""
    secl = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", sec).strip().lower()
    lg = lg.strip("| ").strip()
    if re.search(r"playoff", secl + " " + lg.lower()): return False, "playoffs", sec
    if re.fullmatch(r"[\d.]+", lg) : return False, "misparsed_columns", sec
    if secl in ("nba", "nba regular season", "nba statistics", "nba career statistics") : return False, "nba", sec
    if re.search(r"college|ncaa|collegiate", secl) : return False, "college", sec
    if EXC_NATL.search(secl + " " + lg + " " + tm): return False, "national_youth_or_academy", sec
    label = lg if lg else sec
    if (not lg) and secl in GENERIC: return False, "ambiguous_section", sec
    if lg and secl in ("regular season",) and re.search(r"^nba$", lg.lower()): return False, "nba", sec
    if COLLEGE.search(tm) and not lg: return False, "college", sec
    return True, league_code(label, tm), label

def pct(v):
    if v is None: return None
    return v / 100.0 if v > 1.5 else v

def num(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)

def wiki_to_records(rows, dy, src, fname, stats):
    out = []
    for r in rows:
        if r["end"] > dy:
            stats["post_draft_season"] += 1; continue
        keep, code, label = classify_wiki(r)
        if not keep:
            stats["excl_" + code] += 1; continue
        gp, mpg = num(r.get("gp")), num(r.get("mpg"))
        if not gp or gp <= 0 or gp > 120 or (mpg is not None and (mpg <= 0 or mpg > 48)) or (r.get("ppg") or 0) > 60 or (r.get("rpg") or 0) > 25:
            stats["excl_implausible"] += 1; continue
        out.append(dict(src=src, file=fname, season_end=r["end"], league=code, label=label, team=r.get("team", ""), gp=gp, mpg=mpg,
                        pts=num(r.get("ppg")), reb=num(r.get("rpg")), ast=num(r.get("apg")), stl=num(r.get("spg")), blk=num(r.get("bpg")),
                        ft_pct=pct(num(r.get("ft%"))), fg3_pct=pct(num(r.get("3p%"))), detail=None))
    return out

# ---------------------------------------------------------------- exports
def pnum(s):
    if s is None: return None
    if isinstance(s, (int, float)): return float(s)
    m = re.search(r"-?\d+\.?\d*", str(s)); return float(m.group(0)) if m else None

EXP = collections.defaultdict(list)   # norm name -> rows
for comp, lcode in (("E", 1), ("U", 2)):
    for fp in sorted(glob.glob(f"{D}/raw/{comp}20*_trad.json")):
        y = int(re.search(r"[EU](\d{4})_trad", fp).group(1))
        adv = {}
        try:
            adv = {p["player"]["code"]: p for p in json.load(open(fp.replace("_trad", "_adv")))["players"]}
        except Exception: pass
        for p in json.load(open(fp))["players"]:
            nm = p["player"]["name"]
            if "," in nm:
                sur, first = [x.strip() for x in nm.split(",", 1)]; nm = f"{first} {sur}"
            a = adv.get(p["player"]["code"], {})
            EXP[norm_name(nm)].append(dict(src=2, file=os.path.basename(fp), comp=comp, league=lcode, season_start=y, season_end=y + 1, code=p["player"]["code"],
                                          age=p["player"].get("age"), team=p["player"]["team"]["name"], gp=p["gamesPlayed"], mpg=p["minutesPlayed"],
                                          pts=p["pointsScored"], p2m=p["twoPointersMade"], p2a=p["twoPointersAttempted"], p3m=p["threePointersMade"], p3a=p["threePointersAttempted"],
                                          ftm=p["freeThrowsMade"], fta=p["freeThrowsAttempted"], reb=p["totalRebounds"], ast=p["assists"], stl=p["steals"], blk=p["blocks"], tov=p["turnovers"],
                                          adv_ts=pnum(a.get("trueShootingPercentage"))))
GL = collections.defaultdict(list)
glj = json.load(open(f"{D}/gl_test.json"))
glh = glj["resultSets"][0]["headers"]
for row in glj["resultSets"][0]["rowSet"]:
    r = dict(zip(glh, row))
    GL[norm_name(r["PLAYER_NAME"])].append(r)
GL_SEASON_END = int(glj["parameters"]["Season"][:4]) + 1

def export_record(e):
    g = e["gp"]
    return dict(src=2, file=e["file"], season_end=e["season_end"], league=e["league"], label=("EuroLeague" if e["comp"] == "E" else "EuroCup"), team=e["team"], gp=g, mpg=e["mpg"],
                pts=e["pts"], reb=e["reb"], ast=e["ast"], stl=e["stl"], blk=e["blk"], ft_pct=None, fg3_pct=None,
                detail=dict(p2m=e["p2m"], p2a=e["p2a"], p3m=e["p3m"], p3a=e["p3a"], ftm=e["ftm"], fta=e["fta"], tov=e["tov"]), adv_ts=e["adv_ts"])

def gl_record(r):
    g = float(r["GP"]); mn = float(r["MIN"])
    if g <= 0 or mn <= 0: return None
    pg = lambda k: float(r[k]) / g
    return dict(src=3, file="gl_test.json", season_end=GL_SEASON_END, league=6, label="G League", team=r["TEAM_ABBREVIATION"], gp=g, mpg=mn / g,
                pts=pg("PTS"), reb=pg("REB"), ast=pg("AST"), stl=pg("STL"), blk=pg("BLK"), ft_pct=None, fg3_pct=None,
                detail=dict(p2m=pg("FGM") - pg("FG3M"), p2a=pg("FGA") - pg("FG3A"), p3m=pg("FG3M"), p3a=pg("FG3A"), ftm=pg("FTM"), fta=pg("FTA"), tov=pg("TOV")))


# ---------------------------------------------------------------- Task 3: official pages captured by the Wayback Machine (pre-cutoff captures only)
import html as _html
def _cells(row_html):
    return [_html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c))).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S)]
def _nums(cells):
    out = []
    for c in cells:
        try: out.append(float(c))
        except ValueError: out.append(None)
    return out
def parse_ote(raw, dy):
    """Overtime Elite player career page. Column names are read from each table's <thead> (pts ast reb stl blk dnk min 2pm 2pa 2p% 3pm 3pa 3p% fgm fga fg% ftm fta ft% +/- pf to).
    The regular-season table is the one whose 'Average' points equal the page's '<YYYY>-<YYYY> Season Points Per game' summary figure (playoff / preseason tables are skipped).
    GP = number of game rows, accepted only if the mean of the listed games reproduces the Average row (pts within 0.25, min within 0.5)."""
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    txt = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
    ms = re.search(r"(\d{4})-(\d{4}) Season Points Per game ([\d.]+)", txt)
    if not ms: return None
    se, season_pts = int(ms.group(2)), float(ms.group(3))
    for tb in re.findall(r"<table.*?</table>", t, re.S):
        th = re.findall(r"<thead>.*?</thead>", tb, re.S)
        if not th: continue
        hdr = [h.strip().lower() for h in re.findall(r'<span class="desktop-only">(.*?)</span>', th[0])]
        ix = {h: i for i, h in enumerate(hdr)}
        need = ["pts", "ast", "reb", "stl", "blk", "min", "2pm", "2pa", "3pm", "3pa", "ftm", "fta", "to"]
        if any(k not in ix for k in need): continue
        games, avg = [], None
        for tr in re.findall(r"<tr[^>]*>.*?</tr>", tb, re.S):
            first = _cells(tr)[:1]
            vals = _nums(re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S) and [_html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)])
            if len(vals) < len(hdr) or None in [vals[ix[k]] for k in need]: continue
            if 'class="Average"' in tr: avg = vals
            elif re.search(r'class="Date">\d{1,2}/\d{1,2}/\d{4}<', tr): games.append(vals)
        if not avg or abs(avg[ix["pts"]] - season_pts) > 0.051: continue
        n = len(games)
        ok_n = n > 0 and abs(sum(g[ix["pts"]] for g in games) / n - avg[ix["pts"]]) < 0.25 and abs(sum(g[ix["min"]] for g in games) / n - avg[ix["min"]]) < 0.5
        g = lambda k: avg[ix[k]]
        rec = dict(src=5, file="", season_end=se, league=7, label="Overtime Elite", team="", gp=float(n) if ok_n else None, mpg=g("min"), pts=g("pts"), reb=g("reb"), ast=g("ast"), stl=g("stl"), blk=g("blk"),
                   ft_pct=None, fg3_pct=None, detail=dict(p2m=g("2pm"), p2a=g("2pa"), p3m=g("3pm"), p3a=g("3pa"), ftm=g("ftm"), fta=g("fta"), tov=g("to")))
        return [rec] if se <= dy else []
    return None

def parse_nbl(raw, dy):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    s = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
    i = s.find("Full Career")
    if i < 0: return None
    seg = s[i:i + 900]
    seg = seg.split("Latest News")[0]
    has_gp = bool(re.search(r"Team GP Mins", seg)) or " GP " in seg[:80]
    out = []
    for m in re.finditer(r"(\d{4})-(\d{4})((?:\s+-?\d+(?:\.\d+)?(?![\d-])){10,12})", seg):
        v = [float(x) for x in m.group(3).split()]
        if has_gp and len(v) >= 11: gp, v = v[0], v[1:]
        elif len(v) == 10: gp = None
        else: continue
        se = int(m.group(2))
        if se > dy or not v[0] or v[0] <= 0: continue
        mins, fg, ft, reb, ast, blk, stl, to, pf, pts = v[:10]
        out.append(dict(src=5, file="", season_end=se, league=5, label="NBL", team="", gp=gp, mpg=mins, pts=pts, reb=reb, ast=ast, stl=stl, blk=blk, ft_pct=ft / 100.0, fg3_pct=None,
                        detail=None, tov_pg=to))
    return out
WB = {}
_wl = f"{P}/wayback_log.csv"
if os.path.exists(_wl):
    for r in pd.read_csv(_wl).itertuples():
        if r.result in ("fetched", "cached") and r.site in ("ote", "nbl"): WB.setdefault(r.pid, []).append(r)

# ---------------------------------------------------------------- birthdates (verified csv, else pre-draft wiki infobox)
def infobox_bd(wt):
    m = re.search(r"birth[ _-]?date[^|}]*\|\s*(?:(?:df|mf)\s*=\s*\w+\s*\|\s*)*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})", wt or "", re.I)
    if m:
        try: return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError: return None
    m = re.search(r"birth[ _-]?date[^|}]*\|\s*(?:(?:df|mf)\s*=\s*\w+\s*\|\s*)*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", wt or "", re.I)
    if m:
        try: return dt.datetime.strptime(f"{m.group(1)} {m.group(2)[:3]} {m.group(3)}", "%d %b %Y").date()
        except ValueError: return None
    m = re.search(r"birth[ _-]?date[^|}]*\|\s*(?:(?:df|mf)\s*=\s*\w+\s*\|\s*)*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", wt or "", re.I)
    if m:
        try: return dt.datetime.strptime(f"{m.group(1)[:3]} {m.group(2)} {m.group(3)}", "%b %d %Y").date()
        except ValueError: return None
    return None

def load_prerev(pid):
    for fp in (f"{D}/wiki_raw/prerev_{pid}.json", f"{P}/raw/predraft/{pid}.json"):
        if os.path.exists(fp):
            j = json.load(open(fp)); j["_file"] = os.path.relpath(fp, D)
            if j.get("status") == "ok" or "status" in j: return j
    return None

# ---------------------------------------------------------------- aggregation
def combine(recs):
    """combine records of the same (season, league, src) by games: totals -> per game"""
    if len(recs) == 1: return recs[0]
    if any(r["gp"] is None for r in recs): return max(recs, key=lambda r: r["mpg"] or 0)
    gp = sum(r["gp"] for r in recs)
    out = dict(recs[0]); out["gp"] = gp
    if all(r["mpg"] for r in recs): out["mpg"] = sum(r["gp"] * r["mpg"] for r in recs) / gp
    else: out["mpg"] = None
    for k in ("pts", "reb", "ast", "stl", "blk"):
        out[k] = sum(r["gp"] * r[k] for r in recs) / gp if all(r[k] is not None for r in recs) else None
    out["ft_pct"] = out["fg3_pct"] = None
    if all(r.get("detail") for r in recs):
        out["detail"] = {k: sum(r["gp"] * r["detail"][k] for r in recs) / gp for k in recs[0]["detail"]}
    else: out["detail"] = None
    out["team"] = "/".join(r["team"] for r in recs); out["n_merged"] = len(recs)
    return out

def features_from(rec, bd, dy):
    f = {}
    g, m = rec["gp"], rec["mpg"]
    if g is not None: f["pw_gp"] = g
    if m:
        f["pw_mpg"] = m; s = 36.0 / m
        for k in ("pts", "reb", "ast", "stl", "blk"):
            if rec[k] is not None: f[f"pw_{k}36"] = rec[k] * s
        d = rec.get("detail")
        if d:
            fga = d["p2a"] + d["p3a"]; fgm = d["p2m"] + d["p3m"]; fta, ftm = d["fta"], d["ftm"]; tov = d["tov"]
            pts = rec["pts"]
            f["pw_tov36"] = tov * s
            if fga + 0.44 * fta > 0: f["pw_ts_pct"] = pts / (2 * (fga + 0.44 * fta))
            if fga > 0:
                f["pw_efg_pct"] = (fgm + 0.5 * d["p3m"]) / fga; f["pw_fg3ar"] = d["p3a"] / fga; f["pw_ftar"] = fta / fga
            if fta > 0: f["pw_ft_pct"] = ftm / fta
            if d["p3a"] > 0: f["pw_fg3_pct"] = d["p3m"] / d["p3a"]
            f["pw_usg_proxy"] = (fga + 0.44 * fta + tov) * s
            if None not in (rec["reb"], rec["ast"], rec["stl"], rec["blk"]):
                f["pw_box_impact"] = (pts + 0.7 * rec["reb"] + 0.7 * rec["ast"] + 1.5 * rec["stl"] + 1.5 * rec["blk"] - tov - 0.7 * (fga - fgm) - 0.35 * (fta - ftm)) * s
        else:
            if rec.get("tov_pg") is not None: f["pw_tov36"] = rec["tov_pg"] * s
            if rec["ft_pct"] is not None: f["pw_ft_pct"] = rec["ft_pct"]
            if rec["fg3_pct"] is not None: f["pw_fg3_pct"] = rec["fg3_pct"]
        if None not in (rec["pts"], rec["reb"], rec["ast"], rec["stl"], rec["blk"]):
            f["pw_box_lite"] = (rec["pts"] + 0.7 * rec["reb"] + 0.7 * rec["ast"] + 1.5 * rec["stl"] + 1.5 * rec["blk"]) * s
    if bd:
        f["pw_age_at_season"] = (dt.date(rec["season_end"], 2, 1) - bd).days / 365.25
    f["pw_league_code"] = rec["league"]
    f["pw_source"] = rec["src"]
    f["pw_season_gap"] = dy - rec["season_end"]
    return f

MAX_GAP = 3   # seasons between the last table season and the draft year; older records are dropped as not representative
SRC_RANK = {2: 0, 3: 1, 1: 2, 5: 3, 4: 4}
FEATS = ["pw_gp","pw_mpg","pw_pts36","pw_reb36","pw_ast36","pw_stl36","pw_blk36","pw_tov36","pw_ts_pct","pw_efg_pct","pw_fg3ar","pw_ftar","pw_ft_pct","pw_fg3_pct","pw_usg_proxy","pw_box_impact","pw_age_at_season","pw_league_code","pw_source","pw_box_lite","pw_season_gap"]

# ---------------------------------------------------------------- main loop
feat_rows, prov_rows, unm_rows = [], [], []
gstats = collections.Counter()
for t in aud.itertuples():
    pid, dy = t.pid, int(t.draft_year); nm = norm_name(names[pid])
    st = collections.Counter(); cands = []; notes = []
    # --- pre-draft revision
    pr = load_prerev(pid); wiki_status = "no_cache"; rev_ts = ""; prerev_ok = False; bd = bd_ver.get(pid); age_src = 1 if bd else 0
    ident_ok = None
    if pr:
        wiki_status = pr.get("status", "?")
        if pr.get("status") == "ok" and pr.get("wikitext"):
            wt = pr["wikitext"]; rev_ts = pr.get("rev_ts", "")
            ibd = infobox_bd(wt)
            if bd and ibd and abs((ibd - bd).days) > 400:
                wiki_status = "identity_mismatch"; notes.append("prerev_birthdate_mismatch")
            else:
                prerev_ok = True
                if ibd and ibd is not None:
                    ident_ok = 1 if bd else None
                    if not bd: bd = ibd; age_src = 2
                rows = pwparse.rows_from(wt)
                st["prerev_rows"] = len(rows)
                cands += wiki_to_records(rows, dy, 1, pr["_file"], st)
                for c in cands: c["rev_ts"] = rev_ts
    # --- current article career_rows (post-draft fetch; restricted to seasons ending <= draft year)
    ap = f"{D}/wiki_raw/attn_{pid}.json"; attn_title_ok = None
    if os.path.exists(ap):
        aj = json.load(open(ap))
        rows = aj.get("career_rows") or []
        st["attn_rows"] = len(rows)
        if pr and pr.get("title") and aj.get("title"): attn_title_ok = (pr.get("title") == aj.get("title") or pr.get("resolved_title") == aj.get("title"))
        if wiki_status != "identity_mismatch" and attn_title_ok is not False:
            c4 = wiki_to_records(rows, dy, 4, f"wiki_raw/attn_{pid}.json", st)
            cands += c4
        elif rows: notes.append("attn_title_differs_from_prerev_title")
    # --- euroleague / eurocup exports
    amb = False
    ref_age = None
    ex = EXP.get(nm, [])
    ex = [e for e in ex if dy - 8 <= e["season_end"] <= dy]
    if ex:
        ok = []
        for e in ex:
            if e["age"] is None: continue
            if bd:
                a = (dt.date(e["season_start"], 10, 1) - bd).days / 365.25
                if abs(a - e["age"]) > 1.6: continue
            elif not (16 <= e["age"] <= 29): continue
            ok.append(e)
        codes = {e["code"] for e in ok}
        if len(codes) > 1: amb = True; notes.append("export_ambiguous_name")
        elif ok:
            if not bd: notes.append("export_age_unchecked")
            for e in ok: cands.append(export_record(e))
        else: notes.append("export_name_found_age_rejected")
    gl = GL.get(nm, []) if dy >= GL_SEASON_END else []
    if gl:
        okg = []
        for r in gl:
            if bd:
                a = (dt.date(GL_SEASON_END - 1, 12, 1) - bd).days / 365.25
                if abs(a - float(r["AGE"])) > 1.6: continue
            else:
                continue   # no birthdate: G League name match not accepted (common names, no independent age check)
            okg.append(r)
        ids = {r["PLAYER_ID"] for r in okg}
        if len(ids) > 1: notes.append("gleague_ambiguous_name")
        elif okg:
            gr = gl_record(okg[0])
            if gr: cands.append(gr)
        else: notes.append("gleague_name_found_age_rejected_or_no_birthdate")

    # --- Wayback captures of official pages (Task 3)
    for w in WB.get(pid, []):
        fpw = f"{P}/raw/wayback/{pid}_{w.site}.html"
        if not os.path.exists(fpw): continue
        raw = open(fpw, errors="replace").read()
        recs = (parse_ote if w.site == "ote" else parse_nbl)(raw, dy)
        if recs is None: notes.append(f"wayback_{w.site}_unparsed"); continue
        for rr in recs:
            rr["file"] = f"raw/wayback/{pid}_{w.site}.html@{w.capture}"; cands.append(rr)
    # --- select record
    if not cands:
        reason = []
        reason.append(f"wiki_prerev={wiki_status}")
        reason.append(f"prerev_table_rows={st['prerev_rows']}; current_article_rows={st['attn_rows']}")
        ex_ = {k: v for k, v in st.items() if k.startswith("excl_") or k == "post_draft_season"}
        if ex_: reason.append("dropped:" + ",".join(f"{k}={v}" for k, v in sorted(ex_.items())))
        if notes: reason.append("notes:" + ",".join(notes))
        unm_rows.append(dict(pid=pid, draft_year=dy, path=t.path, n_intl_filled=t.n_intl_filled, underfilled=t.underfilled, status="no_record", reason="no pre-draft pro season in any cache; " + "; ".join(reason)))
        gstats["no_record"] += 1
        continue
    groups = collections.defaultdict(list)
    for c in cands: groups[(c["season_end"], c["league"], c["src"])].append(c)
    merged = {k: combine(v) for k, v in groups.items()}
    # cross-source resolution for the same (season, league)
    byk = collections.defaultdict(list)
    for (se, lg, sr), rec in merged.items(): byk[(se, lg)].append(rec)
    final = []
    for (se, lg), recs in byk.items():
        recs.sort(key=lambda r: SRC_RANK[r["src"]])
        best = dict(recs[0])
        if len(recs) > 1 and recs[0]["gp"] is not None and recs[1]["gp"] is not None and abs(recs[0]["gp"] - recs[1]["gp"]) > 1: best["conflict"] = 1
        best["n_sources"] = len(recs)
        final.append(best)
    stale = [r for r in final if dy - r["season_end"] > MAX_GAP]
    final = [r for r in final if dy - r["season_end"] <= MAX_GAP]
    if not final:
        unm_rows.append(dict(pid=pid, draft_year=dy, path=t.path, n_intl_filled=t.n_intl_filled, underfilled=t.underfilled, status="no_record",
                             reason=f"only stale seasons found (latest season ends {max(r['season_end'] for r in stale)}, more than {MAX_GAP} seasons before the draft; sources {sorted({r['src'] for r in stale})})"))
        gstats["stale_only"] += 1
        continue
    last_se = max(r["season_end"] for r in final)
    pool = [r for r in final if r["season_end"] == last_se]
    pool.sort(key=lambda r: (-((r["gp"] or 20) * (r["mpg"] or 0)), SRC_RANK[r["src"]]))
    rec = pool[0]
    f = features_from(rec, bd, dy)
    f["pid"] = pid
    feat_rows.append(f)
    prov_rows.append(dict(pid=pid, draft_year=dy, path=t.path, underfilled=t.underfilled, pw_source=rec["src"], source_file=rec["file"],
                          season_label=f"{last_se-1}-{str(last_se)[-2:]}", season_end=last_se, comp_label=str(rec["label"]).replace("|", "")[:40], league_code=rec["league"],
                          n_competitions_that_season=len(pool), n_seasons_available=len({r["season_end"] for r in final}), src_conflict=rec.get("conflict", 0),
                          wiki_prerev_status=wiki_status, wiki_prerev_rev_ts=rev_ts, age_src=age_src, notes=";".join(notes)))
    partial = "pw_usg_proxy" not in f
    if partial or "pw_age_at_season" not in f or f.get("pw_season_gap", 0) >= 2:
        why = []
        if partial: why.append("no FGA/FTA/TOV in source (wiki per-game table): ts/efg/fg3ar/ftar/tov36/usg_proxy/box_impact empty")
        if "pw_age_at_season" not in f: why.append("no birthdate")
        if f.get("pw_season_gap", 0) >= 2: why.append(f"stale: last table season is {f['pw_season_gap']} seasons before draft")
        unm_rows.append(dict(pid=pid, draft_year=dy, path=t.path, n_intl_filled=t.n_intl_filled, underfilled=t.underfilled, status="partial", reason="; ".join(why)))
    gstats[f"src{rec['src']}"] += 1

feat = pd.DataFrame(feat_rows)[["pid"] + FEATS]
feat = feat.sort_values("pid")
for c in FEATS:
    if c in ("pw_gp","pw_league_code","pw_source","pw_season_gap"): continue
    feat[c] = feat[c].round(4)
feat.to_csv(f"{P}/features.csv", index=False)
pd.DataFrame(prov_rows).sort_values("pid").to_csv(f"{P}/provenance.csv", index=False)
pd.DataFrame(unm_rows).sort_values(["status", "pid"]).to_csv(f"{P}/unmatched.csv", index=False)
json.dump(dict(gstats), open(f"{P}/build_stats.json", "w"))
print("features rows", len(feat), dict(gstats))

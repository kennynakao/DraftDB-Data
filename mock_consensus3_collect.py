"""Dated multi-publisher mock consensus, batch 3 (NEW publishers), draft years 2015-2026.
Per site: one Wayback CDX listing (cached), then per draft year the candidate captures dated in [draft-40d, draft date 22:00 UTC).
Candidates ranked by ('final' in URL, year in URL, timestamp); up to MAXFETCH fetched; each capture is validated:
  - >= 25 names of that draft class found in the page text (first-appearance order = rank)
  - Spearman(rank, actual pick) >= MINRHO (scrape sanity: mock draft, not a results/alphabetical page)
  - no results language ("was selected" / "selected by") within 200 chars of a class-member name or the draft year
  - draft year appears in the text; capture timestamp < draft date 22:00 UTC
Among valid candidates the best by ('final' in URL/title, ts) is kept. Names come from identity/tabular_names.csv.
Outputs: mock_consensus3_ranks.csv, mock_consensus3_report.md, mock_consensus3_unmatched.csv, mock_raw/consensus3/ cache.
Usage: python mock_consensus3_collect.py [--offline] [--minutes 45]
"""
import json, os, re, sys, time, csv, hashlib, unicodedata, subprocess, collections, datetime as dt
DATA = os.path.dirname(os.path.abspath(__file__))
RAW = f"{DATA}/mock_raw/consensus3"; os.makedirs(RAW, exist_ok=True)
UA = "DraftDB-research (student project; contact via github.com/kennynakao)"
OFFLINE = "--offline" in sys.argv
MINUTES = float(sys.argv[sys.argv.index("--minutes") + 1]) if "--minutes" in sys.argv else 45
T0 = time.time()
DRAFT = {2015:"2015-06-25",2016:"2016-06-23",2017:"2017-06-22",2018:"2018-06-21",2019:"2019-06-20",2020:"2020-11-18",2021:"2021-07-29",
         2022:"2022-06-23",2023:"2023-06-22",2024:"2024-06-26",2025:"2025-06-25",2026:"2026-06-24"}
MINNAMES = 25; MINRHO = 0.3; MAXFETCH = 4; WINDOW_DAYS = 40
# Wayback CDX filter scans are slow/504 on whole big domains, so big publishers are queried with narrow per-year URL prefixes
# (their known URL layouts); small publishers are queried once for the whole site. Entries: (pattern, matchType, scope) scope 'g'=global, 'y'=per-year window
def months(y):
    D = dt.datetime.strptime(DRAFT[y], "%Y-%m-%d"); L = D - dt.timedelta(days=WINDOW_DAYS); out = []
    while (L.year, L.month) <= (D.year, D.month):
        out.append((L.year, L.month)); L = (L.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
    return out
def pats(site, y):
    M = months(y)
    if site == "basketballnews": return [("basketballnews.com/*", "g")]
    if site == "rookiescale": return [("rookiescale.com/*", "g")]
    if site == "noceilings": return [("noceilings.com/*", "g")]
    if site == "bleacherreport":
        return [("bleacherreport.com/articles/*", "g")] + [(f"bleacherreport.com/articles/{d}*", "g") for d in (24, 25, 26, 27, 28, 29)] if y <= 2020 else [("bleacherreport.com/articles/*", "g")]
    if site == "si": return [(f"si.com/nba/{y}-nba-mock*", "y"), ("si.com/nba/nba-mock*", "y"), ("si.com/nba/mock-draft*", "y")] + [(f"si.com/nba/{yy}/{mm:02d}/*", "y") for yy, mm in M] + [(f"sportsillustrated.com/nba/{yy}/{mm:02d}/*", "y") for yy, mm in M if y <= 2018]
    if site == "yahoo": return [(f"sports.yahoo.com/{y}-nba-mock*", "y"), (f"sports.yahoo.com/nba-mock*", "y"), (f"sports.yahoo.com/final-nba-mock*", "y")]
    if site == "usatoday": return [(f"usatoday.com/story/sports/nba/{yy}/{mm:02d}/*", "y") for yy, mm in M] + [(f"ftw.usatoday.com/{yy}/{mm:02d}/*", "y") for yy, mm in M]
    if site == "nbcsports": return [(f"nba.nbcsports.com/{yy}/{mm:02d}/*", "y") for yy, mm in M] + [(f"nbcsports.com/nba/news/{y}-nba-mock*", "y"), ("nbcsports.com/nba/news/nba-mock*", "y")]
    if site == "foxsports": return [(f"foxsports.com/stories/nba/{y}-nba-mock*", "y"), ("foxsports.com/stories/nba/nba-mock*", "y"), (f"foxsports.com/stories/nba/{y}-nba-draft*", "y")]
    if site == "sbnation": return [(f"sbnation.com/nba/{yy}/{mm}/*", "y") for yy, mm in M]
    return []
SITES = ["basketballnews", "bleacherreport", "si", "yahoo", "usatoday", "nbcsports", "foxsports", "sbnation", "rookiescale", "noceilings"]
YEAR_ORDER = [2026,2025,2024,2023,2022,2021,2020,2019,2018,2017,2016,2015]
def log(*a): print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)

# ---------------- identity ----------------
def norm(s): return re.sub(r"\s+"," ",re.sub(r"[^a-z ]","",unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower().replace(".",""))).strip()
def strip_suffix(n): return re.sub(r"\s+"," ",re.sub(r"\b(jr|sr|ii|iii|iv)\b","",n)).strip()
uni = collections.defaultdict(dict); dups = []
for r in csv.DictReader(open(f"{DATA}/identity/tabular_names.csv")):
    y = int(float(r["draft_year"])); k = strip_suffix(norm(r["player_name"]))
    if k in uni[y]:
        dups.append((y, k, r["pid"], uni[y][k][0])); uni[y][k] = None   # ambiguous: drop, log
    elif k in uni[y] and uni[y][k] is None: dups.append((y, k, r["pid"], ""))
    else: uni[y][k] = (r["pid"], r.get("actual_pick", ""))
for y in uni: uni[y] = {k: v for k, v in uni[y].items() if v is not None and len(k.split()) >= 2}

# ---------------- polite fetching ----------------
_last = [0.0]
def curl(url, timeout):
    """one request, >=1.5s spacing; returns (http_code, body_bytes)"""
    wait = 1.5 - (time.time() - _last[0])
    if wait > 0: time.sleep(wait)
    tmp = f"{RAW}/.tmp_dl"
    p = subprocess.run(["curl", "-g", "-s", "--compressed", "-L", "-m", str(timeout), "-A", UA, "-o", tmp, "-w", "%{http_code}", url], capture_output=True, text=True)
    _last[0] = time.time()
    code = p.stdout.strip()[-3:] or "000"
    body = open(tmp, "rb").read() if os.path.exists(tmp) else b""
    if os.path.exists(tmp): os.remove(tmp)
    return code, body
import gzip
def read_cache(path):
    b = open(path, "rb").read()
    if b[:2] == b"\x1f\x8b":   # some Wayback id_ responses were cached gzip-compressed (before --compressed was added)
        try: b = gzip.decompress(b)
        except Exception: pass
    return b.decode("utf-8", "ignore")
fails = collections.Counter(); stopped = {}
try: stopped.update({k: v for k, v in json.load(open(f"{RAW}/run_state.json")).get("stopped", {}).items() if "HTTP 000" not in v})   # sites stopped by an earlier run stay stopped (rule: stop after 3 consecutive failures)
except Exception: pass
def get(site, url, cache, timeout, want_json=False):
    """cached GET with exponential backoff on 429/503/timeouts. Returns text or None. 3 consecutive failures stop the site."""
    if os.path.exists(cache) and os.path.getsize(cache) > 0 or os.path.exists(cache + ".empty"):
        return read_cache(cache) if os.path.exists(cache) else ""
    if OFFLINE or site in stopped: return None
    delay = 8
    for attempt in range(3):
        code, body = curl(url, timeout)
        txt = body.decode("utf-8", "ignore")
        bad = code in ("429", "503", "502", "504", "000") or "Temporarily Offline" in txt[:600] or (want_json and txt.lstrip().startswith("<"))
        if code == "404": fails[site] = 0; open(cache + ".empty", "w").close(); return ""   # not a site failure
        if not bad and code.startswith("2"):
            fails[site] = 0
            if not txt.strip(): open(cache + ".empty", "w").close(); return ""
            open(cache, "w").write(txt); return txt
        fails[site] += 1
        log(f"  {site}: request failed (code {code}), consecutive failures {fails[site]}: {url[:110]}")
        if fails[site] >= 3:
            stopped[site] = f"3 consecutive failures (last HTTP {code}) at {url[:100]}"; return None
        time.sleep(delay); delay *= 3
    return None

_cdx_mem = {}
def cdx_list(site, y):
    out = []; ok = True
    for pat, scope in pats(site, y):
        D = dt.datetime.strptime(DRAFT[y], "%Y-%m-%d")
        frm = "20150401" if scope == "g" else (D - dt.timedelta(days=WINDOW_DAYS)).strftime("%Y%m%d"); to = "20260624" if scope == "g" else D.strftime("%Y%m%d")
        key = hashlib.md5(f"{pat}|{frm}|{to}".encode()).hexdigest()[:10]
        if key not in _cdx_mem:
            u = f"https://web.archive.org/cdx/search/cdx?url={pat}&filter=original:.*mock.?.?.?draft.*&filter=statuscode:200&from={frm}&to={to}&output=json&fl=timestamp,original&limit=20000"
            legacy = f"{RAW}/cdx_{site}_0.json" if pat in ("basketballnews.com/*", "bleacherreport.com/articles/*") else f"{RAW}/cdx_{site}_{key}.json"
            if not os.path.exists(legacy) and pat == "bleacherreport.com/articles/*": legacy = f"{RAW}/cdx_{site}_{key}.json"
            txt = get(site, u, legacy, 400, want_json=True)
            if txt is None: _cdx_mem[key] = None
            else:
                rows = []   # tolerant parse: the CDX stream can be cut off mid-way (truncated listing); keep complete lines
                for ln in txt.splitlines():
                    ln = ln.strip().rstrip(",")
                    if ln.count('"') < 4: continue
                    try: v = json.loads("[" + ln.lstrip("[").rstrip("]") + "]")
                    except Exception: continue
                    if len(v) == 2 and str(v[0]).isdigit(): rows.append(v)
                _cdx_mem[key] = [(r[0], r[1]) for r in rows]
        if _cdx_mem[key] is None: ok = False
        else: out += _cdx_mem[key]
    return out, ok

# ---------------- page validation ----------------
def visible_text(html):
    h = re.sub(r"(?is)<(script|style|noscript|svg|head)\b.*?</\1>", " ", html)
    h = re.sub(r"<[^>]+>", " ", h); h = h.replace("&amp;", "&").replace("&#8217;", "'").replace("&nbsp;", " ")
    return h
def spearman(a, b):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
        while i < len(o):
            j = i
            while j+1 < len(o) and v[o[j+1]] == v[o[i]]: j += 1
            for k in range(i, j+1): r[o[k]] = (i+j)/2+1
            i = j+1
        return r
    ra, rb = rk(a), rk(b); n = len(a); ma, mb = sum(ra)/n, sum(rb)/n
    cov = sum((x-ma)*(y-mb) for x, y in zip(ra, rb)); va = sum((x-ma)**2 for x in ra); vb = sum((y-mb)**2 for y in rb)
    return cov/(va*vb)**0.5 if va > 0 and vb > 0 else None
def analyse(html, y):
    text = visible_text(html); tn = " " + norm(text) + " "
    pos = []
    for nm, (pid, pk) in uni[y].items():
        i = tn.find(" " + nm + " ")
        if i >= 0: pos.append((i, nm, pid, pk))
    pos.sort()
    picks = [(k, float(pk)) for k, (i, nm, pid, pk) in enumerate(pos, 1) if pk not in ("", "nan")]
    rho = spearman([p[0] for p in picks], [p[1] for p in picks]) if len(picks) >= 10 else None
    # results language near a class-member name or the draft year (works on lowercased accent-stripped raw text)
    low = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    leak = 0; names = list(uni[y].keys())
    for m in re.finditer(r"was selected|selected by", low):
        w = norm(low[max(0, m.start()-200):m.end()+200]); w = " " + w + " "
        if str(y) in low[max(0, m.start()-200):m.end()+200] or any(" "+nm+" " in w for nm in names): leak += 1
    title = re.search(r"(?is)<title[^>]*>(.*?)</title>", html); title = (title.group(1) if title else "").lower()
    return dict(pos=pos, picks=picks, rho=rho, leak=leak, has_year=str(y) in text, final_title=("final" in title))

# ---------------- main ----------------
def nkey(u): return re.sub(r"/+$", "", re.sub(r"[?#].*$", "", re.sub(r"^https?://(www\.)?", "", u.lower())))
rows_out = []; report = {}; attempts = []; unmatched = []
for (y, k, a, b) in dups: unmatched.append(dict(draft_year=y, site="", ts="", kind="ambiguous_class_name", pid=a, actual_pick="", note=f"normalized name '{k}' duplicated within class (also {b}); excluded from matching"))
def deadline_hit(): return (time.time() - T0) > MINUTES * 60
PRI = ["bleacherreport", "nbcsports", "yahoo", "si", "usatoday"]; REST = [x for x in SITES if x not in PRI]
Y_TEST = [2023, 2022, 2021, 2020, 2019]; Y_RECENT = [2024, 2025, 2026]; Y_OLD = [2018, 2017, 2016, 2015]
phases = [(Y_TEST, PRI), (Y_TEST, REST), (Y_RECENT, SITES), (Y_OLD, SITES)]   # priority: 2019-2023 for the five big publishers first
for ph, (years, sitelist) in enumerate(phases):
  for y in years:
    for site in sitelist:
            if (site, y) in report: continue
            if deadline_hit(): report[(site, y)] = "not run: time budget exhausted"; continue
            listing, lok = cdx_list(site, y)
            if not lok and not listing: report[(site, y)] = (f"site skipped: {stopped[site]}" if site in stopped else "CDX listing failed (HTTP error/timeout)"); continue
            if False: report[(site, y)] = "CDX listing failed (HTTP error/timeout)"; continue
            log(f"{site} {y}: {len(listing)} listing rows")
            D = dt.datetime.strptime(DRAFT[y], "%Y-%m-%d"); lo = (D - dt.timedelta(days=WINDOW_DAYS)).strftime("%Y%m%d000000"); hi = D.strftime("%Y%m%d") + "215959"
            best = {}
            for ts, orig in listing:
                if not (lo <= ts <= hi): continue
                lu = orig.lower()
                if not re.search(r"nba|basketball", lu) or re.search(r"nfl|nhl|mlb|wnba|mls|fantasy|football|hockey|baseball|women", lu): continue
                yrs = set(re.findall(r"(?<!\d)(20[12]\d)(?!\d)", lu))
                if yrs and str(y) not in yrs: continue
                kk = nkey(orig)
                if kk not in best or ts > best[kk][0]: best[kk] = (ts, orig)
            cands = sorted(best.values(), key=lambda t: ("final" in t[1].lower(), str(y) in t[1], t[0]), reverse=True)
            if not cands: report[(site, y)] = "no candidate capture in 40-day window (CDX)"; continue
            valid = []; why = []
            for ts, orig in cands[:MAXFETCH]:
                cache = f"{RAW}/page_{site}_{y}_{ts}_{hashlib.md5(orig.encode()).hexdigest()[:8]}.html"
                html = get(site, f"https://web.archive.org/web/{ts}id_/{orig}", cache, 90)
                if not html: why.append(f"{ts}: fetch failed/empty"); continue
                a = analyse(html, y); n = len(a["pos"])
                attempts.append((site, y, ts, orig, n, len(a["picks"]), a["rho"], a["leak"]))
                if n < MINNAMES: why.append(f"{ts}: only {n} class names"); continue
                if a["leak"]: why.append(f"{ts}: results language x{a['leak']}"); continue
                if not a["has_year"]: why.append(f"{ts}: draft year absent from text"); continue
                if a["rho"] is None or a["rho"] < MINRHO: why.append(f"{ts}: rho {None if a['rho'] is None else round(a['rho'],2)} < {MINRHO} (not a draft-ordered mock)"); continue
                valid.append((("final" in orig.lower()) or a["final_title"], ts, orig, a))
            if not valid:
                report[(site, y)] = ("rejected: " + "; ".join(why)) if why else (("site skipped: " + stopped[site]) if site in stopped else "no fetch")
                if why and site in stopped: report[(site, y)] += " (further candidates not fetched: site stopped)"
                continue
            valid.sort(key=lambda v: (v[0], v[1])); fin, ts, orig, a = valid[-1]
            days = (D - dt.datetime.strptime(ts, "%Y%m%d%H%M%S")).total_seconds() / 86400
            for k, (i, nm, pid, pk) in enumerate(a["pos"], 1): rows_out.append(dict(pid=pid, draft_year=y, site=site, rank=k, ts=ts))
            found = {pid for (_, _, pid, _) in a["pos"]}
            for nm, (pid, pk) in uni[y].items():
                try: top = float(pk) <= 30
                except Exception: top = False
                if top and pid not in found: unmatched.append(dict(draft_year=y, site=site, ts=ts, kind="top30_pick_not_found_on_page", pid=pid, actual_pick=pk, note=nm))
            report[(site, y)] = dict(ts=ts, days=round(days, 2), names=len(a["pos"]), drafted=len(a["picks"]), rho=None if a["rho"] is None else round(a["rho"], 3), final=bool(fin), url=orig)
            log(f"OK {site} {y} {ts} names={len(a['pos'])} rho={a['rho']:.2f}")
            for ts2, orig2, why2 in [(v[1], v[2], "valid_not_selected") for v in valid[:-1]]: unmatched.append(dict(draft_year=y, site=site, ts=ts2, kind="alt_valid_capture_not_used", pid="", actual_pick="", note=orig2))
  log(f"phase {ph} done")

# ---------------- write outputs ----------------
with open(f"{DATA}/mock_consensus3_ranks.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["pid", "draft_year", "site", "rank", "ts"]); w.writeheader(); [w.writerow(r) for r in rows_out]
with open(f"{DATA}/mock_consensus3_unmatched.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["draft_year", "site", "ts", "kind", "pid", "actual_pick", "note"]); w.writeheader(); [w.writerow(r) for r in unmatched]
json.dump({"report": {f"{s}|{y}": v for (s, y), v in report.items()}, "attempts": attempts, "stopped": stopped}, open(f"{RAW}/run_state.json", "w"), default=str)
print("MOCK3_COLLECT_DONE rows", len(rows_out))

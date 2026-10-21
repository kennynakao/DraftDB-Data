#!/usr/bin/env python3
"""Task 3: official league player pages via the Wayback Machine ONLY (web.archive.org CDX + id_ raw captures). No live requests to nbl.com.au / lnb.fr /
gleague.nba.com / overtimeelite.com. URLs come from the player's own PRE-DRAFT Wikipedia revision (external links). The capture used is the last one with
timestamp <= draft-night cutoff (22:00 UTC, COLLECTOR_RULES.md). >=2 s between archive.org requests. Cache: raw/wayback/<pid>_<site>.html; log: wayback_log.csv."""
import os, re, json, time, csv, urllib.request, urllib.parse
import pandas as pd
D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
P = f"{D}/novel/pathway"; os.makedirs(f"{P}/raw/wayback", exist_ok=True)
UA = "DraftDB-research/1.0 (NBA draft research; contact mike@alphax.inc) python-urllib/3"
CUT = {2019:"20190620",2020:"20201118",2021:"20210729",2022:"20220623",2023:"20230622",2024:"20240626",2025:"20250625"}
SITES = {"nbl": r"https?://(?:www\.)?nbl\.com\.au/player/\d+/\d+/[^\s|\]}<>\"']+", "ote": r"https?://(?:www\.)?overtimeelite\.com/players/[0-9a-f-]{36}",
         "gleague": r"https?://(?:www\.)?gleague\.nba\.com/player/[^\s|\]}<>\"']+", "lnb": r"https?://(?:www\.)?lnb\.fr/(?:elite/joueur/\?id=\d+|fr/proa/joueurs/[^\s|\]}<>\"']+)"}
last = [0.0]
def get(url, tries=4):
    for k in range(tries):
        dt_ = time.time() - last[0]
        if dt_ < 2.0: time.sleep(2.0 - dt_)
        last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90) as r: return r.read()
        except Exception as e:
            code = getattr(e, "code", None)
            if code in (429, 503) or code is None: time.sleep(6 * 2 ** k); continue
            return None
    return None
def cdx(url, to):
    q = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode({"url": url, "output": "json", "to": to + "220000", "limit": "-1", "filter": "statuscode:200", "fl": "timestamp,original,length"})
    b = get(q)
    if not b: return None
    try: j = json.loads(b)
    except Exception: return None
    return j[1] if len(j) > 1 else None
a = pd.read_csv(f"{P}/coverage_audit.csv"); f = pd.read_csv(f"{P}/features.csv"); fp = f.set_index("pid")
log = []
for t in a[a.draft_year >= 2019].itertuples():
    if t.pid in fp.index and fp.loc[t.pid, "pw_season_gap"] == 0 and fp.loc[t.pid, "pw_source"] in (2, 3): continue   # already served by a structured export
    txt = ""
    for p_ in (f"{D}/wiki_raw/prerev_{t.pid}.json", f"{P}/raw/predraft/{t.pid}.json"):
        if os.path.exists(p_):
            j = json.load(open(p_)); txt = j.get("wikitext") or ""
            if txt: break
    for site, rx in SITES.items():
        urls = list(dict.fromkeys(re.findall(rx, txt)))
        if not urls: continue
        url = urls[0]
        if site == "ote": url = url + "/career"
        out = f"{P}/raw/wayback/{t.pid}_{site}.html"
        rec = dict(pid=t.pid, draft_year=t.draft_year, site=site, url=url, capture="", bytes=0, result="")
        if os.path.exists(out): rec.update(capture=open(out + ".ts").read() if os.path.exists(out + ".ts") else "", bytes=os.path.getsize(out), result="cached"); log.append(rec); continue
        c = cdx(url.split("://", 1)[1].replace("www.", "", 1) if site != "lnb" else url.split("://", 1)[1], CUT[t.draft_year])
        if not c and site == "ote":   # fall back to the player's main page
            c = cdx(urls[0].split("://", 1)[1].replace("www.", "", 1), CUT[t.draft_year]); 
        if not c: rec["result"] = "no_capture_before_cutoff"; log.append(rec); continue
        ts, orig = c[0], c[1]; rec["capture"] = ts
        b = get(f"https://web.archive.org/web/{ts}id_/{orig}")
        if not b: rec["result"] = "fetch_failed"; log.append(rec); continue
        open(out, "wb").write(b); open(out + ".ts", "w").write(ts)
        rec.update(bytes=len(b), result="fetched"); log.append(rec)
        print(t.pid, site, ts, len(b), flush=True)
pd.DataFrame(log).to_csv(f"{P}/wayback_log.csv", index=False)
print("WAYBACK_DONE", len(log), flush=True)

#!/usr/bin/env python3
"""Fetch the last English-Wikipedia revision strictly BEFORE draft-night cutoff (22:00 UTC, COLLECTOR_RULES.md) for target pids that
have no wiki_raw/prerev_<pid>.json. Same method as novel/wikitext/fetch_predraft.py. Cache: raw/predraft/<pid>.json (resumable).
Polite: >=1.1 s between requests, descriptive UA, exponential backoff on 429/503."""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error
import pandas as pd
D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(D, "novel/pathway/raw/predraft"); os.makedirs(OUT, exist_ok=True)
UA = "DraftDB-research/1.0 (NBA draft research; contact mike@alphax.inc) python-urllib/3"
API = "https://en.wikipedia.org/w/api.php"
CUT = {2007:"2007-06-28",2008:"2008-06-26",2009:"2009-06-25",2010:"2010-06-24",2011:"2011-06-23",2012:"2012-06-28",2013:"2013-06-27",2014:"2014-06-26",2015:"2015-06-25",2016:"2016-06-23",2017:"2017-06-22",2018:"2018-06-21",2019:"2019-06-20",2020:"2020-11-18",2021:"2021-07-29",2022:"2022-06-23",2023:"2023-06-22",2024:"2024-06-26",2025:"2025-06-25"}
def fetch(title, cutoff):
    p = {"action":"query","prop":"revisions","titles":title,"rvprop":"timestamp|content|ids","rvslots":"main","rvlimit":"1","rvdir":"older","rvstart":cutoff,"format":"json","formatversion":"2","redirects":"1"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(p), headers={"User-Agent": UA})
    for k in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as r: return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503): time.sleep(5 * 2 ** k); continue
            raise
    raise RuntimeError("backoff exhausted")
a = pd.read_csv(os.path.join(D, "novel/pathway/coverage_audit.csv"))
todo = []
for r in a.itertuples():
    if os.path.exists(f"{D}/wiki_raw/prerev_{r.pid}.json") or os.path.exists(f"{OUT}/{r.pid}.json"): continue
    q = f"{D}/wiki_raw/attn_{r.pid}.json"
    t = json.load(open(q)).get("title") if os.path.exists(q) else None
    if t: todo.append((r.pid, t, CUT[r.draft_year] + "T22:00:00Z"))
print("to fetch", len(todo), flush=True)
for i, (pid, title, cut) in enumerate(todo, 1):
    rec = dict(pid=pid, title=title, cutoff=cut)
    try:
        d = fetch(title, cut); pg = d["query"]["pages"][0]
        if pg.get("missing"): rec["status"] = "missing_page"
        elif not pg.get("revisions"): rec["status"] = "no_predraft_rev"
        else:
            rv = pg["revisions"][0]; rec.update(status="ok", rev_ts=rv["timestamp"], revid=rv["revid"], wikitext=rv["slots"]["main"]["content"], resolved_title=pg["title"])
            assert rec["rev_ts"] < cut.replace("T22:00:00Z", "T22:00:00Z")
    except Exception as e:
        rec["status"] = "error:" + repr(e)[:80]
    json.dump(rec, open(f"{OUT}/{pid}.json", "w"))
    if i % 20 == 0: print(i, len(todo), flush=True)
    time.sleep(1.2)
print("FETCH_DONE", flush=True)

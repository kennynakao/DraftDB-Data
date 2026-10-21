import json, urllib.parse
from pgfetch import get
def wiki(title):
    q = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content", "rvslots": "main",
         "titles": title, "format": "json", "formatversion": 2})
    r = get(q, "wiki")
    if r is None: return None
    d = json.loads(r)
    p = d["query"]["pages"][0]
    if "revisions" not in p: return None
    rv = p["revisions"][0]
    return {"title": p["title"], "revid": rv["revid"], "ts": rv["timestamp"], "text": rv["slots"]["main"]["content"]}
if __name__ == "__main__":
    import csv
    titles = [f"{y} McDonald's All-American Boys Game" for y in range(2006, 2026)]
    titles += ["Jordan Brand Classic", "Nike Hoop Summit", "McDonald's All-American Game"]
    titles += [f"{y} Jordan Brand Classic" for y in range(2006, 2026)] + [f"{y} Nike Hoop Summit" for y in range(2006, 2026)]
    with open("wiki_sources.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["title", "revid", "rev_timestamp", "chars", "url"])
        for t in titles:
            r = wiki(t)
            if r: w.writerow([r["title"], r["revid"], r["ts"], len(r["text"]), "https://en.wikipedia.org/w/index.php?oldid=%d" % r["revid"]])
            else: w.writerow([t, "", "", 0, ""])

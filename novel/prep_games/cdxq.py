import sys, urllib.parse
from pgfetch import get
def cdxq(url, match="prefix", filt=None, limit=20000, collapse="urlkey"):
    p = {"url": url, "matchType": match, "output": "txt", "fl": "timestamp,original,statuscode,mimetype",
         "filter": ["statuscode:200"], "limit": limit}
    if collapse: p["collapse"] = collapse
    if filt: p["filter"].append(filt)
    q = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(p, doseq=True)
    return get(q, "cdx")
if __name__ == "__main__":
    r = cdxq(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    print(r)

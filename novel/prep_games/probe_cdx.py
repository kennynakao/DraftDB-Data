import sys, urllib.parse
from pgfetch import get
def cdx(url, match="prefix", limit=5000, extra=""):
    q = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(
        {"url": url, "matchType": match, "output": "txt", "fl": "timestamp,original,statuscode,mimetype",
         "collapse": "urlkey", "filter": "statuscode:200", "limit": limit})
    return get(q, "cdx")
if __name__ == "__main__":
    r = cdx(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "prefix")
    print(r if r is None else r[:6000])

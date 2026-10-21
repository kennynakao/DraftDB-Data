"""Polite cached fetcher (offline on re-run). One request at a time, >=2.0 s between requests to the same host,
exponential backoff on 429/503/5xx, descriptive User-Agent."""
import os, time, hashlib, urllib.request, urllib.error, urllib.parse, json, csv, sys
HERE = os.path.dirname(os.path.abspath(__file__))
UA = "DraftDB-research-collector/1.0 (academic NBA draft-model research; contact mk2107@nyu.edu)"
MIN_GAP = 2.0
_last = {}
LOG = os.path.join(HERE, "fetch_log.csv")
OFFLINE = os.environ.get("PG_OFFLINE") == "1"

def _log(url, status, nbytes, cached):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["utc","url","status","bytes","cached"])
        w.writerow([time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), url, status, nbytes, int(cached)])

def cache_path(sub, url):
    return os.path.join(HERE, "raw", sub, hashlib.sha1(url.encode()).hexdigest()[:20] + ".txt")

def get(url, sub, max_tries=6, ok_404=True, binary=False):
    """Return text or None (404 / persistent failure). Caches successes and 404s."""
    p = cache_path(sub, url)
    if binary:
        p = p[:-4] + ".bin"
        if os.path.exists(p):
            b = open(p, "rb").read()
            return None if b == b"#PG404" else b
    elif os.path.exists(p):
        with open(p, encoding="utf-8", errors="replace") as f:
            s = f.read()
        if s.startswith("#PG404\n"): return None
        # first line stores URL
        return s.split("\n", 1)[1] if s.startswith("#URL ") else s
    if OFFLINE: return None
    host = urllib.parse.urlparse(url).netloc
    delay = 5
    for i in range(max_tries):
        gap = time.time() - _last.get(host, 0)
        if gap < MIN_GAP: time.sleep(MIN_GAP - gap)
        _last[host] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
                if not binary: data = data.decode("utf-8", errors="replace")
                st = r.status
            _last[host] = time.time()
            if (data[:400].decode("utf-8","ignore") if binary else data[:400]).find("Internet Archive: Temporarily Offline") >= 0:
                raise urllib.error.HTTPError(url, 503, "IA offline", {}, None)
            _log(url, st, len(data), False)
            if binary:
                open(p, "wb").write(data)
                open(p[:-4] + ".url", "w").write(url)
            else:
                with open(p, "w", encoding="utf-8") as f: f.write("#URL " + url + "\n" + data)
            return data
        except urllib.error.HTTPError as e:
            _log(url, e.code, 0, False)
            if e.code in (404, 403) and ok_404:
                if binary: open(p, "wb").write(b"#PG404")
                else:
                    with open(p, "w") as f: f.write("#PG404\n")
                return None
            if e.code in (429, 503, 500, 502, 504):
                time.sleep(delay); delay = min(delay * 2, 240); continue
            return None
        except Exception as e:
            _log(url, "ERR " + type(e).__name__, 0, False)
            time.sleep(delay); delay = min(delay * 2, 240)
    return None

def wb(url, ts="2", binary=False):
    """Fetch a Wayback capture (raw bytes, id_ flavour). ts='2' -> nearest capture via redirect; or a 14-digit timestamp."""
    return get("https://web.archive.org/web/%sid_/%s" % (ts, url), "wayback", binary=binary)

#!/usr/bin/env python3
"""NBA Draft early-entry candidate lists, 2019-2025, from the league's own releases.

For every draft the NBA publishes (a) the initial early-entry list in April, (b) one to three
withdrawal releases (after the NCAA deadline and after the league's own deadline), and sometimes
(c) a handful of late additions that only show up in the counts of the later releases. The set that
was draft-eligible on draft night is (a) + (c) - (b). Everything here was public before the draft,
so a universe built from it carries no information about who later reached the NBA.

Sources: nba.com/news and pr.nba.com release pages (the text sits either in HTML tables or in an
escaped JSON blob inside the page); Hoops Rumors' post-deadline "official early entrants list"
posts, which copy the league's final list including the late additions, are used to reconcile the
count where the NBA's own pages do not add up. Raw pages are cached under early_entry_raw/ with a
provenance.json (url, capture time, bytes, sha256). Re-runs are offline.

Outputs: early_entry_raw/early_entry_rows.csv (every parsed row with its page and kind),
early_entry_{year}.csv (the remaining candidates per draft: name, school, height, class_or_born,
international flag, source) and a printed reconciliation against the NBA's stated counts.

Usage: python3 early_entry_collect.py [--refetch]
"""
import os, re, sys, json, time, hashlib, html, unicodedata, datetime as dt, urllib.request, csv
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "early_entry_raw")
UA = "DraftDB-research/1.0 (mk2107@nyu.edu) non-commercial NBA draft research"
os.makedirs(RAW, exist_ok=True)

# kind: initial | withdraw | final (a page that lists the remaining candidates outright)
PAGES = {
 2019: [("initial", "https://pr.nba.com/early-entry-candidates-2019-draft"),
        ("withdraw", "https://www.nba.com/news/eighty-nine-early-entry-candidates-withdraw-draft"),
        ("final", "https://www.nba.com/news/47-international-early-entry-candidates-withdraw-draft-official-release")],
 2020: [("initial", "https://www.nba.com/news/early-entry-candidates-announced-2020-nba-draft-official-release"),
        ("withdraw", "https://pr.nba.com/2020-early-entry-update"),
        ("final", "https://pr.nba.com/twenty-three-early-entry-candidates-withdraw-from-nba-draft-2020-presented-by-state-farm")],
 2021: [("initial", "https://www.nba.com/news/nba-announces-early-entry-candidates-for-nba-draft-2021"),
        ("withdraw", "https://www.nba.com/news/early-entry-candidates-withdraw-draft-2021"),
        ("withdraw", "https://www.nba.com/news/nba-announces-51-early-entry-candidates-withdraw-from-2021-draft"),
        ("hr_final", "https://hoopsrumors.com/2021/07/official-early-entrants-list-for-2021-nba-draft.html")],
 2022: [("initial", "https://www.nba.com/news/nba-announces-early-entry-candidates-for-nba-draft-2022"),
        ("withdraw", "https://www.nba.com/news/112-early-entry-candidates-withdraw-from-nba-draft-2022"),
        ("final", "https://www.nba.com/news/24-early-entry-candidates-withdraw-from-nba-draft-2022"),
        ("hr_final", "https://hoopsrumors.com/2022/06/official-early-entrants-list-for-2022-nba-draft.html")],
 2023: [("initial", "https://www.nba.com/news/nba-draft-2023-early-entry-candidates"),
        ("withdraw", "https://www.nba.com/news/108-early-entry-candidates-withdraw-from-nba-draft-2023"),
        ("final", "https://www.nba.com/news/44-early-entry-candidates-withdraw-from-nba-draft-2023"),
        ("hr_final", "https://hoopsrumors.com/2023/06/official-early-entrants-list-for-2023-nba-draft.html")],
 2024: [("initial", "https://www.nba.com/news/nba-draft-2024-early-entry-candidates"),
        ("final", "https://www.nba.com/news/31-early-entry-candidates-withdraw-2024-nba-draft"),
        ("hr_final", "https://hoopsrumors.com/2024/06/official-early-entrants-list-for-2024-nba-draft.html")],
 2025: [("initial", "https://www.nba.com/news/2025-nba-draft-early-entry-candidates"),
        ("final", "https://www.nba.com/news/13-additional-early-entry-candidates-withdraw-2025-draft"),
        ("hr_final", "https://hoopsrumors.com/2025/06/official-early-entrants-list-for-2025-nba-draft.html")],
}
# Pages with no parsable article body (the text is loaded client-side on both nba.com and pr.nba.com):
# 2024 "93 candidates withdraw", 2025 "50 early entry candidates withdraw", 2022 "112 withdraw" on pr.nba.com.
# None is needed: the league's post-deadline release for each of those years lists the remaining candidates in full.
# the league's stated remaining counts (college-or-other, international) in its last pre-draft release
STATED = {2019: (86, 12), 2020: (71, 15), 2021: (209, 8), 2022: (135, 14), 2023: (84, 8), 2024: (62, 15), 2025: (32, 14)}

COUNTRIES = {"argentina","australia","austria","belgium","bosnia","brazil","bulgaria","canada","china","croatia","czech republic","denmark",
 "dominican republic","egypt","estonia","finland","france","georgia","germany","greece","hungary","iceland","israel","italy","japan","latvia",
 "lithuania","luxembourg","mexico","montenegro","netherlands","new zealand","nigeria","north macedonia","macedonia","norway","poland","portugal",
 "puerto rico","romania","russia","senegal","serbia","slovakia","slovenia","south korea","spain","sweden","switzerland","turkey","ukraine",
 "united kingdom","england","uruguay","venezuela","angola","cameroon","mali","philippines","taiwan","czechia","ivory coast","kosovo","cyprus","bahamas"}
HEIGHT = re.compile(r"^\d-\d{1,2}$")
CLASSW = {"freshman", "sophomore", "junior", "senior", "graduate", "grad", "redshirt freshman", "redshirt sophomore", "redshirt junior", "redshirt senior", "fifth year", "5th year"}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", " ", s.replace(".", " ").replace("'", "").replace("’", ""))
    return re.sub(r"[^a-z ]", " ", s).strip().replace("  ", " ").replace("  ", " ")


def fetch(url, refetch=False):
    fn = os.path.join(RAW, hashlib.sha1(url.encode()).hexdigest()[:12] + ".html")
    prov_fn = os.path.join(RAW, "provenance.json")
    prov = json.load(open(prov_fn)) if os.path.exists(prov_fn) else {}
    if os.path.exists(fn) and not refetch and os.path.getsize(fn) > 2000:
        return open(fn, "rb").read().decode("utf-8", "ignore")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read(); code = r.status
    open(fn, "wb").write(body)
    prov[url] = dict(file=os.path.basename(fn), captured=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), bytes=len(body),
                     sha256=hashlib.sha256(body).hexdigest(), http=code)
    json.dump(prov, open(prov_fn, "w"), indent=1)
    time.sleep(3)
    return body.decode("utf-8", "ignore")


def tokens(page):
    """Flatten a release page into a token stream: table cells, bullet-separated fields and
    newline-separated lines all become one token each, in page order."""
    t = page
    # nba.com pages carry the article as an escaped JSON string
    t = t.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\/", "/")
    t = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), t)
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"</(td|th|tr|p|li|h\d|div|table)>", "\n", t, flags=re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    out = []
    for line in t.split("\n"):
        for piece in re.split(r"\s\|\s|•|\u2022|[ \t\u00a0]{2,}", line):
            p = re.sub(r"\s+", " ", piece).strip(" \t *")
            if p:
                out.append(p)
    return out


def parse(page):
    """Rows (name, school, height, class_or_born) from the token stream, with the section heading in force."""
    toks = tokens(page)
    rows = []; section = ""
    for i, tk in enumerate(toks):
        low = tk.lower()
        if len(tk) < 220 and not HEIGHT.match(tk) and not low.startswith("update") and re.search(r"follow|here is|here are|below is|remain|withdr|applied", low):
            # a heading broken over several tokens: glue the preceding short "the following ..." fragments back on
            for j in range(i - 1, max(i - 6, -1), -1):
                pj = toks[j].lower()
                if len(pj) > 160 or pj.endswith(":") or HEIGHT.match(pj):
                    break
                if re.match(r"(the )?following|here is|here are|below is", pj):
                    low = " ".join(x.lower() for x in toks[j:i]) + " " + low
                    break
            section = low
        if HEIGHT.match(tk) and i >= 2:
            name, school = toks[i - 2], toks[i - 1]
            if HEIGHT.match(name) or HEIGHT.match(school) or len(name) > 40 or len(school) > 60 or name.lower() in ("player", "height", "school"):
                continue
            if not re.search(r"[A-Za-z]{2,}", name) or re.search(r"\d{3}", name):
                continue
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            cls = nxt if (nxt.lower() in CLASSW or re.fullmatch(r"(19|20)\d\d( dob)?", nxt.lower()) or nxt.lower().startswith("redshirt")) else ""
            cls = cls.replace(" DOB", "")
            sk = "remain" if "remain" in section else ("withdraw" if re.search(r"ha(ve|s) withdrawn|withdrawn (his|their) name|players? (who )?withdrew", section) else "initial")
            rows.append(dict(name=name, school=school, height=tk, class_or_born=cls, section=section, section_kind=sk))
    return rows


def is_international(row):
    """The league's own grouping (its headings say 'international players' or 'non-international players');
    the club-country regex is the fallback for the few pages whose college heading carries no keyword."""
    s = row["school"].lower(); sec = row["section"]
    if "non-international" in sec or "colleges" in sec or "college" in sec:
        return 0
    if "international" in sec:
        return 1
    m = re.search(r"\(([^)]+)\)\s*$", s)
    if m and m.group(1).strip() in COUNTRIES:
        return 1
    if re.fullmatch(r"(19|20)\d\d", row["class_or_born"] or "") and "college" not in sec:
        return 1
    if "international" in sec and "college" not in sec and "underclass" not in sec and "senior" not in sec:
        return 1
    return 0


def hoopsrumors_final(page):
    """Hoops Rumors' final list: lines 'Name, POS, School (class)' under headings."""
    toks = tokens(page); rows = []; section = ""
    for i, tk in enumerate(toks):
        low = tk.lower()
        if low.endswith(":") and len(tk) < 80:
            section = low; continue
        m = re.match(r"^([A-Z][^,]+?)\s*,\s*([A-Z/]{1,3})\s*,\s*(.+)$", tk)
        if not m and i and tk.startswith(","):      # 2021-2022 layout: the name is its own token, then ", POS, School (class)"
            m2 = re.match(r"^,\s*([A-Z/]{1,3})\s*,\s*(.+)$", tk)
            if m2 and re.match(r"^[A-Z][A-Za-z.'’\- ]+$", toks[i - 1]):
                m = re.match(r"^(.+?)\s*,\s*([A-Z/]{1,3})\s*,\s*(.+)$", toks[i - 1] + tk)
        if m and section and ("college" in section or "international" in section or "not technically" in section) and m.group(2) in ("G", "F", "C", "G/F", "F/G", "F/C", "C/F"):
            name, pos, rest = m.groups()
            born = re.search(r"\(born (\d{4})\)", rest); cl = re.search(r"\((freshman|sophomore|junior|senior)\)", rest)
            school = re.sub(r"\s*\((born \d{4}|freshman|sophomore|junior|senior)\)\s*$", "", rest).strip()
            rows.append(dict(name=name.strip(), school=school, height="", class_or_born=(born.group(1) if born else (cl.group(1) if cl else ("senior" if "senior" in section else ""))),
                             section=section, international=int("international" in section), auto_eligible=int("not technically" in section)))
    return rows


def main():
    refetch = "--refetch" in sys.argv
    allrows = []; summary = {}
    for year, pages in PAGES.items():
        initial, withdrawn, remain, hr = {}, {}, {}, {}
        for kind, url in pages:
            page = fetch(url, refetch)
            if kind == "hr_final":
                rows = hoopsrumors_final(page)
                for r in rows: r["section_kind"] = "hr_final"
            else:
                rows = parse(page)
                for r in rows:
                    r["international"] = is_international(r); r["auto_eligible"] = 0
            for r in rows:
                r.update(year=year, kind=kind, url=url, key=norm(r["name"]))
                allrows.append(r)
            if any(r["section_kind"] == "remain" for r in rows):
                remain = {}                                  # a later release's remaining list supersedes an earlier one
            for r in rows:
                {"initial": initial, "withdraw": withdrawn, "remain": remain, "hr_final": hr}[r["section_kind"]][r["key"]] = r
            print(f"{year} {kind:8s} {len(rows):4d} rows ({collections.Counter(r['section_kind'] for r in rows)})  {url}")
        derived = {k: v for k, v in initial.items() if k not in withdrawn}
        hr_ee = {k: v for k, v in hr.items() if not v.get("auto_eligible")}
        if remain:
            final = dict(remain); source = "league remain list"
        else:
            final = dict(hr_ee); source = "hoops rumors official list"
        for k, v in final.items():
            v["kind"] = source
        rows_out = sorted(final.values(), key=lambda r: (r["international"], r["key"]))
        n_col = sum(1 for r in rows_out if not r["international"]); n_int = len(rows_out) - n_col
        summary[year] = dict(source=source, initial=len(initial), withdrawn=len(withdrawn), remain_college=n_col, remain_intl=n_int, stated=STATED[year],
                             derived_minus_final=sorted(k for k in derived if k not in final), final_minus_derived=sorted(k for k in final if k not in derived),
                             hr_minus_final=sorted(k for k in hr_ee if k not in final), final_minus_hr=sorted(k for k in final if hr_ee and k not in hr_ee))
        with open(os.path.join(HERE, f"early_entry_{year}.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["year", "name", "school", "height", "class_or_born", "international", "kind", "url"])
            w.writeheader()
            for r in rows_out:
                w.writerow({k: r.get(k, "") for k in w.fieldnames})
    with open(os.path.join(RAW, "early_entry_rows.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "kind", "section_kind", "name", "school", "height", "class_or_born", "international", "section", "url"])
        w.writeheader()
        for r in allrows:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})
    print("\nreconciliation (remaining college / international vs the league's stated counts):")
    for y, s in summary.items():
        print(f"  {y}: {s['source']:26s} initial {s['initial']:3d}  withdrawn {s['withdrawn']:3d}  remain {s['remain_college']:3d}/{s['remain_intl']:2d}  stated {s['stated'][0]:3d}/{s['stated'][1]:2d}")
        for k in ("derived_minus_final", "final_minus_derived", "hr_minus_final", "final_minus_hr"):
            if s[k]: print(f"       {k} ({len(s[k])}): {', '.join(s[k][:12])}{' ...' if len(s[k]) > 12 else ''}")
    json.dump(summary, open(os.path.join(RAW, "summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

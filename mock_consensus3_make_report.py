"""Builds mock_consensus3_report.md and lab/out/notes_mock3.md from mock_raw/consensus3/run_state.json + mock_consensus3_ranks.csv."""
import json, csv, os, collections
DATA = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.abspath(f"{DATA}/../lab/out/notes_mock3.md")
st = json.load(open(f"{DATA}/mock_raw/consensus3/run_state.json"))
rep = {tuple(k.split("|")): v for k, v in st["report"].items()}
rows = list(csv.DictReader(open(f"{DATA}/mock_consensus3_ranks.csv")))
SITES = ["basketballnews", "bleacherreport", "si", "yahoo", "usatoday", "nbcsports", "foxsports", "sbnation", "rookiescale", "noceilings"]
YEARS = list(range(2015, 2027))
ok = {(s, int(y)): v for (s, y), v in rep.items() if isinstance(v, dict)}
byyear = collections.defaultdict(list)
for (s, y), v in ok.items(): byyear[y].append(s)
cover = collections.Counter(s for (s, y) in ok); cover19 = collections.Counter(s for (s, y) in ok if y >= 2019)
L = []
L.append("# Mock consensus batch 3 (new publishers, Wayback only)\n")
L.append(f"Rows in mock_consensus3_ranks.csv: **{len(rows)}** (pid, draft_year, site, rank, ts); distinct (site, year) captures accepted: **{len(ok)}**.\n")
L.append("Method: Wayback CDX listings (narrow per-year URL prefixes for big hosts, whole-site listing for small hosts), candidates restricted to captures dated in the 40 days before the draft and before 22:00 UTC on draft day; "
         "up to 4 candidates per site/year fetched via `web/<ts>id_/<url>` (raw capture), ranked by ('final' in URL, year in URL, timestamp). Accepted capture = >= 25 class names found in page text, Spearman(rank, actual pick) >= 0.3, "
         "draft year in text, and no 'was selected'/'selected by' within 200 chars of a class-member name or the draft year. Rank = order of first appearance of the normalized full name (same rule as mock_consensus_collect_d.py). "
         "Among accepted candidates the best by ('final' in URL/title, timestamp) is kept. Rate >= 1.5 s, exponential backoff, 3 consecutive failures stop a site. Spearman is a scrape sanity check only. "
         "`final` column: 'final' appears in the URL or <title>.\n")
L.append("## Publishers accepted per draft year\n")
L.append("| year | n | publishers |\n|---|---|---|")
for y in YEARS: L.append(f"| {y} | {len(byyear[y])} | {', '.join(sorted(byyear[y])) or '-'} |")
L.append("\n## Best-covered new publishers\n")
for s, n in cover.most_common(3): L.append(f"- {s}: {n} draft years ({cover19[s]} of them in 2019-2026): " + ", ".join(str(y) for y in sorted(y for (ss, y) in ok if ss == s)))
L.append("\n## Per site / year (accepted captures)\n")
L.append("| site | year | capture ts (UTC) | days before draft | names matched | drafted matched | Spearman vs pick | final | URL |\n|---|---|---|---|---|---|---|---|---|")
for (s, y), v in sorted(ok.items(), key=lambda x: (x[0][0], x[0][1])):
    L.append(f"| {s} | {y} | {v['ts']} | {v['days']} | {v['names']} | {v['drafted']} | {v['rho']} | {v['final']} | {v['url'][:120]} |")
L.append("\n## Per site / year (not accepted, and why)\n")
L.append("| site | year | status |\n|---|---|---|")
for s in SITES:
    for y in YEARS:
        v = rep.get((s, str(y)))
        if isinstance(v, dict): continue
        L.append(f"| {s} | {y} | {(v or 'not reached').replace('|', '/')[:300]} |")
L.append("\n## Every fetched candidate capture (diagnostic)\n")
L.append("| site | year | ts | class names | drafted matched | Spearman | results-language hits | URL |\n|---|---|---|---|---|---|---|---|")
for a in sorted(st["attempts"], key=lambda a: (a[0], a[1], a[2])):
    L.append(f"| {a[0]} | {a[1]} | {a[2]} | {a[4]} | {a[5]} | {None if a[6] is None else round(a[6], 2)} | {a[7]} | {a[3][:100]} |")
L.append("\n## Sites stopped\n")
L.append("\n".join(f"- {k}: {v}" for k, v in st["stopped"].items()) or "- none stopped by the 3-consecutive-failure rule in the final run")
L.append("\n## Not attempted / limitations\n- The Athletic (paywalled) and ESPN Insider mocks skipped by instruction.\n- Wayback CDX was heavily degraded (503/504/timeouts, mid-stream truncation); a CDX miss therefore does not prove that a publisher had no mock that year, and URL-prefix patterns for big hosts only cover the known URL layouts (see pats() in mock_consensus3_collect.py).\n"
         "- Pages that render the mock from JavaScript only (no names in the raw capture) fail the >= 25 names test and are listed above as rejected.\n- Unmatched/diagnostic rows: mock_consensus3_unmatched.csv (ambiguous class names, top-30 picks absent from an accepted page, alternative valid captures not used).\n")
open(f"{DATA}/mock_consensus3_report.md", "w").write("\n".join(L))
S = [f"# notes_mock3 (mock consensus batch 3)\n", f"- rows in mock_consensus3_ranks.csv: {len(rows)}; accepted (site, year) captures: {len(ok)}",
     "- publishers found per year: " + "; ".join(f"{y}: {', '.join(sorted(byyear[y])) or 'none'}" for y in YEARS),
     "- three best-covered new publishers: " + "; ".join(f"{s} ({n} yrs)" for s, n in cover.most_common(3)),
     "- sites stopped: " + ("; ".join(st["stopped"]) or "none"), "- per site/year numbers (ts, days before, names, drafted, Spearman): see DraftDB-Data/mock_consensus3_report.md", "",
     "| site | year | days before | names | drafted | Spearman |", "|---|---|---|---|---|---|"] + \
    [f"| {s} | {y} | {v['days']} | {v['names']} | {v['drafted']} | {v['rho']} |" for (s, y), v in sorted(ok.items())]
os.makedirs(os.path.dirname(NOTES), exist_ok=True); open(NOTES, "w").write("\n".join(S) + "\n")
print("\n".join(S))

# pathway - last pre-draft pro season for international / pathway prospects

One row per `pid` (166 of the 305 audited rows), numeric columns only, missing = empty (never 0 for unknown). Built offline from caches already on disk plus
two small polite extensions (see Sources). No names in `features.csv`, `provenance.csv`, `unmatched.csv`; names appear only in `coverage_audit.csv` and `report.txt` (private repo).

## Why
In the model inputs the rows with `path` in (`international`, `college_pre2008_or_unlinked`) carry about 23 of 34 `intl_*` columns on average (max 33), and
`intl_impact` is empty for 125 of 305 rows, `intl_usg_pct` for 92 and `intl_ts_pct` for 89 (see `coverage_audit.csv`, `audit_summary.txt`). NBL Next Stars, G League Ignite,
OTE and non-EuroLeague European rows are the worst. `college_pre2008_or_unlinked` is mostly college players with no link (not pathway players), so ~half of the
no-record rows below are legitimately empty.

## Task 1 audit (`coverage_audit.csv`, `audit_summary.txt`, `audit.py`)
305 rows with path in the two values, classes 2007-2018 (train, 168 rows) and 2019-2025 (7 test files, 137 rows). Columns: pid, draft_year, path, n_intl_filled (of the 34 intl_ columns),
has_impact/usg/ts/gp/minutes, name (from `identity/tabular_names.csv`). Filled-column mean 23.4, median 27, min 1, max 33. "Under-filled" = any of the five core columns missing (153 rows).

## Features (`features.csv`)
| column | definition |
|---|---|
| pw_gp, pw_mpg | games and minutes/game of the chosen season (pw_gp empty when the source has no GP: NBL Wayback pages before 2024, OTE pages whose game list does not reproduce the Average row) |
| pw_pts36, pw_reb36, pw_ast36, pw_stl36, pw_blk36, pw_tov36 | per-game stat x 36 / mpg |
| pw_ts_pct | PTS / (2 (FGA + 0.44 FTA)) |
| pw_efg_pct | (FGM + 0.5 3PM) / FGA |
| pw_fg3ar, pw_ftar | 3PA/FGA, FTA/FGA |
| pw_ft_pct, pw_fg3_pct | FTM/FTA, 3PM/3PA (wiki/NBL sources: the published percentage) |
| pw_usg_proxy | (FGA + 0.44 FTA + TOV) per 36 (no team totals) |
| pw_box_impact | PTS + 0.7 REB + 0.7 AST + 1.5 STL + 1.5 BLK - 1.0 TOV - 0.7 missed FG - 0.35 missed FT, per 36 |
| pw_age_at_season | (1 Feb of the season's end year - birthdate)/365.25; birthdate from `age_verified_wiki.csv`, else the infobox birth date in the pre-draft Wikipedia revision (`age_src` in provenance: 1 verified csv, 2 infobox) |
| pw_league_code | 1 EuroLeague, 2 EuroCup, 3 ACB, 4 LNB Pro A (French top flight), 5 NBL Australia, 6 G League (incl. Ignite, D-League), 7 Overtime Elite, 8 other top European (top-flight domestic leagues LBA/GBL-HEBA/BSL/BBL/ABA-KLS-A1/Israel/VTB/LKL/BLB/Slovenia/Estonia, plus Basketball Champions League / Europe Cup / EuroChallenge), 9 other (second tiers, CBA, JBA, BAL, Americas, unknown) |
| pw_source | 1 wiki career table of the pre-draft revision, 2 EuroLeague/EuroCup export, 3 G League json, **4 (added) career table of the CURRENT article restricted to seasons ended before draft night**, **5 (added) official page captured by the Wayback Machine before draft night** |
| pw_box_lite (extra) | PTS + 0.7 REB + 0.7 AST + 1.5 STL + 1.5 BLK per 36 (no TOV / misses): the only composite computable from per-game tables that lack FGA/TOV |
| pw_season_gap (extra) | draft year - season end year (0 = the season that just finished) |

Field availability depends on the source: sources 2 and 3 (box totals with FGA/FTA/TOV) fill all columns; source 5 OTE fills all except pw_gp sometimes; source 1/4/5-NBL are per-game tables
without attempts/turnovers, so pw_ts_pct, pw_efg_pct, pw_fg3ar, pw_ftar, pw_usg_proxy, pw_box_impact (and pw_tov36 for 1/4) are empty and are NOT imputed. Fill counts by source are in `report.txt`.

## Selection rule
For each pid all candidate records are collected, then (1) only seasons ending on or before the draft year are kept (2020 class: Nov 2020 draft, so 2019-20 counts and 2020-21 does not); playoffs, NBA, college,
national-team/youth/academy rows, ambiguous generic sections and mis-parsed columns are dropped; (2) seasons older than 3 seasons before the draft are dropped; (3) the LATEST season wins; (4) within that season the
competition with the most minutes (GP x MPG) wins; multiple rows of the same competition (team changes) are merged by games; if the same competition comes from several sources the order is export (2) > G League (3) >
pre-draft wiki (1) > Wayback (5) > current-article (4). Competitions are never pooled (unlike intl2, which pools by minutes).

## Sources, dating
1. `wiki_raw/prerev_<pid>.json` (last English-Wikipedia revision before draft night) and, for 136 pids that had none, revisions fetched by `fetch_prerev.py` into `raw/predraft/` (MediaWiki API, 1.2 s spacing, same method as `novel/wikitext/fetch_predraft.py`; rev_ts strictly before 22:00 UTC on the draft date). Career tables parsed by `pwparse.py` (the project's own `traj_features.rows_from`, rule-based). Identity guard: infobox birth date vs `age_verified_wiki` (>400 days apart = reject).
2. `raw/E{y}_trad|adv.json`, `raw/U{y}_trad|adv.json` (EuroLeague / EuroCup season exports, season label = start year). Name match (accent/punctuation/suffix-normalised full name) + age within 1.6 years of the birthdate when known (else plausible 16-29 and flagged `export_age_unchecked`); several export codes for one name = ambiguous = skipped. Per-game values are 0.1-rounded in the API, so rare-event rates (TOV, STL, BLK) for low-minute players are noisy. Cross-check against `novel/euroleague/features.csv`: for the 38 pids whose chosen record is a EuroLeague season, GP equals `el2_ls_games` in 36 and ts agrees to a median 0.003; the two GP mismatches are 2020-class rows where that block's "last season" differs.
3. `gl_test.json` (G League 2019-20 totals): only one season on disk; name + birthdate (required) match. 4 rows (all later classes, stale-ish).
4. `wiki_raw/attn_<pid>.json` `career_rows`. **These are parsed from the CURRENT article (fetched after the draft), not from the pre-draft revision**, so they are post-draft Wikipedia text; only rows of seasons that ended before draft night are used and they are completed-season facts, but their existence in the table is not knowable pre-draft. They are flagged `pw_source = 4`; filter them out for a strictly pre-draft-sourced variant (71 rows).
5. Wayback captures of official pages (Task 3): see below. Capture timestamp <= cutoff, recorded in provenance `source_file` (`@timestamp`).

## Task 3 - exactly what worked (`wayback_fetch.py`, `wayback_log.csv`, `raw/wayback/`)
Only web.archive.org (CDX API for the last 200-capture <= cutoff, then `/web/<ts>id_/<url>`), 2 s spacing; archive.org robots.txt does not restrict `/web/`; URLs taken from the player's own pre-draft Wikipedia revision. 24 pids tried.
* **Overtime Elite** player `/career` pages: captures exist before draft night and the HTML contains a server-rendered game-log table with an `Average` row (pts ast reb stl blk dnk min 2pm 2pa 2p% 3pm 3pa 3p% fgm fga fg% ftm fta ft% +/- pf to). WORKED for 3 test players with full box detail (4 pages fetched, 1 superseded by a later NBL season). Caveat: GP = game rows only if the listed games reproduce the Average row; otherwise empty.
* **NBL (nbl.com.au/player/...)**: captures from 2022 onward are server-rendered ("Full Career" per-game table: Mins FG% FT% Reb Ast Blk Stl To Pf Pts; GP only from the 2024+ layout) - WORKED for 4 pids (partial detail). Captures from 2020-21 are a JavaScript shell ("doesn't work properly without JavaScript") - FAILED for the 2020-21 NBL Next Stars (4 pids).
* **G League (gleague.nba.com/player/...)**: captures exist (Ignite prospects of 2021-2023) but the page is navigation only, no statistics - FAILED (7 pids).
* **LNB (lnb.fr)**: old 2019 template contains a server-rendered summary (GP, GS, MPG, PPG, RPG, APG, STL, BLK, 2P/3P/FT%), not parsed because it only concerns an already-covered 2019 row; the new Betclic Elite player pages (2022+) have empty JS-filled stats tables - FAILED for the 2023 and 2025 pathway players; 1 pid had no capture before the cutoff.
Not attempted: stats.gleague.nba.com pages and the LNB stats-center (JavaScript apps, no static data).

## Coverage (full tables in `report.txt`; re-create with `python3 report.py`)
Rows in features.csv: 166 (305 audited). By band: 2007-2018: 99 of 168 rows (underfilled rows covered: 28 of 70); 2019-2025: 67 of 137 (underfilled: 30 of 83).
By draft year (pw rows / audited rows): 2007 4/9, 2008 5/11, 2009 6/9, 2010 5/8, 2011 7/13, 2012 10/13, 2013 11/18, 2014 11/17, 2015 10/14, 2016 11/18, 2017 11/23, 2018 8/15 | 2019 12/20, 2020 12/18, 2021 11/24, 2022 4/18, 2023 11/20, 2024 9/22, 2025 8/15.
By league (2007-2018 | 2019-2025): EuroLeague 44|20, EuroCup 14|13, ACB 14|1, LNB Pro A 5|1, NBL 1|9, G League 0|9, OTE 0|3, other top European 14|7, other 7|4.
By source (2007-2018 | 2019-2025): 1: 8|12, 2: 37|27, 3: 0|4, 4: 54|17, 5: 0|7. Season gap 0 for 140 rows, 1 for 14, 2 for 9, 3 for 3.
No record (139): 82 have an article with no career table, 34 have no pre-draft article, 23 have a table with no usable pre-draft pro season; about half of the 2019-2025 no-record rows are college players in the `unlinked` path.
Partial (103 rows, in `unmatched.csv` with reason): no FGA/FTA/TOV (95), no birthdate (16), stale season gap >= 2 (12).

## Limitations
* Pre-draft Wikipedia tables lag: the last table season can be a year or two old (e.g. a 2023 #1 prospect's pre-draft table only lists his 2021-22 EuroLeague games; his 2022-23 French league season is in no cache and the LNB site could not be read). `pw_season_gap` exposes this; the gap is not a quality flag for the stat itself.
* Pathway players who matter most for the model (G League Ignite 2020-23, most NBL Next Stars before 2022, LNB stars, Serbian/Croatian/Turkish second leagues) remain mostly unfilled: no structured source on disk and the official sites are JavaScript apps. Net improvement on the test years over the existing intl_ block is therefore modest: 67 test-year rows get pw values, mean 1.2 newly-filled mapped columns per row, 8 rows gain a full pw_box_impact where intl_impact was empty and 21 gain either that or the lite box composite (see `report.txt`).
* The E/U exports list only about 155-208 players per season (low-usage players below the API's games threshold are absent; e.g. a teenage prospect with 13 EuroLeague games is missing from the 2021-22 file), so a player can be missing from source 2 while present in the wiki table.
* Tiny samples are kept (pw_gp = 1 happens); use pw_gp/pw_mpg as weights or thresholds.
* Source 4 is post-draft Wikipedia text (see above). Wiki tables mix per-game rows of different leagues in one season only by the competition rule above; league labels are dictionary-based (`build.py` LEAGUE_RULES) and ambiguous labels (bare `NBL`, `LNB`, `Pro A`) are disambiguated by club-name dictionaries.
* G League source covers 2019-20 only; no per-season G League/Ignite history is on disk (`gleague_raw/` is absent from this checkout).
* Name matching of exports is by full-name equality; a name collision with a different player of similar age would pass the age gate (none observed in the 38-row cross-check).

## Re-run
`python3 audit.py` (Task 1) -> `python3 fetch_prerev.py` (network, resumable) -> `python3 wayback_fetch.py` (network, resumable) -> `python3 build.py` (offline) -> `python3 report.py`.
Files: audit.py, fetch_prerev.py, wayback_fetch.py, pwparse.py, build.py, report.py, build_stats.json, report.txt, top10_test_improvement_nonames.csv, wayback_log.csv, raw/ (caches).

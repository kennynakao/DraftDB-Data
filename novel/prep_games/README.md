# prep_games: box-score lines from the high-school all-star games (McDonald's AA, Jordan Brand Classic, Nike Hoop Summit)

Built for the NBA redraft model. One row per pid in `features.csv` (pid + numeric columns only; empty = missing, never 0 for unknown).
Names appear only in the private files `games_long.csv`, `matches.csv`, `unmatched.csv` (all in this private repo); `features.csv` has none.

## What the features are
Sums over the games in which the player has a box-score line (a line = a row in an official/transcribed box score; players who did not
play, or who were not listed, have no line):

| column | definition |
|---|---|
| pg_games | number of games (of the three series) with a line |
| pg_min, pg_pts, pg_reb, pg_ast, pg_stl, pg_blk, pg_tov | sums of minutes, points, total rebounds, assists, steals, blocks, turnovers (over games where that stat is available) |
| pg_fgm, pg_fga, pg_3pm, pg_3pa, pg_ftm, pg_fta | shooting sums |
| pg_pts_per_min | sum(pts)/sum(min) over games that have both |
| pg_box_per_min | sum(PTS + 0.7 REB + 0.7 AST + 1.5 STL + 1.5 BLK - TOV - 0.7 (FGA-FGM) - 0.35 (FTA-FTM)) / sum(min), over games with the complete line only |
| pg_pts_rank_in_game | mean over the player's games of his points rank among all players with a points figure in that game (both teams; ties = average rank; 1 = most points) |
| pg_mcd, pg_jordan, pg_hoop_summit | 1 if the player has a box line in that series, else 0. NOTE: 0 means "no box line found", it does not prove non-participation (e.g. games without a recoverable box score; use the existing hs_* flags for participation) |
| pg_hoop_summit_world | 1 if his Hoop Summit line is for the World Select team, 0 if for USA; empty if no Hoop Summit line |

Minutes: all three are 40-minute games (200 team minutes) with different rules (Hoop Summit uses FIBA rules); the per-minute columns are the comparable ones.
A player with only a shooting line (OCR sources, see below) has pg_pts, pg_fgm.. pg_fta and pg_games but empty pg_min/pg_reb/.../pg_box_per_min.

## Sources (all dated by game date; the games are 2006-2025 spring games, i.e. before every draft of the players concerned)
Capture/revision timestamps are NOT used to date anything: a box score is a record of one game on a fixed date (March/April of the class year),
which precedes the draft by 1-5 years; the Wayback capture or Wikipedia revision merely carries the document. (Wikipedia revision timestamps in
2026 are therefore later than the draft; the content transcribed from them is the official game box score, cross-checked below.)
1. English Wikipedia (API action=query&prop=revisions, wikitext): full box-score wikitables exist for the McDonald's games 2006-2010
   (`2006..2010 McDonald's All-American Boys Game`); the other years carry rosters/leaders only (no box). The `Jordan Brand Classic` and `Nike Hoop Summit`
   articles contain rosters, MVPs and game leaders only, no box scores. Revision ids are in `wiki_sources.csv` and `provenance.csv`.
2. Wayback Machine (web.archive.org/web/<ts>id_/<url>; capture timestamps in the table below) copies of the games' own pages:
   mcdepk.com / mcdonaldsallamerican.com / epkzone.com (McDonald's), jordanbrandclassic.com (`wp-content/uploads/archive/*.pdf`, `Archives/*.html`),
   usab.com per-year Hoop Summit pages (`/history/nike-hoop-summit/<roman>-annual-nike-hoop-summit-<year>.aspx`, which carry the full HTML box score; located with the CDX API,
   output in `usab_cdx.txt`). nikehoopsummit.com only has the 2018 box (an image PDF, not used since usab has the same game as clean HTML).
   Not used: sports-reference, realgm, ESPN, MaxPreps, EYBL/Nike EYB.
Cross-check: the Wikipedia tables and the official pages agree line for line (2006: 24/24 lines identical; 2007: 24/24; 2010: 23/24; 2013 not on Wikipedia).
Team point sums of the parsed lines equal the official final score for most games (see `games_qa.csv`, column `team_pts`); where a roster player is missing
from the official document (e.g. McDonald's 2018: 10+11 lines in the PDF) nothing is imputed.

## Parsing rules (rule-based only)
* Stat Crew text (HTML `<pre>` or pdfminer text): one regex per player line `NO NAME [pos] FGM-FGA 3PM-3PA FTM-FTA <10 ints>`; column order read from the header
  (OF DE TOT PF TP A TO BLK S MIN). New 2022+ format (`NO. Name Min FG 3P FT OR DR TOT PF FD TP AS TO ST BS BA +/-`) and JBC 2008 format (no hyphen pairs) have their own regexes.
  A block ends at the `Totals` row; the first two non-empty blocks of a document are the full-game boxes (later blocks are half/period splits).
* HTML tables (usab Hoop Summit pages, Wikipedia wikitables): header-driven column mapping (FG/FGA, 3P/3PA, FT/FTA, OR/DR/TOT, A, PF, ST, TO, BS/BLK, PTS/TP, MIN); rows with colspan/"Did not play", TEAM and TOTALS rows are dropped; Hoop Summit side taken from the block heading (World vs USA).
* Internal check on every row: PTS == 2*FGM + 3PM + FTM (`pts_ok` in `games_long.csv`; 5 of 932 lines fail, one Wikipedia line (McDonald's 2007) and four Hoop Summit usab lines; they are kept with the published PTS).
* OCR (macOS Vision via `ocr/ocr_pdf.swift`) is used only for image-only PDFs: McDonald's 2012 (West team only), McDonald's 2024, JBC 2012 (partial), JBC 2022.
  OCR rows are accepted only when three shooting pairs parse and are internally consistent (3PM<=FGM, 3PA<=FGA ...); then ONLY the shooting line is kept and PTS is derived as 2*FGM+3PM+FTM.
  Minutes/rebounds/assists etc. from OCR are never used (`ocr`=1 in games_long.csv). These are the "points-only/shooting-only" players.
* Name matching (`match_features.py`): normalise (accents, punctuation, Jr/Sr/II/III), convert "LAST, First"; candidate pids must have draft_year in [game_year+1, game_year+5]
  (identity file `tabular_names.csv`, 2000-2025 drafts only, so the 2025 games cannot match anybody). Rule 1 exact full name. Rule 2 (only if rule 1 finds nobody): same surname
  (or surname = last word of a compound/middle-named identity surname) and compatible first name (initials/2-letter forms, a fixed nickname table, or >=3-letter common prefix),
  flagged `lastname+first_prefix` in `matches.csv` (43 of 667 matches). Several candidates -> keep the one whose RSCI class year (draft_year - rsci_years_to_draft, rsci_top100=1) equals the game year, else log as ambiguous;
  a single candidate whose RSCI class differs from the game year by more than 1 is rejected. Every non-match, ambiguity and rejection is in `unmatched.csv` with a reason
  (most rows are `no_candidate_in_window`: undrafted players or players drafted after 2025).

## Coverage by draft class (identity file, pids with at least one line)
| draft class | drafted (identity) | players with a line | full line | shooting/points only | in MCD | in JBC | in Hoop Summit |
|---|---|---|---|---|---|---|---|
| 2007 | 65 | 8 | 8 | 0 | 8 | 0 | 4 |
| 2008 | 70 | 15 | 15 | 0 | 13 | 0 | 8 |
| 2009 | 71 | 17 | 17 | 0 | 14 | 5 | 10 |
| 2010 | 79 | 23 | 23 | 0 | 19 | 6 | 11 |
| 2011 | 88 | 18 | 18 | 0 | 15 | 3 | 11 |
| 2012 | 86 | 22 | 22 | 0 | 17 | 6 | 16 |
| 2013 | 91 | 19 | 18 | 1 | 15 | 6 | 10 |
| 2014 | 90 | 22 | 20 | 2 | 14 | 12 | 12 |
| 2015 | 81 | 27 | 26 | 1 | 25 | 19 | 15 |
| 2016 | 104 | 24 | 23 | 1 | 16 | 12 | 12 |
| 2017 | 132 | 31 | 31 | 0 | 27 | 17 | 13 |
| 2018 | 125 | 30 | 30 | 0 | 22 | 25 | 17 |
| 2019 | 137 | 32 | 32 | 0 | 21 | 19 | 13 |
| 2020 | 112 | 27 | 27 | 0 | 18 | 16 | 14 |
| 2021 | 233 | 16 | 16 | 0 | 7 | 10 | 7 |
| 2022 | 97 | 6 | 6 | 0 | 2 | 4 | 4 |
| 2023 | 101 | 18 | 16 | 2 | 16 | 11 | 1 |
| 2024 | 114 | 15 | 13 | 2 | 11 | 4 | 1 |
| 2025 | 106 | 10 | 1 | 9 | 10 | 0 | 0 |

Total rows in features.csv: 393 (players with a complete line in at least one game: 373; shooting/points-only: 20).

## Coverage by game
| game | year | lines parsed | matched to pid | with minutes/full line | format | source (Wayback timestamp + original URL, or Wikipedia revision) |
|---|---|---|---|---|---|---|
| Nike Hoop Summit | 2006 | 21 | 10 | 10 | usab_html | web.archive.org/web/20150907031652/http://www.usab.com/history/nike-hoop-summit/ixth-annual-nike-hoop-summit-2006.aspx |
| Nike Hoop Summit | 2007 | 21 | 14 | 14 | usab_html | web.archive.org/web/20150907023833/http://www.usab.com/history/nike-hoop-summit/xth-annual-nike-hoop-summit-2007.aspx |
| Nike Hoop Summit | 2008 | 21 | 10 | 10 | usab_html | web.archive.org/web/20150325163335/http://www.usab.com:80/history/nike-hoop-summit/xith-annual-nike-hoop-summit-2008.aspx |
| Nike Hoop Summit | 2009 | 20 | 9 | 9 | usab_html | web.archive.org/web/20150906234859/http://www.usab.com/history/nike-hoop-summit/xii-annual-nike-hoop-summit-2009.aspx |
| Nike Hoop Summit | 2010 | 20 | 14 | 14 | usab_html | web.archive.org/web/20150325182325/http://www.usab.com:80/history/nike-hoop-summit/xiii-annual-nike-hoop-summit-2010.aspx |
| Nike Hoop Summit | 2011 | 21 | 15 | 15 | usab_html | web.archive.org/web/20150325182254/http://www.usab.com:80/history/nike-hoop-summit/xiv-annual-nike-hoop-summit-2011.aspx |
| Nike Hoop Summit | 2012 | 21 | 9 | 9 | usab_html | web.archive.org/web/20150325182334/http://www.usab.com:80/history/nike-hoop-summit/xv-annual-nike-hoop-summit-2012.aspx |
| Nike Hoop Summit | 2013 | 21 | 13 | 13 | usab_html | web.archive.org/web/20150928174807/http://www.usab.com/history/nike-hoop-summit/xvi-annual-nike-hoop-summit-2013.aspx |
| Nike Hoop Summit | 2014 | 22 | 13 | 13 | usab_html | web.archive.org/web/20150907023503/http://www.usab.com/history/nike-hoop-summit/xvii-annual-nike-hoop-summit-2014.aspx |
| Nike Hoop Summit | 2015 | 22 | 16 | 16 | usab_html | web.archive.org/web/20150907022832/http://www.usab.com/history/nike-hoop-summit/xviii-annual-nike-hoop-summit-2015.aspx |
| Nike Hoop Summit | 2016 | 24 | 15 | 15 | usab_html | web.archive.org/web/20190720181209/https://www.usab.com/history/nike-hoop-summit/xix-annual-nike-hoop-summit-2016.aspx |
| Nike Hoop Summit | 2017 | 23 | 16 | 16 | usab_html | web.archive.org/web/20170809132409/https://www.usab.com/history/nike-hoop-summit/xx-annual-nike-hoop-summit-2017.aspx |
| Nike Hoop Summit | 2018 | 22 | 16 | 16 | usab_html | web.archive.org/web/20190720182707/https://www.usab.com/history/nike-hoop-summit/xxi-annual-nike-hoop-summit-2018.aspx |
| Nike Hoop Summit | 2019 | 24 | 16 | 16 | usab_html | web.archive.org/web/20191203224550/https://www.usab.com/history/nike-hoop-summit/xxii-annual-nike-hoop-summit-2019.aspx |
| Jordan Brand Classic (national game) | 2008 | 21 | 15 | 15 | official_E | web.archive.org/web/20110305031733/http://www.jordanbrandclassic.com:80/Archives/2008-jordan-brand-classic-national-box-score.html |
| Jordan Brand Classic (national game) | 2011 | 21 | 18 | 18 | official_A | web.archive.org/web/20150405231049/http://jordanbrandclassic.com/wp-content/uploads/archive/jbc-all-american2011-stats.pdf |
| Jordan Brand Classic (national game) | 2012 | 7 | 2 | 0 | ocr_shooting | web.archive.org/web/20150405200342/http://jordanbrandclassic.com/wp-content/uploads/archive/NationalBoxScore.pdf (OCR) |
| Jordan Brand Classic (national game) | 2013 | 22 | 16 | 16 | official_A | web.archive.org/web/20160816033647/http://jordanbrandclassic.com/wp-content/uploads/archive/NationalBoxScore2013.pdf |
| Jordan Brand Classic (national game) | 2014 | 23 | 20 | 20 | official_A | web.archive.org/web/20150406003813/http://jordanbrandclassic.com/wp-content/uploads/archive/2014nationalboxscore.pdf |
| Jordan Brand Classic (national game) | 2015 | 22 | 20 | 20 | official_A | web.archive.org/web/20150501031530/http://jordanbrandclassic.com/wp-content/uploads/2015/03/Box-Score-All-America-Game.pdf |
| Jordan Brand Classic (national game) | 2016 | 20 | 18 | 18 | official_A | web.archive.org/web/20161228103814/http://jordanbrandclassic.com/wp-content/uploads/2016/01/Jordan-Classic-National-Box-Score.pdf |
| Jordan Brand Classic (national game) | 2017 | 23 | 21 | 21 | official_A | web.archive.org/web/20170420150506/http://jordanbrandclassic.com/wp-content/uploads/2017/04/2017-Jordan-Brand-Classic-National-Boys-Game.pdf |
| Jordan Brand Classic (national game) | 2018 | 19 | 17 | 17 | official_A | web.archive.org/web/20180508185136/https://jordanbrandclassic.com/wp-content/uploads/2018/04/2018JBCBoysFinalBox.pdf |
| Jordan Brand Classic (national game) | 2019 | 23 | 17 | 17 | official_A | web.archive.org/web/20221207031941/https://jordanbrandclassic.com/wp-content/uploads/2019/04/Boys-Game.pdf |
| Jordan Brand Classic (national game) | 2022 | 20 | 14 | 0 | ocr_shooting | web.archive.org/web/20220516163000/https://jordanbrandclassic.com/wp-content/uploads/2022/04/Boys-Jordan-Game-4-15-22.pdf (OCR) |
| McDonald's All-American Boys | 2006 | 24 | 20 | 20 | wiki | en.wikipedia.org oldid=1366894093 (2026-07-30T20:05:30Z) |
| McDonald's All-American Boys | 2007 | 25 | 19 | 19 | wiki | en.wikipedia.org oldid=1376762048 (2026-09-26T02:41:11Z) |
| McDonald's All-American Boys | 2008 | 24 | 19 | 19 | wiki | en.wikipedia.org oldid=1369204920 (2026-08-13T13:50:07Z) |
| McDonald's All-American Boys | 2009 | 23 | 15 | 15 | wiki | en.wikipedia.org oldid=1369546550 (2026-08-15T16:57:24Z) |
| McDonald's All-American Boys | 2010 | 24 | 17 | 17 | wiki | en.wikipedia.org oldid=1346492601 (2026-04-01T03:30:04Z) |
| McDonald's All-American Boys | 2011 | 24 | 19 | 19 | official_A | web.archive.org/web/20110405070346/http://www.mcdonaldsallamerican.com:80/2011/mcdb.htm |
| McDonald's All-American Boys | 2012 | 11 | 8 | 0 | ocr_shooting | web.archive.org/web/20120417021031/http://mcdonaldsallamerican.com:80/2012BoysGameResults.pdf (OCR) |
| McDonald's All-American Boys | 2013 | 25 | 18 | 18 | official_A | web.archive.org/web/20130407023601/http://www.mcdepk.com:80/2013allamericangames/media/BoysGameStats.html |
| McDonald's All-American Boys | 2014 | 24 | 21 | 21 | official_A | web.archive.org/web/20140407071914/http://epkzone.com/2014allamericangames/media/2014AllAmericanGamesBoxScores.pdf |
| McDonald's All-American Boys | 2015 | 23 | 21 | 21 | official_A | web.archive.org/web/20150402125613/http://www.mcdonaldsallamerican.com/content/aag/en/MediaCenter/2015-game-materials/2015-Results-Boys/_jcr_content/featuredcontent/everything/file.res/2015%20McDonalds%20Boys%20Final%20Box.pdf |
| McDonald's All-American Boys | 2016 | 24 | 20 | 20 | official_A | web.archive.org/web/20160428225357/http://www.mcdonaldsallamerican.com:80/content/aag/en/MediaCenter/2016/2016-game-materials/2016-Boy-Results/_jcr_content/genericpagecontent/everything/file.res/2016%20McDonalds%20Boys%20Book.pdf |
| McDonald's All-American Boys | 2017 | 24 | 21 | 21 | official_A | web.archive.org/web/20180404145445/http://www.mcdonaldsallamerican.com:80/content/aag/en/MediaCenter/2017/2017-game-materials/BoysResults/_jcr_content/featuredcontent/everything/file.res/2017%20McDonalds%20Boys%20Box.pdf |
| McDonald's All-American Boys | 2018 | 21 | 18 | 18 | official_A | web.archive.org/web/20181003221127/https://www.mcdonaldsallamerican.com/content/dam/aag/AABOYS.pdf |
| McDonald's All-American Boys | 2019 | 23 | 19 | 19 | official_A | web.archive.org/web/20190405230440/https://www.mcdonaldsallamerican.com/content/dam/aag/2019-boys-game-final-score.pdf |
| McDonald's All-American Boys | 2022 | 20 | 16 | 16 | official_D | web.archive.org/web/20220523074107/https://www.mcdonaldsallamerican.com/content/dam/sites/allamerican/Content/Sponsor/MediaCenter/22_MCDAAG_Boys_Final.pdf |
| McDonald's All-American Boys | 2023 | 24 | 11 | 11 | official_D | web.archive.org/web/20230329180919/https://www.mcdonaldsallamerican.com/content/dam/sites/allamerican/Content/HomeContent/Box%20Score%20East%20at%20West%2029%20March.pdf |
| McDonald's All-American Boys | 2024 | 22 | 11 | 0 | ocr_shooting | web.archive.org/web/20240403053314/https://www.mcdonaldsallamerican.com/content/dam/sites/allamerican/2024-media-resources-files/McDonald%27s%20All%20American%20Boys%20Game%20Box%20Score.pdf (OCR) |
| McDonald's All-American Boys | 2025 | 23 | 10 | 10 | official_D | web.archive.org/web/20250516213210/https://www.mcdonaldsallamerican.com/content/dam/sites/allamerican/2025-media-resources-/Box%20Score%20West%20at%20East%2002%20April%20Boys.pdf |

## Known gaps (honest list)
* **No games exist for the high-school classes of 2020 and 2021 (draft classes 2021 and 2022 mostly): McDonald's, JBC and Hoop Summit were not played in spring 2020 (COVID) and 2021 (rosters were named but no box scores exist).**
  So the sanity targets of the 2020 high-school class (Scottie Barnes, Cade Cunningham) have NO box lines in any of these sources; this block does not help for them.
  Draft classes 2021 and 2022 are thin (class of 2021 played only the 2022 games; class of 2020 none).
* Jordan Brand Classic: 2005-2007, 2009-2010 national boxes exist only as low-quality scans (OCR garbles the stat columns), so they were NOT used; no JBC box located for 2020-2021 (not played), and 2023-2025 (not sourced; Wikipedia lists only rosters; the jordanbrandclassic.com 2023+ boxes were not found in the Wayback CDX). JBC regional/international games are not included (national all-star game only).
  JBC 2012 (OCR, 2 pids) and 2022 (OCR, shooting only) are weak.
* McDonald's 2012 (OCR, only the West team recovered), 2024 (OCR, shooting only), 2025 (no draft classes in the identity file).
* Nike Hoop Summit: usab.com pages 2006-2019 parsed; 2022 page has no box score; 2020-2021 not played; 2023-2025 not sourced. The 2018 World/USA assignment is from the usab block headings.
* Official documents sometimes omit non-playing roster members; players with no line simply have no row.
* pg_mcd/pg_jordan/pg_hoop_summit equal 0 when no line was found for that series (see column notes).
* Cached Wayback captures were taken years after the games (2010-2023); their content is the official box score but the capture time says nothing about the draft cutoff.
* Fuzzy (rule 2) matches: 43; review them in `matches.csv` (`match_rule`).

## Files
`features.csv` (the deliverable), `matches.csv` / `games_long.csv` / `unmatched.csv` (names, private), `games_qa.csv`, `provenance.csv`, `coverage_by_draft_class.csv`, `coverage_by_game.csv`,
`wiki_sources.csv`, `fetch_log.csv` (every network request with UTC time/status), `usab_cdx.txt`, `raw/` (all cached pages/PDFs/OCR text), scripts `pgfetch.py` (polite cached fetcher: >=2.0 s per host,
exponential backoff on 429/503, User-Agent "DraftDB-research-collector/1.0 (academic NBA draft-model research; contact ...)"), `fetch_texts.py`, `fetch_wiki.py`, `build_games.py`, `match_features.py`, `run_all.sh`
(offline re-run: `PG_OFFLINE=1 ./run_all.sh`; `vendor/` holds pdfminer.six installed with pip --target).

## Sanity check (names allowed here only)
* Anthony Edwards: MCD 2019: 21 min, 12 pts, 2 reb, 3 ast, 0 stl, 1 blk, 1 tov, FG 5/8, 3P 1/2, FT 1/4; JBC 2019: 18 min, 21 pts, 0 reb, 1 ast, 1 stl, 0 blk, 0 tov, FG 9/15, 3P 0/4, FT 3/4
* Darius Garland: MCD 2018: 20 min, 2 pts, 2 reb, 11 ast, 2 stl, 0 blk, 5 tov, FG 0/7, 3P 0/2, FT 2/2; JBC 2018: 20 min, 6 pts, 0 reb, 5 ast, 1 stl, 0 blk, 4 tov, FG 3/6, 3P 0/1, FT 0/0; HS 2018: 27 min, 16 pts, 4 reb, 5 ast, 2 stl, 0 blk, 2 tov, FG 6/13, 3P 4/7, FT 0/0
* Tyrese Maxey: MCD 2019: 19 min, 13 pts, 0 reb, 1 ast, 2 stl, 0 blk, 0 tov, FG 5/10, 3P 3/6, FT 0/0; JBC 2019: 25 min, 13 pts, 5 reb, 4 ast, 2 stl, 0 blk, 3 tov, FG 3/13, 3P 1/6, FT 6/6; HS 2019: 24 min, 8 pts, 3 reb, 2 ast, 1 stl, 0 blk, 1 tov, FG 3/8, 3P 0/3, FT 2/2
* Immanuel Quickley: MCD 2018: 17 min, 3 pts, 4 reb, 8 ast, 1 stl, 0 blk, 4 tov, FG 0/2, 3P 0/1, FT 3/4
* Scottie Barnes: no line (class of 2020: games not played)
* Cade Cunningham: no line (class of 2020: games not played)

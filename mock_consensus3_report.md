# Mock consensus batch 3 (new publishers, Wayback only)

Rows in mock_consensus3_ranks.csv: **1493** (pid, draft_year, site, rank, ts); distinct (site, year) captures accepted: **38**.

Method: Wayback CDX listings (narrow per-year URL prefixes for big hosts, whole-site listing for small hosts), candidates restricted to captures dated in the 40 days before the draft and before 22:00 UTC on draft day; up to 4 candidates per site/year fetched via `web/<ts>id_/<url>` (raw capture), ranked by ('final' in URL, year in URL, timestamp). Accepted capture = >= 25 class names found in page text, Spearman(rank, actual pick) >= 0.3, draft year in text, and no 'was selected'/'selected by' within 200 chars of a class-member name or the draft year. Rank = order of first appearance of the normalized full name (same rule as mock_consensus_collect_d.py). Among accepted candidates the best by ('final' in URL/title, timestamp) is kept. Rate >= 1.5 s, exponential backoff, 3 consecutive failures stop a site. Spearman is a scrape sanity check only. `final` column: 'final' appears in the URL or <title>.

## Publishers accepted per draft year

| year | n | publishers |
|---|---|---|
| 2015 | 0 | - |
| 2016 | 0 | - |
| 2017 | 0 | - |
| 2018 | 3 | bleacherreport, si, usatoday |
| 2019 | 4 | bleacherreport, nbcsports, sbnation, si |
| 2020 | 6 | basketballnews, bleacherreport, foxsports, sbnation, si, usatoday |
| 2021 | 2 | sbnation, si |
| 2022 | 7 | basketballnews, bleacherreport, foxsports, sbnation, si, usatoday, yahoo |
| 2023 | 4 | bleacherreport, foxsports, sbnation, usatoday |
| 2024 | 4 | bleacherreport, foxsports, sbnation, usatoday |
| 2025 | 6 | bleacherreport, foxsports, nbcsports, sbnation, si, usatoday |
| 2026 | 2 | nbcsports, si |

## Best-covered new publishers

- bleacherreport: 7 draft years (6 of them in 2019-2026): 2018, 2019, 2020, 2022, 2023, 2024, 2025
- si: 7 draft years (6 of them in 2019-2026): 2018, 2019, 2020, 2021, 2022, 2025, 2026
- sbnation: 7 draft years (7 of them in 2019-2026): 2019, 2020, 2021, 2022, 2023, 2024, 2025

## Per site / year (accepted captures)

| site | year | capture ts (UTC) | days before draft | names matched | drafted matched | Spearman vs pick | final | URL |
|---|---|---|---|---|---|---|---|---|
| basketballnews | 2020 | 20201103132050 | 14.44 | 30 | 30 | 0.583 | False | https://www.basketballnews.com/stories/nba-2020-draft-rumors-mock-draft-projection-top-pick-trade-matt-babcock-anthony-e |
| basketballnews | 2022 | 20220622233449 | 0.02 | 48 | 44 | 0.867 | False | https://www.basketballnews.com/stories/2022-nba-mock-draft-jabari-smith-chet-holmgren-jaden-ivey-paolo-banchero-magic-ro |
| bleacherreport | 2018 | 20180621142837 | -0.6 | 55 | 51 | 0.894 | True | https://bleacherreport.com/articles/2781931-2018-nba-mock-draft-final-2-round-predictions |
| bleacherreport | 2019 | 20190620131313 | -0.55 | 57 | 49 | 0.774 | True | https://bleacherreport.com/articles/2841103-bleacher-reports-final-2019-nba-mock-draft |
| bleacherreport | 2020 | 20201118113438 | -0.48 | 60 | 54 | 0.903 | True | https://bleacherreport.com/articles/2917825-bleacher-reports-final-2020-nba-mock-draft |
| bleacherreport | 2022 | 20220623194123 | -0.82 | 52 | 46 | 0.905 | True | https://bleacherreport.com/articles/10039256-brs-final-2022-nba-mock-draft |
| bleacherreport | 2023 | 20230622215545 | -0.91 | 56 | 51 | 0.898 | True | https://bleacherreport.com/articles/10080062-brs-final-2023-nba-mock-draft-full-2-round-predictions |
| bleacherreport | 2024 | 20240626173708 | -0.73 | 52 | 47 | 0.893 | False | https://bleacherreport.com/articles/10125089-2024-nba-mock-draft-full-2-round-predictions-with-one-week-to-go |
| bleacherreport | 2025 | 20250625020748 | -0.09 | 41 | 39 | 0.698 | False | https://bleacherreport.com/articles/10151924-2025-nba-mock-draft-pro-comparisons-and-full-2-round-predictions |
| foxsports | 2020 | 20201112022502 | 5.9 | 30 | 30 | 0.921 | False | https://www.foxsports.com/stories/nba/nba-mock-draft-6-0-one-week-left?shortlink=8c4d88ef&af_sub2=article&pid=spark&af_c |
| foxsports | 2022 | 20220623144408 | -0.61 | 30 | 30 | 0.852 | False | https://www.foxsports.com/stories/nba/nba-mock-draft-jabari-smith-to-orlando-magic-at-no-1 |
| foxsports | 2023 | 20230622194611 | -0.82 | 29 | 29 | 0.834 | False | https://www.foxsports.com/stories/nba/2023-nba-mock-draft-how-will-the-top-10-shake-out |
| foxsports | 2024 | 20240626204228 | -0.86 | 31 | 31 | 0.785 | False | https://www.foxsports.com/stories/nba/nba-mock-draft-2-0-what-will-atlanta-hawks-do-no-1-pick |
| foxsports | 2025 | 20250623193735 | 1.18 | 30 | 30 | 0.896 | False | https://www.foxsports.com/stories/nba/2025-nba-mock-draft-3-0-ace-bailey-falls-no-4 |
| nbcsports | 2019 | 20190620162507 | -0.68 | 28 | 28 | 0.755 | True | https://nba.nbcsports.com/2019/06/19/nba-mock-draft-7-0-the-final-mock-before-the-draft-starts/amp/ |
| nbcsports | 2025 | 20250624175412 | 0.25 | 54 | 49 | 0.899 | False | https://www.nbcsports.com/nba/news/2025-nba-mock-draft-3-0-76ers-take-edgecombe-grizzlies-select-sorber-after-bane-trade |
| nbcsports | 2026 | 20260624051936 | -0.22 | 54 | 54 | 0.804 | False | https://www.nbcsports.com/nba/news/nba-mock-draft-volume-4-aj-dybantsa-remains-wizards-pick-bucks-add-yaxel-lendeborg-af |
| sbnation | 2019 | 20190619123042 | 0.48 | 30 | 30 | 0.775 | False | https://www.sbnation.com/nba/2019/6/19/18680945/nba-mock-draft-2019-zion-williamson-ja-morant-pelicans-hawks-trade-rumor |
| sbnation | 2020 | 20201118194704 | -0.82 | 33 | 32 | 0.85 | True | https://www.sbnation.com/nba/2020/11/17/21561225/nba-mock-draft-2020-timberwolves-warriors-lamelo-ball?utm_campaign=sbna |
| sbnation | 2021 | 20210729192446 | -0.81 | 29 | 29 | 0.548 | True | https://www.sbnation.com/nba/2021/7/28/22596770/nba-mock-draft-2021-rumors-first-round-latest-projection |
| sbnation | 2022 | 20220623141522 | -0.59 | 30 | 30 | 0.784 | True | https://www.sbnation.com/nba/2022/6/23/23179568/nba-mock-draft-2022-final-projection-latest-rumors-trades-updates?utm_co |
| sbnation | 2023 | 20230622191242 | -0.8 | 56 | 51 | 0.895 | True | https://www.sbnation.com/nba/2023/6/22/23768774/nba-mock-draft-final-projection-two-rounds-intel |
| sbnation | 2024 | 20240626173708 | -0.73 | 30 | 30 | 0.793 | True | https://www.sbnation.com/nba/2024/6/18/24179880/nba-mock-draft-2024-after-nba-finals-latest-rumors |
| sbnation | 2025 | 20250624080129 | 0.67 | 28 | 28 | 0.811 | True | https://www.sbnation.com/nba/2025/6/23/24451800/nba-mock-draft-2025-updated-projection-with-nba-finals-now-over |
| si | 2018 | 20180621162850 | -0.69 | 55 | 50 | 0.866 | True | https://www.si.com/nba/2018/06/21/nba-mock-draft-2018-trade-rumors-final-picks-deandre-ayton-trae-young |
| si | 2019 | 20190620213003 | -0.9 | 31 | 28 | 0.644 | False | https://www.si.com/nba/2019/06/19/nba-mock-draft-social-media-clemson-university-zion-williamson-ja-morant-rj-barrett |
| si | 2020 | 20201118191416 | -0.8 | 58 | 53 | 0.878 | True | https://www.si.com/nba/2020/11/18/nba-mock-draft-final-projections-buzz-rumors?suid=5cc1c5cc24c17c4939490857 |
| si | 2021 | 20210729190915 | -0.8 | 52 | 45 | 0.889 | False | https://www.si.com/nba/2021/07/28/nba-mock-draft-2021-latest-buzz-rumors-cade-cunningham-jalen-green-evan-mobley |
| si | 2022 | 20220623211012 | -0.88 | 53 | 45 | 0.929 | True | https://www.si.com/nba/2022/06/23/nba-mock-draft-jabari-smith-chet-holmgren-paolo-banchero-final-projections |
| si | 2025 | 20250624023605 | 0.89 | 30 | 30 | 0.915 | True | https://www.si.com/nba/nba-mock-draft-final-first-round-projections-including-where-ace-bailey-lands |
| si | 2026 | 20260622033805 | 1.85 | 25 | 25 | 0.882 | False | https://www.si.com/nba/nba-mock-draft-first-board-with-lottery-odds-post-ncaa-tournament-projections |
| usatoday | 2018 | 20180621173253 | -0.73 | 29 | 29 | 0.759 | False | https://www.usatoday.com/story/sports/nba/2018/05/16/2018-nba-mock-draft-suns-kings-land-stars-deandre-ayton-luka-doncic |
| usatoday | 2020 | 20201118144510 | -0.61 | 30 | 30 | 0.841 | False | https://www.usatoday.com/story/sports/nba/2020/11/12/nba-mock-draft-lamelo-ball-anthony-edwards-no-1-pick/6235919002/ |
| usatoday | 2022 | 20220623183309 | -0.77 | 31 | 31 | 0.885 | False | https://www.usatoday.com/story/sports/nba/2022/06/22/nba-mock-draft-2022-magic-no-1-pick/7689404001/?ref=biztoc.com&cura |
| usatoday | 2023 | 20230604225218 | 17.05 | 30 | 30 | 0.713 | False | https://www.usatoday.com/story/sports/nba/2023/06/01/nba-mock-draft-wembanyama-to-spurs-1st-then-brandon-miller-to-horne |
| usatoday | 2024 | 20240626214855 | -0.91 | 29 | 28 | 0.854 | True | https://www.usatoday.com/story/sports/nba/2024/06/26/2024-nba-mock-draft-final-pre-draft-analysis/74205652007/ |
| usatoday | 2025 | 20250619030111 | 5.87 | 36 | 35 | 0.793 | False | https://www.usatoday.com/story/sports/nba/2025/06/18/nba-mock-draft-2025-ai-predictions-cooper-flagg-dylan-harper/842433 |
| yahoo | 2022 | 20220623212520 | -0.89 | 31 | 30 | 0.89 | False | https://sports.yahoo.com/2022-nba-mock-draft-sixers-191500118.html |

## Per site / year (not accepted, and why)

| site | year | status |
|---|---|---|
| basketballnews | 2015 | no candidate capture in 40-day window (CDX) |
| basketballnews | 2016 | no candidate capture in 40-day window (CDX) |
| basketballnews | 2017 | no candidate capture in 40-day window (CDX) |
| basketballnews | 2018 | no candidate capture in 40-day window (CDX) |
| basketballnews | 2019 | no candidate capture in 40-day window (CDX) |
| basketballnews | 2021 | rejected: 20210724064405: only 3 class names; 20210713055453: only 0 class names |
| basketballnews | 2023 | no candidate capture in 40-day window (CDX) |
| basketballnews | 2024 | rejected: 20240618224045: only 0 class names; 20240618214104: only 0 class names; 20240616125631: only 0 class names |
| basketballnews | 2025 | rejected: 20250622091237: only 0 class names; 20250621142733: only 0 class names; 20250619184738: only 0 class names |
| basketballnews | 2026 | rejected: 20260521022113: only 0 class names |
| bleacherreport | 2015 | rejected: 20150621013327: fetch failed/empty; 20150617142336: fetch failed/empty; 20150613012145: fetch failed/empty; 20150625170408: fetch failed/empty |
| bleacherreport | 2016 | rejected: 20160613110311: fetch failed/empty; 20160623190130: fetch failed/empty; 20160623190004: fetch failed/empty; 20160623183155: fetch failed/empty |
| bleacherreport | 2017 | rejected: 20170622215558: fetch failed/empty; 20170622155637: fetch failed/empty; 20170622154338: fetch failed/empty; 20170620000002: fetch failed/empty |
| bleacherreport | 2021 | no candidate capture in 40-day window (CDX) |
| bleacherreport | 2026 | no candidate capture in 40-day window (CDX) |
| si | 2015 | CDX listing failed (HTTP error/timeout) |
| si | 2016 | CDX listing failed (HTTP error/timeout) |
| si | 2017 | CDX listing failed (HTTP error/timeout) |
| si | 2023 | no candidate capture in 40-day window (CDX) |
| si | 2024 | no candidate capture in 40-day window (CDX) |
| yahoo | 2015 | site skipped: 3 consecutive failures (last HTTP 503) at https://web.archive.org/cdx/search/cdx?url=sports.yahoo.com/nba-mock*&filter=original:.*mock.?.?.?dr |
| yahoo | 2016 | site skipped: 3 consecutive failures (last HTTP 503) at https://web.archive.org/cdx/search/cdx?url=sports.yahoo.com/nba-mock*&filter=original:.*mock.?.?.?dr |
| yahoo | 2017 | site skipped: 3 consecutive failures (last HTTP 503) at https://web.archive.org/cdx/search/cdx?url=sports.yahoo.com/nba-mock*&filter=original:.*mock.?.?.?dr |
| yahoo | 2018 | site skipped: 3 consecutive failures (last HTTP 503) at https://web.archive.org/cdx/search/cdx?url=sports.yahoo.com/nba-mock*&filter=original:.*mock.?.?.?dr |
| yahoo | 2019 | site skipped: 3 consecutive failures (last HTTP 503) at https://web.archive.org/cdx/search/cdx?url=sports.yahoo.com/nba-mock*&filter=original:.*mock.?.?.?dr |
| yahoo | 2020 | site skipped: 3 consecutive failures (last HTTP 503) at https://web.archive.org/cdx/search/cdx?url=sports.yahoo.com/nba-mock*&filter=original:.*mock.?.?.?dr |
| yahoo | 2021 | rejected: 20210728042945: fetch failed/empty; 20210729201244: fetch failed/empty; 20210727195050: fetch failed/empty; 20210726145503: fetch failed/empty (further candidates not fetched: site stopped) |
| yahoo | 2023 | rejected: 20230622214411: only 8 class names; 20230622200603: only 5 class names; 20230622191952: only 4 class names; 20230622132122: only 7 class names (further candidates not fetched: site stopped) |
| yahoo | 2024 | site skipped: 3 consecutive failures (last HTTP 503) at https://web.archive.org/cdx/search/cdx?url=sports.yahoo.com/nba-mock*&filter=original:.*mock.?.?.?dr |
| yahoo | 2025 | rejected: 20250531105100: only 0 class names (further candidates not fetched: site stopped) |
| yahoo | 2026 | no candidate capture in 40-day window (CDX) |
| usatoday | 2015 | CDX listing failed (HTTP error/timeout) |
| usatoday | 2016 | CDX listing failed (HTTP error/timeout) |
| usatoday | 2017 | CDX listing failed (HTTP error/timeout) |
| usatoday | 2019 | no candidate capture in 40-day window (CDX) |
| usatoday | 2021 | no candidate capture in 40-day window (CDX) |
| usatoday | 2026 | rejected: 20260624105555: only 7 class names; 20260624104244: only 3 class names; 20260624103324: only 3 class names; 20260624103117: only 1 class names |
| nbcsports | 2015 | CDX listing failed (HTTP error/timeout) |
| nbcsports | 2016 | CDX listing failed (HTTP error/timeout) |
| nbcsports | 2017 | CDX listing failed (HTTP error/timeout) |
| nbcsports | 2018 | CDX listing failed (HTTP error/timeout) |
| nbcsports | 2020 | rejected: 20201116232302: only 7 class names |
| nbcsports | 2021 | no candidate capture in 40-day window (CDX) |
| nbcsports | 2022 | no candidate capture in 40-day window (CDX) |
| nbcsports | 2023 | rejected: 20230622162530: only 14 class names; 20230622162529: only 0 class names; 20230622162528: only 14 class names |
| nbcsports | 2024 | rejected: 20240524122939: only 0 class names |
| foxsports | 2015 | CDX listing failed (HTTP error/timeout) |
| foxsports | 2016 | CDX listing failed (HTTP error/timeout) |
| foxsports | 2017 | CDX listing failed (HTTP error/timeout) |
| foxsports | 2018 | CDX listing failed (HTTP error/timeout) |
| foxsports | 2019 | no candidate capture in 40-day window (CDX) |
| foxsports | 2021 | rejected: 20210625010427: only 14 class names; 20210723202402: only 0 class names |
| foxsports | 2026 | no candidate capture in 40-day window (CDX) |
| sbnation | 2015 | CDX listing failed (HTTP error/timeout) |
| sbnation | 2016 | CDX listing failed (HTTP error/timeout) |
| sbnation | 2017 | CDX listing failed (HTTP error/timeout) |
| sbnation | 2018 | CDX listing failed (HTTP error/timeout) |
| sbnation | 2026 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2015 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2016 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2017 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2018 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2019 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2020 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2021 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2022 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2023 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2024 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2025 | no candidate capture in 40-day window (CDX) |
| rookiescale | 2026 | no candidate capture in 40-day window (CDX) |
| noceilings | 2015 | no candidate capture in 40-day window (CDX) |
| noceilings | 2016 | no candidate capture in 40-day window (CDX) |
| noceilings | 2017 | no candidate capture in 40-day window (CDX) |
| noceilings | 2018 | no candidate capture in 40-day window (CDX) |
| noceilings | 2019 | no candidate capture in 40-day window (CDX) |
| noceilings | 2020 | no candidate capture in 40-day window (CDX) |
| noceilings | 2021 | no candidate capture in 40-day window (CDX) |
| noceilings | 2022 | no candidate capture in 40-day window (CDX) |
| noceilings | 2023 | no candidate capture in 40-day window (CDX) |
| noceilings | 2024 | no candidate capture in 40-day window (CDX) |
| noceilings | 2025 | no candidate capture in 40-day window (CDX) |
| noceilings | 2026 | no candidate capture in 40-day window (CDX) |

## Every fetched candidate capture (diagnostic)

| site | year | ts | class names | drafted matched | Spearman | results-language hits | URL |
|---|---|---|---|---|---|---|---|
| basketballnews | 2020 | 20201021221149 | 31 | 31 | 0.83 | 0 | https://www.basketballnews.com/stories/nba-mock-draft-rumors-2020-lamelo-ball-obi-toppin-james-wisem |
| basketballnews | 2020 | 20201103132050 | 30 | 30 | 0.58 | 0 | https://www.basketballnews.com/stories/nba-2020-draft-rumors-mock-draft-projection-top-pick-trade-ma |
| basketballnews | 2021 | 20210713055453 | 0 | 0 | None | 0 | https://www.basketballnews.com/_next/static/chunks/pages/draft/%5Bmock_draft_url%5D/players/%5Bdraft |
| basketballnews | 2021 | 20210724064405 | 3 | 3 | None | 0 | https://www.basketballnews.com/stories/2021-nba-mock-draft-matt-babcock-highlights-prospects-highest |
| basketballnews | 2022 | 20220519164958 | 1 | 1 | None | 0 | https://www.basketballnews.com/draft/2022-nba-mock-draft/players/nikola-jovic |
| basketballnews | 2022 | 20220621070830 | 1 | 1 | None | 0 | https://www.basketballnews.com/nba-draft/2022-nba-mock-draft/players/jabari-smith |
| basketballnews | 2022 | 20220622233449 | 48 | 44 | 0.87 | 0 | https://www.basketballnews.com/stories/2022-nba-mock-draft-jabari-smith-chet-holmgren-jaden-ivey-pao |
| basketballnews | 2022 | 20220623143343 | 1 | 1 | None | 0 | https://www.basketballnews.com/nba-draft/2022-nba-mock-draft/players/ryan-rollins |
| basketballnews | 2024 | 20240616125631 | 0 | 0 | None | 0 | https://www.basketballnews.com/stories/nba-draft-qa-with-matt-babcock-on-his-first-mock-draft-notabl |
| basketballnews | 2024 | 20240618214104 | 0 | 0 | None | 0 | https://www.basketballnews.com/stories/nba-mock-draft-wembanyama-easy-no-1-miller-at-2-henderson-3rd |
| basketballnews | 2024 | 20240618224045 | 0 | 0 | None | 0 | https://www.basketballnews.com/stories/nba-mock-draft-wembanyama-to-spurs-at-1-then-miller-to-hornet |
| basketballnews | 2025 | 20250619184738 | 0 | 0 | None | 0 | https://www.basketballnews.com/stories/nba-mock-draft-wembanyama-easy-no-1-miller-at-2-henderson-3rd |
| basketballnews | 2025 | 20250621142733 | 0 | 0 | None | 0 | https://www.basketballnews.com/stories/nba-draft-qa-with-matt-babcock-on-his-first-mock-draft-notabl |
| basketballnews | 2025 | 20250622091237 | 0 | 0 | None | 0 | https://www.basketballnews.com/stories/nba-mock-draft-wembanyama-to-spurs-at-1-then-miller-to-hornet |
| basketballnews | 2026 | 20260521022113 | 0 | 0 | None | 0 | https://www.basketballnews.com/stories/nba-mock-draft-wembanyama-to-spurs-at-1-then-miller-to-hornet |
| bleacherreport | 2018 | 20180605012015 | 45 | 36 | 0.75 | 0 | http://bleacherreport.com:80/articles/2750626-final-2018-nba-mock-draft-before-the-new-year-trae-you |
| bleacherreport | 2018 | 20180617192703 | 54 | 49 | 0.82 | 0 | https://bleacherreport.com/articles/2777981-nba-mock-draft-predicting-every-pick-as-2018-finals-begi |
| bleacherreport | 2018 | 20180618133948 | 54 | 49 | 0.82 | 0 | http://bleacherreport.com:80/articles/2777981-nba-mock-draft-predicting-every-pick-as-2018-finals-be |
| bleacherreport | 2018 | 20180621142837 | 55 | 51 | 0.89 | 0 | https://bleacherreport.com/articles/2781931-2018-nba-mock-draft-final-2-round-predictions |
| bleacherreport | 2019 | 20190523192652 | 28 | 26 | 0.57 | 0 | https://bleacherreport.com/articles/2811588-final-2019-nba-mock-draft-before-the-new-year |
| bleacherreport | 2019 | 20190619142100 | 30 | 30 | 0.84 | 0 | https://bleacherreport.com/articles/2841570-2019-nba-mock-draft-predictions-for-zion-williamson-and- |
| bleacherreport | 2019 | 20190620131313 | 57 | 49 | 0.77 | 0 | https://bleacherreport.com/articles/2841103-bleacher-reports-final-2019-nba-mock-draft |
| bleacherreport | 2019 | 20190620140010 | 30 | 30 | 0.7 | 0 | https://bleacherreport.com/articles/2841703-nba-mock-draft-2019-1st-round-predictions-and-top-prospe |
| bleacherreport | 2020 | 20201022043303 | 0 | 0 | None | 0 | https://bleacherreport.com/articles/2875010-nba-all-star-rosters-2020-final-mock-draft-for-team-gian |
| bleacherreport | 2020 | 20201112035617 | 1 | 0 | None | 0 | https://bleacherreport.com/articles/2715270-latest-nba-mock-draft-post-nba-finals-edition |
| bleacherreport | 2020 | 20201118113438 | 60 | 54 | 0.9 | 0 | https://bleacherreport.com/articles/2917825-bleacher-reports-final-2020-nba-mock-draft |
| bleacherreport | 2020 | 20201118162219 | 30 | 30 | 0.68 | 0 | https://bleacherreport.com/articles/2881349-2020-nba-mock-draft-questions-loom-during-basketball-hia |
| bleacherreport | 2022 | 20220617094733 | 30 | 30 | 0.84 | 0 | https://bleacherreport.com/articles/10037673-2022-nba-mock-draft-how-3-trades-can-shake-up-the-top-1 |
| bleacherreport | 2022 | 20220620145323 | 5 | 5 | None | 0 | https://bleacherreport.com/articles/10039210-knicks-2022-nba-mock-draft-roundup-of-br-staff-expert-p |
| bleacherreport | 2022 | 20220621221435 | 3 | 3 | None | 0 | https://bleacherreport.com/articles/10039215-76ers-2022-nba-mock-draft-roundup-of-br-staff-expert-pi |
| bleacherreport | 2022 | 20220623194123 | 52 | 46 | 0.91 | 0 | https://bleacherreport.com/articles/10039256-brs-final-2022-nba-mock-draft |
| bleacherreport | 2023 | 20230616024622 | 2 | 2 | None | 0 | https://bleacherreport.com/articles/10079249-lakers-ideal-2023-nba-mock-draft-and-players-to-target- |
| bleacherreport | 2023 | 20230621202108 | 56 | 52 | 0.88 | 0 | https://bleacherreport.com/articles/10077669-brs-final-2023-nba-mock-draft-full-2-round-predictions |
| bleacherreport | 2023 | 20230621205444 | 56 | 52 | 0.88 | 0 | https://bleacherreport.com/articles/10077669-2023-nba-mock-draft-updated-full-2-round-predictions |
| bleacherreport | 2023 | 20230622215545 | 56 | 51 | 0.9 | 0 | https://bleacherreport.com/articles/10080062-brs-final-2023-nba-mock-draft-full-2-round-predictions |
| bleacherreport | 2024 | 20240626042627 | 50 | 44 | 0.83 | 0 | https://bleacherreport.com/articles/10118310-2024-nba-mock-draft-lottery-simulation-and-full-2-round |
| bleacherreport | 2024 | 20240626055651 | 3 | 3 | None | 0 | https://bleacherreport.com/articles/10120766-bronny-james-goes-undrafted-in-espns-2024-nba-mock-draf |
| bleacherreport | 2024 | 20240626173708 | 52 | 47 | 0.89 | 0 | https://bleacherreport.com/articles/10125089-2024-nba-mock-draft-full-2-round-predictions-with-one-w |
| bleacherreport | 2024 | 20240626195301 | 17 | 16 | 0.67 | 0 | https://bleacherreport.com/articles/10125940-brs-final-2024-nba-mock-draft-full-2-round-predictions |
| bleacherreport | 2025 | 20250615095850 | 39 | 37 | 0.83 | 0 | https://bleacherreport.com/articles/10146847-2025-nba-mock-draft-pro-comparisons-and-full-2-round-pr |
| bleacherreport | 2025 | 20250625020748 | 41 | 39 | 0.7 | 0 | https://bleacherreport.com/articles/10151924-2025-nba-mock-draft-pro-comparisons-and-full-2-round-pr |
| foxsports | 2020 | 20201027044815 | 30 | 29 | 0.88 | 0 | https://www.foxsports.com/stories/nba/nba-mock-draft-3-0 |
| foxsports | 2020 | 20201112022502 | 30 | 30 | 0.92 | 0 | https://www.foxsports.com/stories/nba/nba-mock-draft-6-0-one-week-left?shortlink=8c4d88ef&af_sub2=ar |
| foxsports | 2021 | 20210625010427 | 14 | 14 | 0.73 | 0 | https://www.foxsports.com/stories/nba/nba-mock-draft-2021-forecasting-how-the-lottery-will-unfold-an |
| foxsports | 2021 | 20210723202402 | 0 | 0 | None | 0 | https://www.foxsports.com/stories/nba/nba-mock-draft-first-round-picks |
| foxsports | 2022 | 20220623073955 | 30 | 30 | 0.83 | 0 | https://www.foxsports.com/stories/nba/nba-mock-draft-jabari-smith-remains-safe-bet-for-magic-at-no-1 |
| foxsports | 2022 | 20220623144408 | 30 | 30 | 0.85 | 0 | https://www.foxsports.com/stories/nba/nba-mock-draft-jabari-smith-to-orlando-magic-at-no-1 |
| foxsports | 2023 | 20230531162613 | 28 | 28 | 0.67 | 0 | https://www.foxsports.com/stories/nba/2023-nba-mock-draft-plenty-of-intrigue-following-victor-wemban |
| foxsports | 2023 | 20230622183527 | 30 | 30 | 0.89 | 0 | https://www.foxsports.com/stories/nba/2023-nba-mock-draft-3-0-who-snags-scoot-henderson-brandon-mill |
| foxsports | 2023 | 20230622194611 | 29 | 29 | 0.83 | 0 | https://www.foxsports.com/stories/nba/2023-nba-mock-draft-how-will-the-top-10-shake-out |
| foxsports | 2024 | 20240517234306 | 30 | 30 | 0.78 | 0 | https://www.foxsports.com/stories/nba/2024-nba-mock-draft-1-0-how-high-will-zach-edey-donovan-clinga |
| foxsports | 2024 | 20240625190039 | 30 | 28 | 0.87 | 0 | https://www.foxsports.com/stories/nba/2024-nba-mock-draft-hawks-take-alex-sarr-top-pick-donovan-clin |
| foxsports | 2024 | 20240626204207 | 30 | 28 | 0.89 | 0 | https://www.foxsports.com/stories/nba/2024-nba-mock-draft-2-0-alex-sarr-falls-no-3-zach-edey-taken-t |
| foxsports | 2024 | 20240626204228 | 31 | 31 | 0.79 | 0 | https://www.foxsports.com/stories/nba/nba-mock-draft-2-0-what-will-atlanta-hawks-do-no-1-pick |
| foxsports | 2025 | 20250602113841 | 30 | 30 | 0.84 | 0 | https://www.foxsports.com/stories/nba/2025-nba-mock-draft-cooper-flagg-lottery |
| foxsports | 2025 | 20250612212120 | 30 | 30 | 0.86 | 0 | https://www.foxsports.com/stories/nba/2025-nba-mock-draft-vj-edgecombe-moves-top-3-cedric-coward-mak |
| foxsports | 2025 | 20250614073740 | 25 | 25 | 0.66 | 0 | https://www.foxsports.com/stories/nba/2025-nba-mock-draft-2-0-who-goes-after-cooper-flagg |
| foxsports | 2025 | 20250623193735 | 30 | 30 | 0.9 | 0 | https://www.foxsports.com/stories/nba/2025-nba-mock-draft-3-0-ace-bailey-falls-no-4 |
| nbcsports | 2019 | 20190616165951 | 0 | 0 | None | 0 | https://nba.nbcsports.com/2019/06/15/nbc-sports-rotoworld-nba-draft-preview-show-and-mock-draft/feed |
| nbcsports | 2019 | 20190620130430 | 28 | 28 | 0.76 | 0 | https://nba.nbcsports.com/2019/06/19/nba-mock-draft-7-0-the-final-mock-before-the-draft-starts/ |
| nbcsports | 2019 | 20190620155958 | 0 | 0 | None | 0 | https://nba.nbcsports.com/2019/06/19/nba-mock-draft-7-0-the-final-mock-before-the-draft-starts/feed/ |
| nbcsports | 2019 | 20190620162507 | 28 | 28 | 0.76 | 0 | https://nba.nbcsports.com/2019/06/19/nba-mock-draft-7-0-the-final-mock-before-the-draft-starts/amp/ |
| nbcsports | 2020 | 20201116232302 | 7 | 7 | None | 0 | https://nba.nbcsports.com/2020/11/16/pbt-podcast-2020-nba-mock-draft-and-some-james-harden-talk/ |
| nbcsports | 2023 | 20230622162528 | 14 | 14 | 0.76 | 0 | https://nba.nbcsports.com/2023/06/21/consensus-nba-mock-draft-the-lottery-picks-starting-with-wemban |
| nbcsports | 2023 | 20230622162529 | 0 | 0 | None | 0 | https://nba.nbcsports.com/2023/06/21/consensus-nba-mock-draft-the-lottery-picks-starting-with-wemban |
| nbcsports | 2023 | 20230622162530 | 14 | 14 | 0.76 | 0 | https://nba.nbcsports.com/2023/06/21/consensus-nba-mock-draft-the-lottery-picks-starting-with-wemban |
| nbcsports | 2024 | 20240524122939 | 0 | 0 | None | 0 | https://www.nbcsports.com/nba/news/nba-mock-draft-7-0-the-final-mock-before-the-draft-starts |
| nbcsports | 2025 | 20250602211925 | 29 | 29 | 0.5 | 0 | https://www.nbcsports.com/nba/news/2025-nba-mock-draft-2-0-thunder-add-thomas-sorber-and-rasheer-fle |
| nbcsports | 2025 | 20250624175412 | 54 | 49 | 0.9 | 0 | https://www.nbcsports.com/nba/news/2025-nba-mock-draft-3-0-76ers-take-edgecombe-grizzlies-select-sor |
| nbcsports | 2026 | 20260526131119 | 28 | 28 | 0.83 | 0 | https://www.nbcsports.com/nba/news/nba-mock-draft-vol-2-aj-dybantsa-remains-in-the-top-spot |
| nbcsports | 2026 | 20260607082536 | 29 | 29 | 0.82 | 0 | https://www.nbcsports.com/nba/news/2026-nba-mock-draft-vol-1-wizards-land-first-overall-pick |
| nbcsports | 2026 | 20260624051936 | 54 | 54 | 0.8 | 0 | https://www.nbcsports.com/nba/news/nba-mock-draft-volume-4-aj-dybantsa-remains-wizards-pick-bucks-ad |
| sbnation | 2019 | 20190517205814 | 30 | 30 | 0.73 | 0 | https://www.sbnation.com/nba/2019/5/14/18536853/nba-mock-draft-2019-lottery-zion-williamson-new-orle |
| sbnation | 2019 | 20190619123042 | 30 | 30 | 0.78 | 0 | https://www.sbnation.com/nba/2019/6/19/18680945/nba-mock-draft-2019-zion-williamson-ja-morant-pelica |
| sbnation | 2020 | 20201108174625 | 30 | 30 | 0.87 | 0 | https://www.sbnation.com/nba/2020/11/5/21546769/nba-mock-draft-2020-lamelo-ball-anthony-edwards-warr |
| sbnation | 2020 | 20201117183756 | 30 | 30 | 0.87 | 0 | https://www.sbnation.com/nba/2020/11/12/21557121/nba-mock-draft-2020-team-writers-picks-anthony-edwa |
| sbnation | 2020 | 20201118194704 | 33 | 32 | 0.85 | 0 | https://www.sbnation.com/nba/2020/11/17/21561225/nba-mock-draft-2020-timberwolves-warriors-lamelo-ba |
| sbnation | 2021 | 20210628052948 | 28 | 27 | 0.78 | 0 | https://www.sbnation.com/nba/2021/6/17/22534812/nba-mock-draft-2021-lottery-order-first-round-cade-c |
| sbnation | 2021 | 20210727233002 | 29 | 28 | 0.76 | 0 | https://www.sbnation.com/nba/2021/6/22/22539039/nba-mock-draft-2021-instant-first-round-picks-detroi |
| sbnation | 2021 | 20210728181033 | 29 | 29 | 0.75 | 0 | https://www.sbnation.com/nba/2021/7/22/22583959/nba-mock-draft-2021-sb-nation-bloggers-make-picks |
| sbnation | 2021 | 20210729192446 | 29 | 29 | 0.55 | 0 | https://www.sbnation.com/nba/2021/7/28/22596770/nba-mock-draft-2021-rumors-first-round-latest-projec |
| sbnation | 2022 | 20220622160154 | 28 | 28 | 0.78 | 0 | https://www.sbnation.com/nba/2022/5/17/23060018/nba-mock-draft-2022-instant-first-round-picks-final- |
| sbnation | 2022 | 20220623121048 | 30 | 30 | 0.65 | 2 | https://www.sbnation.com/nba/2022/6/8/23154102/nba-mock-draft-jaden-ivey-scouting-report-highlights- |
| sbnation | 2022 | 20220623122421 | 33 | 33 | 0.79 | 0 | https://www.sbnation.com/nba/2022/6/15/23166148/nba-mock-draft-2022-updated-projection-after-withdra |
| sbnation | 2022 | 20220623141522 | 30 | 30 | 0.78 | 0 | https://www.sbnation.com/nba/2022/6/23/23179568/nba-mock-draft-2022-final-projection-latest-rumors-t |
| sbnation | 2023 | 20230622135601 | 28 | 28 | 0.86 | 0 | https://www.sbnation.com/nba/2023/6/12/23755905/nba-mock-draft-2023-first-round-update-victor-wemban |
| sbnation | 2023 | 20230622142259 | 30 | 30 | 0.75 | 0 | https://www.sbnation.com/nba/2023/6/19/23761689/nba-mock-draft-2023-first-round-latest-projection-pe |
| sbnation | 2023 | 20230622172716 | 31 | 31 | 0.84 | 0 | https://www.sbnation.com/nba/2023/6/20/23764760/2023-nba-mock-draft-projections-victor-wembanyama-sc |
| sbnation | 2023 | 20230622191242 | 56 | 51 | 0.89 | 0 | https://www.sbnation.com/nba/2023/6/22/23768774/nba-mock-draft-final-projection-two-rounds-intel |
| sbnation | 2024 | 20240626135316 | 28 | 28 | 0.66 | 0 | https://www.sbnation.com/nba/2024/6/10/24172870/nba-mock-draft-2024-perfect-picks-for-every-team |
| sbnation | 2024 | 20240626145256 | 29 | 29 | 0.79 | 0 | https://www.sbnation.com/nba/2024/6/25/24185235/nba-mock-draft-projections-alex-sarr-zaccharie-risac |
| sbnation | 2024 | 20240626150925 | 29 | 29 | 0.8 | 0 | https://www.sbnation.com/nba/2024/6/26/24186156/nba-mock-draft-2024-final-projection-first-round-haw |
| sbnation | 2024 | 20240626173708 | 30 | 30 | 0.79 | 0 | https://www.sbnation.com/nba/2024/6/18/24179880/nba-mock-draft-2024-after-nba-finals-latest-rumors |
| sbnation | 2025 | 20250613185000 | 30 | 30 | 0.76 | 0 | https://www.sbnation.com/nba/2025/6/12/24447320/nba-mock-draft-2025-perfect-picks-for-each-team |
| sbnation | 2025 | 20250614032433 | 27 | 27 | 0.76 | 0 | https://www.sbnation.com/nba/2025/5/1/24420930/nba-mock-draft-2025-pre-lottery-update-changes-inside |
| sbnation | 2025 | 20250618130902 | 29 | 29 | 0.84 | 0 | https://www.sbnation.com/nba/2025/6/2/24440050/nba-mock-draft-2025-first-round-projection-june-after |
| sbnation | 2025 | 20250624080129 | 28 | 28 | 0.81 | 0 | https://www.sbnation.com/nba/2025/6/23/24451800/nba-mock-draft-2025-updated-projection-with-nba-fina |
| si | 2018 | 20180620012747 | 54 | 49 | 0.87 | 0 | https://www.si.com/nba/2018/06/19/nba-mock-draft-2018-rumors-deandre-ayton-marvin-bagley-trae-young- |
| si | 2018 | 20180620172355 | 29 | 29 | 0.53 | 0 | https://www.si.com/nba/2018/06/20/nba-mock-draft-2018-youtube-highlights-trae-young-michael-porter-j |
| si | 2018 | 20180621162756 | 4 | 4 | None | 0 | https://www.si.com/nba/2018/06/21/lonnie-walker-iv-nba-draft-2018-mock-draft-miami-kyrie-irving |
| si | 2018 | 20180621162850 | 55 | 50 | 0.87 | 0 | https://www.si.com/nba/2018/06/21/nba-mock-draft-2018-trade-rumors-final-picks-deandre-ayton-trae-yo |
| si | 2019 | 20190618211738 | 0 | 0 | None | 0 | https://www.si.com/nba/2019/05/14/nba-mock-draft-pelicans-grizzlies-knicks-lakers-zion-williamson-ja |
| si | 2019 | 20190618223246 | 58 | 48 | 0.89 | 0 | https://www.si.com/nba/2019/06/17/nba-mock-draft-anthony-davis-trade-zion-williamson-ja-morant-rj-ba |
| si | 2019 | 20190620131342 | 58 | 48 | 0.89 | 0 | https://www.si.com/nba/2019/06/19/nba-mock-draft-trade-rumors-zion-williamson-ja-morant-rj-barrett |
| si | 2019 | 20190620213003 | 31 | 28 | 0.64 | 0 | https://www.si.com/nba/2019/06/19/nba-mock-draft-social-media-clemson-university-zion-williamson-ja- |
| si | 2020 | 20201117221601 | 57 | 50 | 0.86 | 0 | https://www.si.com/nba/2020/10/14/nba-mock-draft-projections-post-finals |
| si | 2020 | 20201118042335 | 58 | 52 | 0.87 | 0 | https://www.si.com/nba/2020/11/16/nba-mock-draft-latest-updates-rumors-daily-cover |
| si | 2020 | 20201118191416 | 58 | 53 | 0.88 | 0 | https://www.si.com/nba/2020/11/18/nba-mock-draft-final-projections-buzz-rumors?suid=5cc1c5cc24c17c49 |
| si | 2021 | 20210727232947 | 52 | 46 | 0.91 | 0 | https://www.si.com/nba/2021/07/20/nba-mock-draft-cade-cunningham-evan-mobley-jalen-green |
| si | 2021 | 20210728154048 | 52 | 44 | 0.91 | 0 | https://www.si.com/nba/2021/07/26/nba-mock-draft-2021-latest-buzz-rumors-cade-cunningham-jalen-green |
| si | 2021 | 20210729174337 | 52 | 46 | 0.91 | 0 | https://www.si.com/nba/2021/07/29/nba-mock-draft-2021-rumors-cade-cunningham-jalen-green-evan-mobley |
| si | 2021 | 20210729190915 | 52 | 45 | 0.89 | 0 | https://www.si.com/nba/2021/07/28/nba-mock-draft-2021-latest-buzz-rumors-cade-cunningham-jalen-green |
| si | 2022 | 20220623075232 | 9 | 9 | None | 0 | https://www.si.com/nba/2022/06/22/nba-draft-mock-draft-rankings-jabari-smith-chet-holmgren |
| si | 2022 | 20220623132615 | 53 | 47 | 0.86 | 0 | https://www.si.com/nba/2022/06/06/nba-mock-draft-jabari-smith-chet-holmgren-paolo-banchero-jaden-ive |
| si | 2022 | 20220623180619 | 52 | 46 | 0.93 | 0 | https://www.si.com/nba/2022/06/20/nba-mock-draft-jabari-smith-chet-holmgren-paolo-banchero-latest-bu |
| si | 2022 | 20220623211012 | 53 | 45 | 0.93 | 0 | https://www.si.com/nba/2022/06/23/nba-mock-draft-jabari-smith-chet-holmgren-paolo-banchero-final-pro |
| si | 2025 | 20250517133149 | 28 | 28 | 0.79 | 0 | https://www.si.com/nba/2025-nba-mock-draft-how-the-first-round-projects-after-ncaa-tournament |
| si | 2025 | 20250604141220 | 32 | 32 | 0.88 | 0 | https://www.si.com/nba/2025-nba-mock-draft-after-ncaa-deadline-older-prospects-getting-more-consider |
| si | 2025 | 20250620054128 | 29 | 29 | 0.83 | 0 | https://www.si.com/nba/2025-nba-mock-draft-cooper-flagg-to-mavericks-all-first-round-picks-after-lot |
| si | 2025 | 20250624023605 | 30 | 30 | 0.92 | 0 | https://www.si.com/nba/nba-mock-draft-final-first-round-projections-including-where-ace-bailey-lands |
| si | 2026 | 20260618071321 | 30 | 30 | 0.74 | 0 | https://www.si.com/nba/mock-draft-2026-how-first-round-shakes-out-after-ncaa-withdrawal-deadline |
| si | 2026 | 20260618110342 | 29 | 29 | 0.78 | 0 | https://www.si.com/nba/2026-nba-mock-draft-where-top-players-land-after-wizards-win-lottery |
| si | 2026 | 20260622033805 | 25 | 25 | 0.88 | 0 | https://www.si.com/nba/nba-mock-draft-first-board-with-lottery-odds-post-ncaa-tournament-projections |
| usatoday | 2018 | 20180523110958 | 2 | 2 | None | 0 | https://ftw.usatoday.com/2018/05/nba-mock-draft-2018-roundup-phoenix-suns-deandre-ayton-luka-doncic/ |
| usatoday | 2018 | 20180617070011 | 30 | 30 | 0.55 | 0 | https://www.usatoday.com/story/sports/nba/2018/06/15/nba-mock-draft-michael-porter-jaren-jackson-mar |
| usatoday | 2018 | 20180621152342 | 29 | 29 | 0.86 | 0 | https://www.usatoday.com/story/sports/nba/2018/06/20/2018-nba-mock-draft-marvin-bagley-michael-porte |
| usatoday | 2018 | 20180621173253 | 29 | 29 | 0.76 | 0 | https://www.usatoday.com/story/sports/nba/2018/05/16/2018-nba-mock-draft-suns-kings-land-stars-deand |
| usatoday | 2020 | 20201117140730 | 30 | 30 | 0.8 | 0 | https://www.usatoday.com/story/sports/nba/2020/11/05/nba-mock-draft-lamelo-ball-dips-riskier-pick-an |
| usatoday | 2020 | 20201117221601 | 30 | 30 | 0.84 | 0 | https://www.usatoday.com/story/sports/nba/2020/10/29/nba-mock-draft-lamelo-ball-anthony-edwards-firs |
| usatoday | 2020 | 20201118143701 | 30 | 30 | 0.84 | 0 | https://www.usatoday.com/story/sports/nba/2020/11/17/nba-mock-draft-anthony-edwards-lamelo-ball/6325 |
| usatoday | 2020 | 20201118144510 | 30 | 30 | 0.84 | 0 | https://www.usatoday.com/story/sports/nba/2020/11/12/nba-mock-draft-lamelo-ball-anthony-edwards-no-1 |
| usatoday | 2022 | 20220622183738 | 0 | 0 | None | 0 | https://www.usatoday.com/story/sports/nba/2022/05/18/nba-mock-draft-no-clear-cut-no-1-pick-magic/981 |
| usatoday | 2022 | 20220623183309 | 31 | 31 | 0.89 | 0 | https://www.usatoday.com/story/sports/nba/2022/06/22/nba-mock-draft-2022-magic-no-1-pick/7689404001/ |
| usatoday | 2023 | 20230604091105 | 30 | 30 | 0.77 | 0 | https://www.usatoday.com/story/sports/nba/2023/05/17/nba-mock-draft-lottery-victor-wembanyama/702217 |
| usatoday | 2023 | 20230604225218 | 30 | 30 | 0.71 | 0 | https://www.usatoday.com/story/sports/nba/2023/06/01/nba-mock-draft-wembanyama-to-spurs-1st-then-bra |
| usatoday | 2024 | 20240624211905 | 29 | 28 | 0.86 | 0 | https://www.usatoday.com/story/sports/nba/2024/06/20/nba-mock-draft-post-finals-risacher-sarr-remain |
| usatoday | 2024 | 20240626171117 | 1 | 1 | None | 0 | https://ftw.usatoday.com/2024/06/nba-mock-draft-yahoo-bronny-james-lakers |
| usatoday | 2024 | 20240626171726 | 2 | 2 | None | 0 | https://ftw.usatoday.com/2024/06/nba-mock-draft-espn-lakers-zach-edey-2024 |
| usatoday | 2024 | 20240626214855 | 29 | 28 | 0.85 | 0 | https://www.usatoday.com/story/sports/nba/2024/06/26/2024-nba-mock-draft-final-pre-draft-analysis/74 |
| usatoday | 2025 | 20250606054937 | 27 | 27 | 0.69 | 0 | https://www.usatoday.com/story/sports/nba/2025/05/31/nba-mock-draft-2025-meta-ai-predictions/8394753 |
| usatoday | 2025 | 20250607053518 | 27 | 27 | 0.61 | 0 | https://www.usatoday.com/story/sports/nba/2025/06/03/nba-mock-draft-2025-grok-ai-predictions/8400781 |
| usatoday | 2025 | 20250607190730 | 27 | 27 | 0.7 | 0 | https://www.usatoday.com/story/sports/nba/2025/06/06/nba-mock-draft-2025-chatgpt-ai-predictions/8405 |
| usatoday | 2025 | 20250619030111 | 36 | 35 | 0.79 | 0 | https://www.usatoday.com/story/sports/nba/2025/06/18/nba-mock-draft-2025-ai-predictions-cooper-flagg |
| usatoday | 2026 | 20260624103117 | 1 | 1 | None | 0 | https://www.usatoday.com/story/sports/nba/2026/06/23/toronto-raptors-final-mock-draft-bennett-stirtz |
| usatoday | 2026 | 20260624103324 | 3 | 3 | None | 0 | https://www.usatoday.com/story/sports/nba/2026/06/23/nate-ament-mock-draft-final-intel-prediction/90 |
| usatoday | 2026 | 20260624104244 | 3 | 3 | None | 0 | https://www.usatoday.com/story/sports/nba/2026/06/23/los-angeles-lakers-final-mock-draft-koa-peat/90 |
| usatoday | 2026 | 20260624105555 | 7 | 7 | None | 0 | https://www.usatoday.com/story/sports/nba/2026/06/23/cameron-carr-mock-draft-final-intel-prediction/ |
| yahoo | 2022 | 20220622205117 | 13 | 13 | 0.51 | 0 | https://sports.yahoo.com/2022-nba-mock-drafts-final-151441560.html |
| yahoo | 2022 | 20220623145015 | 31 | 31 | 0.85 | 0 | https://sports.yahoo.com/2022-nba-mock-draft-projecting-172600778.html |
| yahoo | 2022 | 20220623150411 | 7 | 4 | None | 1 | https://sports.yahoo.com/2022-nba-mock-draft-where-150929565.html?src=rss |
| yahoo | 2022 | 20220623212520 | 31 | 30 | 0.89 | 0 | https://sports.yahoo.com/2022-nba-mock-draft-sixers-191500118.html |
| yahoo | 2023 | 20230622132122 | 7 | 7 | None | 0 | https://sports.yahoo.com/2023-nba-mock-draft-roundup-210531494.html?src=rss |
| yahoo | 2023 | 20230622191952 | 4 | 4 | None | 0 | https://sports.yahoo.com/2023-nba-mock-draft-roundup-213001885.html?src=rss |
| yahoo | 2023 | 20230622200603 | 5 | 5 | None | 0 | https://sports.yahoo.com/2023-nba-mock-draft-three-152503306.html?src=rss |
| yahoo | 2023 | 20230622214411 | 8 | 5 | None | 0 | https://sports.yahoo.com/nba-mock-draft-2023-phoenix-005557723.html?src=rss |
| yahoo | 2025 | 20250531105100 | 0 | 0 | None | 0 | https://sports.yahoo.com/nba-mock-draft-30-anthony-edwards-moves-to-no-1-164633107.html |

## Sites stopped

- yahoo: 3 consecutive failures (last HTTP 503) at https://web.archive.org/cdx/search/cdx?url=sports.yahoo.com/nba-mock*&filter=original:.*mock.?.?.?dr

## Not attempted / limitations
- The Athletic (paywalled) and ESPN Insider mocks skipped by instruction.
- Wayback CDX was heavily degraded (503/504/timeouts, mid-stream truncation); a CDX miss therefore does not prove that a publisher had no mock that year, and URL-prefix patterns for big hosts only cover the known URL layouts (see pats() in mock_consensus3_collect.py).
- Pages that render the mock from JavaScript only (no names in the raw capture) fail the >= 25 names test and are listed above as rejected.
- Unmatched/diagnostic rows: mock_consensus3_unmatched.csv (ambiguous class names, top-30 picks absent from an accepted page, alternative valid captures not used).

## Run notes (honest account)
- 'days before draft' is measured from 00:00 of the draft date; a negative value means the capture is from the morning/afternoon of draft day but before 22:00 UTC (the COLLECTOR_RULES draft-night cutoff). No capture is after 22:00 UTC on draft day; results-language check passed for all accepted captures.
- The run was resumed several times (connection error / machine sleep, Wayback 503/504 bursts). All CDX listings and pages are cached in mock_raw/consensus3/, so `python mock_consensus3_collect.py --offline` reproduces the outputs; mock_consensus3_make_report.py regenerates this report.
- Bug fixed mid-run: early cached pages were saved after a lossy text decode (gzip bytes corrupted -> 0 class names); they were discarded (*.badenc) and refetched with curl --compressed. Rejections with "0 class names" on the remaining pages (basketballnews 2024-26, nbcsports 2024, yahoo 2025) are pages whose raw capture contains no names (client-side rendered).
- Yahoo was stopped after 3 consecutive HTTP 503 listing failures (retried once in a resumed run and failed again); 2022 yahoo was accepted from listings fetched before the stop, other years are unfilled, not absent. foxsports/sbnation had been stopped by connection errors (HTTP 000) from the machine going offline; that stop was reset because it was environmental, and both were then collected.
- Priority met for 2019-2023 for bleacherreport (2019, 2020, 2022, 2023; 2021 had no CDX candidate), si (2019-2022), usatoday (2020, 2022, 2023, 2024), nbcsports (2019, plus 2025 and 2026; 2020/2023 pages had < 25 names; 2021/2022 no CDX candidate), yahoo (2022 only). 2015-2017 were not reached for any site within the time budget; 2018 only partially (bleacherreport, si, usatoday).
- Whole-domain Wayback CDX filter queries returned 504 for the big hosts, so those hosts are only queried via known URL prefixes (see pats()); coverage for undated URL layouts (e.g. si.com 2023-24, bleacherreport 2021) may be understated.

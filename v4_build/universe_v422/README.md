# universe_v422 — the clean pre-draft universe, 2019–2025 (H7, built 2026-10-20)

Built by `../../universe_build.py` from `../../early_entry_{year}.csv` (the league's final early-entry lists,
`../../early_entry_collect.py`), the Torvik season tables in `../../tracking_raw/`, the EuroLeague/EuroCup exports in
`../../raw/`, the RSCI lists in `../../recruit_raw/`, the v4.22 test rows in `../staging_v422/` and the identity file.
No outcome information is used to decide who is in the universe; see the rule in the script's docstring and in the
model repo's `docs/METRICS.md` (Expanded pool). Torvik's post-draft `pick` column is dropped at load and never read.

| file | contents |
|---|---|
| `universe_{Y}_inputs.csv` | one row per universe member: `pid, draft_year, was_drafted` + the 1,673 v4.22 input columns (the existing test row where the player has one, else a rebuilt row; empty where nothing can be rebuilt) |
| `universe_{Y}_outcomes.csv` | `pid, was_drafted, actual_pick, universe_source, in_test_file, has_inputs, input_route, international, ambiguous_torvik, reached_nba_no_outcome, outcome_known, y_s1..5_war` |
| `rebuilt_check_{Y}.csv` | the Torvik rebuild of every college player who also has a real v4.22 row (consistency check, uniform-rows sensitivity) |
| `universe_summary.json` | counts per class: sources, input routes, seniors removed for playing again in Y+1, drafted players outside the rule, the test-file rows the rule does not reach (with names and the reason) |
| `universe_check.json` | per-column correlation of rebuilt vs real rows for drafted college players |

Names are in `../../identity/universe_names.csv` (pid, draft_year, player_name, school, universe_source, input_route); new
players carry pids starting with `U` (sha1 of normalised name, class and source), so they never collide with the identity file.

Input routes: `test_row` (real v4.22 row), `torvik_rebuild` (col_/bio_/hs_ from Torvik and RSCI plus the tc_ block from
`novel/torvik_context/build.py`'s functions; the NCAA-tournament tc_ columns stay empty because the game files are not
cached here), `euro_rebuild` (intl_ from the EuroLeague/EuroCup exports), `none` (no Division-I or EuroLeague season).

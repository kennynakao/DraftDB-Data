#!/usr/bin/env python3
"""Clean pre-draft universe for the 2019-2025 classes (MAKE_IT_BETTER.md H7).

Rule, stated so a reader can check that no outcome information enters: a player is in the universe
of draft Y if, before draft night Y, he was
  (a) on the league's final early-entry list for Y (early_entry_collect.py: initial list minus every
      withdrawal, cross-checked against the league's stated counts), college or international; or
  (b) a Division-I senior in season Y (Torvik class 'Sr') with at least 40% of his team's minutes and
      10 games, i.e. automatically eligible by exhausting college eligibility. Torvik's 'Sr' tag means
      fourth year, not exhausted eligibility, and from 2021 many seniors held a pandemic year; a senior
      who then played Division-I basketball in season Y+1 had eligibility left and was not in the Y
      pool, so he is removed (eligibility was public before the draft; our proxy for it is the next
      season's roster, which is post-draft information about college, never about the NBA); or
  (c) a EuroLeague or EuroCup player listed at age 22 in season Y (the automatic international
      eligibility age) who had not been in an earlier draft class and had no NBA record before Y.
Every player actually drafted in Y is in the universe by definition (the draft enumerates them); the
few drafted outside (a)-(c) are flagged `drafted_outside_rule` and counted. Undrafted players enter
ONLY through (a)-(c); the test files' undrafted rows that the rule does not reach are dropped, which
is the point of the exercise. Torvik's `pick` column is never read.

Inputs for a universe row: an existing v4.22 test row when the player is in the identity file for Y;
otherwise a row rebuilt from the same public sources the v4 pipeline used - Torvik for the college
line (col_: direct columns and the derived ones, verified column by column against the existing rows
in universe_check.json), bio_ age/height/position from Torvik's birthdate, listed height and role,
hs_rsci_rank from the RSCI lists, and the Torvik-context block tc_ from novel/torvik_context/build.py
run on the same seasons (the tournament columns stay empty: the game files are not cached here).
EuroLeague/EuroCup rows get the intl_ block from the league exports. Blocks that need a source we
cannot rebuild (combine, dated profiles, mock consensus, NBADraft.net grades, game logs, hoop-math,
pre_ history) stay empty, as they are for most undrafted rows already. Rows with no usable source
(non-D1 colleges, G League, domestic leagues abroad) keep has_inputs = 0 and are listed but not scored.

Outcomes: existing pids take the answers file; new pids are 0 WAR (they never played in the NBA)
unless the NBA's all-players list has a player of that name debuting in or after Y, in which case
the outcome is unknown (reached_nba_no_outcome = 1) and the row is excluded from outcome metrics.

Writes v4_build/universe_v422/universe_{Y}_inputs.csv, universe_{Y}_outcomes.csv,
universe_summary.json, universe_check.json, rebuilt_check_{Y}.csv (rebuilt rows for every college
player who also has a real v4.22 row: the consistency check and the uniform-rows sensitivity) and identity/universe_names.csv (private).
"""
import os, re, sys, json, hashlib, unicodedata, datetime as dt, collections
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("DRAFTDB_REPO", os.path.join(os.path.dirname(HERE), "draftdb"))
V4 = os.path.join(HERE, "v4_build", "staging_v422")
OUT = os.path.join(HERE, "v4_build", "universe_v422")
TORVIK = os.path.join(HERE, "tracking_raw")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "novel", "torvik_context"))
import early_entry_collect as EE
import build as TCB

YEARS = list(range(2019, 2026))
DRAFT_DATE = {2019: "2019-06-20", 2020: "2020-11-18", 2021: "2021-07-29", 2022: "2022-06-23", 2023: "2023-06-22", 2024: "2024-06-26", 2025: "2025-06-25"}
SR_MIN_PER, SR_GP = 40.0, 10          # rule (b)
INTL_AGE = 22                          # rule (c)
INPUTS = json.load(open(f"{V4}/input_columns.json"))["inputs"]
S = [f"y_s{i}_war" for i in range(1, 6)]
ALIAS = {"mohamed": "mo", "mohammed": "mo", "cameron": "cam", "michael": "mike", "matthew": "matt", "nicolas": "nick", "nicholas": "nick",
         "joshua": "josh", "christopher": "chris", "jonathan": "jon", "kenneth": "kenny", "william": "will", "robert": "rob", "daniel": "danny",
         "zachary": "zach", "benjamin": "ben", "alexander": "alex", "jacob": "jake", "joseph": "joe", "thomas": "tom", "timothy": "tim",
         "samuel": "sam", "gregory": "greg", "patrick": "pat", "jeffrey": "jeff", "herbert": "herb", "anthony": "ant", "isaiah": "isaiah",
         "jamal": "jamal", "dennis": "dennis", "javonte": "javonte", "raymond": "ray", "edward": "ed", "andrew": "drew", "charles": "charlie"}
US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())
POS = {"C": 6, "Combo G": 2, "PF/C": 5, "Pure PG": 1, "Scoring PG": 1, "Stretch 4": 5, "Wing F": 3, "Wing G": 2}
CLASS = {"Fr": 1, "So": 2, "Jr": 3, "Sr": 4}
LEVEL_STR = {4: 1.0, 3: 0.72}


def key(name):
    k = EE.norm(name)
    k = re.sub(r"\b([a-z]) (?=[a-z]\b)", r"\1", k).strip()          # c j -> cj
    p = k.split()
    if p and p[0] in ALIAS:
        p[0] = ALIAS[p[0]]
    return " ".join(p)


def keys(name):
    """All the names a release or a roster may use: full name, quoted nickname + surname, first + last only."""
    out = {key(name)}
    m = re.search(r'["“”\'‘’]([A-Za-z.]+)["“”\'‘’]', name)
    base = re.sub(r'\s*["“”\'‘’][A-Za-z.]+["“”\'‘’]\s*', " ", name)
    out.add(key(base))
    parts = key(base).split()
    if m and parts:
        out.add(key(m.group(1) + " " + parts[-1]))
    if len(parts) >= 3:
        out.add(parts[0] + " " + parts[-1])
    return {k for k in out if k}


def ekey(n):
    last, first = (n.split(",") + [""])[:2]
    return key(first.strip() + " " + last.strip())


def new_pid(k, y, src):
    return "U" + hashlib.sha1(f"{k}|{y}|{src}".encode()).hexdigest()[:10]


# ------------------------------------------------------------------ Torvik (the tc_ builder's loader, reading the cached .gz files)
def load_torvik():
    frames = []
    for y in range(2008, 2027):
        p = f"{TORVIK}/torvik_{y}.csv.gz"
        if os.path.exists(p):
            frames.append(pd.read_csv(p, header=None, names=TCB.ADV_COLS, low_memory=False))
    t = pd.concat(frames, ignore_index=True).drop(columns=TCB.DROP_LEAK)       # `pick` dropped at load, never read
    for c in TCB.ADV_COLS:
        if c in t.columns and c not in ("player_name", "team", "conf", "yr", "ht", "hometown", "role", "birthdate"):
            t[c] = pd.to_numeric(t[c], errors="coerce")
    t["year"] = t.year.astype(int); t["tpid"] = t.tpid.astype("Int64")
    t["key"] = t.player_name.map(key)
    t["minutes"] = t.mpg * t.GP
    bd = pd.to_datetime(t.birthdate, errors="coerce"); t["bd"] = bd
    t["age_imputed"] = ((bd.dt.month == 10) & (bd.dt.day == 15)).astype(float)
    t["age"] = (pd.to_datetime(t.year.astype(str) + "-01-15") - bd).dt.days / 365.25
    t["bpm_pos"] = t.bpm.clip(lower=0); t["porpag_pos"] = t.porpag.clip(lower=0)
    t["pts40"] = t.pts * 40.0 / t.mpg.replace(0, np.nan)
    t["dunks_per40"] = t.dunkmade * 40.0 / t.minutes.replace(0, np.nan)
    t["dunkatt_per40"] = t.dunkatt * 40.0 / t.minutes.replace(0, np.nan)
    t["rec_rank"] = (501.0 - 5.0 * t.rec_rank_raw).round(); t.loc[t.rec_rank_raw.isna(), "rec_rank"] = np.nan
    return t


def load_team_games():
    rows = []
    for y in range(2008, 2027):
        p = f"{TORVIK}/torvik_team_{y}.csv"
        if not os.path.exists(p):
            continue
        hdr = open(p).readline().strip().split(","); names, seen = [], {}
        for h in hdr + ["extra"]:
            seen[h] = seen.get(h, 0) + 1; names.append(h if seen[h] == 1 else f"{h}.{seen[h]}")
        d = pd.read_csv(p, header=None, skiprows=1, names=names)
        rec = d.record.astype(str).str.extract(r"(\d+)-(\d+)").astype(float)
        rows.append(pd.DataFrame(dict(team=d.team, year=y, tg_wins=rec[0], tg_losses=rec[1], tg_games=rec[0] + rec[1],
                                      tg_win_pct=rec[0] / (rec[0] + rec[1]), barthag=pd.to_numeric(d.barthag, errors="coerce"),
                                      barthag_rank=pd.to_numeric(d["rank"], errors="coerce"), tm_adjoe=pd.to_numeric(d.adjoe, errors="coerce"),
                                      tm_adjde=pd.to_numeric(d.adjde, errors="coerce"))))
    tg = pd.concat(rows, ignore_index=True)
    for c in ["tg_opp_barthag_mean", "tg_neutral", "tg_ncaa_games", "tg_ncaa_wins", "tg_final_four", "tg_champion", "tg_conf_t_games", "tg_conf_t_wins"]:
        tg[c] = np.nan                      # need the game files, not cached here
    return tg


def load_rsci():
    out = []
    for fp in sorted(os.listdir(f"{HERE}/recruit_raw")):
        m = re.match(r"rsci_(\d{4})\.csv", fp)
        if not m:
            continue
        hs = int(m.group(1))
        import csv
        lines = list(csv.reader(open(f"{HERE}/recruit_raw/{fp}", encoding="utf-8", errors="ignore")))
        try:
            hi = next(i for i, l in enumerate(lines) if "RSCI" in [c.strip() for c in l] and "Total" in [c.strip() for c in l])
        except StopIteration:
            continue
        hdr = [c.strip() for c in lines[hi]]; ri = hdr.index("RSCI"); tot = hdr.index("Total")
        for l in lines[hi + 1:]:
            if len(l) > tot and re.fullmatch(r"\d+", (l[ri] or "").strip()):
                nm = next((c for c in l[ri + 1:tot] if re.search(r"[A-Za-z]{2,} [A-Za-z]", c)), "")
                if nm:
                    out.append(dict(hs_class=hs, rsci_rank=int(l[ri]), key=key(re.sub(r"\*|\(.*?\)", "", nm))))
    return pd.DataFrame(out)


def load_euro():
    rows = []
    for y in YEARS:
        for lg, lv in (("E", 4), ("U", 3)):
            try:
                tr = json.load(open(f"{HERE}/raw/{lg}{y}_trad.json"))["players"]; ad = {p["player"]["code"]: p for p in json.load(open(f"{HERE}/raw/{lg}{y}_adv.json"))["players"]}
            except FileNotFoundError:
                continue
            pct = lambda v: float(str(v).rstrip("%")) if v not in (None, "") else np.nan
            for p in tr:
                a = ad.get(p["player"]["code"], {})
                rows.append(dict(code=p["player"]["code"], name=p["player"]["name"], key=ekey(p["player"]["name"]), year=y, level=lv, age=p["player"]["age"],
                                 gp=p["gamesPlayed"], mpg=p["minutesPlayed"], pts=p["pointsScored"], reb=p["totalRebounds"], ast=p["assists"], stl=p.get("steals"), blk=p.get("blocks"),
                                 p2a=p["twoPointersAttempted"], p3a=p["threePointersAttempted"], p3m=p["threePointersMade"], fta=p["freeThrowsAttempted"], ftm=p["freeThrowsMade"], pir=p.get("pir"),
                                 ts=pct(a.get("trueShootingPercentage")), efg=pct(a.get("effectiveFieldGoalPercentage")), orb_pct=pct(a.get("offensiveReboundsPercentage")), drb_pct=pct(a.get("defensiveReboundsPercentage")),
                                 team=(p["player"].get("team") or {}).get("name", "")))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ feature rebuilds
def college_row(L, car, tg_row, team_rank, rsci_rank, Y):
    """col_/bio_/hs_ columns from a Torvik final-season row L, its career rows car (year <= Y), team context."""
    r = {}
    mins = L.mpg * L.GP
    bd = L.bd
    r["col_age"] = (pd.Timestamp(f"{Y}-04-30") - bd).days / 365.25 if pd.notna(bd) else np.nan
    r["col_gp"] = L.GP; r["col_mpg"] = L.mpg
    for a, b in (("pts", "pts"), ("reb", "treb"), ("ast", "ast"), ("stl", "stl"), ("blk", "blk")):
        r[f"col_{a}36"] = getattr(L, b) * 36.0 / L.mpg if L.mpg else np.nan
        r[f"col_{a}_pg"] = getattr(L, b)
    for a, b in (("usg_pct", "usg"), ("ts_pct", "TS_per"), ("efg_pct", "eFG"), ("ast_pct", "AST_per"), ("tov_pct", "TO_per"), ("orb_pct", "ORB_per"), ("drb_pct", "DRB_per"),
                 ("stl_pct", "stl_per"), ("blk_pct", "blk_per"), ("ft_pct", "FT_per"), ("fg3_pct", "TP_per"), ("fg2_pct", "twoP_per"), ("ortg", "ORtg"), ("drtg", "drtg"),
                 ("adj_ortg", "adjoe"), ("adj_drtg", "adrtg"), ("impact", "bpm"), ("impact_off", "obpm"), ("impact_def", "dbpm"), ("value", "porpag"),
                 ("recruit_score", "rec_rank_raw"), ("rim_fg_pct", "rim_pct"), ("mid_fg_pct", "mid_pct")):
        r[f"col_{a}"] = getattr(L, b)
    fga = L.TPA + L.twoPA
    r["col_fg3ar"] = L.TPA / fga if fga else np.nan
    r["col_ftar"] = L.ftr / 100.0
    shots = L.rimatt + L.midatt + L.TPA
    r["col_rim_fga_share"] = L.rimatt / shots if shots else np.nan
    r["col_mid_fga_share"] = L.midatt / shots if shots else np.nan
    r["col_dunks_per40"] = L.dunkmade * 40.0 / mins if mins else np.nan
    r["col_fg3a_per40"] = L.TPA * 40.0 / mins if mins else np.nan
    if tg_row is not None:
        r["col_games_missed"] = tg_row.tg_games - L.GP
        r["col_minutes_share"] = mins / (tg_row.tg_games * 200.0)
        r["col_team_strength"] = tg_row.tm_adjoe - tg_row.tm_adjde
    r["col_usage_rank_team"] = team_rank
    r["col_final_season"] = Y; r["col_class_index"] = CLASS.get(str(L.yr).strip(), np.nan)
    r["col_n_seasons"] = len(car); r["col_minutes_total"] = float((car.mpg * car.GP).sum())
    first = car.sort_values("year").iloc[0]
    r["col_first_usg"] = first.usg; r["col_usg_delta"] = L.usg - first.usg
    r["col_final_is_current"] = 1.0; r["col_basic_fill"] = 0.0; r["intl_src"] = 0.0
    r["hs_mcdonalds_aa"] = 0; r["hs_jordan_brand"] = 0; r["hs_hoop_summit"] = 0
    r["hs_rsci_rank"] = rsci_rank
    r["bio_age_src"] = 0; r["bio_age_at_draft"] = (pd.Timestamp(DRAFT_DATE[Y]) - bd).days / 365.25 if pd.notna(bd) else np.nan
    m = re.match(r"(\d+)-(\d+)", str(L.ht))
    r["bio_height_src"] = 0; r["bio_height_in"] = int(m.group(1)) * 12 + int(m.group(2)) if m else np.nan
    r["bio_pos_src"] = 0; r["bio_pos_code"] = POS.get(str(L.role).strip(), np.nan)
    hm = str(L.hometown) if pd.notna(L.hometown) else ""
    st = re.search(r",\s*([A-Z]{2})\s*$", hm)
    r["bio_country_usa"] = (1.0 if st and st.group(1) in US_STATES else 0.0) if hm else np.nan
    return r


def euro_row(e, hist, Y):
    r = {}
    pm = lambda v: v / e.mpg * 36.0 if e.mpg else np.nan
    r.update(intl_age=e.age, intl_gp=e.gp, intl_minutes=e.gp * e.mpg, intl_mpg=e.mpg, intl_pts36=pm(e.pts), intl_reb36=pm(e.reb), intl_ast36=pm(e.ast),
             intl_stl36=pm(e.stl) if pd.notna(e.stl) else np.nan, intl_blk36=pm(e.blk) if pd.notna(e.blk) else np.nan,
             intl_ts_pct=e.ts, intl_efg_pct=e.efg, intl_orb_pct=e.orb_pct, intl_drb_pct=e.drb_pct,
             intl_fg3ar=e.p3a / (e.p2a + e.p3a) if (e.p2a + e.p3a) else np.nan, intl_ftar=e.fta / (e.p2a + e.p3a) if (e.p2a + e.p3a) else np.nan,
             intl_ft_pct=e.ftm / e.fta if e.fta else np.nan, intl_fg3_pct=e.p3m / e.p3a if e.p3a else np.nan, intl_impact=e.pir,
             intl_level=e.level, intl_last_level=e.level, intl_n_seasons=len(hist), intl_best_level=max(hist.level.max(), e.level),
             intl_lg_strength=LEVEL_STR[e.level], intl_lg_adj_pts36=pm(e.pts) * LEVEL_STR[e.level] if e.mpg else np.nan, intl_season_gap=0, intl_src=2.0,
             col_basic_fill=0.0, bio_age_src=0, bio_age_at_draft=e.age + 0.5, bio_height_src=0, bio_pos_src=0, hs_mcdonalds_aa=0, hs_jordan_brand=0, hs_hoop_summit=0)
    prev = hist[hist.year == Y - 1]
    if len(prev):
        p = prev.iloc[0]; r["intl_prev_pts36"] = p.pts / p.mpg * 36.0 if p.mpg else np.nan
    return r


def tc_block(m, t, tg, ts, fits):
    """tc_ columns for matched rows m (pid, tpid, F, draft_year) with the torvik_context builder's own functions."""
    if not len(m):
        return pd.DataFrame(columns=["pid"])
    fin = t.rename(columns={"year": "F"})
    D = m.merge(fin, on=["tpid", "F"], how="left", validate="m:1"); D["year"] = D.F; D = D.reset_index(drop=True)
    years = sorted(D.draft_year.unique())
    c = TCB.career(m, t)
    parts = [D[["pid"]], TCB.cohort_percentiles(D, t), TCB.age_features(D, fits), TCB.team_features(D, ts), TCB.conf_features(D, ts),
             TCB.game_features(D, tg, years), TCB.availability(D, c, tg), TCB.dev_features(D, c, fits), TCB.shooting(D, c, t, years), TCB.shot_mix(D), TCB.overpay(D, t)]
    out = pd.concat(parts, axis=1); out = out.loc[:, ~out.columns.duplicated()]
    return out.replace([np.inf, -np.inf], np.nan)


# ------------------------------------------------------------------ main
def main():
    idn = pd.read_csv(f"{HERE}/identity/tabular_names.csv"); idn["key"] = idn.player_name.map(key)
    t = load_torvik(); tg = load_team_games(); rsci = load_rsci(); euro = load_euro()
    ts = TCB.team_season(t); fits = TCB.age_fits(t, YEARS)
    nba = json.load(open(f"{HERE}/nba_all_players.json"))["resultSets"][0]; H = {h: i for i, h in enumerate(nba["headers"])}
    NBA = pd.DataFrame([{"key": key(r[H["DISPLAY_FIRST_LAST"]]), "from": int(r[H["FROM_YEAR"]])} for r in nba["rowSet"]])
    nba_first = NBA.groupby("key")["from"].min()
    all_id_keys = set(idn.key)
    t["usg_rank"] = t[t.Min_per >= 10].groupby(["team", "year"]).usg.rank(ascending=False, method="min")
    tgi = tg.set_index(["team", "year"])
    summary, check, names_out = {}, {}, []
    for Y in YEARS:
        ee = pd.read_csv(f"{HERE}/early_entry_{Y}.csv"); ee["key"] = ee.name.map(key)
        idy = idn[idn.draft_year == Y]
        id_by_key = {}
        for r_ in idy.itertuples():
            for k_ in keys(r_.player_name):
                id_by_key.setdefault(k_, r_.pid)
        earlier = set(idn[idn.draft_year < Y].key); later = set(idn[idn.draft_year > Y].key)
        tv = t[t.year == Y]
        next_season = set(t[t.year == Y + 1].tpid.dropna().astype(int)) if (t.year == Y + 1).any() else set()
        test = pd.read_csv(f"{V4}/tests/test_{Y}_inputs.csv", low_memory=False)
        ans = pd.read_csv(f"{REPO}/data/answers/answers_{Y}.csv", low_memory=False)
        U = {}       # key -> record

        def add(k, name, src, **kw):
            r = U.setdefault(k, dict(key=k, name=name, sources=set(), school=kw.get("school", ""), international=0, tpid=None, euro_code=None))
            r["sources"].add(src)
            for a, b in kw.items():
                if b not in (None, "") and not (isinstance(b, float) and np.isnan(b)):
                    r[a] = b
        # (a) early entrants
        for e in ee.itertuples():
            k_ = next((k for k in keys(e.name) if k in id_by_key), e.key)      # the identity file's spelling wins
            add(k_, e.name, "early_entry", school=e.school, international=int(e.international))
        # (b) seniors
        sr_all = tv[(tv.yr == "Sr") & (tv.Min_per >= SR_MIN_PER) & (tv.GP >= SR_GP)]
        returned = sr_all[sr_all.tpid.astype(int).isin(next_season)]          # played D-I again in Y+1: eligibility left, not in this pool
        sr = sr_all[~sr_all.tpid.astype(int).isin(next_season)]
        n_sr_namesake = 0
        for s in sr.itertuples():
            if s.key in (earlier | later) and s.key not in id_by_key:
                n_sr_namesake += 1; continue  # a namesake of a player from another class, nothing to do with this one
            add(s.key, s.player_name, "senior", school=s.team, tpid=int(s.tpid))
        # (c) EuroLeague / EuroCup age 22
        eu = euro[(euro.year == Y) & (euro.age == INTL_AGE)]
        for e in eu.itertuples():
            if (e.key in earlier) or (nba_first.get(e.key, 9999) < Y):
                continue
            add(e.key, e.name, "intl_22", school=e.team, international=1, euro_code=e.code)
        # Torvik match for college entrants without a tpid: name + season Y, school to disambiguate
        for k, r in U.items():
            if r["tpid"] is None and not r["international"]:
                cand = tv[tv.key == k]
                if len(cand) > 1 and r.get("school"):
                    sch = EE.norm(re.sub(r"\(.*?\)", "", r["school"])).split()
                    pref = cand[cand.team.map(lambda x: any(w in EE.norm(x) for w in sch if len(w) > 3))]
                    cand = pref if len(pref) else cand
                if len(cand) == 1:
                    r["tpid"] = int(cand.tpid.iloc[0])
                elif len(cand) > 1:
                    r["ambiguous_torvik"] = 1
            if r["euro_code"] is None and r["international"]:
                cand = euro[(euro.year == Y) & (euro.key == k)]
                if len(cand) == 1:
                    r["euro_code"] = cand.code.iloc[0]
        # pids: by name, else by the Torvik season signature (games, minutes per game) of a college test row of this class,
        # which resolves the nickname cases (Bones Hyland is Nah'Shon Hyland on Torvik)
        sig = {}
        for r_ in test[test.path.astype(str).str.startswith("college")].itertuples():
            if pd.notna(r_.col_gp) and pd.notna(r_.col_mpg):
                sig.setdefault((int(r_.col_gp), round(float(r_.col_mpg), 1)), []).append(r_.pid)
        for k, r in U.items():
            r["pid"] = id_by_key.get(k)
            if r["pid"] is None and r["tpid"] is not None:
                L = tv[tv.tpid == r["tpid"]]
                if len(L):
                    cands = sig.get((int(L.GP.iloc[0]), round(float(L.mpg.iloc[0]), 1)), [])
                    if len(cands) == 1:
                        r["pid"] = cands[0]; r["matched_by_signature"] = 1
            r["in_identity"] = int(r["pid"] is not None)
            if r["pid"] is None:
                r["pid"] = new_pid(k, Y, "u")
        # two spellings of one player collapse onto one record
        by_pid = {}
        for k in list(U):
            r = U[k]; q = by_pid.get(r["pid"])
            if q is None:
                by_pid[r["pid"]] = r
            else:
                q["sources"] |= r["sources"]
                for a in ("tpid", "euro_code", "school"):
                    if q.get(a) in (None, "") and r.get(a) not in (None, ""):
                        q[a] = r[a]
                q["international"] = max(q["international"], r["international"])
                del U[k]
        # drafted players outside the rule
        captured = {r["pid"] for r in U.values()}
        for d in idy[idy.actual_pick.notna()].itertuples():
            if d.pid not in captured:
                kk = d.key if d.key not in U else d.key + "#"
                add(kk, d.player_name, "drafted_outside_rule"); U[kk]["pid"] = d.pid; U[kk]["in_identity"] = 1
        # existing test rows the rule does not reach (dropped)
        captured = {r["pid"] for r in U.values()}
        tx = test.merge(ans[["pid", "was_drafted"] + S], on="pid", how="left", suffixes=("", "_a"))
        dropped = tx[~tx.pid.isin(captured)]
        drop_tab = dropped.groupby(["path", "declared_only"]).agg(n=("pid", "size"), with_war=(S[0], lambda s: int((pd.to_numeric(s, errors="coerce").fillna(0) != 0).sum()))).reset_index().to_dict("records")
        dropped_rows = []
        for r_ in dropped.itertuples():
            nm_ = idy.set_index("pid").player_name.get(r_.pid, "?"); kk = key(nm_)
            tvr = tv[tv.key == kk]
            why = ("not in Torvik season %d" % Y) if not len(tvr) else ("Torvik %s, Min_per %.0f, GP %d%s" % (tvr.yr.iloc[0], tvr.Min_per.iloc[0], tvr.GP.iloc[0], ", played D-I in %d" % (Y + 1) if int(tvr.tpid.iloc[0]) in next_season else ""))
            dropped_rows.append(dict(pid=r_.pid, name=nm_, path=r_.path, declared_only=int(r_.declared_only), war5=round(float(pd.to_numeric(pd.Series([getattr(r_, c) for c in S]), errors="coerce").fillna(0).sum()), 1), why=why))

        # ---- inputs
        test_by_pid = test.set_index("pid")
        rows, meta, m_tc, rebuilt_check = [], [], [], []
        ans_by = ans.set_index("pid")
        for k, r in U.items():
            pid = r["pid"]; src = "+".join(sorted(r["sources"]))
            feat = {}; has = 0; route = "none"
            if pid in test_by_pid.index:
                feat = test_by_pid.loc[pid, INPUTS].to_dict(); has = 1; route = "test_row"
            elif r["tpid"] is not None:
                L = tv[tv.tpid == r["tpid"]]
                if len(L):
                    L = L.iloc[0]; car = t[(t.tpid == r["tpid"]) & (t.year <= Y)]
                    tgr = tgi.loc[(L.team, Y)] if (L.team, Y) in tgi.index else None
                    rs = rsci[(rsci.key == k) & (rsci.hs_class <= Y - 1) & (rsci.hs_class >= Y - 6)]
                    feat = college_row(L, car, tgr, L.usg_rank, (rs.sort_values("hs_class").rsci_rank.iloc[-1] if len(rs) else np.nan), Y)
                    m_tc.append(dict(pid=pid, tpid=r["tpid"], F=Y, draft_year=Y)); has = 1; route = "torvik_rebuild"
            elif r["euro_code"] is not None:
                e = euro[(euro.code == r["euro_code"]) & (euro.year == Y)].iloc[0]
                hist = euro[(euro.code == r["euro_code"]) & (euro.year <= Y)]
                feat = euro_row(e, hist, Y); has = 1; route = "euro_rebuild"
            row = {c: feat.get(c, np.nan) for c in INPUTS}
            drafted = pid in idy.pid.values and pd.notna(idy.set_index("pid").actual_pick.get(pid, np.nan))
            pick = float(idy.set_index("pid").actual_pick.get(pid, np.nan)) if drafted else np.nan
            if pid in ans_by.index:
                a = ans_by.loc[pid]; war = [float(pd.to_numeric(a[c], errors="coerce")) if pd.notna(a[c]) else np.nan for c in S]; reached = 0
                out_known = 1
            else:
                # an NBA player of this name who is in no draft class of the identity file = an undrafted NBA player the test files missed
                reached = int(k not in all_id_keys and Y <= nba_first.get(k, 9999) <= Y + 3)
                war = [np.nan] * 5 if reached else [0.0] * 5
                out_known = 0 if reached else 1
            meta.append(dict(pid=pid, draft_year=Y, was_drafted=int(drafted), actual_pick=pick, universe_source=src, in_test_file=int(pid in test_by_pid.index),
                             has_inputs=has, input_route=route, international=r["international"], ambiguous_torvik=int(r.get("ambiguous_torvik", 0)),
                             reached_nba_no_outcome=reached, outcome_known=out_known, **{c: w for c, w in zip(S, war)}))
            rows.append(dict(pid=pid, draft_year=Y, was_drafted=int(drafted), **row))
            names_out.append(dict(pid=pid, draft_year=Y, player_name=r["name"], school=r.get("school", ""), universe_source=src, input_route=route))
            # rebuilt rows for every college player who has a real row: the consistency check and the uniform-rows sensitivity
            if route == "test_row" and r["tpid"] is not None and str(test_by_pid.loc[pid, "path"]).startswith("college"):
                L = tv[tv.tpid == r["tpid"]]
                if len(L):
                    L = L.iloc[0]; car = t[(t.tpid == r["tpid"]) & (t.year <= Y)]
                    tgr = tgi.loc[(L.team, Y)] if (L.team, Y) in tgi.index else None
                    rs = rsci[(rsci.key == k) & (rsci.hs_class <= Y - 1) & (rsci.hs_class >= Y - 6)]
                    rb = college_row(L, car, tgr, L.usg_rank, (rs.sort_values("hs_class").rsci_rank.iloc[-1] if len(rs) else np.nan), Y)
                    rebuilt_check.append(dict(pid=pid, tpid=r["tpid"], was_drafted=int(drafted), **rb))
        X = pd.DataFrame(rows); M = pd.DataFrame(meta)
        tc = tc_block(pd.DataFrame(m_tc), t, tg, ts, fits)
        if len(tc):
            tc = tc.set_index("pid")
            for c in [c for c in tc.columns if c in INPUTS]:
                X.loc[X.pid.isin(tc.index), c] = X.loc[X.pid.isin(tc.index), "pid"].map(tc[c]).values
        # rebuilt rows (with tc_) for the check
        RB = pd.DataFrame(rebuilt_check)
        if len(RB):
            tcr = tc_block(RB[["pid", "tpid"]].assign(F=Y, draft_year=Y), t, tg, ts, fits).set_index("pid")
            for c in [c for c in tcr.columns if c in INPUTS]:
                RB[c] = RB.pid.map(tcr[c]).values
            full = RB.merge(test[["pid"] + INPUTS], on="pid", suffixes=("", "_real"))
            cmp = {}
            for c in [c for c in RB.columns if c in INPUTS]:
                a = pd.to_numeric(full[c], errors="coerce"); b = pd.to_numeric(full[c + "_real"], errors="coerce"); ok = a.notna() & b.notna()
                if ok.sum() >= 10 and a[ok].std() > 0 and b[ok].std() > 0:
                    cmp[c] = dict(n=int(ok.sum()), corr=round(float(np.corrcoef(a[ok], b[ok])[0, 1]), 3), ratio_med=round(float((a[ok] / b[ok].replace(0, np.nan)).median()), 3))
            check[Y] = dict(n_rebuilt=len(RB), columns=cmp)
            RB.to_csv(f"{OUT}/rebuilt_check_{Y}.csv", index=False)
        X.to_csv(f"{OUT}/universe_{Y}_inputs.csv", index=False)
        M.to_csv(f"{OUT}/universe_{Y}_outcomes.csv", index=False)
        cov = X.loc[M.has_inputs == 1, INPUTS].notna().mean()
        summary[Y] = dict(n=len(M), drafted=int(M.was_drafted.sum()), undrafted=int((M.was_drafted == 0).sum()),
                          sources=M.universe_source.value_counts().to_dict(), routes=M.input_route.value_counts().to_dict(),
                          has_inputs=int(M.has_inputs.sum()), reached_nba_no_outcome=int(M.reached_nba_no_outcome.sum()),
                          drafted_outside_rule=int(M.universe_source.str.contains("drafted_outside_rule").sum()),
                          existing_test_rows_dropped=drop_tab, dropped_rows=dropped_rows, n_seniors_rule=int(len(sr_all)), n_seniors_returned_Y1=int(len(returned)), n_seniors_namesake_dropped=n_sr_namesake,
                          n_entrants=len(ee), n_intl22=int(len(eu)),
                          coverage_rebuilt=dict(col=round(float(cov[[c for c in INPUTS if c.startswith('col_')]].mean()), 3), tc=round(float(cov[[c for c in INPUTS if c.startswith('tc_')]].mean()), 3)))
        print(f"{Y}: universe {len(M)} (drafted {summary[Y]['drafted']}, undrafted {summary[Y]['undrafted']}); inputs for {summary[Y]['has_inputs']}; routes {summary[Y]['routes']}; "
              f"sources {summary[Y]['sources']}; reached NBA w/o outcome {summary[Y]['reached_nba_no_outcome']}; drafted outside rule {summary[Y]['drafted_outside_rule']}; dropped test rows {sum(d['n'] for d in drop_tab)}", flush=True)
    pd.DataFrame(names_out).to_csv(f"{HERE}/identity/universe_names.csv", index=False)
    json.dump(dict(rule=dict(senior_min_per=SR_MIN_PER, senior_gp=SR_GP, intl_age=INTL_AGE), years=summary), open(f"{OUT}/universe_summary.json", "w"), indent=1, default=str)
    json.dump(check, open(f"{OUT}/universe_check.json", "w"), indent=1)


if __name__ == "__main__":
    main()

"""Match games_long.csv names -> pid (tabular_names.csv) and build features.csv, unmatched.csv, matches.csv, coverage.csv."""
import csv, os, re, sys, unicodedata, collections
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", ".."))
ID = pd.read_csv(os.path.join(DATA, "identity", "tabular_names.csv"))
RS = pd.read_csv(os.path.join(DATA, "rsci_features.csv"))
SUF = r"\b(jr|sr|ii|iii|iv|v)\b"
def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[.'`]", "", s); s = re.sub(r"[^a-z ]", " ", s); s = re.sub(SUF, " ", s)
    return re.sub(r"\s+", " ", s).strip()
def box_name(raw):
    s = re.sub(r"\(c\)|\*|\bDNP\b", " ", str(raw), flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" .")
    if "," in s:
        last, first = s.split(",", 1); s = first.strip() + " " + last.strip()
    return s
rs = RS.set_index("pid")
ID["rsci_class"] = [ (dy - rs.loc[p, "rsci_years_to_draft"]) if (p in rs.index and rs.loc[p, "rsci_top100"] == 1 and pd.notna(rs.loc[p, "rsci_years_to_draft"])) else np.nan
                     for p, dy in zip(ID.pid, ID.draft_year)]
ID["n"] = ID.player_name.map(norm)
ID["first"] = ID.n.map(lambda s: s.split()[0] if s else "")
ID["last"] = ID.n.map(lambda s: " ".join(s.split()[1:]) if s else "")
by_full = ID.groupby("n").apply(lambda d: d.to_dict("records"), include_groups=False).to_dict()
by_last = ID.groupby("last").apply(lambda d: d.to_dict("records"), include_groups=False).to_dict()
by_lastword = collections.defaultdict(list)       # last word of the identity surname (Kidd-Gilchrist -> gilchrist, middle names)
for r_ in ID.to_dict("records"):
    for w_ in set(r_["last"].split()): by_lastword[w_].append(r_)
NICK = {}
for grp in ["mike michael mick mickey", "tony anthony", "tom thomas tommy", "joe joseph joey", "jim james jimmy jamie", "bob robert bobby rob robbie", "bill william will billy willie",
            "dan daniel danny", "dave david", "ed edward eddie", "ken kenneth kenny", "steve stephen steven", "tim timothy", "andy andrew drew", "alex alexander alexis", "greg gregory",
            "jeff jeffrey jeffery", "jon jonathan jonathon john johnny", "josh joshua", "nate nathan nathaniel", "sam samuel", "zach zachary zack", "pat patrick patty", "rick richard ricky rich",
            "phil phillip philip", "ron ronald ronnie", "don donald", "larry lawrence", "jerry jerome gerald", "terry terrence terrance terence", "vince vincent", "ray raymond",
            "nick nicholas nicolas nico", "chris christopher", "matt matthew", "ben benjamin benny", "cam cameron", "naz nazreon", "jay jason jaylen", "kenny kenneth", "charlie charles chuck chas",
            "cj", "pj", "dj", "tj", "bj", "aj", "jj", "kj", "jr"]:
    ws = grp.split()
    for w in ws: NICK.setdefault(w, set()).update(ws)

def window(c, Y): return [x for x in c if Y + 1 <= x["draft_year"] <= Y + 5]
def resolve(c, Y):
    """c: window-filtered candidates -> (record, reason)"""
    if not c: return None, "no_candidate_in_window"
    if len(c) > 1:
        c2 = [x for x in c if x["rsci_class"] == Y]
        if len(c2) == 1: return c2[0], "rsci_class_tiebreak"
        return None, "ambiguous:" + "|".join(sorted(x["pid"] for x in c))
    x = c[0]
    if not np.isnan(x["rsci_class"]) and abs(x["rsci_class"] - Y) > 1: return None, "rsci_class_mismatch"
    return x, "ok"
def match(name, Y):
    n = norm(box_name(name))
    if not n: return None, "empty", ""
    c = window(by_full.get(n, []), Y)
    if c:
        r, why = resolve(c, Y); return r, why, "full_name"
    toks = n.split()
    if len(toks) < 2: return None, "single_token", ""
    first, last = toks[0], " ".join(toks[1:])
    cand = window(by_last.get(last, []), Y)
    # box surname may be the last word of a compound / middle-named identity surname (Kidd-Gilchrist, James Michael McAdoo)
    if not cand: cand = window(by_lastword.get(toks[-1], []), Y)
    if not cand and len(toks) > 2: cand = window(by_last.get(toks[-1], []), Y)
    if not cand: return None, "no_candidate_in_window", ""
    def fm(a, b):   # first-name compatibility: initials / short forms, nickname table, >=3-char common prefix
        if len(a) <= 2 or len(b) <= 2: return a[0] == b[0]
        if b in NICK.get(a, ()) : return True
        k = min(len(a), len(b), 3)
        return len(a) >= 3 and len(b) >= 3 and (a.startswith(b[:k]) or b.startswith(a[:k])) and (a.startswith(b) or b.startswith(a) or a[:3] == b[:3])
    c2 = [x for x in cand if fm(first, x["first"])]
    if not c2: return None, "no_candidate_in_window", ""
    r, why = resolve(c2, Y); return r, why, "lastname+first_prefix"

def main():
    L = pd.read_csv(os.path.join(HERE, "games_long.csv"))
    rows = []; unm = []; conflicts = []
    for i, d in L.iterrows():
        rec, why, rule = match(d["name"], int(d["year"]))
        if rec is None:
            unm.append(dict(game=d["game"], year=d["year"], name=d["name"], reason=why)); continue
        rows.append(dict(d, pid=rec["pid"], draft_year=rec["draft_year"], match_rule=rule, match_note=why, matched_name=rec["player_name"]))
    M = pd.DataFrame(rows)
    # duplicate pid within one game: keep both flagged, drop the later
    dup = M.duplicated(["pid", "game", "year"], keep="first")
    for _, d in M[dup].iterrows(): unm.append(dict(game=d["game"], year=d["year"], name=d["name"], reason="duplicate_pid_in_game:" + d["pid"]))
    M = M[~dup].copy()
    M.to_csv(os.path.join(HERE, "matches.csv"), index=False)
    U = pd.DataFrame(unm)
    # rank of points inside the game (all players with a points figure, both teams; ties -> average rank; 1 = most)
    L["pts_rank"] = L.groupby(["game", "year"])["pts"].rank(ascending=False, method="average")
    M = M.merge(L[["game", "year", "name", "team", "pts_rank"]].drop_duplicates(["game", "year", "name", "team"]), on=["game", "year", "name", "team"], how="left")
    M["world"] = M.team.fillna("").str.contains("World", case=False).astype(int)
    out = []
    for pid, g in M.groupby("pid"):
        r = {"pid": pid, "pg_games": len(g)}
        def ssum(c):
            v = g[c].dropna(); return v.sum() if len(v) else np.nan
        for c in ["min", "pts", "reb", "ast", "stl", "blk", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "tov"]:
            r["pg_" + {"tpm": "3pm", "tpa": "3pa"}.get(c, c)] = ssum(c)
        gm = g.dropna(subset=["pts", "min"]); gm = gm[gm["min"] > 0]
        r["pg_pts_per_min"] = gm.pts.sum() / gm["min"].sum() if len(gm) else np.nan
        need = ["pts", "reb", "ast", "stl", "blk", "tov", "fga", "fgm", "fta", "ftm", "min"]
        gf = g.dropna(subset=need); gf = gf[gf["min"] > 0]
        if len(gf):
            bx = (gf.pts + 0.7 * gf.reb + 0.7 * gf.ast + 1.5 * gf.stl + 1.5 * gf.blk - gf.tov - 0.7 * (gf.fga - gf.fgm) - 0.35 * (gf.fta - gf.ftm)).sum()
            r["pg_box_per_min"] = bx / gf["min"].sum()
        else: r["pg_box_per_min"] = np.nan
        r["pg_pts_rank_in_game"] = g.pts_rank.mean() if g.pts_rank.notna().any() else np.nan
        r["pg_mcd"] = int((g.game == "mcd").any()); r["pg_jordan"] = int((g.game == "jbc").any()); r["pg_hoop_summit"] = int((g.game == "hs").any())
        r["pg_hoop_summit_world"] = int(g[g.game == "hs"].world.max()) if (g.game == "hs").any() else np.nan
        r["_full"] = int(len(gf) > 0)
        out.append(r)
    F = pd.DataFrame(out)
    cols = ["pid", "pg_games", "pg_min", "pg_pts", "pg_reb", "pg_ast", "pg_stl", "pg_blk", "pg_fgm", "pg_fga", "pg_3pm", "pg_3pa", "pg_ftm", "pg_fta", "pg_tov",
            "pg_pts_per_min", "pg_box_per_min", "pg_pts_rank_in_game", "pg_mcd", "pg_jordan", "pg_hoop_summit", "pg_hoop_summit_world"]
    F[cols].to_csv(os.path.join(HERE, "features.csv"), index=False, float_format="%.6g")
    U.to_csv(os.path.join(HERE, "unmatched.csv"), index=False)
    # coverage
    cov = F.merge(ID[["pid", "draft_year"]], on="pid").groupby("draft_year").agg(players=("pid", "count"), full=("_full", "sum"),
          mcd=("pg_mcd", "sum"), jbc=("pg_jordan", "sum"), hs=("pg_hoop_summit", "sum"))
    tot = ID.groupby("draft_year").size().rename("drafted")
    cov = cov.join(tot, how="outer").fillna(0).astype(int)
    cov["points_only"] = cov.players - cov.full
    cov.to_csv(os.path.join(HERE, "coverage_by_draft_class.csv"))
    gc = M.groupby(["game", "year"]).agg(matched=("pid", "count"), full=("min", lambda s: int(s.notna().sum()))).reset_index()
    ql = L.groupby(["game", "year"]).size().rename("lines").reset_index()
    gc = ql.merge(gc, on=["game", "year"], how="left").fillna(0)
    gc.to_csv(os.path.join(HERE, "coverage_by_game.csv"), index=False)
    return F, cov, gc, U, M
if __name__ == "__main__":
    F, cov, gc, U, M = main()
    print("rows", len(F)); print(cov.loc[2007:2025]); print(gc.to_string()); print(U.reason.str.split(":").str[0].value_counts())

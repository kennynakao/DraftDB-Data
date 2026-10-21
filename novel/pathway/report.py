#!/usr/bin/env python3
"""Coverage report for novel/pathway (reads features.csv, provenance.csv, coverage_audit.csv, model inputs). Names are printed to the terminal only."""
import os, glob, pandas as pd
D = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
P = f"{D}/novel/pathway"
LG = {1:"EuroLeague",2:"EuroCup",3:"ACB",4:"LNB Pro A",5:"NBL Australia",6:"G League",7:"OTE",8:"other top European",9:"other"}
SRC = {1:"1 wiki pre-draft revision",2:"2 EuroLeague/EuroCup export",3:"3 G League json",4:"4 current-article table (seasons<=draft yr)",5:"5 Wayback official page"}
a = pd.read_csv(f"{P}/coverage_audit.csv"); f = pd.read_csv(f"{P}/features.csv"); pv = pd.read_csv(f"{P}/provenance.csv")
a["underfilled"] = (~((a.has_impact==1)&(a.has_usg==1)&(a.has_ts==1)&(a.has_gp==1)&(a.has_minutes==1))).astype(int)
a["has_pw"] = a.pid.isin(f.pid).astype(int)
a["band"] = pd.cut(a.draft_year, [2006, 2018, 2025], labels=["2007-2018", "2019-2025"])
out = []
def p(*x):
    s = " ".join(str(i) for i in x); print(s); out.append(s)
p("== rows in features.csv:", len(f), "of", len(a), "audited pathway rows")
p("\n== coverage by band x path (rows / with pw / underfilled rows / underfilled with pw)")
g = a.groupby(["band", "path"], observed=True).agg(rows=("pid", "size"), pw=("has_pw", "sum"), underfilled=("underfilled", "sum")); g["underfilled_with_pw"] = a[a.underfilled == 1].groupby(["band", "path"], observed=True).has_pw.sum(); p(g.to_string())
p("\n== coverage by draft year")
g = a.groupby("draft_year").agg(rows=("pid", "size"), pw=("has_pw", "sum"), underfilled=("underfilled", "sum")); g["underfilled_with_pw"] = a[a.underfilled == 1].groupby("draft_year").has_pw.sum(); g["pct"] = (100 * g.pw / g.rows).round(0); p(g.fillna(0).astype(int).to_string())
p("\n== by league code x band (rows in features.csv)")
x = f.merge(a[["pid", "band"]], on="pid"); x["league"] = x.pw_league_code.map(LG)
p(pd.crosstab(x.league, x.band).to_string())
p("\n== by source x band")
x["src"] = x.pw_source.map(SRC); p(pd.crosstab(x.src, x.band).to_string())
p("\n== column fill counts by source")
cols = [c for c in f.columns if c.startswith("pw_") and c not in ("pw_source",)]
p(f.groupby("pw_source")[cols].count().T.to_string())
p("\n== season gap (draft year - season end)")
p(f.pw_season_gap.value_counts().sort_index().to_string())
# improvement in filled columns vs the intl_ block (test years)
IC = {"pw_gp":"intl_gp","pw_mpg":"intl_mpg","pw_pts36":"intl_pts36","pw_reb36":"intl_reb36","pw_ast36":"intl_ast36","pw_stl36":"intl_stl36","pw_blk36":"intl_blk36","pw_tov36":"intl_tov_pct",
      "pw_ts_pct":"intl_ts_pct","pw_efg_pct":"intl_efg_pct","pw_fg3ar":"intl_fg3ar","pw_ftar":"intl_ftar","pw_ft_pct":"intl_ft_pct","pw_fg3_pct":"intl_fg3_pct","pw_usg_proxy":"intl_usg_pct","pw_box_impact":"intl_impact","pw_age_at_season":"intl_age"}
EXTRA = ["pw_box_lite"]
tests = pd.concat([pd.read_csv(fp, usecols=lambda c: c in ["pid"] + list(IC.values())) for fp in sorted(glob.glob(f"{D}/v4_build/staging_v422/tests/test_*_inputs.csv"))])
m = f.merge(tests, on="pid", how="inner")
nm = pd.read_csv(f"{D}/identity/tabular_names.csv")[["pid", "player_name", "draft_year"]]
imp = pd.DataFrame({"pid": m.pid})
imp["pw_filled"] = m[list(IC)].notna().sum(axis=1).values
imp["newly_filled"] = sum(((m[k].notna()) & (m[v].isna())).astype(int) for k, v in IC.items()).values
imp = imp.merge(a[["pid", "n_intl_filled", "has_impact"]], on="pid").merge(pv[["pid", "comp_label", "season_label", "pw_source"]], on="pid").merge(nm, on="pid")
imp = imp.sort_values(["newly_filled", "pw_filled", "n_intl_filled"], ascending=[False, False, True])
p("\n== TEST-YEAR (2019-2025) players: newly filled = pw columns present where the matching intl_ column is empty (17 mapped pairs)")
p(f"test-year rows with pw: {len(imp)}; mean newly_filled {imp.newly_filled.mean():.1f}; rows with >=1 new: {(imp.newly_filled>0).sum()}; rows where intl_impact was empty and pw_box_impact now present: {int(((m.intl_impact.isna()) & (m.pw_box_impact.notna())).sum())}; rows where intl_usg_pct was empty and pw_usg_proxy present: {int(((m.intl_usg_pct.isna()) & (m.pw_usg_proxy.notna())).sum())}")
p(f"rows where intl_impact is empty and a pw box composite exists (pw_box_impact or the lite version): {int(((m.intl_impact.isna()) & (m.pw_box_impact.notna() | m.pw_box_lite.notna())).sum())}")
p(imp.head(10)[["pid", "player_name", "draft_year", "n_intl_filled", "pw_filled", "newly_filled", "comp_label", "season_label", "pw_source"]].to_string(index=False))
imp.head(10).drop(columns=["player_name"]).to_csv(f"{P}/top10_test_improvement_nonames.csv", index=False)
open(f"{P}/report.txt", "w").write("\n".join(out))

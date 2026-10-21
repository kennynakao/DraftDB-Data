import pandas as pd, glob, os
D='/Users/kennakao/Library/Application Support/Claude/scratch-workspaces/09fd2e70-0c87-4d61-903f-008f616ff01e/615844ca-6df6-47ed-8e1d-060f66490ccc/scratch-2026-10-18-6bf8cb/DraftDB-Data'
IC="intl_age intl_gp intl_minutes intl_mpg intl_pts36 intl_reb36 intl_ast36 intl_stl36 intl_blk36 intl_usg_pct intl_ts_pct intl_efg_pct intl_ast_pct intl_tov_pct intl_orb_pct intl_drb_pct intl_fg3ar intl_ftar intl_ft_pct intl_fg3_pct intl_impact intl_level intl_last_level intl_n_seasons intl_best_level intl_youth_pts36 intl_youth_n intl_lg_adj_pts36 intl_lg_strength intl_prev_pts36 intl_season_gap intl_src intl_two_minutes intl_two_pts36".split()
fs=[D+'/v4_build/staging_v422/train_2000_2018.csv']+sorted(glob.glob(D+'/v4_build/staging_v422/tests/test_*_inputs.csv'))
dfs=[]
for f in fs:
    d=pd.read_csv(f,usecols=lambda c:c in ['pid','draft_year','path','was_drafted']+IC)
    d['file']=os.path.basename(f);dfs.append(d)
d=pd.concat(dfs)
print(d.groupby('file').path.value_counts().to_string())
d=d[d.draft_year>=2007]
sel=d[d.path.isin(['international','college_pre2008_or_unlinked'])].copy()
sel['n_intl_filled']=sel[IC].notna().sum(axis=1)
for a,b in [('has_impact','intl_impact'),('has_usg','intl_usg_pct'),('has_ts','intl_ts_pct'),('has_gp','intl_gp'),('has_minutes','intl_minutes')]:
    sel[a]=sel[b].notna().astype(int)
nm=pd.read_csv(D+'/identity/tabular_names.csv')[['pid','player_name']].rename(columns={'player_name':'name'})
sel=sel.merge(nm,on='pid',how='left')
sel[['pid','draft_year','path','n_intl_filled','has_impact','has_usg','has_ts','has_gp','has_minutes','name']].to_csv(D+'/novel/pathway/coverage_audit.csv',index=False)
print(sel.groupby(['draft_year','path']).agg(n=('pid','size'),mean_filled=('n_intl_filled','mean'),impact=('has_impact','sum'),usg=('has_usg','sum'),ts=('has_ts','sum'),gp=('has_gp','sum'),mins=('has_minutes','sum'),zero=('n_intl_filled',lambda s:(s==0).sum())).round(1).to_string())
print(sel.n_intl_filled.describe())
print(sel.name.isna().sum(),'missing names; was_drafted', sel.was_drafted.value_counts().to_dict())

def build_team_metrics_from_pbp(pbp):
    off = pbp[(pbp["play_type"].isin(["run","pass"])) & (~pbp["posteam"].isna())]
    off_grp = off.groupby("posteam")["epa"].mean().reset_index().rename(columns={"posteam":"team","epa":"off_epa"})
    def_grp = off.groupby("defteam")["epa"].mean().reset_index().rename(columns={"defteam":"team","epa":"def_epa"})
    out = off_grp.merge(def_grp, on="team", how="outer").fillna(0.0)
    out["neutral_pace"] = 28.0
    return out

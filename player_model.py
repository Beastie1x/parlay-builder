import numpy as np
def project_qb_passing_yards(team_off_epa, team_proe, neutral_pace, opp_def_pass_epa, wind_mph, base_yppa=6.8):
    pace_adj = np.clip((30 - neutral_pace)/10, -0.3, 0.3)
    attempts = 32 * (1 + team_proe*0.6) * (1 + pace_adj)
    ypa = base_yppa * (1 + team_off_epa*0.5 - opp_def_pass_epa*0.4 - (0.02 if wind_mph>15 else 0))
    return attempts * ypa
def project_wr_rec_yards(team_pass_attempts, tgt_share, ypt, opp_def_pass_epa, wind_mph):
    adj_ypt = ypt * (1 - opp_def_pass_epa*0.3 - (0.02 if wind_mph>15 else 0))
    return team_pass_attempts * tgt_share * adj_ypt
def project_rb_rush_yards(team_rush_attempts, carry_share, ypc, opp_def_rush_epa, box_factor=0.0):
    adj_ypc = ypc * (1 - opp_def_rush_epa*0.25 + box_factor*0.1)
    return team_rush_attempts * carry_share * adj_ypc
def distribution_normal(mean, sd):
    return {"type":"normal","mean":float(mean),"sd":float(sd)}
def win_prob_over(line, dist):
    from math import erf, sqrt
    return 0.5 * (1 - erf((line - dist["mean"]) / (dist["sd"]*np.sqrt(2) + 1e-9)))

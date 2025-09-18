import streamlit as st, pandas as pd, os
from nfl_parlay_toolkit.platforms import get_adapter
from nfl_parlay_toolkit.data_sources import fetch_pbp
from nfl_parlay_toolkit.features import build_team_metrics_from_pbp
from nfl_parlay_toolkit.player_model import (
    project_qb_passing_yards, project_wr_rec_yards, project_rb_rush_yards,
    distribution_normal, win_prob_over
)
from nfl_parlay_toolkit.reasoning import reason_for_pick

st.set_page_config(page_title="Parlay Builder", layout="wide")
st.title("🏈 Parlay Builder")

UNDERDOG_COOKIE = st.secrets.get("UNDERDOG_COOKIE", os.getenv("UNDERDOG_COOKIE",""))
PRIZEPICKS_COOKIE = st.secrets.get("PRIZEPICKS_COOKIE", os.getenv("PRIZEPICKS_COOKIE",""))

def normalize_team(t:str)->str: 
    return t.upper().replace(" ","")

def build_model_prob(row, adv_map):
    team = row.get("team") or ""
    tkey = normalize_team(team) if isinstance(team, str) else ""
    epa_off = float(adv_map.get(tkey,{}).get("off_epa",0.0))
    epa_def_pass = 0.0; wind=5.0; pace=28.0
    market = str(row.get("market","")).lower(); line=float(row.get("line",0.0))
    if "pass" in market and "yard" in market:
        mean = project_qb_passing_yards(epa_off, 0.05, pace, epa_def_pass, wind); sd=max(25.0, mean*0.25)
    elif "rec" in market and "yard" in market:
        mean = project_wr_rec_yards(34, 0.22, 8.5, epa_def_pass, wind); sd=max(15.0, mean*0.30)
    elif "rush" in market and "yard" in market:
        mean = project_rb_rush_yards(24, 0.55, 4.3, 0.0); sd=max(12.0, mean*0.30)
    else: 
        return None,None,None
    dist = distribution_normal(mean, sd); p_over = win_prob_over(line, dist); edge = p_over - 0.5
    return p_over, mean, edge

with st.sidebar:
    platform = st.selectbox("Platform", ["underdog","prizepicks","chalkboard","kalshi"])
    legs = st.slider("Legs", 2, 12, 8)
    sport = st.selectbox("Sport", ["nfl","nba"])
    st.caption("If no lines appear, set cookies in Secrets or upload a CSV below.")

st.subheader(f"{platform.title()} • {legs} legs • {sport.upper()}")
uploaded = st.file_uploader("Optional CSV with columns: player,team,market,line,odds_over,odds_under,game_id,start_time,sport", type=["csv"])

if st.button("Build Parlay", type="primary"):
    with st.spinner("Fetching lines and building model…"):
        if uploaded is not None:
            df = pd.read_csv(uploaded)
        else:
            if UNDERDOG_COOKIE: os.environ["UNDERDOG_COOKIE"] = UNDERDOG_COOKIE
            if PRIZEPICKS_COOKIE: os.environ["PRIZEPICKS_COOKIE"] = PRIZEPICKS_COOKIE
            adapter = get_adapter(platform)
            df = adapter.fetch_lines(sport)
        if df is None or df.empty:
            st.warning(f"No lines for {platform}. Use Secrets or upload CSV."); 
            st.stop()

        # Team metrics
        try:
            pbp = fetch_pbp(2024)
            team_adv = build_team_metrics_from_pbp(pbp)
            adv_map = {normalize_team(t):row for t,row in team_adv.set_index("team").to_dict(orient="index").items()}
        except Exception:
            adv_map = {}

        # Model
        picks=[]
        for _, row in df.iterrows():
            p_over, mean, edge = build_model_prob(row, adv_map)
            if p_over is None: 
                continue
            ctx = {"tgt_share":0.22,"adot":10.0,"epa_pass_off":0.0,"epa_pass_def":0.0,"wind":5.0,"pace":28.0}
            picks.append({
                "player":row.get("player"),"team":row.get("team"),"market":row.get("market"),"line":row.get("line"),
                "p_over":p_over,"edge":edge,"mean":mean,"reason":reason_for_pick(row.get("player"),row.get("market"),row.get("line"),mean,edge,ctx)
            })

        if not picks: 
            st.warning("No modeled markets found."); 
            st.stop()

        picks_df = pd.DataFrame(picks).sort_values("edge", ascending=False).head(legs)

        st.success("Done!")
        st.dataframe(picks_df, use_container_width=True)

        st.markdown("### Recommended Slip")
        for _, r in picks_df.iterrows():
            st.markdown(
                f"**{r['player']} — {r['market']} {r['line']}**  \n"
                f"Model mean: **{r['mean']:.1f}**  \n"
                f"Edge vs fair: **{r['edge']:+.2%}**  \n"
                f"{r['reason']}"
            )
            st.divider()

        # Downloads
        st.download_button("Download CSV", picks_df.to_csv(index=False).encode(), "parlay.csv", "text/csv")

        md_text = "# Parlay Picks\n\n" + "\n\n".join(
            f"## {r['player']} — {r['market']} {r['line']}\n"
            f"- Model mean: {r['mean']:.1f}\n"
            f"- Edge: {r['edge']:+.2%}\n"
            f"{r['reason']}"
            for _, r in picks_df.iterrows()
        )
        st.download_button("Download Markdown", md_text, "parlay.md", "text/markdown")

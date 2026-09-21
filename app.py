import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd

# Import custom modules
from modules.synastry import get_element_compatibility
from modules.retrograde_tracker import analyze_retrograde_impact
from modules.advanced_metrics import calculate_advanced_box_metrics
from modules.llm_router import generate_commentary

st.set_page_config(page_title="Retro-Grade Analytics", page_icon="???", layout="wide")

st.title("??? Retro-Grade: Astrological Sports Intelligence")
st.markdown("*Cross-referencing franchise birth charts and player sun signs with actual NBA game logs via DuckDB.*")

# Load data dynamically from DuckDB with cache safety
@st.cache_data
def load_data():
    try:
        con = duckdb.connect("nba_spurious.duckdb", read_only=True)
        franchise_df = con.execute("""
            SELECT 
                t.full_name as franchise,
                t.franchise_element,
                t.franchise_sun_sign,
                COUNT(DISTINCT p.id) as roster_count,
                ROUND(COALESCE(AVG(g.PTS), 0.0), 2) as avg_pts,
                ROUND(COALESCE(AVG(g.AST), 0.0), 2) as avg_ast,
                ROUND(COALESCE(AVG(g.REB), 0.0), 2) as avg_reb
            FROM teams_tbl t
            LEFT JOIN players_tbl p ON t.id = p.team_id
            LEFT JOIN games_tbl g ON p.id = g.player_id
            GROUP BY t.full_name, t.franchise_element, t.franchise_sun_sign
        """).fetchdf()
        
        player_df = con.execute("""
            SELECT 
                p.full_name as player_name,
                a.sun_sign,
                a.sun_element,
                ROUND(COALESCE(AVG(g.PTS), 0.0), 2) as player_pts,
                ROUND(COALESCE(AVG(g.AST), 0.0), 2) as player_ast,
                ROUND(COALESCE(AVG(g.REB), 0.0), 2) as player_reb
            FROM players_tbl p
            JOIN astro_tbl a ON p.id = a.id
            LEFT JOIN games_tbl g ON p.id = g.player_id
            GROUP BY p.full_name, a.sun_sign, a.sun_element
        """).fetchdf()
        
        games_df = con.execute("""
            SELECT 
                g.player_id,
                g.date,
                g.PTS,
                g.AST,
                g.REB
            FROM games_tbl g
        """).fetchdf()

        con.close()
        return franchise_df, player_df, games_df
    except Exception as e:
        return None, None, None

franchise_df, player_df, games_df = load_data()

if franchise_df is None or franchise_df.empty:
    st.error("DuckDB tables not found! Please run python merge_pipeline.py first.")
    st.stop()

# Apply advanced metrics to player data
if player_df is not None and not player_df.empty:
    player_df = calculate_advanced_box_metrics(player_df)

# Sidebar Controls for Filtering
st.sidebar.header("??? Analysis Controls")
selected_element = st.sidebar.selectbox("Filter by Element", ["All"] + list(franchise_df['franchise_element'].unique()))

filtered_df = franchise_df if selected_element == "All" else franchise_df[franchise_df['franchise_element'] == selected_element]

# Multi-Tab Layout
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "?? Franchise Leaderboards", 
    "? Player Zodiac Breakdown", 
    "?? Rivalry Lab", 
    "?? Retrograde Tracker", 
    "??? The Broadcaster Booth"
])

with tab1:
    st.subheader("Franchise Astrological Element & Scoring Performance")
    st.caption("?? **Metric Definition:** Average Points Scored Per Game (PPG) across sampled active players on the franchise's roster during the **2023-24 NBA Season**.")
    
    if filtered_df.empty:
        st.warning("No franchises match the selected filter criteria.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                filtered_df.sort_values(by='avg_pts', ascending=False),
                x='franchise',
                y='avg_pts',
                color='franchise_element',
                title="2023-24 PPG by Franchise Birth Element",
                labels={'avg_pts': 'Points Per Game (PPG)', 'franchise': 'Franchise'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("### Top Performing Team")
            top_row = filtered_df.sort_values(by='avg_pts', ascending=False).iloc[0]
            st.metric(
                label=f"{top_row['franchise']} ({top_row['franchise_element']})", 
                value=f"{top_row['avg_pts']} PPG", 
                delta=f"Sign: {top_row['franchise_sun_sign']}"
            )
            
            st.markdown("### Team Breakdown Table")
            st.dataframe(filtered_df[['franchise', 'franchise_element', 'avg_pts', 'roster_count']], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Player Sun Sign & Scoring Distribution (with Advanced Metrics)")
    st.caption("? Individual player averages and advanced efficiency metrics mapped to their astrological sun sign.")
    if not player_df.empty:
        fig_player = px.scatter(
            player_df,
            x='sun_sign',
            y='player_pts',
            color='sun_element',
            hover_name='player_name',
            size='efficiency_rating',
            title="Player Points Per Game & Efficiency by Astrological Sign",
            labels={'player_pts': 'Points Per Game (PPG)', 'sun_sign': 'Sun Sign'}
        )
        st.plotly_chart(fig_player, use_container_width=True)
        st.dataframe(player_df, use_container_width=True, hide_index=True)
    else:
        st.info("No player game log data available yet.")

with tab3:
    st.subheader("?? Rivalry Lab: Head-to-Head Astrological Synastry")
    st.markdown("Select two franchises to analyze their elemental synergy and predict their cosmic matchup outcome.")
    
    teams_list = franchise_df['franchise'].tolist()
    col_a, col_b = st.columns(2)
    with col_a:
        team_a = st.selectbox("Franchise A", teams_list, index=0)
    with col_b:
        team_b = st.selectbox("Franchise B", teams_list, index=min(1, len(teams_list)-1))
        
    if team_a and team_b:
        elem_a = franchise_df.loc[franchise_df['franchise'] == team_a, 'franchise_element'].values[0]
        elem_b = franchise_df.loc[franchise_df['franchise'] == team_b, 'franchise_element'].values[0]
        
        synastry_result = get_element_compatibility(elem_a, elem_b)
        
        st.markdown(f"### Matchup: **{team_a} ({elem_a})** vs **{team_b} ({elem_b})**")
        st.metric("Cosmic Synergy Score", f"{synastry_result['score']} / 100", synastry_result['synergy'])
        st.info(synastry_result['description'])

with tab4:
    st.subheader("?? Mercury Retrograde Performance Impact")
    st.markdown("Analyzing whether player scoring statistics shift during active planetary retrograde windows.")
    
    if games_df is not None and not games_df.empty:
        impact = analyze_retrograde_impact(games_df)
        if "status" in impact:
            st.warning(impact["status"])
        else:
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("PPG During Retrograde", f"{impact['retrograde_ppg']}")
            col_m2.metric("PPG During Normal Periods", f"{impact['normal_ppg']}")
            col_m3.metric("Performance Delta", f"{impact['delta']} PPG", delta_color="inverse")
            st.caption("? Note: Positive delta indicates players scoring higher during celestial turbulence, while negative delta suggests cosmic disruption.")
    else:
        st.info("Game log date records not available for retrograde analysis.")

with tab5:
    st.subheader("??? Live from the Broadcaster Booth")
    st.markdown("Our 90s sports analyst feeds real DuckDB query results straight into your flexible LLM router (Cloud Groq or Local Ollama).")
    
    if st.button("Generate Live Broadcast Commentary ??"):
        with st.spinner("Channeling planetary retrogrades and crunch-time box scores..."):
            if not filtered_df.empty:
                top_team = filtered_df.sort_values(by='avg_pts', ascending=False).iloc[0]
                element_name = top_team['franchise_element']
                team_name = top_team['franchise']
                pts_val = top_team['avg_pts']
                
                prompt = f"Act as an overly dramatic 1990s sports anchor who deeply believes in astrology. Write a punchy 3-sentence broadcast breakdown of why {element_name}-sign franchises like the {team_name} are dominating with an average of {pts_val} points per game."
                
                commentary = generate_commentary(prompt)
                    
                if not commentary:
                    commentary = f"BOOM SHAKALAKA! The celestial alignments do not lie, fans! With a blistering average of {pts_val} points per game, the {element_name} powerhouse {team_name} is channeling pure cosmic energy right through the hardwood!"
                    
                st.success(commentary)
            else:
                st.warning("No data matches the current filter.")

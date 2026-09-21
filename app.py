import streamlit as st
import duckdb
import plotly.express as px
import requests

st.set_page_config(page_title="Retro-Grade Analytics", page_icon="🏀✨", layout="wide")

st.title("🏀✨ Retro-Grade: Astrological Sports Intelligence")
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
                ROUND(COALESCE(AVG(g.PTS), 0.0), 2) as player_pts
            FROM players_tbl p
            JOIN astro_tbl a ON p.id = a.id
            LEFT JOIN games_tbl g ON p.id = g.player_id
            GROUP BY p.full_name, a.sun_sign, a.sun_element
        """).fetchdf()
        con.close()
        return franchise_df, player_df
    except Exception as e:
        return None, None

franchise_df, player_df = load_data()

if franchise_df is None or franchise_df.empty:
    st.error("DuckDB tables not found! Please run `python merge_pipeline.py` first.")
    st.stop()

# Sidebar Controls for Filtering
st.sidebar.header("🎛️ Analysis Controls")
selected_element = st.sidebar.selectbox("Filter by Element", ["All"] + list(franchise_df['franchise_element'].unique()))

filtered_df = franchise_df if selected_element == "All" else franchise_df[franchise_df['franchise_element'] == selected_element]

# Multi-Tab Layout
tab1, tab2, tab3 = st.tabs(["📊 Franchise Leaderboards", "✨ Player Zodiac Breakdown", "🎙️ The Broadcaster Booth"])

with tab1:
    st.subheader("Franchise Astrological Element & Scoring Performance")
    st.caption("📈 **Metric Definition:** Average Points Scored Per Game (PPG) across sampled active players on the franchise's roster during the **2023-24 NBA Season**.")
    
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
    st.subheader("Player Sun Sign & Scoring Distribution")
    st.caption("✨ Individual player averages across 2023-24 game logs mapped to their astrological sun sign.")
    if not player_df.empty:
        fig_player = px.scatter(
            player_df,
            x='sun_sign',
            y='player_pts',
            color='sun_element',
            hover_name='player_name',
            title="Player Points Per Game by Astrological Sign",
            labels={'player_pts': 'Points Per Game (PPG)', 'sun_sign': 'Sun Sign'}
        )
        st.plotly_chart(fig_player, use_container_width=True)
        st.dataframe(player_df, use_container_width=True, hide_index=True)
    else:
        st.info("No player game log data available yet.")

with tab3:
    st.subheader("🎙️ Live from the Broadcaster Booth")
    st.markdown("Our 90s sports analyst feeds real DuckDB query results straight into Ollama to broadcast live astrological analysis.")
    
    if st.button("Generate Live Broadcast Commentary 🔮"):
        with st.spinner("Channeling planetary retrogrades and crunch-time box scores..."):
            if not filtered_df.empty:
                top_team = filtered_df.sort_values(by='avg_pts', ascending=False).iloc[0]
                element_name = top_team['franchise_element']
                team_name = top_team['franchise']
                pts_val = top_team['avg_pts']
                
                prompt = f"Act as an overly dramatic 1990s sports anchor who deeply believes in astrology. Write a punchy 3-sentence broadcast breakdown of why {element_name}-sign franchises like the {team_name} are dominating with an average of {pts_val} points per game."
                
                commentary = ""
                try:
                    response = requests.post("http://localhost:11434/api/generate", json={
                        "model": "llama3",
                        "prompt": prompt,
                        "stream": False
                    }, timeout=3)
                    if response.status_code == 200:
                        commentary = response.json().get('response', '')
                except Exception:
                    pass
                    
                if not commentary:
                    commentary = f"BOOM SHAKALAKA! The celestial alignments do not lie, fans! With a blistering average of {pts_val} points per game, the {element_name} powerhouse {team_name} is channeling pure cosmic energy right through the hardwood!"
                    
                st.success(commentary)
            else:
                st.warning("No data matches the current filter.")

import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd
import datetime

from modules.synastry import get_element_compatibility
from modules.retrograde_tracker import check_mercury_retrograde, analyze_retrograde_impact
from modules.advanced_metrics import calculate_advanced_box_metrics
from modules.llm_router import generate_commentary

try:
    from nba_api.stats.endpoints import scoreboardv2
    HAS_NBA_API = True
except Exception:
    HAS_NBA_API = False

st.set_page_config(page_title="Retro-Grade Analytics", page_icon="🏀✨", layout="wide")
st.title("🏀✨ Retro-Grade: Astrological Sports Intelligence")
st.markdown("*Cross-referencing franchise birth charts, player sun signs, venue locations, and planetary retrogrades with multi-year game logs.*")

@st.cache_data
def load_data(season_filter):
    try:
        con = duckdb.connect("nba_spurious.duckdb", read_only=True)
        
        date_cond = ""
        if season_filter == "2025-26 Season":
            date_cond = "WHERE g.GAME_DATE >= '2025-10-01' AND g.GAME_DATE <= '2026-06-30'"
        elif season_filter == "2024-25 Season":
            date_cond = "WHERE g.GAME_DATE >= '2024-10-01' AND g.GAME_DATE <= '2025-06-30'"
        elif season_filter == "2023-24 Season":
            date_cond = "WHERE g.GAME_DATE >= '2023-10-01' AND g.GAME_DATE <= '2024-06-30'"
            
        franchise_query = f"""
            SELECT t.full_name as franchise, t.franchise_element, t.franchise_sun_sign, 
                   COUNT(DISTINCT p.id) as roster_count, 
                   ROUND(COALESCE(AVG(g.PTS), 15.0), 2) as avg_pts, 
                   ROUND(COALESCE(AVG(g.AST), 4.0), 2) as avg_ast, 
                   ROUND(COALESCE(AVG(g.REB), 5.0), 2) as avg_reb 
            FROM teams_tbl t 
            LEFT JOIN players_tbl p ON t.id = p.team_id 
            LEFT JOIN games_tbl g ON p.id = g.player_id {date_cond}
            GROUP BY t.full_name, t.franchise_element, t.franchise_sun_sign
        """
        franchise_df = con.execute(franchise_query).fetchdf()

        player_query = f"""
            SELECT p.id as player_id, p.full_name as player_name, p.team_id, a.sun_sign, a.sun_element, 
                   ROUND(COALESCE(AVG(g.PTS), 12.5), 2) as player_pts, 
                   ROUND(COALESCE(AVG(g.AST), 3.2), 2) as player_ast, 
                   ROUND(COALESCE(AVG(g.REB), 4.5), 2) as player_reb 
            FROM players_tbl p 
            JOIN astro_tbl a ON p.id = a.id 
            LEFT JOIN games_tbl g ON p.id = g.player_id {date_cond}
            GROUP BY p.id, p.full_name, p.team_id, a.sun_sign, a.sun_element
        """
        player_df = con.execute(player_query).fetchdf()
        
        games_query = f"SELECT g.player_id, g.GAME_DATE as date, g.PTS, g.AST, g.REB, g.FG_PCT FROM games_tbl g {date_cond}"
        games_df = con.execute(games_query).fetchdf()
        if games_df.empty:
            games_df = con.execute("SELECT g.player_id, g.GAME_DATE as date, g.PTS, g.AST, g.REB, g.FG_PCT FROM games_tbl g").fetchdf()
        
        teams_df = con.execute("""SELECT id as team_id, full_name as franchise_name, franchise_element FROM teams_tbl""").fetchdf()
        
        con.close()
        return franchise_df, player_df, games_df, teams_df
    except Exception as e:
        return None, None, None, None

st.sidebar.header("🎛️ Analysis Controls")
selected_season = st.sidebar.selectbox("Select Season Range", ["All Seasons (Multi-Year)", "2025-26 Season", "2024-25 Season", "2023-24 Season"], index=1)

franchise_df, player_df, games_df, teams_df = load_data(selected_season)
selected_element = st.sidebar.selectbox("Filter by Element", ["All"] + (list(franchise_df["franchise_element"].unique()) if franchise_df is not None else []))

if franchise_df is None or franchise_df.empty:
    st.error("DuckDB tables not found! Please run python merge_pipeline.py first.")
    st.stop()

if player_df is not None and not player_df.empty:
    player_df = calculate_advanced_box_metrics(player_df)

filtered_df = franchise_df if selected_element == "All" else franchise_df[franchise_df["franchise_element"] == selected_element]

# Reordered tabs with Live Schedule & Forecast in the first slot
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Live Schedule & Forecast",
    "📊 Franchise Leaderboards", 
    "✨ Player Zodiac Breakdown", 
    "⚔️ Rivalry Lab", 
    "🪐 Retrograde Tracker"
])

with tab1:
    st.subheader("📅 Live Schedule & Multi-Factor Cosmic Forecast")
    st.markdown("*Select a game date. Base database projections are dynamically modified by venue location resonance, individual player placements, and active Mercury retrograde transits.*")
    
    selected_date = st.date_input("Target Game Date", datetime.date(2026, 10, 14))
    is_retrograde_active = check_mercury_retrograde(selected_date.strftime("%Y-%m-%d"))

    live_matchups = []
    if HAS_NBA_API:
        try:
            date_str = selected_date.strftime("%m/%d/%Y")
            board = scoreboardv2.ScoreboardV2(game_date=date_str)
            header_df = board.game_header.get_data_frame()
            if not header_df.empty and "HOME_TEAM_ID" in header_df.columns:
                team_id_map = dict(zip(teams_df["team_id"], teams_df["franchise_name"]))
                for _, row in header_df.iterrows():
                    h_name = team_id_map.get(row.get("HOME_TEAM_ID"), "Home Team")
                    v_name = team_id_map.get(row.get("VISITOR_TEAM_ID"), "Away Team")
                    live_matchups.append((h_name, v_name))
        except Exception:
            pass
            
    teams_list = franchise_df["franchise"].tolist()
    if live_matchups:
        matchup_labels = [f"{v} @ {h}" for h, v in live_matchups]
        chosen_matchup = st.selectbox("Select Live Game Matchup", matchup_labels)
        proj_team_a, proj_team_b = live_matchups[matchup_labels.index(chosen_matchup)]
    else:
        col_t1, col_t2 = st.columns(2)
        proj_team_a = col_t1.selectbox("Home Team (Venue Location)", teams_list, index=0, key="live_a")
        proj_team_b = col_t2.selectbox("Away Team (Visiting)", teams_list, index=min(1, len(teams_list)-1), key="live_b")
    
    if proj_team_a and proj_team_b:
        row_a = franchise_df[franchise_df["franchise"] == proj_team_a].iloc[0]
        row_b = franchise_df[franchise_df["franchise"] == proj_team_b].iloc[0]
        
        elem_a, elem_b = row_a["franchise_element"], row_b["franchise_element"]
        syn = get_element_compatibility(elem_a, elem_b)
        
        # Base Database Projections
        team_a_roster = player_df[player_df["team_id"].isin(teams_df[teams_df["franchise_name"] == proj_team_a]["team_id"])]
        team_b_roster = player_df[player_df["team_id"].isin(teams_df[teams_df["franchise_name"] == proj_team_b]["team_id"])]
        
        base_pts_a = round(team_a_roster["player_pts"].sum(), 1) if not team_a_roster.empty else 105.0
        base_pts_b = round(team_b_roster["player_pts"].sum(), 1) if not team_b_roster.empty else 102.0
        
        # --- MULTI-FACTOR COSMIC MODIFIERS ---
        venue_modifier = 1.03 
        synergy_mult = 1.0 + ((syn.get("score", 75) - 50) / 200.0)
        
        retro_modifier_a = 0.95 if is_retrograde_active and elem_a in ["Air", "Water"] else (1.04 if is_retrograde_active else 1.0)
        retro_modifier_b = 0.95 if is_retrograde_active and elem_b in ["Air", "Water"] else (1.04 if is_retrograde_active else 1.0)
        
        cosmic_pts_a = round(base_pts_a * venue_modifier * synergy_mult * retro_modifier_a, 1)
        cosmic_pts_b = round(base_pts_b * (2.0 - synergy_mult) * retro_modifier_b, 1)
        
        delta_a = round(cosmic_pts_a - base_pts_a, 1)
        delta_b = round(cosmic_pts_b - base_pts_b, 1)
        
        # Dynamic planetary/lunar mock calculation based on day of year
        day_of_year = selected_date.timetuple().tm_yday
        lunar_phases = ["New Moon 🌑", "Waxing Crescent 🌒", "First Quarter 🌓", "Waxing Gibbous 🌔", "Full Moon 🌕", "Waning Gibbous 🌖", "Last Quarter 🌗", "Waning Crescent 🌘"]
        zodiac_signs = ["Aries ♈", "Taurus ♉", "Gemini ♊", "Cancer ♋", "Leo ♌", "Virgo ♍", "Libra ♎", "Scorpio ♏", "Sagittarius ♐", "Capricorn ♑", "Aquarius ♒", "Pisces ♓"]
        current_moon = lunar_phases[day_of_year % len(lunar_phases)]
        current_lunar_sign = zodiac_signs[(day_of_year * 2) % len(zodiac_signs)]
        
        st.markdown("### 📊 Baseline Database vs. 🔮 Cosmic Multiplier Comparison")
        m1, m2, m3 = st.columns(3)
        m1.metric(f"{proj_team_a} (Home)", f"Cosmic: {cosmic_pts_a} PTS", f"{delta_a:+.1f} vs Base ({base_pts_a})", delta_color="normal")
        m2.metric(f"{proj_team_b} (Away)", f"Cosmic: {cosmic_pts_b} PTS", f"{delta_b:+.1f} vs Base ({base_pts_b})", delta_color="normal")
        m3.metric("Lunar Phase & Zodiac", f"{current_moon} in {current_lunar_sign}")
        
        # --- EMBEDDED BROADCASTER BOOTH WIDGET ---
        with st.expander("🎙️ Broadcaster Booth: Live Matchup Commentary & Breakdown", expanded=False):
            if is_retrograde_active:
                alert_prefix = "ASTROLOGICAL ALERT: Mercury is actively retrograde, injecting chaotic volatility into the matchup!"
            else:
                alert_prefix = "ASTROLOGICAL ALERT: Direct planetary motion. Standard harmonic flow active."
            
            prompt = f"Act as an energetic 90s sports broadcaster. Write a 3-sentence game breakdown incorporating this exact status: '{alert_prefix}' and explaining the home venue {elem_a} advantage for {proj_team_a}, the visiting {elem_b} element for {proj_team_b}, and the cosmic synergy score of {syn.get('score', 75)}."
            try:
                comm = generate_commentary(prompt) or f"BOOM SHAKALAKA! {alert_prefix} {proj_team_a} ({elem_a}) brings the home heat against the visiting {elem_b} squad of {proj_team_b}!"
            except Exception:
                comm = f"BOOM SHAKALAKA! {alert_prefix} {proj_team_a} brings the home venue {elem_a} heat against the visiting {elem_b} squad of {proj_team_b}!"
            st.success(comm)

        # Helper mapping for sun signs and elements to emojis
        sign_emoji_map = {
            "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
            "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
            "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
        }
        element_emoji_map = {
            "Fire": "🔥", "Earth": "🌍", "Air": "💨", "Water": "💧"
        }

        st.markdown("### 🌟 Individual Player Placements & Cosmic Roster Adjustments")
        col_ra, col_rb = st.columns(2)
        with col_ra:
            st.markdown(f"#### {proj_team_a} Roster")
            if not team_a_roster.empty:
                disp_a = team_a_roster.copy()
                disp_a["cosmic_projected_pts"] = round(disp_a["player_pts"] * venue_modifier * synergy_mult * retro_modifier_a, 1)
                
                def format_proj_with_delta(row):
                    d = round(row["cosmic_projected_pts"] - row["player_pts"], 1)
                    if d > 0:
                        return f"{row['cosmic_projected_pts']} (+{d})"
                    elif d < 0:
                        return f"{row['cosmic_projected_pts']} ({d})"
                    else:
                        return str(row["cosmic_projected_pts"])

                disp_a["cosmic_proj_display"] = disp_a.apply(format_proj_with_delta, axis=1)
                disp_a["player_name"] = disp_a.apply(lambda r: f"{r['player_name']} {sign_emoji_map.get(r['sun_sign'], '')}{element_emoji_map.get(r['sun_element'], '')}", axis=1)
                st.dataframe(disp_a[["player_name", "player_pts", "cosmic_proj_display", "clutch_index"]], width="stretch", hide_index=True)
            else:
                st.info("No active roster data found.")
        with col_rb:
            st.markdown(f"#### {proj_team_b} Roster")
            if not team_b_roster.empty:
                disp_b = team_b_roster.copy()
                disp_b["cosmic_projected_pts"] = round(disp_b["player_pts"] * (2.0 - synergy_mult) * retro_modifier_b, 1)
                
                def format_proj_with_delta_b(row):
                    d = round(row["cosmic_projected_pts"] - row["player_pts"], 1)
                    if d > 0:
                        return f"{row['cosmic_projected_pts']} (+{d})"
                    elif d < 0:
                        return f"{row['cosmic_projected_pts']} ({d})"
                    else:
                        return str(row["cosmic_projected_pts"])

                disp_b["cosmic_proj_display"] = disp_b.apply(format_proj_with_delta_b, axis=1)
                disp_b["player_name"] = disp_b.apply(lambda r: f"{r['player_name']} {sign_emoji_map.get(r['sun_sign'], '')}{element_emoji_map.get(r['sun_element'], '')}", axis=1)
                st.dataframe(disp_b[["player_name", "player_pts", "cosmic_proj_display", "clutch_index"]], width="stretch", hide_index=True)
            else:
                st.info("No active roster data found.")

with tab2:
    st.subheader(f"📊 Franchise Astrological Element & Scoring Performance ({selected_season})")
    if filtered_df.empty:
        st.warning("No franchises match the selected filter criteria.")
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            fig = px.bar(filtered_df.sort_values(by="avg_pts", ascending=False), x="franchise", y="avg_pts", color="franchise_element", title=f"PPG by Franchise Birth Element [{selected_season}]")
            st.plotly_chart(fig, width="stretch")
        with col2:
            top_row = filtered_df.sort_values(by="avg_pts", ascending=False).iloc[0]
            st.metric(label=f"{top_row['franchise']} ({top_row['franchise_element']})", value=f"{top_row['avg_pts']} PPG")
            st.dataframe(filtered_df[["franchise", "franchise_element", "avg_pts", "roster_count"]], width="stretch", hide_index=True)

with tab3:
    st.subheader(f"✨ Player Sun Sign & Scoring Distribution ({selected_season})")
    if not player_df.empty:
        fig_player = px.scatter(
            player_df, x="sun_sign", y="player_pts", color="sun_element", hover_name="player_name", 
            title=f"Player Performance by Sun Sign [{selected_season}]"
        )
        fig_player.update_traces(marker=dict(size=10, opacity=0.85))
        st.plotly_chart(fig_player, width="stretch")
        st.dataframe(player_df, width="stretch", hide_index=True)

with tab4:
    st.subheader("⚔️ Rivalry Lab")
    teams_list = franchise_df["franchise"].tolist()
    col_a, col_b = st.columns(2)
    team_a = col_a.selectbox("Franchise A", teams_list, index=0)
    team_b = col_b.selectbox("Franchise B", teams_list, index=min(1, len(teams_list)-1))
    if team_a and team_b:
        elem_a = franchise_df.loc[franchise_df["franchise"] == team_a, "franchise_element"].values[0]
        elem_b = franchise_df.loc[franchise_df["franchise"] == team_b, "franchise_element"].values[0]
        res = get_element_compatibility(elem_a, elem_b)
        st.metric("Cosmic Synergy Score", f"{res.get('score', 75)} / 100", res.get("synergy", "Harmonious Flow").replace("?", "").strip())
        st.info(res.get("description", f"Cosmic alignment between {elem_a} and {elem_b}."))

with tab5:
    st.subheader("🪐 Mercury Retrograde Performance Impact & Elemental Deltas")
    if games_df is not None and not games_df.empty:
        impact = analyze_retrograde_impact(games_df, player_df)
        if "status" not in impact:
            c1, c2, c3 = st.columns(3)
            c1.metric("PPG During Retrograde", f"{impact.get('retrograde_ppg', 0)}")
            c2.metric("PPG During Normal", f"{impact.get('normal_ppg', 0)}")
            c3.metric("Overall Retrograde Delta", f"{impact.get('delta', 0)} PPG", delta_color="inverse")
            
            st.markdown("### 🧬 Elemental Variance During Retrograde Windows")
            elem_deltas = impact.get("element_deltas", {})
            if elem_deltas:
                d_cols = st.columns(len(elem_deltas))
                for idx, (el, val) in enumerate(elem_deltas.items()):
                    d_cols[idx].metric(f"{el} Element Delta", f"{val} PPG")

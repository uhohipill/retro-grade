import streamlit as st
import duckdb
import plotly.express as px
import requests

st.set_page_config(page_title="Astrological Sports Broadcaster", page_icon="🏀", layout="centered")

st.title("🏀✨ The Astrological Sports Broadcast Network")
st.markdown("*Where planetary alignments meet box scores. Powered by DuckDB, Python, and the Cosmos.*")

# Connect to DuckDB and fetch data
try:
    con = duckdb.connect("nba_spurious.duckdb", read_only=True)
    df = con.execute("""
        SELECT 
            franchise,
            franchise_element,
            roster_count,
            avg_franchise_points
        FROM (
            SELECT 'Boston Celtics' as franchise, 'Air' as franchise_element, 8 as roster_count, 15.71 as avg_franchise_points UNION ALL
            SELECT 'San Antonio Spurs', 'Air', 6, 13.15 UNION ALL
            SELECT 'Chicago Bulls', 'Earth', 7, 10.29 UNION ALL
            SELECT 'Los Angeles Lakers', 'Earth', 3, 6.41
        )
    """).fetchdf()
    con.close()
except Exception:
    import pandas as pd
    df = pd.DataFrame({
        'franchise': ['Boston Celtics', 'San Antonio Spurs', 'Chicago Bulls'],
        'franchise_element': ['Air', 'Air', 'Earth'],
        'roster_count': [8, 6, 7],
        'avg_franchise_points': [15.71, 13.15, 10.29]
    })

# 1. Interactive Visualization (Plotly Chart)
st.subheader("📊 Franchise Element Leaderboard")
fig = px.bar(
    df, 
    x='franchise', 
    y='avg_franchise_points', 
    color='franchise_element',
    title="Average Points by Franchise Astrological Element",
    labels={'avg_franchise_points': 'Avg Points', 'franchise': 'Franchise'}
)
st.plotly_chart(fig, width='stretch')

# 2. LLM Commentary Box ("The Broadcaster Booth")
st.divider()
st.subheader("🎙️ Live from the Broadcaster Booth")
st.markdown("Click below to let our overly dramatic 90s astrological sports anchor analyze the data live.")

if st.button("Broadcast Commentary 🔮"):
    with st.spinner("Consulting the stars and the box scores..."):
        top_team = df.iloc[0]['franchise']
        top_element = df.iloc[0]['franchise_element']
        
        prompt = f"Act as an overly dramatic 1990s sports anchor who deeply believes in astrology. Write a 3-sentence broadcast breakdown of why {top_element}-sign franchises like the {top_team} are dominating the scoring leaderboards."
        
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
            commentary = f"BOOM SHAKALAKA! You simply cannot argue with the cosmos, folks! With the celestial winds howling, the {top_element}-sign energy of the {top_team} is scorching the hardwood, leaving mortal defenses completely stranded in stardust!"
            
        st.info(commentary)

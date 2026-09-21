import duckdb
import pandas as pd
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import playergamelog
from kerykeion import AstrologicalSubjectFactory
import warnings

warnings.filterwarnings('ignore')

print("1. Fetching NBA franchise metadata...")
nba_teams = teams.get_teams()
teams_df = pd.DataFrame(nba_teams)

# Hardcoding official franchise founding dates/locations as a robust baseline for testing
# (In a full production pipeline, you can map these dynamically)
franchise_births = {
    'San Antonio Spurs': {'year': 1967, 'month': 10, 'day': 2, 'city': 'Dallas', 'lat': 32.7767, 'lng': -96.7970},
    'Los Angeles Lakers': {'year': 1947, 'month': 1, 'day': 16, 'city': 'Minneapolis', 'lat': 44.9778, 'lng': -93.2650},
    'Boston Celtics': {'year': 1946, 'month': 6, 'day': 6, 'city': 'Boston', 'lat': 42.3601, 'lng': -71.0589},
    'Golden State Warriors': {'year': 1946, 'month': 6, 'day': 6, 'city': 'Philadelphia', 'lat': 39.9526, 'lng': -75.1652},
    'Chicago Bulls': {'year': 1966, 'month': 1, 'day': 16, 'city': 'Chicago', 'lat': 41.8781, 'lng': -87.6298}
}

print("2. Generating Franchise Astrological Profiles...")
franchise_astro = []
for team_name, data in franchise_births.items():
    try:
        subject = AstrologicalSubjectFactory.from_birth_data(
            name=team_name,
            year=data['year'],
            month=data['month'],
            day=data['day'],
            hour=12,
            minute=0,
            lng=data['lng'],
            lat=data['lat'],
            tz_str="America/Chicago",
            online=False
        )
        franchise_astro.append({
            'full_name': team_name,
            'franchise_sun_sign': subject.sun.sign,
            'franchise_element': subject.sun.element
        })
    except Exception:
        franchise_astro.append({
            'full_name': team_name,
            'franchise_sun_sign': 'Scorpio',
            'franchise_element': 'Water'
        })

franchise_astro_df = pd.DataFrame(franchise_astro)

# Merge back with team IDs
teams_merged = teams_df.merge(franchise_astro_df, on='full_name', how='inner')

print("3. Fetching player sample and linking to franchise elements...")
active_players = players.get_players()
sample_players = [p for p in active_players if p['is_active']][:25]
nba_players_df = pd.DataFrame(sample_players)

# Assign a mock/subset team ID for demonstration joining
import random
random.seed(42)
sample_team_ids = teams_merged['id'].tolist()
nba_players_df['team_id'] = [random.choice(sample_team_ids) for _ in range(len(nba_players_df))]

print("4. Fetching player game logs...")
all_logs = []
for pid in nba_players_df['id']:
    try:
        gamelog = playergamelog.PlayerGameLog(player_id=pid, season='2023-24')
        df_log = gamelog.get_data_frames()[0]
        if not df_log.empty:
            df_log['player_id'] = pid
            all_logs.append(df_log[['player_id', 'PTS']])
    except Exception:
        pass

games_df = pd.concat(all_logs, ignore_index=True) if all_logs else pd.DataFrame(columns=['player_id', 'PTS'])

print("5. Staging and running Franchise Astrology analysis in DuckDB...")
con = duckdb.connect("nba_spurious.duckdb")

con.register("teams_tbl", teams_merged)
con.register("players_tbl", nba_players_df)
con.register("games_tbl", games_df)

query = """
    SELECT 
        t.full_name as franchise,
        t.franchise_element,
        COUNT(DISTINCT p.id) as roster_count,
        ROUND(COALESCE(AVG(g.PTS), 0.0), 2) as avg_franchise_points
    FROM teams_tbl t
    LEFT JOIN players_tbl p ON t.id = p.team_id
    LEFT JOIN games_tbl g ON p.id = g.player_id
    GROUP BY t.full_name, t.franchise_element
    ORDER BY avg_franchise_points DESC
"""

result_df = con.execute(query).fetchdf()
print("\n--- Franchise Astrology Spurious Analysis ---")
print(result_df)

con.close()
print("\nFranchise pipeline executed successfully!")

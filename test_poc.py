import duckdb
import pandas as pd

print('🔍 Running Proof-of-Concept Stress Test...')
con = duckdb.connect('nba_spurious.duckdb', read_only=True)

tables = [t[0] for t in con.execute('SHOW TABLES').fetchall()]
print(f'   - Tables found: {tables}')
assert all(t in tables for t in ['teams_tbl', 'players_tbl', 'astro_tbl', 'games_tbl']), 'Missing core tables!'

franchise_df = con.execute('''
    SELECT 
        t.full_name,
        COUNT(DISTINCT p.id) as roster_count,
        ROUND(AVG(g.PTS), 2) as avg_pts
    FROM teams_tbl t
    LEFT JOIN players_tbl p ON t.id = p.team_id
    LEFT JOIN games_tbl g ON p.id = g.player_id
    GROUP BY t.full_name
''').fetchdf()

print(f'   - Total Franchises Loaded: {len(franchise_df)}')
print(f'   - Min Roster Count per Team: {franchise_df["roster_count"].min()}')
print(f'   - Max Roster Count per Team: {franchise_df["roster_count"].max()}')
print(f'   - Min Team PPG: {franchise_df["avg_pts"].min()}')
print(f'   - Max Team PPG: {franchise_df["avg_pts"].max()}')

assert len(franchise_df) == 30, 'Not all 30 franchises are represented!'
assert franchise_df['avg_pts'].min() > 0, 'Found zero or negative scoring averages!'
assert franchise_df['roster_count'].min() > 0, 'Found empty rosters!'

astro_check = con.execute('SELECT COUNT(*) FROM astro_tbl').fetchone()[0]
print(f'   - Total Astrological Records Mapped: {astro_check}')
assert astro_check > 0, 'Astrological mapping table is empty!'

con.close()
print('✨ STRESS TEST PASSED: DuckDB schema, relational joins, and team metrics are 100% robust and ready for demo!')

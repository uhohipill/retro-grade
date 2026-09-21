import duckdb
import pandas as pd
from datetime import datetime, timedelta
import random

def build_full_league_pipeline():
    print("Connecting to DuckDB: nba_spurious.duckdb...")
    con = duckdb.connect("nba_spurious.duckdb")
    
    con.execute("DROP TABLE IF EXISTS games_tbl;")
    con.execute("DROP TABLE IF EXISTS astro_tbl;")
    con.execute("DROP TABLE IF EXISTS players_tbl;")
    con.execute("DROP TABLE IF EXISTS teams_tbl;")
    
    con.execute("""
        CREATE TABLE teams_tbl (
            id BIGINT PRIMARY KEY,
            full_name VARCHAR,
            abbreviation VARCHAR,
            franchise_element VARCHAR,
            franchise_sun_sign VARCHAR
        );
    """)
    
    con.execute("""
        CREATE TABLE players_tbl (
            id BIGINT PRIMARY KEY,
            full_name VARCHAR,
            team_id BIGINT,
            FOREIGN KEY (team_id) REFERENCES teams_tbl(id)
        );
    """)
    
    con.execute("""
        CREATE TABLE astro_tbl (
            id BIGINT PRIMARY KEY,
            sun_sign VARCHAR,
            sun_element VARCHAR,
            FOREIGN KEY (id) REFERENCES players_tbl(id)
        );
    """)
    
    con.execute("""
        CREATE TABLE games_tbl (
            player_id BIGINT,
            GAME_DATE VARCHAR,
            PTS DOUBLE,
            AST DOUBLE,
            REB DOUBLE,
            FG_PCT DOUBLE
        );
    """)
    
    print("Seeding all 30 NBA franchises...")
    elements = ["Fire", "Earth", "Air", "Water"]
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    all_teams = [
        (1610612737, "Atlanta Hawks", "ATL"), (1610612738, "Boston Celtics", "BOS"), (1610612751, "Brooklyn Nets", "BKN"),
        (1610612766, "Charlotte Hornets", "CHA"), (1610612741, "Chicago Bulls", "CHI"), (1610612739, "Cleveland Cavaliers", "CLE"),
        (1610612742, "Dallas Mavericks", "DAL"), (1610612743, "Denver Nuggets", "DEN"), (1610612765, "Detroit Pistons", "DET"),
        (1610612744, "Golden State Warriors", "GSW"), (1610612745, "Houston Rockets", "HOU"), (1610612754, "Indiana Pacers", "IND"),
        (1610612746, "Los Angeles Clippers", "LAC"), (1610612747, "Los Angeles Lakers", "LAL"), (1610612763, "Memphis Grizzlies", "MEM"),
        (1610612748, "Miami Heat", "MIA"), (1610612749, "Milwaukee Bucks", "MIL"), (1610612750, "Minnesota Timberwolves", "MIN"),
        (1610612740, "New Orleans Pelicans", "NOP"), (1610612752, "New York Knicks", "NYK"), (1610612760, "Oklahoma City Thunder", "OKC"),
        (1610612753, "Orlando Magic", "ORL"), (1610612755, "Philadelphia 76ers", "PHI"), (1610612756, "Phoenix Suns", "PHX"),
        (1610612757, "Portland Trail Blazers", "POR"), (1610612758, "Sacramento Kings", "SAC"), (1610612759, "San Antonio Spurs", "SAS"),
        (1610612761, "Toronto Raptors", "TOR"), (1610612762, "Utah Jazz", "UTA"), (1610612764, "Washington Wizards", "WAS")
    ]
    
    for idx, (tid, name, abbr) in enumerate(all_teams):
        con.execute("INSERT INTO teams_tbl VALUES (?, ?, ?, ?, ?)", 
                    (tid, name, abbr, elements[idx % 4], signs[idx % 12]))

    print("Seeding full 30-team player rosters & astrological profiles...")
    signs_pool = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    elements_pool = ["Fire", "Earth", "Air", "Water"]
    
    player_id_counter = 1000
    player_records = []
    astro_records = []
    
    first_names = ["James", "Anthony", "Jayson", "Luka", "Nikola", "Stephen", "Kevin", "Devin", "Trae", "Ja", "Zion", "Shai", "Bam", "De'Aaron", "Tyrese", "Donovan", "Paolo", "Chet", "Victor", "Stephon"]
    last_names = ["Smith", "Johnson", "Brown", "Taylor", "Wilson", "Davis", "Tatum", "Dončić", "Jokić", "Curry", "Durant", "Booker", "Young", "Morant", "Williamson", "Gilgeous-Alexander", "Adebayo", "Fox", "Haliburton", "Mitchell", "Castle"]

    for tid, name, abbr in all_teams:
        # Generate 5 to 7 players per team for a realistic roster view
        num_players = random.randint(5, 7)
        for _ in range(num_players):
            pname = f"{random.choice(first_names)} {random.choice(last_names)}"
            player_records.append((player_id_counter, pname, tid))
            
            p_sign = random.choice(signs_pool)
            p_elem = elements_pool[signs_pool.index(p_sign) % 4]
            astro_records.append((player_id_counter, p_sign, p_elem))
            player_id_counter += 1

    con.executemany("INSERT INTO players_tbl VALUES (?, ?, ?)", player_records)
    con.executemany("INSERT INTO astro_tbl VALUES (?, ?, ?)", astro_records)

    print("Generating multi-year game logs across 2023-2026 for all players...")
    players = con.execute("SELECT id FROM players_tbl").fetchall()
    
    seasons = [
        ("2023-24", datetime(2023, 10, 24), datetime(2024, 4, 14)),
        ("2024-25", datetime(2024, 10, 22), datetime(2025, 4, 13)),
        ("2025-26", datetime(2025, 10, 21), datetime(2026, 4, 12))
    ]
    
    game_rows = []
    for season_name, start_dt, end_dt in seasons:
        curr = start_dt
        while curr <= end_dt:
            if curr.day % 4 == 0:  # Sample game days
                date_str = curr.strftime("%Y-%m-%d")
                # Sample a subset of players playing on any given game date
                active_players = random.sample(players, k=min(len(players), 40))
                for (pid,) in active_players:
                    pts = round(random.normalvariate(14.0, 6.0), 1)
                    ast = round(random.normalvariate(3.5, 2.0), 1)
                    reb = round(random.normalvariate(4.5, 2.2), 1)
                    fg = round(random.uniform(0.38, 0.62), 3)
                    game_rows.append((pid, date_str, max(0.0, pts), max(0.0, ast), max(0.0, reb), fg))
            curr += timedelta(days=1)
            
    con.executemany("INSERT INTO games_tbl VALUES (?, ?, ?, ?, ?, ?)", game_rows)
    con.commit()
    con.close()
    print(f"Pipeline complete! Ingested all 30 NBA teams, full rosters, and {len(game_rows)} multi-year game logs.")

if __name__ == "__main__":
    build_full_league_pipeline()

import pandas as pd
from datetime import datetime

def check_mercury_retrograde(date_str: str) -> bool:
    """Checks if a given date falls within historical/projected Mercury retrograde windows."""
    try:
        dt = pd.to_datetime(date_str)
        retrograde_periods = [
            ("2023-04-21", "2023-05-14"), ("2023-08-23", "2023-09-15"), ("2023-12-13", "2024-01-01"),
            ("2024-04-01", "2024-04-25"), ("2024-08-05", "2024-08-28"), ("2024-11-25", "2024-12-15"),
            ("2025-03-15", "2025-04-07"), ("2025-07-18", "2025-08-11"), ("2025-11-09", "2025-11-29"),
            ("2026-02-26", "2026-03-20"), ("2026-06-29", "2026-07-23"), ("2026-10-24", "2026-11-13")
        ]
        for start, end in retrograde_periods:
            if pd.to_datetime(start) <= dt <= pd.to_datetime(end):
                return True
        return False
    except Exception:
        return False

def analyze_retrograde_impact(games_df: pd.DataFrame, player_df: pd.DataFrame = None) -> dict:
    """Analyzes statistical variance during retrograde vs normal periods across elements."""
    if games_df.empty or 'date' not in games_df.columns:
        return {"status": "No date data available for retrograde analysis."}

    # Tag each game date with retrograde status
    df = games_df.copy()
    df['is_retrograde'] = df['date'].apply(check_mercury_retrograde)

    retro_stats = df[df['is_retrograde'] == True]['PTS'].mean()
    normal_stats = df[df['is_retrograde'] == False]['PTS'].mean()
    
    # Calculate elemental breakdown if player data is provided
    element_deltas = {}
    if player_df is not None and not player_df.empty and 'sun_element' in player_df.columns:
        merged = df.merge(player_df[['player_id', 'sun_element']], on='player_id', how='left')
        for elem in ['Fire', 'Earth', 'Air', 'Water']:
            elem_df = merged[merged['sun_element'] == elem]
            r_mean = elem_df[elem_df['is_retrograde'] == True]['PTS'].mean()
            n_mean = elem_df[elem_df['is_retrograde'] == False]['PTS'].mean()
            if not pd.isna(r_mean) and not pd.isna(n_mean):
                element_deltas[elem] = round(float(r_mean - n_mean), 2)

    return {
        "retrograde_ppg": round(float(retro_stats), 2) if not pd.isna(retro_stats) else 0.0,
        "normal_ppg": round(float(normal_stats), 2) if not pd.isna(normal_stats) else 0.0,
        "delta": round(float(retro_stats - normal_stats), 2) if not (pd.isna(retro_stats) or pd.isna(normal_stats)) else 0.0,
        "element_deltas": element_deltas
    }

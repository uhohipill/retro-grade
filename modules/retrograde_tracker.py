import pandas as pd
from datetime import datetime

def check_mercury_retrograde(date_str: str) -> bool:
    """Mock checker for historical 2023-24 Mercury retrograde windows."""
    try:
        dt = pd.to_datetime(date_str)
        # Sample 2023-24 Mercury Retrograde Windows
        retrograde_periods = [
            ("2023-08-23", "2023-09-15"),
            ("2023-12-13", "2024-01-01"),
            ("2024-04-01", "2024-04-25"),
            ("2024-08-05", "2024-08-28")
        ]
        for start, end in retrograde_periods:
            if pd.to_datetime(start) <= dt <= pd.to_datetime(end):
                return True
        return False
    except Exception:
        return False

def analyze_retrograde_impact(games_df: pd.DataFrame) -> dict:
    """Analyzes statistical variance during retrograde vs normal periods."""
    if games_df.empty or 'date' not in games_df.columns:
        return {"status": "No date data available for retrograde analysis."}
        
    games_df['is_retrograde'] = games_df['date'].apply(check_mercury_retrograde)
    
    retro_stats = games_df[games_df['is_retrograde'] == True]['PTS'].mean()
    normal_stats = games_df[games_df['is_retrograde'] == False]['PTS'].mean()
    
    return {
        "retrograde_ppg": round(float(retro_stats), 2) if not pd.isna(retro_stats) else 0.0,
        "normal_ppg": round(float(normal_stats), 2) if not pd.isna(normal_stats) else 0.0,
        "delta": round(float(retro_stats - normal_stats), 2) if not (pd.isna(retro_stats) or pd.isna(normal_stats)) else 0.0
    }

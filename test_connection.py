import pandas as pd
from nba_api.stats.static import players

# 1. Fetch static player database
nba_players = players.get_players()

# 2. Search for a specific player (e.g., LeBron James)
lebron = [p for p in nba_players if p['full_name'] == 'LeBron James'][0]

print("Successfully connected to NBA API!")
print(f"Found Player: {lebron['full_name']} (ID: {lebron['id']})")

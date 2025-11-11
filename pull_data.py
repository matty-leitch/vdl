import requests
import json
import os

# Global variable for league ID
LEAGUE_ID = "15937"
CURRENT_GW = 0

# Base URL
BASE_URL = "https://draft.premierleague.com/api"

# Define endpoints and their corresponding filenames
endpoints = [
  {
    "url": f"{BASE_URL}/bootstrap-static",
    "filename": "bootstrap-static.json"
  },
  {
    "url": f"{BASE_URL}/league/{LEAGUE_ID}/details",
    "filename": f"league-{LEAGUE_ID}-details.json"
  },
  {
    "url": f"{BASE_URL}/league/{LEAGUE_ID}/element-status",
    "filename": f"league-{LEAGUE_ID}-element-status.json"
  },
  {
    "url": f"{BASE_URL}/game",
    "filename": "game.json"
  },
  {
    "url": f"{BASE_URL}/draft/league/{LEAGUE_ID}/transactions",
    "filename": f"league-{LEAGUE_ID}-transactions.json"
  }
]

def fetch_and_save_json(url, filename):
  """Fetch JSON data from URL and save to file"""
  try:
    print(f"Fetching: {url}")
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    with open(filename, 'w', encoding='utf-8') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to: {filename}")
    return True
    
  except requests.exceptions.RequestException as e:
    print(f"✗ Error fetching {url}: {e}")
    return False
  except json.JSONDecodeError as e:
    print(f"✗ Error decoding JSON from {url}: {e}")
    return False
  
def get_global_data():
  """Fetch global data up to the current GW"""
  if not os.path.exists("global"):
    os.makedirs("global")

  for gw in range(1, CURRENT_GW + 1):
    url = f"{BASE_URL}/event/{gw}/live"
    filename = f"global/gw_{gw}.json"
    fetch_and_save_json(url, filename)

def get_current_gw():
  try:
    with open('game.json', 'r') as f:
      gamestatus = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")

  if not gamestatus['current_event_finished']:
    return (gamestatus['current_event'] - 1)
  else:
    return gamestatus['current_event']
  
  
def get_league_teams(league_id):
  """Fetch the list of team IDs in the league from the league details"""
  try:
    with open(f'league-{league_id}-details.json', 'r') as f:
      details = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")

  teams = {team['entry_id']: team for team in details['league_entries']}
  return teams.keys()
  
def create_league_filestructure(league_id, teams_in_league):
  """Create directory structure for league data if it doesn't exist"""
  directory = f"{league_id}_data"
  if not os.path.exists(directory):
    os.makedirs(directory)
    for team_id in teams_in_league:
      os.makedirs(os.path.join(directory, str(team_id)))
  
def populate_historic_data(teams_in_league):
  """Populate historic data files. If it exists overwrite with fetched data."""
  for gw in range(1, CURRENT_GW + 1):
    for team_id in teams_in_league:
      url = f"{BASE_URL}/entry/{team_id}/event/{gw}"
      filename = os.path.join(f"{LEAGUE_ID}_data", str(team_id), f"gw_{gw}_complete.json")
      fetch_and_save_json(url, filename)

def main():
  """Main function to fetch all endpoints"""
  print(f"Starting FPL Draft data fetch for League ID: {LEAGUE_ID}\n")
  
  successful = 0
  failed = 0
  
  for endpoint in endpoints:
    if fetch_and_save_json(endpoint["url"], endpoint["filename"]):
      successful += 1
    else:
      failed += 1
    print()
  
  print(f"Complete! {successful} successful, {failed} failed")

  global CURRENT_GW
  CURRENT_GW = get_current_gw()

  print(f"\nCurrent Gameweek: {CURRENT_GW}\n")

  # Fetch global data up to the current GW
  get_global_data()

  # Fetch league teams
  teams_in_league = get_league_teams(LEAGUE_ID)

  # Create league filestructure
  create_league_filestructure(LEAGUE_ID, teams_in_league)

  # Get all GW data for the league
  populate_historic_data(teams_in_league)


if __name__ == "__main__":
  main()

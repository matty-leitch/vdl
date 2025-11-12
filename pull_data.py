import requests
import json
import os
import argparse

BASE_URL = "https://draft.premierleague.com/api"

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
  
def get_global_data(current_gw):
  """Fetch global data up to the current GW"""
  if not os.path.exists("global"):
    os.makedirs("global")

  for gw in range(1, current_gw + 1):
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
    with open(f'{league_id}_data/league-{league_id}-details.json', 'r') as f:
      details = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")

  teams = {team['entry_id']: team for team in details['league_entries']}
  return teams.keys()
  
def create_league_filestructure(league_id, teams_in_league):
  """Create directory structure for league data if it doesn't exist"""
  directory = f"{league_id}_data"
  for team_id in teams_in_league:
    os.makedirs(os.path.join(directory, str(team_id)))
  
def populate_historic_data(league_id, teams_in_league, current_gw):
  """Populate historic data files. If it exists overwrite with fetched data."""
  for gw in range(1, current_gw + 1):
    for team_id in teams_in_league:
      url = f"{BASE_URL}/entry/{team_id}/event/{gw}"
      filename = os.path.join(f"{league_id}_data", str(team_id), f"gw_{gw}_complete.json")
      fetch_and_save_json(url, filename)

def get_endpoints(league_id):
  """Return a list of endpoints to fetch"""
  # Base URL
  BASE_URL = "https://draft.premierleague.com/api"

  # Define endpoints and their corresponding filenames
  endpoints = [
    {
      "url": f"{BASE_URL}/bootstrap-static",
      "filename": "bootstrap-static.json"
    },
    {
      "url": f"{BASE_URL}/league/{league_id}/details",
      "filename": f"{league_id}_data/league-{league_id}-details.json"
    },
    {
      "url": f"{BASE_URL}/league/{league_id}/element-status",
      "filename": f"{league_id}_data/league-{league_id}-element-status.json"
    },
    {
      "url": f"{BASE_URL}/game",
      "filename": "game.json"
    },
    {
      "url": f"{BASE_URL}/draft/league/{league_id}/transactions",
      "filename": f"{league_id}_data/league-{league_id}-transactions.json"
    },
    {
      "url": f"{BASE_URL}/draft/league/{league_id}/trades",
      "filename": f"{league_id}_data/league-{league_id}-trades.json"
    }
  ]

  return endpoints

def check_valid_league(league_id):
    """Check if the provided league ID is valid by attempting to fetch its details"""
    url = f"https://draft.premierleague.com/api/league/{league_id}/details"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad status codes
        data = response.json()
        return 'league' in data
    except (requests.exceptions.RequestException, ValueError):
        return False

def main():
  """Main function to fetch all endpoints"""
  parser = argparse.ArgumentParser(description='Pull FPL Draft data')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  successful = 0
  failed = 0
  
  args = parser.parse_args()
  
  if check_valid_league(args.league_id) == False:
      print(f"✗ Error: League ID {args.league_id} is not valid.")
      exit(1)
  
  if not os.path.exists(f"{args.league_id}_data"):
    os.makedirs(f"{args.league_id}_data")

  for endpoint in get_endpoints(args.league_id):
    if fetch_and_save_json(endpoint["url"], endpoint["filename"]):
      successful += 1
    else:
      failed += 1
    print()
  
  print(f"Complete! {successful} successful, {failed} failed")

  current_gw = get_current_gw()

  print(f"\nCurrent Gameweek: {current_gw}\n")

  # Fetch global data up to the current GW
  get_global_data(current_gw)

  # Fetch league teams
  teams_in_league = get_league_teams(args.league_id)

  # Create league filestructure
  create_league_filestructure(args.league_id, teams_in_league)

  # Get all GW data for the league
  populate_historic_data(args.league_id, teams_in_league, current_gw)


if __name__ == "__main__":
  main()

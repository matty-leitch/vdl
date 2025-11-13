import json
import argparse
from pull_data import get_current_gw

def calculate_gw_stats(league_id, team_id, gw, league_details, bootstrap_players, gw_data_cache):
  """
  Creates a modified json for the specific team and gameweek.
  Points breakdown and bonus status included.
  """
  try:
    with open(f'{league_id}_data/{team_id}/gw_{gw}_complete.json', 'r') as f:
      team_data = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    return None

  # Get the previous gameweek data for total points calculation
  if gw > 1:
    with open(f'{league_id}_data/{team_id}/gw_{gw - 1}_adjusted.json', 'r') as f:
      prev_gw_data = json.load(f)
    prev_total_points = prev_gw_data['total_points']
    prev_optimal_points = prev_gw_data['total_optimal_points']
    prev_total_player_stats = prev_gw_data['total_player_stats']
  else:
    prev_total_player_stats = {}
    prev_total_points = 0
    prev_optimal_points = 0

  entries_by_id = {entry['entry_id']: entry for entry in league_details['league_entries']}

  # Create a new json structure for the output
  output = {
    'team_id': team_id,
    'team_name': entries_by_id[team_id]['entry_name'],
    'team_captain': f"{entries_by_id[team_id]['player_first_name']} {entries_by_id[team_id]['player_last_name']}",
    'gameweek': gw,
    'team_formation': [0, 0, 0, 0],
    'max_formation': [1, 5, 5, 3],
    'min_formation': [1, 3, 2, 1],
    'week_points': 0,
    'benched_points': 0,
    'optimal_points': 0,
    'league_rank': 0,
    'optimal_league_rank': 0,
    'total_points': prev_total_points,
    'total_optimal_points': prev_optimal_points,
    'player_stats': [],
    'total_player_stats': prev_total_player_stats
  }

  # Calculate the points for each player in the team
  for player in team_data['picks']:
    element_id = player['element']
    
    # Use cached gameweek data
    if str(element_id) in gw_data_cache[gw]['elements']:
      player_points = gw_data_cache[gw]['elements'][str(element_id)]["stats"]["total_points"]
    else:
      player_points = 0

    # Use cached bootstrap data
    player_info = bootstrap_players[element_id]
    player_first_name = player_info['first_name']
    player_second_name = player_info['second_name']
    player['first_name'] = player_first_name
    player['second_name'] = player_second_name
    player['true_position'] = player_info['element_type']
    player['points'] = player_points

    # Update points and benched status
    if player['position'] <= 11:
      output['team_formation'][player['true_position'] - 1] += 1
      player['benched'] = False
      output['week_points'] += player_points
      output['total_points'] += player_points

      # Update total player stats
      if str(element_id) in output['total_player_stats']:
        output['total_player_stats'][str(element_id)]['total_points'] += player_points
      else:
        output['total_player_stats'][str(element_id)] = {
          'first_name': player_first_name,
          'second_name': player_second_name,
          'total_points': player_points,
          'total_benched_points': 0
        }
    else:
      player['benched'] = True
      output['benched_points'] += player_points

      # Update total player stats
      if str(element_id) in output['total_player_stats']:
        output['total_player_stats'][str(element_id)]['total_benched_points'] += player_points
      else:
        output['total_player_stats'][str(element_id)] = {
          'first_name': player_first_name,
          'second_name': player_second_name,
          'total_points': 0,
          'total_benched_points': player_points
        }

    output['player_stats'].append(player)

  output = sort_total_player_stats(output)
  output['optimal_points'] = calculate_optimal_points(output['player_stats'])
  output['total_optimal_points'] += output['optimal_points']

  try:
    with open(f'{league_id}_data/{team_id}/gw_{gw}_adjusted.json', 'w', encoding='utf-8') as f:
      json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved adjusted stats to: {league_id}_data/{team_id}/gw_{gw}_adjusted.json")
  except IOError as e:
    print(f"Error saving adjusted stats: {e}")
    return None
  
def sort_total_player_stats(output):
  """Sort the total player stats by total points descending"""
  sorted_stats = dict(sorted(
    output['total_player_stats'].items(),
    key=lambda item: item[1]['total_points'],
    reverse=True
  ))
  output['total_player_stats'] = sorted_stats
  return output

def get_team_ids(league_id):
  """Fetch the list of team IDs in the league from the league details"""
  try:
    with open(f'{league_id}_data/league-{league_id}-details.json', 'r') as f:
      details = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    return []

  teams = {team['entry_id']: team for team in details['league_entries']}
  return teams.keys()

def get_team_name(league_id, team_id):
  """Fetch the team name for a given team ID in the league from the league details"""
  try:
    with open(f'{league_id}_data/league-{league_id}-details.json', 'r') as f:
      details = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    return None

  teams = {team['entry_id']: team for team in details['league_entries']}

  if team_id not in teams:
    print(f"Team ID {team_id} not found in league {league_id}.")
    exit(1)

  return teams[team_id]['entry_name']

def calculate_optimal_points(player_stats):
  """
  Calculates the optimal points for a team in a given gameweek. That is the
  maximum points they could have achieved with perfect selection. Not straight
  forward due to formation constraints.
  """
  squad = [
    [], # Goalkeepers
    [], # Defenders
    [], # Midfielders
    []  # Forwards
  ]

  for player in player_stats:
    squad[player['true_position'] - 1].append(player)

  # Sort each position by points descending
  for pos in range(4):
    squad[pos].sort(key=lambda x: x['points'], reverse=True)
  optimal_points = 0

  # Legal formations
  formations = [
    [1, 3, 5, 2],
    [1, 3, 4, 3],
    [1, 4, 5, 1],
    [1, 4, 4, 2],
    [1, 4, 3, 3],
    [1, 5, 4, 1],
    [1, 5, 3, 2],
    [1, 5, 2, 3]
  ]

  # Loop over every valid formation and calculate points total
  for formation in formations:
    formation_points = 0
    valid_formation = True

    for pos in range(4):
      formation_points += sum(player['points'] for player in squad[pos][:formation[pos]])

    if valid_formation and formation_points > optimal_points:
      optimal_points = formation_points

  return optimal_points

def get_player_info(player_id):
  """
  Helper function to get full player name
  Input - Player ID
  Output - Player info dictionary
  """
  with open('bootstrap-static.json', 'r') as f:
    bootstrap = json.load(f)
    bootstrap_players = {player['id']: player for player in bootstrap['elements']}

  player_info = bootstrap_players[player_id]
  return player_info

def get_player_name(player_id):
  """
  Helper function to get full player name
  Input - Player ID
  Output - Full player name string
  """
  player_info = get_player_info(player_id)
  full_name = f"{player_info['first_name']} {player_info['second_name']}"
  return full_name

def get_player_stats_gw(player_id, gw):
  """
  Helper function to get player stats for a specific gameweek
  Input - Player ID, Gameweek
  Output - Player stats dictionary for the gameweek
  """
  try:
    with open(f'global/gw_{gw}.json', 'r') as f:
      gw_data = json.load(f)
      if str(player_id) not in gw_data['elements']:
        print(f"Player ID {player_id} not found in gameweek {gw} data.")
        return 0
      player_stats = gw_data['elements'][str(player_id)]
      return player_stats
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    exit(1)

def load_bootstrap_players():
  """Load and cache bootstrap player data"""
  with open('bootstrap-static.json', 'r') as f:
    bootstrap = json.load(f)
    return {player['id']: player for player in bootstrap['elements']}

def load_gw_data_cache(current_gw):
  """Pre-load all gameweek data into memory"""
  gw_data_cache = {}
  for gw in range(1, current_gw + 1):
    try:
      with open(f'global/gw_{gw}.json', 'r') as f:
        gw_data_cache[gw] = json.load(f)
    except FileNotFoundError as e:
      print(f"Error loading gameweek {gw} data: {e}")
      exit(1)
  return gw_data_cache

def load_league_details(league_id):
  """Load league details once"""
  try:
    with open(f'{league_id}_data/league-{league_id}-details.json', 'r') as f:
      return json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    exit(1)

def calculate_league_positions(league_id, team_ids, gw):
  """
  Loop over each team to set league positions for the specified gameweek.
  Must be run after calculate_gw_stats for all teams for the gameweek.
  """
  team_ids_points = {}
  team_ids_optimal_points = {}
  team_data_cache = {}
  
  # Load all team data once
  for team_id in team_ids:
    try:
      with open(f'{league_id}_data/{team_id}/gw_{gw}_adjusted.json', 'r', encoding='utf-8') as f:
        team_data = json.load(f)
        team_data_cache[team_id] = team_data
        team_ids_points[team_id] = team_data['total_points']
        team_ids_optimal_points[team_id] = team_data['total_optimal_points']
    except FileNotFoundError as e:
      print(f"Error: {e}")
      print("Code error.")
      exit(1)

  # Sort teams by points descending to determine ranks
  sorted_teams_by_points = sorted(team_ids_points.items(), key=lambda x: x[1], reverse=True)
  sorted_teams_by_optimal_points = sorted(team_ids_optimal_points.items(), key=lambda x: x[1], reverse=True)

  # Update ranks in memory
  for rank, (team_id, _) in enumerate(sorted_teams_by_points, start=1):
    team_data_cache[team_id]['league_rank'] = rank

  for rank, (team_id, _) in enumerate(sorted_teams_by_optimal_points, start=1):
    team_data_cache[team_id]['optimal_league_rank'] = rank

  # Write all files at once
  for team_id, team_data in team_data_cache.items():
    try:
      with open(f'{league_id}_data/{team_id}/gw_{gw}_adjusted.json', 'w', encoding='utf-8') as f:
        json.dump(team_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
      print(f"Error saving team {team_id} data: {e}")
      exit(1)

def main():
  parser = argparse.ArgumentParser(description='Print FPL Draft team squads')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  
  args = parser.parse_args()

  team_ids = get_team_ids(args.league_id)
  current_gw = get_current_gw()

  # Pre-load all data that will be reused
  print("Loading bootstrap player data...")
  bootstrap_players = load_bootstrap_players()
  
  print("Loading gameweek data...")
  gw_data_cache = load_gw_data_cache(current_gw)
  
  print("Loading league details...")
  league_details = load_league_details(args.league_id)

  print("Processing gameweeks...")
  for gw in range(1, current_gw + 1):
    print(f"Processing GW {gw}...")
    for team_id in team_ids:
      calculate_gw_stats(args.league_id, team_id, gw, league_details, bootstrap_players, gw_data_cache)
    calculate_league_positions(args.league_id, team_ids, gw)

if __name__ == "__main__":
  main()

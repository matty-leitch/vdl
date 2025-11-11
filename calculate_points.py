import json
import os
import argparse
from pull_data import get_current_gw

def calculate_gw_stats(league_id, team_id, gw):
  """
  Creates a modified json for the specific team and gameweek.
  Points breakdown and bonus status included.
  """
  try:
    with open(f'global/gw_{gw}.json', 'r') as f:
      gw_data = json.load(f)
    
    with open(f'{league_id}_data/{team_id}/gw_{gw}_complete.json', 'r') as f:
      team_data = json.load(f)

    with open('bootstrap-static.json', 'r') as f:
      bootstrap = json.load(f)
      bootstrap_players = {player['id']: player for player in bootstrap['elements']}

    with open(f'league-{league_id}-details.json', 'r') as f:
      league_details = json.load(f)
      entries_by_id = {entry['entry_id']: entry for entry in league_details['league_entries']}

  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    return None

  # Create a new json structure for the output
  output = {
    'team_id': team_id,
    'team_name': entries_by_id[team_id]['entry_name'],
    'team_captain': f"{entries_by_id[team_id]['player_first_name']} {entries_by_id[team_id]['player_last_name']}",
    'gameweek': gw,
    'team_formation': [0, 0, 0, 0],
    'max_formation': [1, 5, 5, 3],
    'min_formation': [1, 3, 2, 1],
    'total_points': 0,
    'benched_points': 0,
    'optimal_points': 0,
    'player_stats': []
  }

  # Calculate the points for each player in the team
  for player in team_data['picks']:
    element_id = player['element']
    player_points = gw_data['elements'][str(element_id)]["stats"]["total_points"]

    # Gather player info
    player_info = bootstrap_players[element_id]
    player['first_name'] = player_info['first_name']
    player['second_name'] = player_info['second_name']
    player['true_position'] = player_info['element_type']
    player['points'] = player_points

    # Update points and benched status
    if player['position'] <= 11:
      output['team_formation'][player['true_position'] - 1] += 1
      player['benched'] = False
      output['total_points'] += player_points
    else:
      player['benched'] = True
      output['benched_points'] += player_points

    output['player_stats'].append(player)

  output['optimal_points'] = calculate_optimal_points(output['player_stats'])

  try:
    with open(f'{league_id}_data/{team_id}/gw_{gw}_adjusted.json', 'w', encoding='utf-8') as f:
      json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved adjusted stats to: {league_id}_data/{team_id}/gw_{gw}_adjusted.json")
  except IOError as e:
    print(f"Error saving adjusted stats: {e}")
    return None
  
def get_team_ids(league_id):
  """Fetch the list of team IDs in the league from the league details"""
  try:
    with open(f'league-{league_id}-details.json', 'r') as f:
      details = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    return []

  teams = {team['entry_id']: team for team in details['league_entries']}
  return teams.keys()

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

def main():
  parser = argparse.ArgumentParser(description='Print FPL Draft team squads')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--gw', required=True, help='Current Gameweek')
  
  args = parser.parse_args()

  team_ids = get_team_ids(args.league_id)
  current_gw = get_current_gw()

  if args.gw == 'all':
    for gw in range(1, current_gw + 1):
      for team_id in team_ids:
        calculate_gw_stats(args.league_id, team_id, gw)
  elif (args.gw.isdigit() and (1 <= int(args.gw) <= current_gw)):
    for team_id in team_ids:
      calculate_gw_stats(args.league_id, team_id, args.gw)
  else:
    print("Invalid Gameweek specified. Use 'all' or a number between 1 and ", current_gw)

if __name__ == "__main__":
  main()

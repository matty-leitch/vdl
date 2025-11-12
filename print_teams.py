import json
import argparse
from calculate_points import get_team_ids

def print_team_squads(league_id, team_id, gw):
  """Print each team's squad organized by position"""
  try:
    with open(f'{league_id}_data/{team_id}/gw_{gw}_adjusted.json', 'r', encoding='utf-8') as f:
      team_data = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run calculate_points.py first to fetch the data.")
    return

  print(f"\nTeam: {team_data['team_name']} - Gameweek: {gw}")
  print(f"\tCaptain: {team_data['team_captain']}")
  print("-" * 40)

  positions = {1: "Goalkeepers", 2: "Defenders", 3: "Midfielders", 4: "Forwards", 5: "Bench"}
  squad_by_position = {1: [], 2: [], 3: [], 4: [], 5: []}

  for player in team_data['player_stats']:
    if not player['benched']:
      element_type = player['true_position']
      squad_by_position[element_type].append(player)
    else:
      squad_by_position[5].append(player)  # Benched players

  for pos in range(1, 6):
    print(f"\n{positions[pos]}:")
    for player in squad_by_position[pos]:
      print(
        f" - {player['first_name']} {player['second_name']}\n\t"
        f"Points: {player['points']}"
      )
  
  print("Total Points: ", team_data['total_points'])
  print("Benched Points: ", team_data['benched_points'])
  print("Optimal Points: ", team_data['optimal_points'])

def main():
  parser = argparse.ArgumentParser(description='Print FPL Draft team squads')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--gw', required=True, help='Current Gameweek')

  args = parser.parse_args()

  teams = get_team_ids(args.league_id)

  for team_id in teams:
    print_team_squads(args.league_id, team_id, args.gw)

if __name__ == "__main__":
  main()

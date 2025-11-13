import json
import argparse
from calculate_points import get_team_ids
from pull_data import get_current_gw

def get_league_tables(league_id, teams, gw, optimal=False):
  """
  Print each team's squad organized by position
  Specify optimal=True to print the optimal table in addition to the actual played table
  """
  table = {}
  optimal_table = {}
  for team in teams:
    try:
      with open(f'{league_id}_data/{team}/gw_{gw}_adjusted.json', 'r', encoding='utf-8') as f:
        team_data = json.load(f)
    except FileNotFoundError as e:
      print(f"Error: {e}")
      print("Please run calculate_points.py first to fetch the data.")
      return
    
    table[team_data['team_name']] = team_data['total_points']
    optimal_table[team_data['team_name']] = team_data['total_optimal_points']

  return table, optimal_table

def print_tables(league_id, teams, gw, optimal=False):
  table, optimal_table = get_league_tables(league_id, teams, gw, optimal)
  if optimal:
    print(f"=== Gameweek {gw} Optimal Table ===")
    for team_name, points in sorted(optimal_table.items(), key=lambda x: x[1], reverse=True):
      print(f"{team_name}: {points} points")
  else:
    print(f"=== Gameweek {gw} Table ===")
    for team_name, points in sorted(table.items(), key=lambda x: x[1], reverse=True):
      print(f"{team_name}: {points} points")

def main():
  parser = argparse.ArgumentParser(description='Print FPL Draft team squads')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--gw', required=False, help='Gameweek to get table for')
  parser.add_argument('--optimal', action='store_true', help='Include optimal table')

  args = parser.parse_args()

  teams = get_team_ids(args.league_id)
  if not args.gw:
    args.gw = get_current_gw()

  print_tables(args.league_id, teams, args.gw, optimal=args.optimal)

if __name__ == "__main__":
  main()

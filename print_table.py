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
    output = f"**Gameweek {gw} Optimal Table**\n```\n"
    sorted_table = sorted(optimal_table.items(), key=lambda x: x[1], reverse=True)
  else:
    output = f"**Gameweek {gw} Table**\n```\n"
    sorted_table = sorted(table.items(), key=lambda x: x[1], reverse=True)
  
  # Calculate max widths for formatting
  max_name_len = max(len(team_name) for team_name, _ in sorted_table)
  max_points_len = max(len(str(points)) for _, points in sorted_table)
  
  # Add header
  output += f"{'Pos':<4} {'Team':<{max_name_len}} {'Points':>{max_points_len}}\n"
  output += f"{'-'*4} {'-'*max_name_len} {'-'*max_points_len}\n"
  
  # Add each team
  for pos, (team_name, points) in enumerate(sorted_table, 1):
    output += f"{pos:<4} {team_name:<{max_name_len}} {points:>{max_points_len}}\n"
  
  output += "```"
  
  print(output)
  return output

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

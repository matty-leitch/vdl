import json
import argparse
from calculate_points import get_player_stats_gw, get_team_name
from pull_data import get_current_gw

def collect_waiver_data(league_id):
  """
  Collect waiver data and index it by gameweek.
  """
  try:
    with open(f'{league_id}_data/league-{league_id}-transactions.json', 'r') as f:
      full_waiver_data = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    exit(1)

  waiver_summary = {
    'waiver_info': {}
  }
  current_gw = get_current_gw()

  i = 0

  # Could be handled more efficiently. Instead of regenerating all every week
  # we could append new ones and store data like current points more efficiently.
  for waiver in full_waiver_data['transactions']:
    i += 1
    if waiver['result'] == 'a':
      waiver_summary['waiver_info'][i] = {
        'team': get_team_name(league_id, waiver['entry']),
        'team_id': waiver['entry'],
        'kind': waiver['kind'],
        'effective_gw': waiver['event'],
        'player_out': waiver['element_out'],
        'player_in': waiver['element_in'],
        'player_in_points': [],
        'player_out_points': [],
        'player_in_1w_performance': 0,
        'player_out_1w_performance': 0,
        'relative_performance': 0
      }

      for gw in range(1, current_gw + 1):
        player_in_stats_gw = get_player_stats_gw(waiver['element_in'], gw)
        player_out_stats_gw = get_player_stats_gw(waiver['element_out'], gw)

        # Player may not have existed in that GW (e.g., new signings), so handle that case
        player_in_gw_points = player_in_stats_gw['stats']['total_points'] if player_in_stats_gw != 0 else 0
        player_out_gw_points = player_out_stats_gw['stats']['total_points'] if player_out_stats_gw != 0 else 0

        waiver_summary['waiver_info'][i]['player_in_points'].append(player_in_gw_points)
        waiver_summary['waiver_info'][i]['player_out_points'].append(player_out_gw_points)

        if (gw == waiver['event']):
          waiver_summary['waiver_info'][i]['player_in_1w_performance'] = player_in_gw_points
          waiver_summary['waiver_info'][i]['player_out_1w_performance'] = player_out_gw_points
          waiver_summary['waiver_info'][i]['relative_performance'] = player_in_gw_points - player_out_gw_points

  return waiver_summary

def save_waivers_summary(league_id, waivers_summary):
  """
  Save the trades summary to a JSON file.
  """
  try:
    with open(f'{league_id}_data/waiver_tracker.json', 'w', encoding='utf-8') as f:
      json.dump(waivers_summary, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved waiver tracking to: {league_id}_data/waiver_tracker.json")
  except IOError as e:
    print(f"Error saving waiver tracking: {e}")
    exit(1)

def main():
  parser = argparse.ArgumentParser(description='Print FPL Draft team squads')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  # Currently only supports generating for all GWs
  # parser.add_argument('--gw', required=False, help='Gameweek to generate data for, all if not specified')

  args = parser.parse_args()

  waivers_summary = collect_waiver_data(args.league_id)
  save_waivers_summary(args.league_id, waivers_summary)

if __name__ == "__main__":
  main()

import json
import argparse
import sys
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
    sys.exit(1)

  waiver_summary = {
    'waiver_info': {}
  }
  current_gw = get_current_gw()

  # Collect all unique player IDs that we need to fetch
  player_ids = set()
  for waiver in full_waiver_data['transactions']:
    if waiver['result'] == 'a':
      player_ids.add(waiver['element_in'])
      player_ids.add(waiver['element_out'])

  # Pre-fetch all player stats for all gameweeks
  player_stats_cache = {}
  for player_id in player_ids:
    player_stats_cache[player_id] = {}
    for gw in range(1, current_gw + 1):
      stats = get_player_stats_gw(player_id, gw)
      points = stats['stats']['total_points'] if stats != 0 else 0
      player_stats_cache[player_id][gw] = points

  i = 0

  # Process waivers using cached data
  for waiver in full_waiver_data['transactions']:
    i += 1
    if waiver['result'] == 'a':
      player_in_id = waiver['element_in']
      player_out_id = waiver['element_out']
      effective_gw = waiver['event']

      waiver_summary['waiver_info'][i] = {
        'team': get_team_name(league_id, waiver['entry']),
        'team_id': waiver['entry'],
        'kind': waiver['kind'],
        'effective_gw': effective_gw,
        'player_out': player_out_id,
        'player_in': player_in_id,
        'player_in_points': [player_stats_cache[player_in_id][gw] for gw in range(1, current_gw + 1)],
        'player_out_points': [player_stats_cache[player_out_id][gw] for gw in range(1, current_gw + 1)],
        'player_in_1w_performance': player_stats_cache[player_in_id][effective_gw],
        'player_out_1w_performance': player_stats_cache[player_out_id][effective_gw],
        'relative_performance': player_stats_cache[player_in_id][effective_gw] - player_stats_cache[player_out_id][effective_gw]
      }

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
    sys.exit(1)

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

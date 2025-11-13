import json
import argparse
import sys
from calculate_points import get_player_info
from calculate_points import get_team_name
from pull_data import get_current_gw

def collect_trades(league_id, gw):
  """
  Process trade data for the league and summarize trade information
  """
  try:
    with open(f'{league_id}_data/league-{league_id}-trades.json', 'r') as f:
      trades_data = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run pull_data.py first to fetch the data.")
    sys.exit(1)
  
  
  trades_summary = {
    'trade_info': {}
  }

  i = 0
  for trade in trades_data['trades']:
    i += 1
    effective_gw = trade['event']

    if (trade['state'] == 'p') or (trade['state'] == 'a'):
      trades_summary['trade_info'][i] = {
        'team_from': get_team_name(league_id, trade['offered_entry']),
        'team_to': get_team_name(league_id, trade['received_entry']),
        'effective_gw': effective_gw,
        'state': trade['state'],
        'players_offered': {},
        'players_received': {}
      }
    
      for trade_item in trade['tradeitem_set']:
        trades_summary['trade_info'][i]['players_offered'][trade_item['element_out']] = \
          track_trade_performance(trade_item['element_out'], effective_gw, gw)

        trades_summary['trade_info'][i]['players_received'][trade_item['element_in']] = \
          track_trade_performance(trade_item['element_in'], effective_gw, gw)

  return trades_summary


def track_trade_performance(player_id, effective_gw, gw):
  """
  Track the performance of trades made in the league up to the specified gameweek.

  Input:
  - player_id: The ID of the player being tracked.
  - effective_gw: The gameweek when the trade became effective.
  - gw: The current gameweek to track performance up to.
  Output:
  - A dictionary containing the player's name, total points since the trade,
    and a breakdown of points per gameweek.
  """
  player_info = get_player_info(player_id)
  performance = {
    'player_name': f"{player_info['first_name']} {player_info['second_name']}",
    'total_points': 0,
    'gameweeks': {}
  }

  if effective_gw > gw:
    return performance

  # Ideally we loop over once to collect all data but cba adding that now
  for working_gw in range(effective_gw, gw + 1):
    try:
      with open(f'global/gw_{working_gw}.json', 'r') as f:
        gw_data = json.load(f)
    except FileNotFoundError as e:
      print(f"Error: {e}")
      print("Please run pull_data.py first to fetch the data.")
      sys.exit(1)

    gw_data_player = gw_data['elements'][str(player_id)]
    performance['gameweeks'][working_gw] = {
      'points': gw_data_player['stats']['total_points'],
    }
    performance['total_points'] += gw_data_player['stats']['total_points']

  return performance

def save_trades_summary(league_id, trades_summary):
  """
  Save the trades summary to a JSON file.
  """
  try:
    with open(f'{league_id}_data/trade_tracker.json', 'w', encoding='utf-8') as f:
      json.dump(trades_summary, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved trade tracking to: {league_id}_data/trade_tracker.json")
  except IOError as e:
    print(f"Error saving trade tracking: {e}")
    sys.exit(1)

def get_most_recent_trade_id(league_id):
  """
  Get the ID of the most recent trade.
  Returns the highest trade ID as an integer, or None if no trades exist.
  """
  try:
    with open(f'{league_id}_data/trade_tracker.json', 'r') as f:
      trade_data = json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run trade_tracker.py first to generate the trade data.")
    sys.exit(1)
  
  if not trade_data['trade_info']:
    return 0
  
  # Get all trade IDs and return the maximum
  trade_ids = [int(trade_id) for trade_id in trade_data['trade_info'].keys()]
  return max(trade_ids)

def main():
  parser = argparse.ArgumentParser(description='Print FPL Draft team squads')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--gw', required=False, help='Gameweek to get table for')

  args = parser.parse_args()

  if not args.gw:
    args.gw = get_current_gw()
  
  trades_summary = collect_trades(args.league_id, args.gw)
  save_trades_summary(args.league_id, trades_summary)

if __name__ == "__main__":
  main()

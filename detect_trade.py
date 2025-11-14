import json
import argparse
import sys
from io import StringIO

def load_trade_data(league_id):
  """
  Load trade data from JSON file.
  """
  try:
    with open(f'{league_id}_data/trade_tracker.json', 'r') as f:
      return json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run trade_tracker.py first to generate the trade data.")
    sys.exit(1)

def display_trade(trade_id, league_id):
  """
  Display details for a specific trade.
  Returns the output text.
  """
  trade_data = load_trade_data(league_id)
  
  # Check if trade ID exists
  if str(trade_id) not in trade_data['trade_info']:
    error_msg = f"❌ Error: Trade ID {trade_id} not found\n"
    error_msg += f"Available trade IDs: {', '.join(trade_data['trade_info'].keys())}"
    print(error_msg)
    sys.exit(1)
  
  trade = trade_data['trade_info'][str(trade_id)]
  
  output = StringIO()
  
  def write_line(text=""):
    """Helper to write to both console and output"""
    print(text)
    output.write(text + "\n")
  
  # Display trade header
  write_line("@everyone")
  # write_line(f"\n{'='*60}")
  write_line(f"🔔 **TRADE ACCEPTED** 🔔")
  # write_line(f"{'='*60}\n")
  
  # Display effective gameweek
  write_line(f"📅 **Proposed Effective Gameweek:** GW{trade['effective_gw']}\n")
  
  write_line(f"{'─'*60}\n")
  
  # Display team_from's offer
  write_line(f"📤 **{trade['team_from']}** offers:")
  for player_data in trade['players_offered'].values():
    write_line(f"   • {player_data['player_name']}")
  
  write_line()
  
  # Display what they want
  write_line(f"📥 Player(s) wanted from **{trade['team_to']}**:")
  for player_data in trade['players_received'].values():
    write_line(f"   • {player_data['player_name']}")
  
  write_line(f"\n{'='*60}\n")
  
  return output.getvalue()

def main():
  parser = argparse.ArgumentParser(description='Display details for a specific trade')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--trade-id', type=int, required=True, help='Trade ID to display')
  
  args = parser.parse_args()
  
  display_trade(args.trade_id, args.league_id)

if __name__ == "__main__":
  main()

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

def calculate_trade_gains(trade):
  """
  Calculate the point gains for both teams in a trade.
  Returns tuple: (team_from_gain, team_to_gain)
  """
  offered_total = sum(p['total_points'] for p in trade['players_offered'].values())
  received_total = sum(p['total_points'] for p in trade['players_received'].values())
  
  team_from_gain = received_total - offered_total
  team_to_gain = offered_total - received_total
  
  return team_from_gain, team_to_gain

def get_trade_winner(team_from_gain, team_to_gain, team_from, team_to):
  """
  Determine the winner of a trade based on gains.
  Returns the team name of the winner, or None for a tie.
  """
  if team_from_gain > team_to_gain:
    return team_from
  elif team_to_gain > team_from_gain:
    return team_to
  else:
    return None

def get_winner_message(trade, team_from_gain, team_to_gain):
  """
  Get the message describing who is winning the trade (for Discord).
  """
  if team_from_gain > team_to_gain:
    return f"**{trade['team_from']}** is winning the trade by `{team_from_gain}` points"
  elif team_to_gain > team_from_gain:
    return f"**{trade['team_to']}** is winning the trade by `{team_to_gain}` points"
  else:
    return "The trade is tied at `0` points"

def write_full_trade_details(output, trade, team_from_gain, team_to_gain):
  """
  Write full trade details for the attached document.
  """
  winner = get_trade_winner(team_from_gain, team_to_gain, trade['team_from'], trade['team_to'])
  
  team_from_crown = " (👑)" if winner == trade['team_from'] else ""
  team_to_crown = " (👑)" if winner == trade['team_to'] else ""
  
  output.write(f"{trade['team_from']}{team_from_crown} and {trade['team_to']}{team_to_crown} (GW{trade['effective_gw']})\n")
  
  # Team From perspective
  output.write(f"   {trade['team_from']} Sent:\n")
  for player_data in trade['players_offered'].values():
    output.write(f"      {player_data['player_name']} ({player_data['total_points']})\n")
  
  output.write(f"   {trade['team_from']} Received:\n")
  for player_data in trade['players_received'].values():
    output.write(f"      {player_data['player_name']} ({player_data['total_points']})\n")
  
  # Get winner message without backticks for text file
  if team_from_gain > team_to_gain:
    winner_msg = f"{trade['team_from']} is winning the trade by {team_from_gain} points"
  elif team_to_gain > team_from_gain:
    winner_msg = f"{trade['team_to']} is winning the trade by {team_to_gain} points"
  else:
    winner_msg = "The trade is tied at 0 points"
  
  output.write(f"{winner_msg}\n\n")

def write_trade_summary_lines(output, trades_with_gains):
  """
  Write summary lines for trades (used for Discord message).
  """
  for trade, team_from_gain, team_to_gain in trades_with_gains:
    winner = get_trade_winner(team_from_gain, team_to_gain, trade['team_from'], trade['team_to'])
    
    # Summary line
    team_from_str = f"**{trade['team_from']}**"
    team_to_str = f"**{trade['team_to']}**"
    
    if winner == trade['team_from']:
      team_from_str += " (👑)"
    elif winner == trade['team_to']:
      team_to_str += " (👑)"
    
    output.write(f"{team_from_str} and {team_to_str} (GW{trade['effective_gw']})\n")
    output.write(f"{get_winner_message(trade, team_from_gain, team_to_gain)}\n\n")

def generate_trade_summary(league_id, gameweek):
  """
  Generate trade summary for a given gameweek.
  Returns tuple: (summary_text, full_report_text)
  """
  trade_data = load_trade_data(league_id)
  
  summary_output = StringIO()
  full_output = StringIO()
  
  def write_line(text=""):
    """Helper to write to both console and summary output"""
    print(text)
    summary_output.write(text + "\n")
  
  # Write header to console/Discord summary
  # write_line(f"\n{'='*60}")
  write_line(f"**TRADE SUMMARY - GAMEWEEK {gameweek}**\n")
  # write_line(f"{'='*60}\n")
  
  # Get trades for this specific gameweek
  gw_trades = [
    trade for trade in trade_data['trade_info'].values()
    if trade['effective_gw'] == gameweek and trade['state'] == 'p'
  ]
  
  if not gw_trades:
    write_line(f"No trades were made in Gameweek {gameweek}\n")
  else:
    write_line(f"📊 **{len(gw_trades)} trade(s) made this gameweek**\n")
  
  # Get all trades up to and including this gameweek with their gains
  all_trades_with_gains = []
  for trade in trade_data['trade_info'].values():
    if trade['effective_gw'] <= gameweek and trade['state'] == 'p':
      team_from_gain, team_to_gain = calculate_trade_gains(trade)
      all_trades_with_gains.append((trade, team_from_gain, team_to_gain))
  
  if all_trades_with_gains:
    # Sort by most impactful (largest margin)
    all_trades_with_gains.sort(key=lambda x: abs(x[1]), reverse=True)
    
    # Determine if we need to truncate for Discord
    show_all = len(all_trades_with_gains) <= 10
    trades_to_show = all_trades_with_gains if show_all else all_trades_with_gains[:10]
    
    write_line(f"♻️ **All Trades** ♻️")
    if not show_all:
      write_line(f"*Showing top 10 most impactful trades (out of {len(all_trades_with_gains)} total)*\n")
    else:
      write_line()
    
    # Write to Discord summary
    write_trade_summary_lines(summary_output, trades_to_show)
    
    # If more than 10 trades, prepend full summary to text file
    if not show_all:
      full_output.write("=" * 60 + "\n")
      full_output.write(f"COMPLETE TRADE SUMMARY - GAMEWEEK {gameweek}\n")
      full_output.write("=" * 60 + "\n\n")
      full_output.write(f"All {len(all_trades_with_gains)} trades:\n\n")
      
      # Write all trades to text file summary section
      for trade, team_from_gain, team_to_gain in all_trades_with_gains:
        winner = get_trade_winner(team_from_gain, team_to_gain, trade['team_from'], trade['team_to'])
        
        team_from_str = trade['team_from']
        team_to_str = trade['team_to']
        
        if winner == trade['team_from']:
          team_from_str += " (👑)"
        elif winner == trade['team_to']:
          team_to_str += " (👑)"
        
        full_output.write(f"{team_from_str} and {team_to_str} (GW{trade['effective_gw']})\n")
        
        # Winner message without backticks or bold
        if team_from_gain > team_to_gain:
          winner_msg = f"{trade['team_from']} is winning the trade by {team_from_gain} points"
        elif team_to_gain > team_from_gain:
          winner_msg = f"{trade['team_to']} is winning the trade by {team_to_gain} points"
        else:
          winner_msg = "The trade is tied at 0 points"
        
        full_output.write(f"{winner_msg}\n\n")
      
      full_output.write("\n" + "=" * 60 + "\n")
      full_output.write("DETAILED TRADE BREAKDOWN\n")
      full_output.write("=" * 60 + "\n\n")
    else:
      # Write normal header for text file
      full_output.write("=" * 60 + "\n")
      full_output.write(f"TRADE SUMMARY - GAMEWEEK {gameweek}\n")
      full_output.write("=" * 60 + "\n\n")
    
    # Write detailed breakdown for all trades
    for trade, team_from_gain, team_to_gain in all_trades_with_gains:
      write_full_trade_details(full_output, trade, team_from_gain, team_to_gain)
  
  write_line("\n📎 *Full trade details attached below*")
  
  return summary_output.getvalue(), full_output.getvalue()

def save_report_to_file(report_text, league_id, gameweek):
  """
  Save full report to a file for Discord upload.
  Returns the filename.
  """
  filename = f"{league_id}_data/trade_summary_gw{gameweek}.txt"
  with open(filename, 'w', encoding='utf-8') as f:
    f.write(report_text)
  return filename

def main():
  parser = argparse.ArgumentParser(description='Generate trade summary for a specific gameweek')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--gw', type=int, required=True, help='Gameweek to generate summary for')
  
  args = parser.parse_args()
  
  summary, full_report = generate_trade_summary(args.league_id, args.gw)
  
  # Save the full report
  filename = save_report_to_file(full_report, args.league_id, args.gw)
  print(f"\nFull report saved to: {filename}")

if __name__ == "__main__":
  main()

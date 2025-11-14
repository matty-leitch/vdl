import json
import argparse
import sys
from io import StringIO
from calculate_points import get_player_name

def load_waiver_data(league_id):
  """
  Load waiver data from JSON file.
  """
  try:
    with open(f'{league_id}_data/waiver_tracker.json', 'r') as f:
      return json.load(f)
  except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please run waiver_tracker.py first to generate the waiver data.")
    sys.exit(1)

def get_recent_scores(points_list, effective_gw, num_weeks=3):
  """
  Get the most recent N weeks of scores for a player after the effective gameweek.
  """
  end_idx = effective_gw + num_weeks
  start_idx = effective_gw
  scores = points_list[start_idx:end_idx]
  return scores

def format_player_with_scores(player_id, points_list, effective_gw):
  """
  Format player name with their recent scores after the effective gameweek.
  """
  player_name = get_player_name(player_id)
  recent_scores = get_recent_scores(points_list, effective_gw)
  scores_str = ','.join(map(str, recent_scores))
  return f"{player_name} ({scores_str})"

def generate_free_agent_summary(league_id, waiver_id):
  """
  Generate free agent summary for a specific waiver_info id.
  Returns tuple: (is_free_agent, summary_text)
  If waiver is not a free agent pickup (kind != 'f'), returns (False, "")
  """
  waiver_data = load_waiver_data(league_id)
  
  # Get the specific waiver by id
  waiver_id_str = str(waiver_id)
  if waiver_id_str not in waiver_data['waiver_info']:
    print(f"Error: Waiver ID {waiver_id} not found")
    return False, ""
  
  waiver = waiver_data['waiver_info'][waiver_id_str]
  
  # Check if it's a free agent pickup
  if waiver['kind'] != 'f':
    return False, ""
  
  summary_output = StringIO()
  
  def write_line(text=""):
    """Helper to write to both console and summary output"""
    print(text)
    summary_output.write(text + "\n")
  
  # Write header
  # write_line(f"\n{'='*60}")
  write_line(f"**FREE AGENT PICKUP - GAMEWEEK {waiver['effective_gw']}**")
  # write_line(f"{'='*60}\n")
  
  write_line(f"🆓 **{waiver['team']}** made a free agent pickup\n")
  
  player_out_formatted = format_player_with_scores(waiver['player_out'], waiver['player_out_points'], waiver['effective_gw'] - 1)
  player_in_formatted = format_player_with_scores(waiver['player_in'], waiver['player_in_points'], waiver['effective_gw'] - 1)
  
  write_line(f"   📤 OUT: {player_out_formatted}")
  write_line(f"   📥 IN:  {player_in_formatted}")
  
  perf_sign = '+' if waiver['relative_performance'] >= 0 else ''
  write_line(f"   `{perf_sign}{waiver['relative_performance']}`\n")
  
  return True, summary_output.getvalue()

def main():
  parser = argparse.ArgumentParser(description='Generate free agent summary for a specific waiver')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--waiver-id', type=int, required=True, help='Waiver info ID to lookup')
  
  args = parser.parse_args()
  
  is_free_agent, summary = generate_free_agent_summary(args.league_id, args.waiver_id)
  
  if not is_free_agent:
    print(f"\nWaiver ID {args.waiver_id} is not a free agent pickup")

if __name__ == "__main__":
  main()

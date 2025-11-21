import json
import argparse
import sys
import random
from io import StringIO
from collections import defaultdict
from calculate_points import get_player_name
from pull_data import get_league_teams

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
  Get the most recent N weeks of scores for a player before the effective gameweek.
  Points list format: [gw1_points, gw2_points, gw3_points, ...]
  Points list is 0-indexed (index 0 = GW1, index 1 = GW2, etc.)
  For a waiver in GW10, shows GW8, GW9, GW10 (indices 7, 8, 9).
  Returns list of points in chronological order (oldest first, most recent last).
  """
  end_idx = effective_gw
  start_idx = max(0, end_idx - num_weeks)
  scores = points_list[start_idx:end_idx]
  return scores

def format_player_with_scores(player_id, points_list, effective_gw):
  """
  Format player name with their recent scores before the effective gameweek.
  For a waiver in GW11, shows scores from GW8, GW9, GW10.
  """
  player_name = get_player_name(player_id)
  recent_scores = get_recent_scores(points_list, effective_gw)
  scores_str = ','.join(map(str, recent_scores))
  return f"{player_name} ({scores_str})"

def get_performance_comment(relative_performance):
  """
  Get a random comment for exceptional transfers (good or bad).
  """
  positive_comments = [
    "Wow.", "Nice.", "Amazing!", "Brilliant!", "Class.", "Elite.", 
    "Genius.", "Masterclass.", "Sensational!", "Outstanding.", "Perfect.",
    "Incredible!", "Superb.", "Stellar!", "Magnificent.", "Exceptional!",
    "Top tier.", "Big brain.", "Chef's kiss.", "Nail it.", "Legend.",
    "Immense.", "Quality.", "Fire.", "Built different.", "That's how it's done."
  ]
  negative_comments = [
    "Shit.", "Do better.", "Really?", "What were you thinking?", "Ouch.", "Yikes.",
    "Awful.", "Terrible.", "Nightmare.", "Disaster.", "Tragic.",
    "Embarrassing.", "Horrendous.", "Shocking.", "Dreadful.", "Abysmal.",
    "Questionable.", "Oof.", "Not it.", "Whoops.", "Rough.",
    "Pain.", "Why?", "Stop.", "Delete club.", "Shambles."
  ]
  
  if relative_performance >= 5:
    return random.choice(positive_comments)
  elif relative_performance <= -5:
    return random.choice(negative_comments)
  else:
    return None

def get_all_time_extremes(waiver_data):
  """
  Get the best and worst transfers of all time.
  Returns (best_waiver, worst_waiver) tuples with full waiver info.
  """
  all_waivers = []
  for waiver_id, waiver in waiver_data['waiver_info'].items():
    if isinstance(waiver['relative_performance'], int):
      all_waivers.append(waiver)
  
  if not all_waivers:
    return None, None
  
  all_waivers.sort(key=lambda x: x['relative_performance'], reverse=True)
  best_ever = all_waivers[0]
  worst_ever = all_waivers[-1]
  
  return best_ever, worst_ever

def generate_waiver_summary(league_id, gameweek):
  """
  Generate a shortened summary suitable for Discord.
  Returns both the summary text and saves full report to file.
  """
  waiver_data = load_waiver_data(league_id)
  prev_gw = gameweek - 1
  
  output = StringIO()
  
  def write_line(text=""):
    output.write(text + "\n")
  
  write_line(f"**WAIVER SUMMARY - GAMEWEEK {gameweek}**\n")
  
  # Get current gameweek transactions count
  current_gw_count = 0
  for waiver_id, waiver in waiver_data['waiver_info'].items():
    if waiver['effective_gw'] == gameweek:
      current_gw_count += 1
  
  if current_gw_count > 0:
    write_line(f"📊 **{current_gw_count} transactions made this gameweek**\n")
  
  # Get all previous week waivers
  all_prev_week_waivers = []
  for waiver_id, waiver in waiver_data['waiver_info'].items():
    if waiver['effective_gw'] == prev_gw:
      all_prev_week_waivers.append({
        'team': waiver['team'],
        'player_in': waiver['player_in'],
        'player_out': waiver['player_out'],
        'player_in_points': waiver['player_in_points'],
        'player_out_points': waiver['player_out_points'],
        'relative_performance': waiver['relative_performance']
      })
  
  if all_prev_week_waivers:
    all_prev_week_waivers.sort(key=lambda x: x['relative_performance'], reverse=True)
    
    write_line(f"🏆 **TOP 3 TRANSFERS (GW{prev_gw})**")
    for i, waiver in enumerate(all_prev_week_waivers[:3], 1):
      player_out_formatted = format_player_with_scores(waiver['player_out'], waiver['player_out_points'], prev_gw)
      player_in_formatted = format_player_with_scores(waiver['player_in'], waiver['player_in_points'], prev_gw)
      comment = get_performance_comment(waiver['relative_performance'])
      comment_str = f" *{comment}*" if comment else ""
      write_line(f"{i}. **{waiver['team']}** ")
      write_line(f"   📤 OUT: {player_out_formatted} ")
      write_line(f"   📥 IN: {player_in_formatted} ")
      write_line(f"   `+{waiver['relative_performance']}` {comment_str}")
    
    write_line(f"\n💩 **BOTTOM 3 TRANSFERS (GW{prev_gw})**")
    for i, waiver in enumerate(all_prev_week_waivers[-3:][::-1], 1):
      player_out_formatted = format_player_with_scores(waiver['player_out'], waiver['player_out_points'], prev_gw)
      player_in_formatted = format_player_with_scores(waiver['player_in'], waiver['player_in_points'], prev_gw)
      perf_sign = '+' if waiver['relative_performance'] >= 0 else ''
      comment = get_performance_comment(waiver['relative_performance'])
      comment_str = f" *{comment}*" if comment else ""
      write_line(f"{i}. **{waiver['team']}** ")
      write_line(f"   📤 OUT: {player_out_formatted} ")
      write_line(f"   📥 IN: {player_in_formatted} ")
      write_line(f"   `{perf_sign}{waiver['relative_performance']}` {comment_str}")
  else:
    write_line(f"No transfers were made in GW{prev_gw}")
  
  # Get all-time best and worst
  best_ever, worst_ever = get_all_time_extremes(waiver_data)
  
  if best_ever and worst_ever:
    write_line(f"\n📈 **BEST TRANSFER EVER**")
    best_player_out = format_player_with_scores(best_ever['player_out'], best_ever['player_out_points'], best_ever['effective_gw'])
    best_player_in = format_player_with_scores(best_ever['player_in'], best_ever['player_in_points'], best_ever['effective_gw'])
    write_line(f"**{best_ever['team']}** (GW{best_ever['effective_gw']})")
    write_line(f"📤 OUT: {best_player_out}")
    write_line(f"📥 IN: {best_player_in}")
    write_line(f"`+{best_ever['relative_performance']}`")
    
    write_line(f"\n📉 **WORST TRANSFER EVER**")
    worst_player_out = format_player_with_scores(worst_ever['player_out'], worst_ever['player_out_points'], worst_ever['effective_gw'])
    worst_player_in = format_player_with_scores(worst_ever['player_in'], worst_ever['player_in_points'], worst_ever['effective_gw'])
    write_line(f"**{worst_ever['team']}** (GW{worst_ever['effective_gw']})")
    write_line(f"📤 OUT: {worst_player_out}")
    write_line(f"📥 IN: {worst_player_in}")
    write_line(f"`{worst_ever['relative_performance']}`")
  
  write_line("\n📎 *Full report attached below*")
  
  return output.getvalue()

def save_report_to_file(report_text, league_id, gameweek):
  """
  Save full report to a file for Discord upload.
  Returns the filename.
  """
  filename = f"{league_id}_data/waiver_report_gw{gameweek}.txt"
  with open(filename, 'w', encoding='utf-8') as f:
    f.write(report_text)
  return filename

def main():
  parser = argparse.ArgumentParser(description='Generate waiver summary for Discord')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--gw', type=int, required=True, help='Gameweek to generate summary for')
  parser.add_argument('--full-report', help='Path to full waiver report text file')
  
  args = parser.parse_args()
  
  # Generate summary
  summary = generate_waiver_summary(args.league_id, args.gw)
  print(summary)
  
  # If full report path is provided, save it to the standard location
  if args.full_report:
    with open(args.full_report, 'r', encoding='utf-8') as f:
      full_report = f.read()
    filename = save_report_to_file(full_report, args.league_id, args.gw)
    print(f"\nFull report saved to: {filename}")

if __name__ == "__main__":
  main()

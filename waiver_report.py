import json
import argparse
import sys
from io import StringIO
from collections import defaultdict
from calculate_points import get_player_name
from pull_data import get_league_teams

def get_team_names(league_id):
  """
  Get list of all teams in the league.
  """
  teams = get_league_teams(league_id)
  team_names = []
  with open(f'{league_id}_data/league-{league_id}-details.json', 'r') as f:
    league_details = json.load(f)
    entries_by_id = {entry['entry_id']: entry for entry in league_details['league_entries']}

  for team_id in teams:
    team_name = entries_by_id[team_id]['entry_name']
    team_names.append(team_name)

  return team_names

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

def get_league_table(league_id, teams, gw):
  """
  Get the league table for a given gameweek.
  Returns a dictionary of team_name: total_points
  """
  table = {}
  for team in teams:
    try:
      with open(f'{league_id}_data/{team}/gw_{gw}_adjusted.json', 'r', encoding='utf-8') as f:
        team_data = json.load(f)
      table[team_data['team_name']] = team_data['total_points']
    except FileNotFoundError:
      # If file doesn't exist, skip this team
      continue
  
  return table

def get_picking_order(league_id, teams, gameweek):
  """
  Determine picking order based on previous gameweek's standings.
  Lower points = higher waiver priority.
  """
  if gameweek <= 1:
    return []
  
  # Get previous gameweek's table
  prev_gw = gameweek - 1
  table = get_league_table(league_id, teams, prev_gw)
  
  if not table:
    return []
  
  # Sort teams by points (ascending - lowest points get first pick)
  sorted_teams = sorted(table.items(), key=lambda x: x[1])
  picking_order = [team_name for team_name, _ in sorted_teams]
  
  return picking_order

def get_waivers_for_gameweek(waiver_data, gameweek):
  """
  Get all waivers for a specific gameweek.
  """
  gw_waivers = defaultdict(list)
  
  for waiver_id, waiver in waiver_data['waiver_info'].items():
    if waiver['effective_gw'] == gameweek:
      team = waiver['team']
      gw_waivers[team].append({
        'id': waiver_id,
        'kind': waiver['kind'],
        'player_in': waiver['player_in'],
        'player_out': waiver['player_out'],
        'relative_performance': waiver['relative_performance']
      })
  
  return gw_waivers

def get_previous_week_waivers(waiver_data, team, gameweek):
  """
  Get waivers for a team from the previous gameweek only.
  """
  prev_gw = gameweek - 1
  team_waivers = []
  
  for waiver_id, waiver in waiver_data['waiver_info'].items():
    if waiver['team'] == team and waiver['effective_gw'] == prev_gw:
      team_waivers.append({
        'id': waiver_id,
        'gameweek': waiver['effective_gw'],
        'kind': waiver['kind'],
        'player_in': waiver['player_in'],
        'player_out': waiver['player_out'],
        'player_in_points': waiver['player_in_points'],
        'player_out_points': waiver['player_out_points'],
        'relative_performance': waiver['relative_performance']
      })
  
  return team_waivers

def get_recent_scores(points_list, effective_gw, num_weeks=3):
  """
  Get the most recent N weeks of scores for a player before the effective gameweek.
  Points list format: [gw1_points, gw2_points, gw3_points, ...]
  Points list is 0-indexed (index 0 = GW1, index 1 = GW2, etc.)
  For a waiver in GW10, shows GW8, GW9, GW10 (indices 7, 8, 9).
  Returns list of points in chronological order (oldest first, most recent last).
  """
  # effective_gw is 1-indexed, but list is 0-indexed
  # For GW10, we want indices 7,8,9 (GW8,9,10)
  end_idx = effective_gw  # For GW10, this is 10
  start_idx = max(0, end_idx - num_weeks)  # For GW10, this is 7
  
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

def format_waiver_kind(kind):
  """
  Format waiver kind for display.
  """
  kind_map = {
    'w': 'Waiver',
    'f': 'Free Agent'
  }
  return kind_map.get(kind, kind)

def generate_waiver_report(league_id, gameweek):
  """
  Generate waiver report for a given gameweek.
  Prints the report and returns it as a string.
  """
  # Create StringIO object to capture output
  output = StringIO()
  
  waiver_data = load_waiver_data(league_id)
  teams = get_league_teams(league_id)
  
  # Get picking order based on previous gameweek's standings
  picking_order = get_picking_order(league_id, teams, gameweek)
  
  gw_waivers = get_waivers_for_gameweek(waiver_data, gameweek)
  
  # Get all teams that exist in the league
  all_teams = get_team_names(league_id)
  
  # Get teams that have been active in last 2 weeks
  recent_teams = set()
  for gw in [gameweek, gameweek - 1]:
    recent_waivers = get_waivers_for_gameweek(waiver_data, gw)
    recent_teams.update(recent_waivers.keys())
  
  # Add teams from picking order if available
  if picking_order:
    recent_teams.update(picking_order)
  
  # Determine teams to report on
  if picking_order:
    teams_to_report = list(reversed(picking_order))
    # Add any teams that made waivers but weren't in picking order
    for team in recent_teams:
      if team not in teams_to_report:
        teams_to_report.append(team)
  else:
    teams_to_report = list(recent_teams) if recent_teams else all_teams
  
  def write_line(text=""):
    """Helper function to write to both stdout and StringIO"""
    print(text)
    output.write(text + "\n")
  
  # write_line(f"\n{'='*60}")
  write_line(f"WAIVER REPORT - GAMEWEEK {gameweek}")
  # write_line(f"{'='*60}\n")
  
  for team in teams_to_report:
    write_line(f"\n{team}")
    write_line("-" * 60)
    
    # Current gameweek waivers
    current_waivers = gw_waivers.get(team, [])
    
    if current_waivers:
      write_line(f"\nGameweek {gameweek} Transactions:")
      for waiver in current_waivers:
        waiver_type = format_waiver_kind(waiver['kind'])
        # For current GW waivers, we need to get the waiver data to access points
        for waiver_id, w_data in waiver_data['waiver_info'].items():
          if (w_data['team'] == team and 
              w_data['effective_gw'] == gameweek and
              w_data['player_in'] == waiver['player_in'] and
              w_data['player_out'] == waiver['player_out']):
            player_out_formatted = format_player_with_scores(w_data['player_out'], w_data['player_out_points'], gameweek)
            player_in_formatted = format_player_with_scores(w_data['player_in'], w_data['player_in_points'], gameweek)
            write_line(f"  [{waiver_type}] OUT: {player_out_formatted} -> IN: {player_in_formatted}")
            break
    else:
      write_line(f"\nNo waivers made in Gameweek {gameweek}")
    
    # All waivers from previous week (sorted best to worst)
    prev_week_waivers = get_previous_week_waivers(waiver_data, team, gameweek)
    
    if prev_week_waivers:
      # Sort by relative performance (best to worst)
      prev_week_waivers.sort(key=lambda x: x['relative_performance'], reverse=True)
      
      write_line(f"\nLast Week's Transactions (GW{gameweek - 1}):")
      for waiver in prev_week_waivers:
        waiver_type = format_waiver_kind(waiver['kind'])
        player_out_name = get_player_name(waiver['player_out'])
        player_in_name = get_player_name(waiver['player_in'])
        perf_sign = '+' if waiver['relative_performance'] >= 0 else ''
        write_line(f"  [{waiver_type}] OUT: {player_out_name} -> IN: {player_in_name}")
        write_line(f"    Performance: {perf_sign}{waiver['relative_performance']}")
    else:
      write_line(f"\nNo waivers made last week")
    
    write_line()
  
  # Report on teams that haven't been active recently
  inactive_teams = set(all_teams) - recent_teams
  if inactive_teams:
    # write_line(f"\n{'='*60}")
    write_line(f"INACTIVE TEAMS (No waivers in last 2 weeks)")
    # write_line(f"{'='*60}\n")
    for team in sorted(inactive_teams):
      write_line(f"  - {team}")
    write_line()
  
  # Top 3 and Bottom 3 transfers from last week across all teams
  all_prev_week_waivers = []
  prev_gw = gameweek - 1
  
  for waiver_id, waiver in waiver_data['waiver_info'].items():
    if waiver['effective_gw'] == prev_gw:
      all_prev_week_waivers.append({
        'team': waiver['team'],
        'kind': waiver['kind'],
        'player_in': waiver['player_in'],
        'player_out': waiver['player_out'],
        'player_in_points': waiver['player_in_points'],
        'player_out_points': waiver['player_out_points'],
        'relative_performance': waiver['relative_performance']
      })
  
  if all_prev_week_waivers:
    # Sort by relative performance
    all_prev_week_waivers.sort(key=lambda x: x['relative_performance'], reverse=True)
    
    # write_line(f"\n{'='*60}")
    write_line(f"TOP 3 TRANSFERS OF THE WEEK (GW{prev_gw})")
    # write_line(f"{'='*60}\n")
    
    for i, waiver in enumerate(all_prev_week_waivers[:3], 1):
      waiver_type = format_waiver_kind(waiver['kind'])
      player_out_formatted = format_player_with_scores(waiver['player_out'], waiver['player_out_points'], prev_gw)
      player_in_formatted = format_player_with_scores(waiver['player_in'], waiver['player_in_points'], prev_gw)
      write_line(f"{i}. {waiver['team']}")
      write_line(f"   [{waiver_type}] OUT: {player_out_formatted} -> IN: {player_in_formatted}")
      write_line(f"   Performance: +{waiver['relative_performance']}\n")
    
    write_line(f"{'='*60}")
    write_line(f"BOTTOM 3 TRANSFERS OF THE WEEK (GW{prev_gw})")
    # write_line(f"{'='*60}\n")
    
    for i, waiver in enumerate(all_prev_week_waivers[-3:][::-1], 1):
      waiver_type = format_waiver_kind(waiver['kind'])
      player_out_formatted = format_player_with_scores(waiver['player_out'], waiver['player_out_points'], prev_gw)
      player_in_formatted = format_player_with_scores(waiver['player_in'], waiver['player_in_points'], prev_gw)
      write_line(f"{i}. {waiver['team']}")
      write_line(f"   [{waiver_type}] OUT: {player_out_formatted} -> IN: {player_in_formatted}")
      perf_sign = '+' if waiver['relative_performance'] >= 0 else ''
      write_line(f"   Performance: {perf_sign}{waiver['relative_performance']}\n")
  
  # write_line(f"{'='*60}\n")
  
  # Return the captured output as a string
  return output.getvalue()

def main():
  parser = argparse.ArgumentParser(description='Generate waiver report for a specific gameweek')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
  parser.add_argument('--gw', type=int, required=True, help='Gameweek to generate report for')
  
  args = parser.parse_args()
  
  generate_waiver_report(args.league_id, args.gw)

if __name__ == "__main__":
  main()

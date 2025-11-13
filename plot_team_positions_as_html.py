#!/usr/bin/env python3
"""
Plot all teams' league position progression across gameweeks.
"""

import json
import plotly.graph_objects as go
from pathlib import Path
import argparse
from calculate_points import get_team_ids


def get_team_data(team_id, league_id, max_gameweek=None):
    """
    Get league position data for a team across gameweeks.
    
    Args:
        team_id: The team ID to get data for
        league_id: The league ID
        max_gameweek: Maximum gameweek to collect (default: auto-detect)
        
    Returns:
        tuple: (gameweeks list, league_ranks list, team_name, team_captain)
               or None if data not found
    """
    # Path to team data
    team_path = Path(f"{league_id}_data/{team_id}")
    
    if not team_path.exists():
        print(f"Warning: Team {team_id} not found in league {league_id}")
        return None
    
    # Collect data from all gameweeks
    gameweeks = []
    league_ranks = []
    team_name = None
    team_captain = None
    
    # Auto-detect max gameweek if not specified
    if max_gameweek is None:
        adjusted_files = sorted(team_path.glob("gw_*_adjusted.json"))
        if adjusted_files:
            max_gameweek = len(adjusted_files)
        else:
            print(f"Warning: No gameweek data found for team {team_id}")
            return None
    
    # Read data from each gameweek
    for gw in range(1, max_gameweek + 1):
        file_path = team_path / f"gw_{gw}_adjusted.json"
        
        if not file_path.exists():
            continue
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                gameweeks.append(gw)
                league_ranks.append(data['league_rank'])
                
                # Get team info from first file
                if team_name is None:
                    team_name = data.get('team_name', f'Team {team_id}')
                    team_captain = data.get('team_captain', 'Unknown')
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Error reading {file_path}: {e}")
            continue
    
    if not gameweeks:
        print(f"Warning: No valid gameweek data found for team {team_id}")
        return None
    
    return gameweeks, league_ranks, team_name, team_captain


def plot_all_teams(league_id, max_gameweek=None):
    """
    Plot league position for all teams in the league across gameweeks.
    
    Args:
        league_id: The league ID
        max_gameweek: Maximum gameweek to plot (default: auto-detect)
    """
    # Get league name from details file
    league_name = f"League {league_id}"  # Default fallback
    details_file = Path(f"{league_id}_data/league-{league_id}-details.json")
    
    if details_file.exists():
        try:
            with open(details_file, 'r') as f:
                details = json.load(f)
                league_name = details.get('league', {}).get('name', league_name)
        except (json.JSONDecodeError, KeyError, IOError):
            pass  # Use default if file can't be read
    
    # Get all team IDs in the league
    team_ids = get_team_ids(league_id)
    
    if not team_ids:
        print(f"Error: No teams found in league {league_id}")
        return
    
    all_gameweeks = set()
    teams_data = []
    max_rank = 0
    
    # Collect data for all teams
    for team_id in team_ids:
        result = get_team_data(team_id, league_id, max_gameweek)
        if result is None:
            continue
        
        gameweeks, league_ranks, team_name, team_captain = result
        teams_data.append({
            'team_id': team_id,
            'gameweeks': gameweeks,
            'league_ranks': league_ranks,
            'team_name': team_name,
            'team_captain': team_captain
        })
        all_gameweeks.update(gameweeks)
        max_rank = max(max_rank, max(league_ranks))
    
    if not teams_data:
        print(f"Error: No valid data found for any team in league {league_id}")
        return
    
    # Create the Plotly figure
    fig = go.Figure()
    
    # Add a trace for each team
    for team in teams_data:
        fig.add_trace(go.Scatter(
            x=team['gameweeks'],
            y=team['league_ranks'],
            mode='lines+markers',
            name=team['team_name'],
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Gameweek: %{x}<br>' +
                         'Position: %{y}<br>' +
                         '<extra></extra>',
            line=dict(width=2),
            marker=dict(size=8)
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'{league_name} - Position Progression',
            font=dict(size=18, family='Arial, sans-serif')
        ),
        xaxis=dict(
            title='Gameweek',
            tickmode='linear',
            tick0=1,
            dtick=1,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='League Position',
            tickmode='linear',
            tick0=1,
            dtick=1,
            gridcolor='lightgray',
            range=[max_rank + 0.5, 0.5],  # Reversed range: higher values at bottom, 1 at top
            autorange=False
        ),
        hovermode='closest',
        template='plotly_white',
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='lightgray',
            borderwidth=1
        ),
        height=600,
        width=1200
    )
    
    # Save as HTML
    output_file = f'{league_id}_data/league_positions_progression.html'
    fig.write_html(output_file)
    print(f"Interactive graph saved to: {output_file}")
    print("Open the file in your browser to view the graph.")


def main():
    parser = argparse.ArgumentParser(
        description='Plot all teams\' league position progression across gameweeks'
    )
    parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
    parser.add_argument('--max-gw', '-m', type=int, help='Maximum gameweek to plot (default: auto-detect)')
    
    args = parser.parse_args()
    
    plot_all_teams(args.league_id, args.max_gw)


if __name__ == '__main__':
    main()

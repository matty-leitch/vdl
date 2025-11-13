#!/usr/bin/env python3
"""
Plot points accrued by players involved in trades after the trade was made.
"""

import json
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import warnings
import unicodedata

# Suppress font-related warnings for unsupported Unicode characters
warnings.filterwarnings('ignore', category=UserWarning, message='.*Glyph.*missing from font.*')


def sanitize_text(text):
    """
    Replace unsupported Unicode characters with readable alternatives.
    
    Converts emojis and special Unicode characters to their descriptive names
    or ASCII equivalents to avoid rendering issues in matplotlib.
    
    Args:
        text: The text to sanitize
        
    Returns:
        str: Sanitized text safe for matplotlib rendering
    """
    result = []
    for char in text:
        # Check if character is likely to be unsupported (non-ASCII, non-Latin)
        if ord(char) > 127:
            try:
                # Get Unicode character name
                char_name = unicodedata.name(char)
                
                # Common emoji/symbol replacements
                emoji_map = {
                    'FIRE': '🔥->fire',
                    'SKULL': '💀->skull',
                    'HUNDRED POINTS': '💯->100',
                    'CROWN': '👑->crown',
                    'TROPHY': '🏆->trophy',
                    'LIGHTNING': '⚡->lightning',
                    'ROCKET': '🚀->rocket',
                    'STAR': '⭐->star',
                    'BOMB': '💣->bomb',
                    'GEM': '💎->gem',
                    'SPARKLES': '✨->sparkles',
                    'COLLISION': '💥->boom',
                    'EYES': '👀->eyes',
                    'CLOWN FACE': '🤡->clown',
                    'PILE OF POO': '💩->poo',
                    'GHOST': '👻->ghost',
                    'ALIEN': '👽->alien',
                    'ROBOT': '🤖->robot',
                    'SMILING FACE WITH SUNGLASSES': '😎->cool',
                    'FACE WITH TEARS OF JOY': '😂->lol',
                    'AUBERGINE': '🍆->eggplant',
                    'PEACH': '🍑->peach',
                }
                
                # Check if it matches a known emoji
                for key, replacement in emoji_map.items():
                    if key in char_name:
                        result.append(replacement.split('->')[-1])
                        break
                else:
                    # For other characters, use abbreviated name
                    # E.g., "RIGHTWARDS ARROW" -> "arrow"
                    simplified = char_name.lower().split()[-1]
                    if len(simplified) <= 10:
                        result.append(simplified)
                    else:
                        # If name is too long, just use a placeholder
                        result.append('?')
            except ValueError:
                # No name available, skip or use placeholder
                result.append('?')
        else:
            result.append(char)
    
    return ''.join(result)


def load_trade_data(league_id):
    """
    Load trade tracker data from the league's trade_tracker.json file.
    
    Args:
        league_id: The league ID
        
    Returns:
        dict: Trade data or None if file not found
    """
    trade_file = Path(f"{league_id}_data/trade_tracker.json")
    
    if not trade_file.exists():
        print(f"Error: {trade_file} not found")
        print("Please run track_trades.py first to generate the trade data.")
        return None
    
    try:
        with open(trade_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {trade_file}: {e}")
        return None


def plot_trade(trade_id, trade_info, league_id):
    """
    Create a plot for a specific trade showing player performance after the trade.
    
    Args:
        trade_id: The trade ID
        trade_info: Dictionary containing trade details
        league_id: The league ID
    """
    team_from = sanitize_text(trade_info['team_from'])
    team_to = sanitize_text(trade_info['team_to'])
    effective_gw = trade_info['effective_gw']
    
    # Create the figure
    _, ax = plt.subplots(figsize=(12, 7))
    
    # Process players offered (from team_from to team_to)
    for player_id, player_data in trade_info['players_offered'].items():
        player_name = sanitize_text(player_data['player_name'])
        gameweeks = sorted([int(gw) for gw in player_data['gameweeks'].keys()])
        points = [player_data['gameweeks'][str(gw)]['points'] for gw in gameweeks]
        
        # Calculate cumulative points
        cumulative_points = []
        total = 0
        for pts in points:
            total += pts
            cumulative_points.append(total)
        
        ax.plot(gameweeks, cumulative_points, 
                marker='o', linewidth=2.5, markersize=8,
                linestyle='-', label=f"{player_name} ({team_from} -> {team_to})")
    
    # Process players received (from team_to to team_from)
    for player_id, player_data in trade_info['players_received'].items():
        player_name = sanitize_text(player_data['player_name'])
        gameweeks = sorted([int(gw) for gw in player_data['gameweeks'].keys()])
        points = [player_data['gameweeks'][str(gw)]['points'] for gw in gameweeks]
        
        # Calculate cumulative points
        cumulative_points = []
        total = 0
        for pts in points:
            total += pts
            cumulative_points.append(total)
        
        ax.plot(gameweeks, cumulative_points, 
                marker='s', linewidth=2.5, markersize=8,
                linestyle='--', label=f"{player_name} ({team_to} -> {team_from})")
    
    # Add vertical line at effective gameweek
    ax.axvline(x=effective_gw, color='red', linestyle='--', linewidth=2, 
               label=f'Trade (GW{effective_gw})', alpha=0.7)
    
    # Customize the plot
    ax.set_xlabel('Gameweek', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cumulative Points Since Trade', fontsize=12, fontweight='bold')
    ax.set_title(f'Trade #{trade_id}: {team_from} <-> {team_to}\n' +
                 f'Points accrued after trade (effective GW{effective_gw})',
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=9, framealpha=0.9)
    
    # Set integer ticks for gameweeks - start from effective_gw
    all_gws = []
    for player_data in list(trade_info['players_offered'].values()) + list(trade_info['players_received'].values()):
        all_gws.extend([int(gw) for gw in player_data['gameweeks'].keys()])
    
    if all_gws:
        max_gw = max(all_gws)
        ax.set_xticks(range(effective_gw, max_gw + 1))
        ax.set_xlim(effective_gw - 0.1, max_gw + 0.5)
    
    # Force y-axis to show only integers
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    plt.tight_layout()
    
    # Save as PNG
    output_file = f'{league_id}_data/trade_{trade_id}_performance.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    plt.close()
    
    return output_file


def plot_all_trades(league_id):
    """
    Create plots for all trades in the league.
    
    Args:
        league_id: The league ID
    """
    trade_data = load_trade_data(league_id)
    
    if trade_data is None:
        return
    
    if 'trade_info' not in trade_data or not trade_data['trade_info']:
        print(f"No trades found in league {league_id}")
        return
    
    print(f"Found {len(trade_data['trade_info'])} trades")
    print("-" * 50)
    
    for trade_id, trade_info in trade_data['trade_info'].items():
        plot_trade(trade_id, trade_info, league_id)
        
        # Print summary
        offered_total = sum(p['total_points'] for p in trade_info['players_offered'].values())
        received_total = sum(p['total_points'] for p in trade_info['players_received'].values())
        
        print(f"\nTrade #{trade_id}: {trade_info['team_from']} <-> {trade_info['team_to']}")
        print(f"  Effective GW: {trade_info['effective_gw']}")
        print(f"  {trade_info['team_from']} gave up: {offered_total} pts")
        print(f"  {trade_info['team_from']} received: {received_total} pts")
        print(f"  Net gain for {trade_info['team_from']}: {received_total - offered_total:+d} pts")
    
    print("\n" + "=" * 50)
    print("All graphs saved as PNG files.")


def plot_specific_trade(league_id, trade_id):
    """
    Create a plot for a specific trade.
    
    Args:
        league_id: The league ID
        trade_id: The trade ID to plot
    """
    trade_data = load_trade_data(league_id)
    
    if trade_data is None:
        return
    
    if 'trade_info' not in trade_data:
        print(f"No trades found in league {league_id}")
        return
    
    trade_id_str = str(trade_id)
    if trade_id_str not in trade_data['trade_info']:
        print(f"Trade #{trade_id} not found in league {league_id}")
        print(f"Available trades: {', '.join(trade_data['trade_info'].keys())}")
        return
    
    trade_info = trade_data['trade_info'][trade_id_str]
    plot_trade(trade_id_str, trade_info, league_id)
    
    # Print summary
    offered_total = sum(p['total_points'] for p in trade_info['players_offered'].values())
    received_total = sum(p['total_points'] for p in trade_info['players_received'].values())
    
    print(f"\nTrade #{trade_id}: {trade_info['team_from']} <-> {trade_info['team_to']}")
    print(f"  Effective GW: {trade_info['effective_gw']}")
    print(f"  {trade_info['team_from']} gave up: {offered_total} pts")
    print(f"  {trade_info['team_from']} received: {received_total} pts")
    print(f"  Net gain for {trade_info['team_from']}: {received_total - offered_total:+d} pts")


def main():
    parser = argparse.ArgumentParser(
        description='Plot player performance after trades are made'
    )
    parser.add_argument('--league-id', required=True, help='FPL Draft league ID')
    parser.add_argument('--trade-id', type=int, help='Specific trade ID to plot (default: plot all trades)')
    
    args = parser.parse_args()
    
    if args.trade_id:
        plot_specific_trade(args.league_id, args.trade_id)
    else:
        plot_all_trades(args.league_id)


if __name__ == '__main__':
    main()

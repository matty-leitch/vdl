#!/usr/bin/env python3
"""
Discord Webhook Message Sender

Sends a message to Discord channel via webhook.
"""

import argparse
import requests
import os
import sys
import json

from pull_data import get_current_gw, get_league_teams
from discord_webhook import send_discord_webhook
from print_table import print_tables
from track_trades import get_most_recent_trade_id
from waiver_report import generate_waiver_report
from waiver_summary import generate_waiver_summary, save_report_to_file
from trade_summary import generate_trade_summary, save_report_to_file as save_trade_report
from detect_trade import display_trade

def send_updates(league_id, config):
  """
  Send league updates to Discord via configured webhooks.
  
  Args:
    league_id: FPL Draft league ID
    config: Configuration dictionary with webhook URLs
    
  Returns:
    None
  """
  sent_updates = check_sent_updates(league_id, config)
  current_gw = get_current_gw()
  teams = get_league_teams(league_id)
  
  # Each update needs to be treated separately
  if (('table_webhook' in config) and config['table_webhook']):
    # What game weeks to send
    last_element_sent = max(sent_updates['table_webhook']) if sent_updates['table_webhook'] else 0
    gameweeks_to_send = range(last_element_sent + 1, current_gw + 1)
    for gw in gameweeks_to_send:
      table_message = print_tables(league_id, teams, gw, optimal=False)
      if table_message:
        success = send_discord_webhook(config['table_webhook'], table_message)
        if success:
          sent_updates['table_webhook'].append(gw)

  # Update after each notification incase of failure
  update_sent_updates(league_id, sent_updates)

  if (('table_optimal_webhook' in config) and config['table_optimal_webhook']):
    # What game weeks to send
    last_element_sent = max(sent_updates['table_optimal_webhook']) if sent_updates['table_optimal_webhook'] else 0
    gameweeks_to_send = range(last_element_sent + 1, current_gw + 1)
    for gw in gameweeks_to_send:
      table_message = print_tables(league_id, teams, gw, optimal=True)
      if table_message:
        success = send_discord_webhook(config['table_optimal_webhook'], table_message)
        if success:
          sent_updates['table_optimal_webhook'].append(gw)

  # Update after each notification incase of failure
  update_sent_updates(league_id, sent_updates)

  if (('waiver_report_webhook' in config) and config['waiver_report_webhook']):
    # What game weeks to send
    last_element_sent = max(sent_updates['waiver_report_webhook']) if sent_updates['waiver_report_webhook'] else 0
    gameweeks_to_send = range(last_element_sent + 1, current_gw + 1)
    for gw in gameweeks_to_send:
      # Generate full report
      full_report = generate_waiver_report(league_id, gw)
      
      # Save full report to file
      report_file = save_report_to_file(full_report, league_id, gw)
      
      # Generate summary for Discord message
      summary_message = generate_waiver_summary(league_id, gw)
      if summary_message and report_file:
        success = send_discord_webhook(config['waiver_report_webhook'], summary_message, report_file)
        if success:
          sent_updates['waiver_report_webhook'].append(gw)

  # Update after each notification incase of failure
  update_sent_updates(league_id, sent_updates)

  if (('trade_tracker_webhook' in config) and config['trade_tracker_webhook']):
    # What game weeks to send
    last_element_sent = max(sent_updates['trade_tracker_webhook']) if sent_updates['trade_tracker_webhook'] else 0
    gameweeks_to_send = range(last_element_sent + 1, current_gw + 1)
    for gw in gameweeks_to_send:
      # Generate trade summary     
      summary_text, full_report = generate_trade_summary(league_id, gw)
      
      # Save full report to file
      trade_file = save_trade_report(full_report, league_id, gw)
      
      if summary_text and trade_file:
        success = send_discord_webhook(config['trade_tracker_webhook'], summary_text, trade_file)
        if success:
          sent_updates['trade_tracker_webhook'].append(gw)

  # Update after each notification incase of failure
  update_sent_updates(league_id, sent_updates)

  if (('trade_free_agent_alert' in config) and config['trade_free_agent_alert']):
    # What trades to send
    last_element_sent = max(sent_updates['trade_free_agent_alert']) if sent_updates['trade_free_agent_alert'] else 0
    most_recent_trade = get_most_recent_trade_id(league_id)

    for trade in range(last_element_sent + 1, most_recent_trade + 1):
      # Generate trade summary     
      summary_text = display_trade(trade, league_id)
      
      if summary_text:
        success = send_discord_webhook(config['trade_free_agent_alert'], summary_text)
        if success:
          sent_updates['trade_free_agent_alert'].append(trade)

  # Update after each notification incase of failure
  update_sent_updates(league_id, sent_updates)

  if (('waiver_tracker_webhook' in config) and config['waiver_tracker_webhook']):
    # Currently not implemented
    pass

  # Update after each notification incase of failure
  update_sent_updates(league_id, sent_updates)

def check_sent_updates(league_id, config):
  """
  Loads in IDs of updates that have already been processed for a given league and config option.

  Args:
    league_id: FPL Draft league ID
    config: Every key in the config dict corresponds to a different type of update.

  Returns:
    A dictionary mapping config keys to lists of already processed update IDs.
  """
  # Initialize sent updates structure
  sent_updates = {}
  updates_file = f'{league_id}_data/sent_updates.json'
  if os.path.exists(updates_file):
    with open(updates_file, 'r', encoding='utf-8') as f:
      sent_updates = json.load(f)
  else:
    # We've never sent any updates yet. Create structure with empty lists.
    for key in config.keys():
      sent_updates[key] = []

  return sent_updates

def check_config_filled(league_id):
  """
  Check if the configuration for sending updates is filled.
  At least one webhook must be configured.
  """
  config_filled = False
  if os.path.exists(f'{league_id}_data/discord_config.json'):
    with open(f'{league_id}_data/discord_config.json', 'r', encoding='utf-8') as f:
      config = json.load(f)
      config_filled = any(key in config and config[key] for key in [
        'table_webhook',
        'table_optimal_webhook',
        'waiver_report_webhook',
        'trade_tracker_webhook',
        'waiver_tracker_webhook',
        'trade_free_agent_alert'
      ])
  if not config_filled:
    print("Error: Configuration for sending updates is incomplete. At least one webhook must be configured.")
    sys.exit(1)

  return config_filled, config

def update_sent_updates(league_id, sent_updates):
  """
  Save the sent updates to a JSON file.
  """
  try:
    with open(f'{league_id}_data/sent_updates.json', 'w', encoding='utf-8') as f:
      json.dump(sent_updates, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved sent updates to: {league_id}_data/sent_updates.json")
  except IOError as e:
    print(f"Error saving sent updates: {e}")
    sys.exit(1)

def main():
  parser = argparse.ArgumentParser(description='Send league updates to Discord via webhook')
  parser.add_argument('--league-id', required=True, help='FPL Draft league ID')

  args = parser.parse_args()

  config_filled, config = check_config_filled(args.league_id)
  if config_filled:
    send_updates(args.league_id, config)
  else:
    print("No webhooks configured. Exiting.")
    sys.exit(1)

if __name__ == "__main__":
  main()

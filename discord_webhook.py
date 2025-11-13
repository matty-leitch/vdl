#!/usr/bin/env python3
"""
Discord Webhook Message Sender

Sends a message to Discord channel via webhook.
"""

import argparse
import requests
import sys
import json


def send_discord_webhook(webhook_url, content, file_path=None):
  """
  Send a message to Discord via webhook, optionally with file attachment.
  
  Args:
    webhook_url: Discord webhook URL
    content: Message content to send
    file_path: Optional path to file to attach
    
  Returns:
    bool: True if successful, False otherwise
  """
  try:
    if file_path:
      # Send with file attachment
      with open(file_path, 'rb') as f:
        files = {'file': (file_path.split('/')[-1], f)}
        data = {'content': content}
        response = requests.post(
          webhook_url,
          data=data,
          files=files,
          timeout=10
        )
    else:
      # Send text-only message
      payload = {
        "content": content
      }
      headers = {
        "Content-Type": "application/json"
      }
      response = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers=headers,
        timeout=10
      )
    
    if response.status_code in [200, 204]:
      print("✓ Message sent successfully!")
      return True
    else:
      print(f"✗ Failed to send message. Status code: {response.status_code}")
      print(f"Response: {response.text}")
      return False
      
  except requests.exceptions.RequestException as e:
    print(f"✗ Error sending message: {e}")
    return False
  except FileNotFoundError:
    print(f"✗ Error: File not found: {file_path}")
    return False


def main():
  parser = argparse.ArgumentParser(description='Send a message to Discord via webhook')
  parser.add_argument('--webhook', required=True, help='Discord webhook URL')
  parser.add_argument('--content', required=True, help='Message content to send')
  parser.add_argument('--file', required=False, help='Optional file to attach')

  args = parser.parse_args()
  
  # Validate webhook URL
  if not args.webhook.startswith("https://discord.com/api/webhooks/"):
    print("✗ Invalid webhook URL. Must start with 'https://discord.com/api/webhooks/'")
    sys.exit(1)
  
  # Send the message
  success = send_discord_webhook(args.webhook, args.content, args.file)
  sys.exit(0 if success else 1)


if __name__ == "__main__":
  main()

#!/bin/bash

# Check if league-id argument is provided
if [ $# -eq 0 ]; then
    echo "Error: No league-id provided"
    echo "Usage: $0 <league-id>"
    exit 1
fi

LEAGUE_ID=$1

echo "Running fantasy league scripts for league-id: $LEAGUE_ID"
echo "================================================"

echo "1. Pulling data..."
python3 pull_data.py --league-id "$LEAGUE_ID"

echo "2. Calculating points..."
python3 calculate_points.py --league-id "$LEAGUE_ID"

echo "3. Tracking waivers..."
python3 track_waivers.py --league-id "$LEAGUE_ID"

echo "4. Tracking trades..."
python3 track_trades.py --league-id "$LEAGUE_ID"

echo "================================================"
echo "All scripts completed for league-id: $LEAGUE_ID"

#!/bin/bash

# Check if league-id argument is provided
if [ $# -eq 0 ]; then
    echo "Error: No league-id provided"
    echo "Usage: $0 <league-id>"
    exit 1
fi

LEAGUE_ID=$1

if ls ${LEAGUE_ID}_data/*/gw_*_adjusted.json 1> /dev/null 2>&1; then
    echo "Generating positional progression graph for league-id: $LEAGUE_ID"
    python3 plot_team_positions_as_html.py --league-id "$LEAGUE_ID"
    echo "Graph generated successfully."
    start "${LEAGUE_ID}_data/league_positions_progression.html"
else
    echo "Error: Required files  not found under ${LEAGUE_ID}_data/. Please run setup.sh first."
    exit 1
fi

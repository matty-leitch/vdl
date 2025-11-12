#!/bin/bash

# Check if league_id argument is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a league ID"
    echo "Usage: $0 <league_id>"
    exit 1
fi

LEAGUE_ID=$1
API_URL="https://draft.premierleague.com/api/draft/league/${LEAGUE_ID}/transactions"
SAVED_FILE="${LEAGUE_ID}_data/league-${LEAGUE_ID}-transactions.json"
TEMP_FILE="/tmp/transactions_${LEAGUE_ID}_temp.json"

# Check if saved file exists
if [ ! -f "$SAVED_FILE" ]; then
    echo "Warning: Saved file not found at $SAVED_FILE"
    echo "Please run pull_data.py first to initialize data"
    rm -f "$TEMP_FILE"
    exit 1
fi

# Fetch current data from API
echo "Fetching transactions data from API..."
if ! curl -s -o "$TEMP_FILE" "$API_URL"; then
    echo "Error: Failed to fetch data from API"
    exit 1
fi

# Compare the files
echo "Comparing with saved data..."
if ! diff -q "$TEMP_FILE" "$SAVED_FILE" > /dev/null 2>&1; then
    echo "✓ Changes detected in transactions!"
    echo "Invoking update_all_data.sh..."
    rm -f "$TEMP_FILE"
    
    # Check if update script exists
    if [ ! -f "./update_all_data.sh" ]; then
        echo "Error: update_all_data.sh not found in current directory"
        exit 1
    fi
    
    # Make sure update script is executable and run it
    ./update_all_data.sh "$LEAGUE_ID"
else
    echo "✓ No changes detected - data is up to date"
    rm -f "$TEMP_FILE"
fi

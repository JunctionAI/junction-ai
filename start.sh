#!/bin/bash
# Junction AI Enterprise - Start Script

cd ~/junction-ai

# Kill any existing instance
pkill -f telegram_bot.py 2>/dev/null
sleep 1

echo "================================"
echo "   Junction AI Enterprise v2"
echo "================================"
echo ""

# Check .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Create .env with your API keys first."
    exit 1
fi

# Start the bot
echo "Starting Junction AI..."
python3 telegram_bot.py

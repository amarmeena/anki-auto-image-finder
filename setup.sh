#!/bin/bash

set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Copy config_example.json to config.json if not present
if [ ! -f config.json ]; then
  cp config_example.json config.json
  echo "Created config.json from config_example.json."
fi

echo "\nSetup complete!"
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo "To run the script on an APKG or CSV file, use:"
echo "  python anki_auto_image_finder.py <input_file> [--deck-name <name>] [--config config.json]" 
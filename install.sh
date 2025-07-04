#!/bin/sh
# Install dependencies and run The Fox Vampire game

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Starting The Fox Vampire..."
python the_fox_vampire.py

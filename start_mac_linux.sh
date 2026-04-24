#!/bin/bash
echo "Installing dependencies..."
pip install flask flask-cors yt-dlp
echo ""
echo "Starting SaveIt server..."
python3 server.py

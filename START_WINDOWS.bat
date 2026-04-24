@echo off
echo Installing dependencies...
pip install flask flask-cors yt-dlp
echo.
echo Starting SaveIt server...
python server.py
pause

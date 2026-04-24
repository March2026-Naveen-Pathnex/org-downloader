# SaveIt — Video Downloader

Paste any video URL → click Download → file saves to ~/Downloads/SaveIt/

## Quick Start

### Windows
Double-click `START_WINDOWS.bat`
Then open → http://localhost:5000

### Mac / Linux
```bash
chmod +x start_mac_linux.sh
./start_mac_linux.sh
```
Then open → http://localhost:5000

## Manual Setup
```bash
pip install flask flask-cors yt-dlp
python server.py
```

## Supported Sites
YouTube, Instagram (public posts), TikTok, Facebook, Twitter/X,
Vimeo, Reddit, Twitch, and 1000+ more via yt-dlp.

## Downloads Location
Files are saved to: ~/Downloads/SaveIt/
Click "Open Folder" in the app after download completes.

## Notes
- Only download content you own or have permission to download
- Instagram/TikTok: only public posts work
- WhatsApp statuses cannot be downloaded via URL (use the file manager method on Android)

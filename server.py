#!/usr/bin/env python3
"""
Org - Video Downloader Server (Cloud Ready)
"""

import os
import re
import json
import subprocess
import threading
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

DOWNLOAD_DIR = Path("/tmp/downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

progress_store = {}


def check_ytdlp():
    return shutil.which("yt-dlp") is not None


def detect_platform(url):
    patterns = {
        "YouTube":   r"youtube\.com|youtu\.be",
        "Instagram": r"instagram\.com",
        "TikTok":    r"tiktok\.com",
        "Facebook":  r"facebook\.com|fb\.watch",
        "Twitter/X": r"twitter\.com|x\.com",
        "Vimeo":     r"vimeo\.com",
        "Reddit":    r"reddit\.com",
        "Twitch":    r"twitch\.tv",
    }
    for name, pattern in patterns.items():
        if re.search(pattern, url, re.I):
            return name
    return "Video"


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/check")
def api_check():
    return jsonify({"ytdlp": check_ytdlp(), "downloadDir": "Cloud Server"})


@app.route("/api/info", methods=["POST"])
def api_info():
    data = request.json or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    if not check_ytdlp():
        return jsonify({"error": "yt-dlp not installed"}), 500
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr.split("\n")[0] or "Could not fetch video info"}), 400
        info = json.loads(result.stdout)
        return jsonify({
            "title":     info.get("title", "Unknown"),
            "thumbnail": info.get("thumbnail", ""),
            "duration":  info.get("duration_string", ""),
            "uploader":  info.get("uploader", ""),
            "platform":  detect_platform(url),
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Request timed out"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.json or {}
    url   = data.get("url", "").strip()
    fmt   = data.get("format", "bv*+ba/best")
    dl_id = data.get("id", "dl")

    if not url:
        return jsonify({"error": "No URL"}), 400
    if not check_ytdlp():
        return jsonify({"error": "yt-dlp not installed"}), 500

    out_tmpl = str(DOWNLOAD_DIR / f"{dl_id}_%(title).80s.%(ext)s")

    if fmt == "audio_mp3":
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", out_tmpl, "--no-playlist", url]
    else:
        cmd = ["yt-dlp", "-f", fmt, "--merge-output-format", "mp4", "-o", out_tmpl, "--no-playlist", url]

    progress_store[dl_id] = {"status": "starting", "percent": 0, "speed": "", "eta": "", "filename": ""}

    def run_download():
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                line = line.strip()
                m = re.search(r"\[download\]\s+([\d.]+)%.*?at\s+([\d.]+\s*\S+).*?ETA\s+(\S+)", line)
                if m:
                    progress_store[dl_id].update({"status": "downloading", "percent": float(m.group(1)), "speed": m.group(2), "eta": m.group(3)})
                m2 = re.search(r"\[download\] Destination: (.+)", line)
                if m2:
                    progress_store[dl_id]["filename"] = m2.group(1).strip()
                m3 = re.search(r'Merging formats into "(.+)"', line)
                if m3:
                    progress_store[dl_id]["filename"] = m3.group(1).strip()
            proc.wait()
            if proc.returncode == 0:
                progress_store[dl_id]["status"] = "done"
                progress_store[dl_id]["percent"] = 100
            else:
                progress_store[dl_id]["status"] = "error"
                progress_store[dl_id]["error"] = "Download failed"
        except Exception as e:
            progress_store[dl_id]["status"] = "error"
            progress_store[dl_id]["error"] = str(e)

    threading.Thread(target=run_download, daemon=True).start()
    return jsonify({"ok": True, "id": dl_id})


@app.route("/api/progress/<dl_id>")
def api_progress(dl_id):
    return jsonify(progress_store.get(dl_id, {"status": "unknown"}))


@app.route("/api/file/<dl_id>")
def api_file(dl_id):
    files = list(DOWNLOAD_DIR.glob(f"{dl_id}_*"))
    if not files:
        return jsonify({"error": "File not found"}), 404
    filepath = files[0]
    filename = filepath.name.replace(f"{dl_id}_", "")
    ext = filepath.suffix.lower()
    mime = "audio/mpeg" if ext == ".mp3" else "video/mp4"
    def generate():
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                yield chunk
        try: filepath.unlink()
        except: pass
    return Response(stream_with_context(generate()), headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": mime,
        "Content-Length": str(filepath.stat().st_size),
    })


@app.route("/api/open-folder")
def api_open_folder():
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  Org — Video Downloader | Port: {port} | yt-dlp: {check_ytdlp()}\n")
   port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=False)

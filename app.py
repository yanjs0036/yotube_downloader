from flask import Flask, request, send_file
import yt_dlp
from googleapiclient.discovery import build
import os
import shutil

app = Flask(__name__)

API_KEY = "AIzaSyCW0J6xcz3Get8fQzHfeH5MBYNtr4ZBAxE"
COOKIES_SRC = "/var/task/cookies.txt"
COOKIES_PATH = "/tmp/cookies.txt"

def ensure_cookies():
    if os.path.exists(COOKIES_SRC):
        with open(COOKIES_SRC, 'rb') as src, open(COOKIES_PATH, 'wb') as dst:
            shutil.copyfileobj(src, dst)
        print(f"已複製 cookies.txt 到 {COOKIES_PATH}")
        with open(COOKIES_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"完整 Cookies 內容 (長度 {len(content)}):\n{content}")
    else:
        print("警告：原始 cookies.txt 不存在")

def download_audio(url, filename):
    ensure_cookies()
    if not os.path.exists(COOKIES_PATH):
        print(f"錯誤：找不到 {COOKIES_PATH}")
    else:
        print(f"找到 cookies.txt 在 {os.path.abspath(COOKIES_PATH)}")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"/tmp/{filename}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
        "cookiefile": COOKIES_PATH,
        "quiet": False,
        "verbose": True,
        "simulate": False,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    }
    try:
        print(f"開始下載: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"下載完成: /tmp/{filename}.mp3")
        return True
    except Exception as e:
        print(f"下載失敗: {e}")
        return False

@app.route("/")
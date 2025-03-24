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
def home():
    return """
    <form method="POST" action="/download">
        <input type="text" name="url" placeholder="貼上 YouTube 連結">
        <input type="submit" value="下載音訊">
    </form>
    <p><a href="/update-cookies">更新 Cookies（管理員用）</a></p>
    """

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "")
    if not url:
        return "請輸入 YouTube 連結！"

    try:
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            return "連結格式不對，請用 YouTube 完整網址！"
    except IndexError:
        return "無法解析連結，請檢查格式！"

    print(f"解析到 video_id: {video_id}")
    if not check_video(video_id):
        return "影片無效或不存在，請檢查連結！"

    filename = f"audio_{video_id}"
    filepath = f"/tmp/{filename}.mp3"

    if os.path.exists(filepath):
        print(f"檔案已存在: {filepath}")
        return send_file(filepath, as_attachment=True)

    if download_audio(url, filename):
        if os.path.exists(filepath):
            print(f"傳回檔案: {filepath}")
            return send_file(filepath, as_attachment=True)
        return "下載完成但檔案沒找到，請稍後再試！"
    return "下載失敗，請檢查日誌！"

@app.route("/update-cookies", methods=["GET", "POST"])
def update_cookies():
    if request.method == "POST":
        if "cookies" not in request.files:
            return "請上傳 cookies 檔案！"
        cookies_file = request.files["cookies"]
        cookies_file.save(COOKIES_PATH)
        print("Cookies 已更新")
        return "Cookies 更新成功！<a href='/'>回首頁</a>"
    return """
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="cookies" accept=".txt">
        <input type="submit" value="上傳 Cookies">
    </form>
    """

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
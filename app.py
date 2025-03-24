from flask import Flask, request, send_file, jsonify
import yt_dlp
from googleapiclient.discovery import build
import os
import threading

app = Flask(__name__)

# 你的 API Key
API_KEY = "AIzaSyCW0J6xcz3Get8fQzHfeH5MBYNtr4ZBAxE"

# 用 API 檢查影片資訊
def check_video(video_id):
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        return bool(response["items"])
    except Exception as e:
        return False

# 下載音訊的函數
def download_audio(url, filename):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"/tmp/{filename}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
        "quiet": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"下載失敗: {e}")

# 主頁面
@app.route("/")
def home():
    return """
    <form method="POST" action="/download">
        <input type="text" name="url" placeholder="貼上 YouTube 連結">
        <input type="submit" value="下載音訊">
    </form>
    """

# 下載路由
@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    try:
        video_id = url.split("v=")[1].split("&")[0]
    except IndexError:
        return "連結格式錯誤，請用 YouTube 網址！"

    if not check_video(video_id):
        return "影片無效，請檢查連結！"

    filename = f"audio_{video_id}"
    filepath = f"/tmp/{filename}.mp3"

    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)

    thread = threading.Thread(target=download_audio, args=(url, filename))
    thread.start()

    return f"正在下載，請稍後訪問 /result/{filename}"

# 結果路由
@app.route("/result/<filename>")
def result(filename):
    filepath = f"/tmp/{filename}.mp3"
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "還在下載中，請再等幾秒！"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
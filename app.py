from flask import Flask, request, send_file
import yt_dlp
from googleapiclient.discovery import build
import os

app = Flask(__name__)

API_KEY = "AIzaSyCW0J6xcz3Get8fQzHfeH5MBYNtr4ZBAxE"

def check_video(video_id):
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        print(f"API 檢查結果: {response.get('items', [])}")
        return bool(response.get("items", []))
    except Exception as e:
        print(f"API 檢查失敗: {e}")
        return False

def download_audio(url, filename):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"/tmp/{filename}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
        #"cookiefile": "cookies.txt",  # 之後加 cookies 時取消註解
        "quiet": True,
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

    # 直接下載，不用執行緒
    if download_audio(url, filename):
        if os.path.exists(filepath):
            print(f"傳回檔案: {filepath}")
            return send_file(filepath, as_attachment=True)
        return "下載完成但檔案沒找到，請稍後再試！"
    return "下載失敗，請檢查日誌！"

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
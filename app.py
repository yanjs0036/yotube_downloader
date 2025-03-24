from flask import Flask, request, send_file
import yt_dlp
from googleapiclient.discovery import build
import os
import threading

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
        "quiet": True,
    }
    try:
        print(f"開始下載: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"下載完成: /tmp/{filename}.mp3")
    except Exception as e:
        print(f"下載失敗: {e}")

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

    print("啟動下載執行緒")
    thread = threading.Thread(target=download_audio, args=(url, filename))
    thread.start()
    print("執行緒已啟動，等待下載")

    return f"正在下載，請稍後訪問 /result/{filename}"

@app.route("/result/<filename>")
def result(filename):
    filepath = f"/tmp/{filename}.mp3"
    if os.path.exists(filepath):
        print(f"傳回檔案: {filepath}")
        return send_file(filepath, as_attachment=True)
    print(f"檔案還沒準備好: {filepath}")
    return "還在下載中，請再等幾秒！"

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
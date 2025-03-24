from flask import Flask, request, send_file, jsonify
import yt_dlp
from googleapiclient.discovery import build
import os
import json
import time

app = Flask(__name__)

API_KEY = "AIzaSyCW0J6xcz3Get8fQzHfeH5MBYNtr4ZBAxE"

# 內嵌最新 Cookies（請更新這部分）
COOKIES_CONTENT = """# Netscape HTTP Cookie File
# 請用最新 cookies.txt 內容替換這裡，導出方法：Chrome 插件 "Get cookies.txt"
.youtube.com	TRUE	/	TRUE	1776999047	__Secure-3PAPISID	rQTSBL3R3M_p6_rq/AWiGsEWhfXWbw18-e
.youtube.com	TRUE	/	FALSE	1745131023	_gcl_au	1.1.1133234477.1737355023
.youtube.com	TRUE	/	TRUE	1776999047	__Secure-3PSID	g.a000vAg-xdtFBP0iAqdgvq-uJAX4fY7iYk_kz9hsER3S4ah1N9qnNRkUhQCz8d1UMdmkGDwr5wACgYKAdgSARISFQHGX2MiBBAc8ISV60rmd2pbX-YGVRoVAUF8yKqTqzf2_RK3OS0XmHUxCTZ90076
.youtube.com	TRUE	/	FALSE	0	PREF	f4=4000000&tz=UTC&repeat=NONE&volume=32&autoplay=true&hl=en
.youtube.com	TRUE	/	TRUE	1774337625	__Secure-1PSIDTS	sidts-CjEB7pHptbAoRznum_KXbzxRdbRvzlVuFWotS8F9fMyc8_dSSjMNGJIAWdrQndjfU3eoEAA
.youtube.com	TRUE	/	TRUE	1774337625	__Secure-3PSIDTS	sidts-CjEB7pHptbAoRznum_KXbzxRdbRvzlVuFWotS8F9fMyc8_dSSjMNGJIAWdrQndjfU3eoEAA
.youtube.com	TRUE	/	TRUE	1774337959	__Secure-3PSIDCC	AKEyXzXBI4OyrSDlfa6zjOlAzzdCq9b6nyX2E3r4DHNdLFwZXkpSAqSaulean1lPNP_3X1TWtIo
.youtube.com	TRUE	/	TRUE	1758356405	VISITOR_INFO1_LIVE	75I-Vm3QxKw
.youtube.com	TRUE	/	TRUE	1758356405	VISITOR_PRIVACY_METADATA	CgJUVxIEGgAgVQ%3D%3D
.youtube.com	TRUE	/	TRUE	1758344501	__Secure-ROLLOUT_TOKEN	CP6u5Y6T18-6EBCnk5_HkfmKAxi0gp__96GMAw%3D%3D
.youtube.com	TRUE	/	TRUE	1742806204	GPS	1
.youtube.com	TRUE	/	TRUE	1805876405	__Secure-YT_TVFAS	t=482497&s=2
.youtube.com	TRUE	/	TRUE	0	YSC	lNi-_SW1d_U
.youtube.com	TRUE	/	TRUE	1758356405	DEVICE_INFO	ChxOelE0TlRJNE56a3lOREkyTVRFd09ETTNPUT09ELWrhL8GGLWrhL8G
"""

COOKIES_PATH = "/tmp/cookies.txt"
if not os.path.exists(COOKIES_PATH):
    with open(COOKIES_PATH, 'w', encoding='utf-8') as f:
        f.write(COOKIES_CONTENT)
    print(f"已寫入內嵌 Cookies 到 {COOKIES_PATH}")

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
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "cookiefile": COOKIES_PATH,
        "quiet": False,
        "verbose": True,
        "simulate": False,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
        "proxy": "http://167.172.92.132:8080",  # 新代理，剛測試可用的
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

    task_id = f"task_{int(time.time())}"
    with open(f"/tmp/{task_id}.json", "w") as f:
        json.dump({"url": url, "filename": filename, "status": "pending"}, f)
    
    print(f"任務 {task_id} 已排程")
    return jsonify({"message": "下載任務已啟動，請稍後檢查", "task_id": task_id})

@app.route("/check/<task_id>")
def check_task(task_id):
    task_file = f"/tmp/{task_id}.json"
    if os.path.exists(task_file):
        with open(task_file, "r") as f:
            task = json.load(f)
        filepath = f"/tmp/{task['filename']}.mp3"
        if task["status"] == "completed" and os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        return jsonify(task)
    return "任務不存在", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
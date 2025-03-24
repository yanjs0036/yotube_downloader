from flask import Flask, request, send_file
import yt_dlp
from googleapiclient.discovery import build
import os
import threading
import time

app = Flask(__name__)

API_KEY = "AIzaSyCW0J6xcz3Get8fQzHfeH5MBYNtr4ZBAxE"

COOKIES_CONTENT = """# 請更新為最新 cookies.txt
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

def download_audio(url, filename, timeout=8):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"/tmp/{filename}.%(ext)s",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "cookiefile": COOKIES_PATH,
        "quiet": False,
        "verbose": True,
        "proxy": "http://167.172.92.132:8080",
    }
    result = {"success": False}
    def run_download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
    
    thread = threading.Thread(target=run_download)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        print("下載超時")
        return False
    return result["success"]

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

    if download_audio(url, filename, timeout=8):
        if os.path.exists(filepath):
            print(f"傳回檔案: {filepath}")
            return send_file(filepath, as_attachment=True)
        return "下載完成但檔案沒找到，請稍後再試！"
    return "下載失敗，請檢查日誌！"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
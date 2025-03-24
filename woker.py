import os
import json
import yt_dlp

COOKIES_PATH = "/tmp/cookies.txt"

def process_task(task_file):
    with open(task_file, "r") as f:
        task = json.load(f)
    url = task["url"]
    filename = task["filename"]
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"/tmp/{filename}.%(ext)s",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "cookiefile": COOKIES_PATH,
        "quiet": False,
        "verbose": True,
        "proxy": "http://167.172.92.132:8080",  # 同上
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        task["status"] = "completed"
    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
    
    with open(task_file, "w") as f:
        json.dump(task, f)

if __name__ == "__main__":
    for task_file in os.listdir("/tmp"):
        if task_file.startswith("task_") and task_file.endswith(".json"):
            process_task(f"/tmp/{task_file}")
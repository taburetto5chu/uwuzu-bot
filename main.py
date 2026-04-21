import requests
import urllib.parse
import os
import time
import threading
from flask import Flask

app = Flask(__name__)

# 設定
DOMAIN = "uwuzu.ut-gov.f5.si"
TOKEN = os.environ.get("UWUZU_TOKEN")
STATUS_FILE = "/tmp/last_stats.txt"
KIRIBAN_STEP = 1  # テストのため1に設定

def get_server_stats():
    url = f"https://{DOMAIN}/api/serverinfo-api"
    print(f"DEBUG: Fetching stats from {url}...")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        usage = data["server_info"]["usage"]
        stats = {"users": int(usage.get("users", 0)), "posts": int(usage.get("ueuse", 0))}
        print(f"DEBUG: Stats received: {stats}")
        return stats
    except Exception as e:
        print(f"DEBUG: Error fetching stats: {e}")
        return None

def post_message(text):
    encoded_text = urllib.parse.quote(text)
    url = f"https://{DOMAIN}/api/ueuse/create?token={TOKEN}&text={encoded_text}"
    print(f"DEBUG: Posting message to uwuzu...")
    try:
        res = requests.post(url, timeout=15)
        print(f"DEBUG: Post response status: {res.status_code}")
    except Exception as e:
        print(f"DEBUG: Error posting message: {e}")

def bot_worker():
    print("--- Bot Worker Started ---")
    while True:
        print("DEBUG: Loop cycle start.")
        stats = get_server_stats()
        
        if stats and TOKEN:
            current_users = stats["users"]
            current_posts = stats["posts"]
            
            last_users, last_posts = 0, 0
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r") as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        last_users = int(lines[0].strip())
                        last_posts = int(lines[1].strip())
            
            print(f"DEBUG: Comparing - Users: {last_users}->{current_users}, Posts: {last_posts}->{current_posts}")

            if last_users != 0:
                if current_users > last_users:
                    post_message(f"【自動投稿】🔔 いらっしゃい！新しい仲間が増えました！\n現在 {current_users} 人です。")
                if (current_posts // KIRIBAN_STEP) > (last_posts // KIRIBAN_STEP):
                    achieved = (current_posts // KIRIBAN_STEP) * KIRIBAN_STEP
                    post_message(f"【自動投稿】🎉 祝・総投稿数 {achieved} 件突破！！")

            with open(STATUS_FILE, "w") as f:
                f.write(f"{current_users}\n{current_posts}")
        else:
            print("DEBUG: Stats or TOKEN missing. Skipping this cycle.")
        
        print("DEBUG: Check complete. Waiting 5 minutes...")
        time.sleep(300)

@app.route('/')
def hello():
    return "Bot is running with Debug mode!"

threading.Thread(target=bot_worker, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)

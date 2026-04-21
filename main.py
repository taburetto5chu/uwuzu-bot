import requests
import urllib.parse
import os
import time
import threading
from flask import Flask

# --- Renderのスリープ防止用Webサーバー ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

# --- 設定 ---
DOMAIN = "uwuzu.ut-gov.f5.si"
TOKEN = os.environ.get("UWUZU_TOKEN")
STATUS_FILE = "last_stats.txt" 
KIRIBAN_STEP = 100 

def get_server_stats():
    url = f"https://{DOMAIN}/api/serverinfo-api"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        usage = data["server_info"]["usage"]
        return {"users": int(usage.get("users", 0)), "posts": int(usage.get("ueuse", 0))}
    except:
        return None

def post_message(text):
    encoded_text = urllib.parse.quote(text)
    url = f"https://{DOMAIN}/api/ueuse/create?token={TOKEN}&text={encoded_text}"
    try:
        requests.post(url, timeout=10)
    except:
        pass

def bot_loop():
    print("Bot loop started!")
    # 起動時に一度だけ「起きたよ」のログを出す（uwuzuには投稿しない）
    print("First check initiating...")
    
    while True:
        stats = get_server_stats()
        if stats and TOKEN:
            current_users = stats["users"]
            current_posts = stats["posts"]
            
            last_users, last_posts = 0, 0
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r") as f:
                    lines = f.readlines()
                    if len(lines) >= 1: last_users = int(lines[0].strip())
                    if len(lines) >= 2: last_posts = int(lines[1].strip())

            # 初回起動時（ファイルがない時）は保存だけして投稿しない
            if last_users == 0:
                print(f"Initializing status file with {current_users} users and {current_posts} posts.")
            else:
                if current_users > last_users:
                    msg = f"【自動投稿】🔔 いらっしゃい！新しい仲間が増えました！\n現在 5chu uwuzu の住民は {current_users} 人です。楽しんで！"
                    post_message(msg)
                    print(f"Posted: New User ({current_users})")

                if (current_posts // KIRIBAN_STEP) > (last_posts // KIRIBAN_STEP):
                    achieved_kiriban = (current_posts // KIRIBAN_STEP) * KIRIBAN_STEP
                    msg = f"【自動投稿】🎉 祝・総投稿数 {achieved_kiriban} 件突破！！\nみんなたくさん投稿してくれてありがとう！"
                    post_message(msg)
                    print(f"Posted: Kiriban ({achieved_kiriban})")

            with open(STATUS_FILE, "w") as f:
                f.write(f"{current_users}\n{current_posts}")
        
        print(f"Check complete. Waiting 5 minutes...")
        
        # 300秒（5分）を、1秒×300回に分けて待つ（フリーズ防止）
        for _ in range(300):
            time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

import os
import requests
import time
import threading
from flask import Flask

app = Flask(__name__)

# 前回のステータス保存
last_stats = {"users": 0, "posts": 0}
# ボットスレッドの管理
bot_thread = None

@app.route('/')
def home():
    return "uwuzu monitoring bot is active."

@app.before_request
def keep_alive_ping():
    # アクセスがあったらボットの生存確認と起動を行う
    print("DEBUG: Access detected! Ensuring bot worker is alive...")
    check_and_start_worker()

# --- Bot Logic ---
UWUZU_URL = "https://uwuzu.ut-gov.f5.si"
API_URL = f"{UWUZU_URL}/api/serverinfo-api"
POST_URL = f"{UWUZU_URL}/api/ueuse/create"
TOKEN = os.environ.get("UWUZU_TOKEN")

def post_to_uwuzu(message):
    if not TOKEN:
        print("DEBUG: ERROR - UWUZU_TOKEN is missing!")
        return
    params = {"token": TOKEN, "text": message}
    try:
        res = requests.post(POST_URL, params=params)
        print(f"DEBUG: Post success! Status: {res.status_code}")
    except Exception as e:
        print(f"ERROR: Post failed: {e}")

def monitor_uwuzu():
    global last_stats
    print("\n--- Bot Monitoring Worker Started ---\n")
    while True:
        try:
            print("\n--- DEBUG: Loop Cycle Start ---")
            response = requests.get(API_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                usage = data.get("server_info", {}).get("usage", {})
                current_users = usage.get("users", 0)
                current_posts = usage.get("ueuse", 0)
                
                print(f"DEBUG: Data Received -> Users: {current_users}, Posts: {current_posts}")

                if last_stats["users"] == 0 and last_stats["posts"] == 0:
                    if current_users > 0 or current_posts > 0:
                        last_stats["users"], last_stats["posts"] = current_users, current_posts
                        print(f"DEBUG: Baseline set at: Users {current_users}, Posts {current_posts}")
                else:
                    # 指定されたメッセージに変更
                    if current_users > last_stats["users"]:
                        post_to_uwuzu(f"🔔新たなユーザーが来ました！楽しんで！現在{current_users}名です。")
                    
                    if current_posts > last_stats["posts"]:
                        post_to_uwuzu(f"🎉総投稿数が{current_posts}件を突破！もっと盛り上げよう！")
                    
                    last_stats["users"], last_stats["posts"] = current_users, current_posts
            
            print("DEBUG: Cycle complete. Waiting 5 minutes...")
        except Exception as e:
            print(f"ERROR: Monitor loop error: {e}")
        time.sleep(300)

def check_and_start_worker():
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        print("DEBUG: Bot worker is sleeping. Waking him up now...")
        bot_thread = threading.Thread(target=monitor_uwuzu, daemon=True)
        bot_thread.start()
    else:
        print("DEBUG: Bot worker is already running in background.")

check_and_start_worker()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

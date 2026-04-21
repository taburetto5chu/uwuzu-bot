import os
import requests
import time
import threading
from flask import Flask

# --- Flask Web Server Setup ---
app = Flask(__name__)

# 前回のステータスを保存する変数
last_stats = {"users": 0, "posts": 0}

@app.route('/')
def home():
    return "uwuzu-bot is running! 24/7 Monitoring Mode."

@app.before_request
def keep_alive_ping():
    # アクセスがあるたびにログを出し、ボットが生きていることを誇示する
    print("DEBUG: Access detected! Keeping the bot worker active.")

# --- Bot Logic ---
UWUZU_URL = "https://uwuzu.ut-gov.f5.si"
API_URL = f"{UWUZU_URL}/api/serverinfo-api"
POST_URL = f"{UWUZU_URL}/api/v1/statuses"
# RenderのEnvironmentで設定したTOKENを読み込む
TOKEN = os.environ.get("UWUZU_TOKEN")

def post_to_uwuzu(message):
    if not TOKEN:
        print("ERROR: UWUZU_TOKEN is not set in Environment Variables!")
        return
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"status": message}
    
    try:
        print(f"DEBUG: Attempting to post message: {message}")
        res = requests.post(POST_URL, headers=headers, json=data)
        print(f"DEBUG: Post response status: {res.status_code}")
    except Exception as e:
        print(f"ERROR: Failed to post to uwuzu: {e}")

def monitor_uwuzu():
    global last_stats
    print("\n--- Bot Worker Started ---\n")
    
    while True:
        try:
            print("\n--- DEBUG: Loop Cycle Start ---")
            print(f"DEBUG: Now calling {API_URL}")
            
            response = requests.get(API_URL)
            print(f"DEBUG: Response code = {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                current_users = data.get("users", 0)
                current_posts = data.get("posts", 0)
                
                print(f"DEBUG: Stats successfully parsed: {{'users': {current_users}, 'posts': {current_posts}}}")

                # 初回起動時（last_statsが0の時）は比較せずに現在の値を保存
                if last_stats["users"] == 0 and last_stats["posts"] == 0:
                    last_stats["users"] = current_users
                    last_stats["posts"] = current_posts
                    print(f"DEBUG: Initial stats set. Monitoring from: Users {current_users}, Posts {current_posts}")
                else:
                    # ユーザーが増えた場合
                    if current_users > last_stats["users"]:
                        diff = current_users - last_stats["users"]
                        post_to_uwuzu(f"【自動投稿】🔔 5chu uwuzuに新しい住民が {diff} 人増えました！現在の住民数: {current_users}人")
                    
                    # 投稿数が増えた場合
                    if current_posts > last_stats["posts"]:
                        diff = current_posts - last_stats["posts"]
                        post_to_uwuzu(f"【自動投稿】🎉 投稿数が {current_posts} 件を突破！ (前回のチェックから {diff} 件増えました)")

                    # 状態を更新
                    print(f"DEBUG: Status Update - Users: {last_stats['users']}->{current_users}, Posts: {last_stats['posts']}->{current_posts}")
                    last_stats["users"] = current_users
                    last_stats["posts"] = current_posts
            
            print("DEBUG: Cycle complete. Waiting 5 minutes...")
            
        except Exception as e:
            print(f"ERROR: Something went wrong in monitor loop: {e}")
        
        # 5分待機
        time.sleep(300)

# --- Start Bot in Background Thread ---
bot_thread = threading.Thread(target=monitor_uwuzu, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    # Renderのポート指定に対応
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

import os
import requests
import time
import threading
from flask import Flask

# --- Flask Web Server Setup ---
app = Flask(__name__)

# 前回のステータスを一時保存する変数
last_stats = {"users": 0, "posts": 0}

@app.route('/')
def home():
    return "uwuzu monitoring bot is active."

@app.before_request
def keep_alive_ping():
    # 外部（cron-job.org等）からのアクセス時にログを表示
    print("DEBUG: Access detected! Keeping the bot process alive.")

# --- Bot Logic ---
UWUZU_URL = "https://uwuzu.ut-gov.f5.si"
# APIドキュメントに基づいたエンドポイント
API_URL = f"{UWUZU_URL}/api/serverinfo-api"
POST_URL = f"{UWUZU_URL}/api/ueuse/create"

# RenderのEnvironmentで設定したアクセストークン
TOKEN = os.environ.get("UWUZU_TOKEN")

def post_to_uwuzu(message):
    if not TOKEN:
        print("DEBUG: ERROR - UWUZU_TOKEN is not configured in Environment Variables.")
        return
    
    # APIドキュメントの指定：?token={token}&text={text}
    params = {
        "token": TOKEN,
        "text": message
    }
    
    try:
        print(f"DEBUG: Attempting to post message: {message}")
        # URLパラメータとして送信
        res = requests.post(POST_URL, params=params)
        print(f"DEBUG: Post response status: {res.status_code}")
    except Exception as e:
        print(f"ERROR: Failed to post to uwuzu: {e}")

def monitor_uwuzu():
    global last_stats
    print("\n--- Bot Monitoring Worker Started ---\n")
    
    while True:
        try:
            print("\n--- DEBUG: Loop Cycle Start ---")
            response = requests.get(API_URL)
            
            if response.status_code == 200:
                data = response.json()
                
                # APIドキュメントの階層構造 [server_info][usage] から取得
                try:
                    usage = data.get("server_info", {}).get("usage", {})
                    current_users = usage.get("users", 0)
                    current_posts = usage.get("ueuse", 0)
                except AttributeError:
                    print("DEBUG: API returned data, but structure was unexpected.")
                    current_users, current_posts = 0, 0
                
                print(f"DEBUG: Data Received -> Users: {current_users}, Posts: {current_posts}")

                # 初回起動、またはリセット後の基準値セット
                if last_stats["users"] == 0 and last_stats["posts"] == 0:
                    if current_users > 0 or current_posts > 0:
                        last_stats["users"] = current_users
                        last_stats["posts"] = current_posts
                        print(f"DEBUG: Initial monitoring baseline set at: Users {current_users}, Posts {current_posts}")
                else:
                    # ユーザー数増加のチェック
                    if current_users > last_stats["users"]:
                        diff = current_users - last_stats["users"]
                        post_to_uwuzu(f"【自動投稿】🔔 5chu uwuzuに新しい住民が増えました！楽しんで！！現在の住民数: {current_users}人")
                    
                    # 投稿数増加のチェック
                    if current_posts > last_stats["posts"]:
                        diff = current_posts - last_stats["posts"]
                        post_to_uwuzu(f"【自動投稿】🎉 投稿数が {current_posts} 件を突破しました！ どんどん発展してます！！")

                    # 基準値を最新の状態に更新
                    if current_users > 0 or current_posts > 0:
                        last_stats["users"] = current_users
                        last_stats["posts"] = current_posts
            
            print("DEBUG: Cycle complete. Waiting 5 minutes...")
            
        except Exception as e:
            print(f"ERROR: Monitor loop error: {e}")
        
        # 5分間待機
        time.sleep(300)

# バックグラウンドで監視を実行
bot_thread = threading.Thread(target=monitor_uwuzu, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    # Renderのポート制約に対応
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

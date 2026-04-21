import requests
import urllib.parse
import os
import time
import threading
from flask import Flask

app = Flask(__name__)

# --- 設定 ---
DOMAIN = "uwuzu.ut-gov.f5.si"
TOKEN = os.environ.get("UWUZU_TOKEN")
STATUS_FILE = "/tmp/last_stats.txt" # Renderの一時フォルダ
KIRIBAN_STEP = 1  # テストのため1に設定中。1件ごとに反応します

def get_server_stats():
    url = f"https://{DOMAIN}/api/serverinfo-api"
    print(f"DEBUG: Now calling {url}")
    try:
        # タイムアウトを少し長めの20秒に設定
        response = requests.get(url, timeout=20)
        print(f"DEBUG: Response code = {response.status_code}")
        
        # もし200（成功）以外が返ってきたらエラーを表示
        response.raise_for_status()
        
        data = response.json()
        usage = data["server_info"]["usage"]
        stats = {"users": int(usage.get("users", 0)), "posts": int(usage.get("ueuse", 0))}
        print(f"DEBUG: Stats successfully parsed: {stats}")
        return stats
    except Exception as e:
        # ここでエラーの「正体」をログに吐き出します
        print(f"DEBUG: Detailed Error in get_server_stats: {str(e)}")
        return None

def post_message(text):
    if not TOKEN:
        print("DEBUG: ERROR - UWUZU_TOKEN is missing!")
        return

    encoded_text = urllib.parse.quote(text)
    url = f"https://{DOMAIN}/api/ueuse/create?token={TOKEN}&text={encoded_text}"
    print(f"DEBUG: Attempting to post message to uwuzu...")
    try:
        res = requests.post(url, timeout=20)
        print(f"DEBUG: Post response status: {res.status_code}")
        if res.status_code != 200:
            print(f"DEBUG: Post failed. Response: {res.text}")
    except Exception as e:
        print(f"DEBUG: Detailed Error in post_message: {str(e)}")

def bot_worker():
    print("--- Bot Worker Started ---")
    while True:
        print("\n--- DEBUG: Loop Cycle Start ---")
        stats = get_server_stats()
        
        if stats:
            current_users = stats["users"]
            current_posts = stats["posts"]
            
            last_users, last_posts = 0, 0
            # 前回の数値を読み込み
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r") as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        last_users = int(lines[0].strip())
                        last_posts = int(lines[1].strip())
            
            print(f"DEBUG: Status - Users: {last_users}->{current_users}, Posts: {last_posts}->{current_posts}")

            # 前回の数値がある場合のみ、差分をチェック
            if last_users != 0:
                # ユーザーが増えた場合
                if current_users > last_users:
                    post_message(f"【自動投稿】🔔 いらっしゃい！新しい仲間が増えました！\n現在 5chu uwuzu の住民は {current_users} 人です。")
                
                # 投稿が増えた場合（KIRIBAN_STEPごと）
                if (current_posts // KIRIBAN_STEP) > (last_posts // KIRIBAN_STEP):
                    achieved = (current_posts // KIRIBAN_STEP) * KIRIBAN_STEP
                    post_message(f"【自動投稿】🎉 祝・総投稿数 {achieved} 件突破！！\nみんなたくさん投稿してくれてありがとう！")

            # 今回の数値を保存
            with open(STATUS_FILE, "w") as f:
                f.write(f"{current_users}\n{current_posts}")
        else:
            print("DEBUG: Skipping this cycle due to fetch error.")
        
        print("DEBUG: Cycle complete. Waiting 5 minutes...")
        time.sleep(300)

@app.route('/')
def hello():
    return "Bot is running with Advanced Debug mode!"

# ボットを裏側で起動
threading.Thread(target=bot_worker, daemon=True).start()

if __name__ == "__main__":
    # Render環境用
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

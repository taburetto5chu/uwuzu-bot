import requests
import urllib.parse
import os

# --- 設定 ---
DOMAIN = "uwuzu.ut-gov.f5.si"
TOKEN = os.environ.get("UWUZU_TOKEN")
STATUS_FILE = "last_stats.txt" 
KIRIBAN_STEP = 100 # 投稿数は100件ごとに祝う

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
    requests.post(url, timeout=10)

def main():
    stats = get_server_stats()
    if not stats or not TOKEN: return

    current_users = stats["users"]
    current_posts = stats["posts"]
    last_users = 0

    # 記憶ファイルがあれば読み込む
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_users = int(f.read().strip())

    # --- ① 新規ユーザーのお祝い（1人増えるごと） ---
    if current_users > last_users and last_users != 0:
        msg = f"【自動投稿】🔔 いらっしゃい！新しい仲間が増えました！\n現在 5chu uwuzu の住民は {current_users} 人です。楽しんで！"
        post_message(msg)
        print(f"新規ユーザーお祝い: {current_users}人")

    # --- ② 投稿数のお祝い（100件ごと） ---
    if current_posts % KIRIBAN_STEP == 0 and current_posts != 0:
        msg = f"【自動投稿】🎉 祝・総投稿数 {current_posts} 件突破！！\nみんなたくさん投稿してくれてありがとう！"
        post_message(msg)
        print(f"キリ番お祝い: {current_posts}件")

    # 今の人数を保存（次回の比較用）
    with open(STATUS_FILE, "w") as f:
        f.write(str(current_users))

if __name__ == "__main__":
    main()

import requests
import urllib.parse
import os

# --- 設定 ---
DOMAIN = "uwuzu.ut-gov.f5.si"
TOKEN = os.environ.get("UWUZU_TOKEN") # 隠し金庫から読み込む
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
    requests.post(url, timeout=10)

def main():
    stats = get_server_stats()
    if not stats or not TOKEN:
        return

    # 今回はシンプルに「キリ番ジャスト」か判定
    # 本格的な判定はまた後日改良しましょう！
    if stats["posts"] % KIRIBAN_STEP == 0 and stats["posts"] != 0:
        msg = f"🎉祝・総投稿数 {stats['posts']} 件突破！！\nいつも 5chu uwuzu を盛り上げてくれてありがとう！"
        post_message(msg)

if __name__ == "__main__":
    main()

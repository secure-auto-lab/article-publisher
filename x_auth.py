"""X OAuth認証スクリプト - Secure Auto Labアカウント用"""
import tweepy

# nami-auto-postsと同じアプリ（Free Tier登録済み）
CONSUMER_KEY = "Jpojr1HdgwAg2bdaIsGid0vVc"
CONSUMER_SECRET = "nQ3cIRErg67i0xMFHV3EPqTcTebxlrKsU6Az3N0aCpxR8503sQ"

auth = tweepy.OAuth1UserHandler(CONSUMER_KEY, CONSUMER_SECRET, callback="oob")

# 1. 認証URLを取得
url = auth.get_authorization_url()
print("=" * 50)
print("以下のURLをブラウザで開いてください:")
print(url)
print("=" * 50)

# 2. PINコード入力
pin = input("\nPINコードを入力: ").strip()

# 3. Access Token取得
access_token, access_token_secret = auth.get_access_token(pin)

print("\n=== 認証成功 ===")
print(f"X_API_KEY={CONSUMER_KEY}")
print(f"X_API_SECRET={CONSUMER_SECRET}")
print(f"X_ACCESS_TOKEN={access_token}")
print(f"X_ACCESS_TOKEN_SECRET={access_token_secret}")

# 4. テスト投稿
client = tweepy.Client(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=access_token,
    access_token_secret=access_token_secret,
)

try:
    me = client.get_me()
    print(f"\nアカウント: @{me.data.username}")
except Exception as e:
    print(f"\nアカウント確認エラー: {e}")

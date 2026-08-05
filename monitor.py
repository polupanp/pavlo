import os
import requests

API_URL = "https://api.raceid.com/api/v1/web/races/14933/participants-count"
PAGE_URL = "https://raceid.com/en/races/14933/startlist"
STATE_FILE = "last_count.txt"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing Telegram secrets!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Telegram API status: {res.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def get_count():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    
    try:
        res = requests.get(API_URL, headers=headers, timeout=10)
        print(f"API HTTP Status: {res.status_code}")
        print(f"Raw API Response: {res.text}")
        
        if res.status_code == 200:
            data = res.json()
            # Handle key-value integer or dict payload
            if isinstance(data, int):
                return data
            elif isinstance(data, dict):
                return data.get("count", data.get("total", data.get("participantsCount", 0)))
    except Exception as e:
        print(f"API Error: {e}")
        
    return 0

def main():
    current_count = get_count()
    print(f"Live participant count detected: {current_count}")

    last_count = 0
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                last_count = int(content)

    print(f"Previous count baseline: {last_count}")

    if current_count > last_count and last_count > 0:
        diff = current_count - last_count
        msg = f"🏃‍♂️ *New Registration Alert!*\n\n*{diff}* new participant(s) registered on RaceID!\nTotal participants: *{current_count}*\n\n[View Start List]({PAGE_URL})"
        send_telegram(msg)
    elif last_count == 0 and current_count > 0:
        send_telegram(f"✅ *RaceID Monitor Activated!*\n\nInitial baseline set at *{current_count}* participants.\nYou will receive alerts when new runners register.")

    if current_count > 0:
        with open(STATE_FILE, "w") as f:
            f.write(str(current_count))

if __name__ == "__main__":
    main()

import os
import requests
from playwright.sync_api import sync_playwright

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

def fetch_participant_count():
    count = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Open page and wait for JavaScript/React to load content
        page.goto(PAGE_URL, wait_until="networkidle")
        page.wait_for_timeout(4000)  # Wait 4 seconds for table render
        
        # Count rows in standard table tags or participant cards
        rows = page.locator("tr").count()
        if rows > 1:
            # Subtract table header row
            count = rows - 1
        else:
            # Alternative count by searching participant cards or list items
            cards = page.locator("[class*='participant'], [class*='startlist']").count()
            count = cards
            
        browser.close()
    return count

def main():
    current_count = fetch_participant_count()
    print(f"Live participant count detected: {current_count}")

    # Read last saved count
    last_count = 0
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                last_count = int(content)

    print(f"Previous count baseline: {last_count}")

    # Send alerts
    if current_count > last_count and last_count > 0:
        diff = current_count - last_count
        msg = f"🏃‍♂️ *New Registration Alert!*\n\n*{diff}* new participant(s) registered on RaceID!\nTotal participants: *{current_count}*\n\n[View Start List]({PAGE_URL})"
        send_telegram(msg)
    elif last_count == 0:
        send_telegram(f"✅ *RaceID Monitor Activated!*\n\nInitial baseline set at *{current_count}* participants.\nYou will receive alerts when new runners register.")

    # Save state
    with open(STATE_FILE, "w") as f:
        f.write(str(current_count))

if __name__ == "__main__":
    main()

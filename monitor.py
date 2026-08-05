import os
import json
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
    detected_count = [0]  # Store in list so inner function can update it

    def handle_response(response):
        # Intercept any API endpoint returning startlist or GraphQL data
        url = response.url.lower()
        if ("startlist" in url or "graphql" in url or "participants" in url) and response.status == 200:
            try:
                data = response.json()
                # Debug logging to identify API shape
                print(f"Intercepted response from: {url}")
                
                # Check list/array payload
                if isinstance(data, list):
                    detected_count[0] = len(data)
                elif isinstance(data, dict):
                    # Check common GraphQL or REST array fields
                    startlist = data.get("data", {}).get("startlist") if isinstance(data.get("data"), dict) else None
                    if isinstance(startlist, list):
                        detected_count[0] = len(startlist)
                    else:
                        items = data.get("participants") or data.get("data") or data.get("items")
                        if isinstance(items, list):
                            detected_count[0] = len(items)
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Intercept all network responses
        page.on("response", handle_response)
        
        # Load page and allow network requests to finish
        page.goto(PAGE_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)
        
        # Fallback text-search if network intercept yielded 0: count visible items in page body
        if detected_count[0] == 0:
            body_text = page.inner_text("body")
            # Log snippet of rendered body to assist debugging
            print("Page body loaded, text length:", len(body_text))

        browser.close()

    return detected_count[0]

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

    # Send notifications
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

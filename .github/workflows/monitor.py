import os
import re
import requests

# URL of the RaceID start list
URL = "https://raceid.com/en/races/14933/startlist"

# File to store the previously observed participant count
STATE_FILE = "last_count.txt"

# Environment variables for credentials
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=data)

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page, status code: {response.status_code}")
        return

    # Option A: Find total participant count from page text (e.g. "Registered (42)" or counting table rows)
    # Extracting numeric occurrences of participant tags or table rows
    html = response.text
    
    # Simple strategy: Count occurrences of participant elements or match total registered text
    # Adjust regex if targeting specific table row CSS classes
    participant_matches = re.findall(r'class="[^"]*participant-[^"]*"', html)
    
    # Fallback to general table row parsing if custom class isn't present
    if not participant_matches:
        participant_matches = re.findall(r'<tr[^>]*>', html)

    current_count = len(participant_matches)
    print(f"Current count detected: {current_count}")

    # Read previous count
    last_count = 0
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                last_count = int(content)

    # Compare and notify
    if current_count > last_count and last_count > 0:
        new_registrations = current_count - last_count
        msg = f"🏃‍♂️ *New Registration Alert!*\n\n{new_registrations} new participant(s) registered on RaceID!\nTotal participants: *{current_count}*\n\n[View Start List]({URL})"
        send_telegram(msg)
    elif last_count == 0:
        print("Initial run. Saving current count baseline.")

    # Save current count for next run
    with open(STATE_FILE, "w") as f:
        f.write(str(current_count))

if __name__ == "__main__":
    main()

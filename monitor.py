import os
import requests

# RaceID GraphQL API endpoint
GRAPHQL_URL = "https://raceid.com/api/graphql"
PAGE_URL = "https://raceid.com/en/races/14933/startlist"
RACE_ID = 14933
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

def get_participant_count():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }
    
    # GraphQL query to fetch participants count for the race
    query = """
    query GetStartlist($raceId: Int!) {
        startlist(raceId: $raceId) {
            id
        }
    }
    """
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": {"raceId": RACE_ID}},
            headers=headers,
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            participants = data.get("data", {}).get("startlist", [])
            if isinstance(participants, list):
                return len(participants)
    except Exception as e:
        print(f"GraphQL request failed: {e}")
        
    # Fallback to general API endpoint if GraphQL structure varies
    try:
        rest_url = f"https://raceid.com/api/v1/races/{RACE_ID}/startlist"
        res = requests.get(rest_url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                return len(data.get("participants", data.get("data", [])))
    except Exception as e:
        print(f"REST API request failed: {e}")

    return 0

def main():
    current_count = get_participant_count()
    print(f"Live participant count detected: {current_count}")

    # Read last saved count
    last_count = 0
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                last_count = int(content)

    print(f"Previous count baseline: {last_count}")

    # Handle notifications
    if current_count > last_count and last_count > 0:
        diff = current_count - last_count
        msg = f"🏃‍♂️ *New Registration Alert!*\n\n*{diff}* new participant(s) registered on RaceID!\nTotal participants: *{current_count}*\n\n[View Start List]({PAGE_URL})"
        send_telegram(msg)
    elif last_count == 0:
        send_telegram(f"✅ *RaceID Monitor Activated!*\n\nInitial baseline set at *{current_count}* participants.\nYou will receive alerts whenever new runners register.")

    # Save state
    with open(STATE_FILE, "w") as f:
        f.write(str(current_count))

if __name__ == "__main__":
    main()

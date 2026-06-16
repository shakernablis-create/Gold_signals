import requests
import json
import time
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SEEN_FILE = "seen.json"

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

GOLD_CURRENCIES = ["USD", "XAU"]

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen)[-300:], f)

def send_telegram(event):
    title = event.get("title", "")
    country = event.get("country", "")
    actual = event.get("actual", "")
    forecast = event.get("forecast", "")
    previous = event.get("previous", "")
    date = event.get("date", "")

    msg = f"""🔴 *خبر هام يؤثر على الذهب*

📰 {title}
🌍 {country}
📅 {date}

📊 الفعلي: {actual or '—'}
📈 المتوقع: {forecast or '—'}
📉 السابق: {previous or '—'}

⚠️ تأثير عالي (High Impact)"""

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    )

def check_news():
    seen = load_seen()
    try:
        res = requests.get(FF_URL, timeout=15)
        events = res.json()
    except Exception as e:
        print(f"Fetch error: {e}")
        return

    for event in events:
        impact = event.get("impact", "")
        country = event.get("country", "")
        title = event.get("title", "")
        event_id = f"{title}_{event.get('date','')}_{country}"

        if impact != "High":
            continue
        if country not in GOLD_CURRENCIES:
            continue
        if event_id in seen:
            continue

        send_telegram(event)
        seen.add(event_id)

    save_seen(seen)

def main():
    print("Gold Radar started - checking every 60 seconds")
    while True:
        check_news()
        time.sleep(60)

if __name__ == "__main__":
    main()

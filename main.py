import requests
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SEEN_FILE = "seen.json"

FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

GOLD_CURRENCIES = ["USD", "XAU"]
LOCAL_TZ = ZoneInfo("Asia/Hebron")

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen)[-300:], f)

def format_local_time(date_str):
    try:
        dt_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(LOCAL_TZ)
        return dt_local.strftime("%Y-%m-%d %I:%M %p")
    except:
        return date_str

def send_telegram(event):
    title = event.get("title", "")
    country = event.get("country", "")
    actual = event.get("actual", "")
    forecast = event.get("forecast", "")
    previous = event.get("previous", "")
    date_str = event.get("date", "")
    local_time = format_local_time(date_str)

    msg = f"""🔴 *خبر هام يؤثر على الذهب*

📰 {title}
🌍 {country}
🕐 {local_time} (توقيت فلسطين)

📊 الفعلي: {actual or '—'}
📈 المتوقع: {forecast or '—'}
📉 السابق: {previous or '—'}

⚠️ تأثير عالي (High Impact)"""

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    )

def main():
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

if __name__ == "__main__":
    main()

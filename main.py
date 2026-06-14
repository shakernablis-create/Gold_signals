import requests
import feedparser
import json
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")
SEEN_FILE = "seen.json"

FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.marketwatch.com/rss/topstories",
]

GOLD_KEYWORDS = [
    "gold","fed","federal reserve","interest rate","inflation",
    "cpi","nfp","jobs","powell","dollar","treasury","war","crisis",
    "opec","oil","geopolitical","china","tariff"
]

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return json.load(f)
    except:
        return []

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen[-200:], f)

def is_gold_related(title):
    title_lower = title.lower()
    return any(k in title_lower for k in GOLD_KEYWORDS)

def analyze(title):
    prompt = f"""أنت محلل أسواق ذهب. حلل تأثير هذا الخبر على سعر الذهب.
الخبر: "{title}"
أجب بـ JSON فقط:
{{"signal": "احمر" أو "اخضر" أو "اصفر", "direction": "صعود" أو "هبوط" أو "تذبذب", "strength": "قوي" أو "متوسط" أو "ضعيف", "summary": "جملة وحدة بالعربية"}}"""

    res = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    text = res.json()["content"][0]["text"]
    clean = text.replace("```json","").replace("```","").strip()
    return json.loads(clean)

def send_telegram(title, link, data):
    icons = {"احمر":"🔴","اخضر":"🟢","اصفر":"🟡"}
    icon = icons.get(data["signal"], "⚪")
    msg = f"""{icon} *إشارة {data['signal']} — ذهب*

📰 {title}

📊 {data['direction']} — {data['strength']}
💬 {data['summary']}

🔗 [اقرأ الخبر]({link})"""

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
    )

def main():
    seen = load_seen()
    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if title in seen:
                continue
            if not is_gold_related(title):
                continue
            try:
                data = analyze(title)
                send_telegram(title, link, data)
                seen.append(title)
            except Exception as e:
                print(f"Error: {e}")
    save_seen(seen)

if __name__ == "__main__":
    main()

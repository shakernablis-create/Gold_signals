import requests
import feedparser
import json
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
OPENROUTER_KEY = os.environ.get("ANTHROPIC_KEY")
SEEN_FILE = "seen.json"

FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.marketwatch.com/rss/topstories",
    "https://rss.cnn.com/rss/money_news_international.rss",
]

GOLD_KEYWORDS = [
    "gold","fed","federal reserve","interest rate","inflation",
    "cpi","nfp","jobs","powell","dollar","treasury","war","crisis",
    "opec","oil","geopolitical","china","tariff",
    "trump","tariffs","trade","sanctions","iran","ukraine",
    "ceasefire","peace","deal","recession","debt"
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
    return any(k in title.lower() for k in GOLD_KEYWORDS)

def analyze(title):
    prompt = f"""أنت محلل أسواق ذهب. حلل تأثير هذا الخبر على سعر الذهب.
الخبر: "{title}"
أجب بـ JSON فقط بدون أي نص خارجه:
{{"signal": "احمر او اخضر او اصفر", "direction": "صعود او هبوط او تذبذب", "strength": "قوي او متوسط او ضعيف", "summary": "جملة وحدة بالعربية"}}"""

    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = res.json()
    print("RESPONSE:", data)
    text = data["choices"][0]["message"]["content"]
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

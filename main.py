import requests
import time
from datetime import datetime, timedelta, timezone
from threading import Thread
from flask import Flask

# ================= CONFIG =================

API_KEY = "15189eebbbae89f2e26e0e1cbe43cf5c"

BOT_TOKEN = "8341652276:AAF0MM-8PMaEUjcrgRh_nE68riYSj3e-ZaA"
CHAT_ID = "8006964769"

SPORTS = [
    "soccer_poland_ekstraklasa",
    "soccer_czech_republic_1_liga",
    "soccer_brazil_serie_b",
    "soccer_sweden_allsvenskan",
    "soccer_norway_eliteserien",
    "soccer_denmark_superliga",
    "soccer_austria_bundesliga",
    "soccer_switzerland_superleague",
    "soccer_belgium_first_div",
    "soccer_portugal_primeira_liga",
    "soccer_greece_super_league"
]

# Only use bookies that work for you
ALLOWED_BOOKMAKERS = [
    "1xBet",
    "Parimatch",
    "Stake",
    "Melbet",
    "4rabet",
    "1Win"
]

params = {
    "apiKey": API_KEY,
    "regions": "eu",
    "markets": "h2h",
    "oddsFormat": "decimal"
}

# ================= TELEGRAM =================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data)
    except:
        print("Telegram error")

# ================= FLASK (KEEP ALIVE) =================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running ✅"

def keep_alive():
    app.run(host="0.0.0.0", port=10000)

# ================= SCANNER =================

def scanner():
    send_telegram("🚀 Bot started and scanning!")

    while True:
        try:
            all_data = []

            for sport in SPORTS:
                url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
                response = requests.get(url, params=params)

                print(f"Fetching: {sport} | Status: {response.status_code}", flush=True)

                if response.status_code == 200:
                    data = response.json()
                    all_data.extend(data)

            print("\nTOTAL MATCHES SCANNED:", len(all_data), flush=True)

            now = datetime.now(timezone.utc)
            time_limit = now + timedelta(hours=72)

            for match in all_data:
                pin_odds = None

                home = match.get('home_team', 'Unknown')
                away = match.get('away_team', 'Unknown')

                match_time = datetime.fromisoformat(
                    match['commence_time'].replace("Z", "+00:00")
                )

                if match_time > time_limit:
                    continue

                for bookmaker in match.get('bookmakers', []):
                    if bookmaker.get('title') == "Pinnacle":
                        pin_odds = bookmaker['markets'][0]['outcomes']

                if not pin_odds:
                    continue

                total_prob = sum([1/o['price'] for o in pin_odds])

                for i in range(len(pin_odds)):
                    pin_price = pin_odds[i]['price']
                    true_prob = (1/pin_price) / total_prob

                    best_price = 0
                    best_book = ""

                    for bookmaker in match.get('bookmakers', []):
                        name = bookmaker.get('title')

                        if name == "Pinnacle":
                            continue

                        if name not in ALLOWED_BOOKMAKERS:
                            continue

                        outcomes = bookmaker['markets'][0]['outcomes']
                        price = outcomes[i]['price']

                        if price > best_price:
                            best_price = price
                            best_book = name

                    if best_price == 0:
                        continue

                    edge = (best_price * true_prob) - 1

                    if edge > 0.001:
                        message = f"""
🔥 VALUE BET

🏟 {home} vs {away}
🎯 {pin_odds[i]['name']}

📊 Pinnacle: {pin_price}
💰 Odds: {best_price} ({best_book})

📈 Edge: {round(edge*100,2)}%
"""
                        print(message, flush=True)
                        send_telegram(message)

            print("\n⏳ Waiting for next scan...\n", flush=True)
            time.sleep(20)

        except Exception as e:
            print("ERROR:", e, flush=True)
            send_telegram(f"❌ Error: {e}")
            time.sleep(60)

# ================= RUN =================

if __name__ == "__main__":
    Thread(target=scanner).start()
    keep_alive()

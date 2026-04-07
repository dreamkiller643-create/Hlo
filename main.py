import requests
import time
from datetime import datetime, timedelta, timezone
from flask import Flask
from threading import Thread

# 🔐 API KEY
API_KEY = "15189eebbbae89f2e26e0e1cbe43cf5c"

# 📲 TELEGRAM SETTINGS
BOT_TOKEN = "8341652276:AAF0MM-8PMaEUjcrgRh_nE68riYSj3e-ZaA"
CHAT_ID = "8006964769"

# ⚽ LEAGUES
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

# 💰 ALLOWED BOOKMAKERS (INDIA FRIENDLY)
ALLOWED_BOOKMAKERS = [
    "1xBet",
    "4rabet",
    "Stake",
    "1Win"
]

# ⚙️ API PARAMS
params = {
    "apiKey": API_KEY,
    "regions": "eu",
    "markets": "h2h",
    "oddsFormat": "decimal"
}

seen_bets = set()

# 📲 TELEGRAM FUNCTION
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        requests.post(url, data=data)
    except:
        pass

# 🌐 KEEP ALIVE SERVER (FOR REPLIT)
app = Flask('')

@app.route('/')
def home():
    return "Bot running"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# 🔁 MAIN LOOP
while True:
    all_data = []

    # 🔄 FETCH ALL LEAGUES
    for sport in SPORTS:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                all_data.extend(response.json())
        except:
            continue

    print("\nTOTAL MATCHES SCANNED:", len(all_data))

    now = datetime.now(timezone.utc)
    time_limit = now + timedelta(hours=72)

    # 🔍 SCAN MATCHES
    for match in all_data:
        pin_odds = None

        # ✅ MATCH NAME FIX
        home = match.get('home_team', 'Unknown')
        away = match.get('away_team', 'Unknown')

        # ⏱ TIME FILTER
        match_time = datetime.fromisoformat(
            match['commence_time'].replace("Z", "+00:00")
        )

        if match_time > time_limit:
            continue

        # 📊 GET PINNACLE ODDS
        for bookmaker in match.get('bookmakers', []):
            if bookmaker.get('title') == "Pinnacle":
                pin_odds = bookmaker['markets'][0]['outcomes']

        if not pin_odds:
            continue

        # 📐 TRUE PROBABILITY
        total_prob = sum([1/o['price'] for o in pin_odds])

        # 🔎 CHECK EACH OUTCOME
        for i in range(len(pin_odds)):
            pin_price = pin_odds[i]['price']
            true_prob = (1/pin_price) / total_prob

            best_price = 0
            best_book = ""

            # 🔍 FIND BEST ALLOWED BOOKMAKER
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

            # 📊 EDGE
            edge = (best_price * true_prob) - 1

            # 🎯 VALUE FILTER (adjust here)
            if edge > 0.01:
                bet_id = f"{home}-{away}-{pin_odds[i]['name']}"

                if bet_id not in seen_bets:
                    seen_bets.add(bet_id)

                    message = f"""
🔥 VALUE BET

🏟 {home} vs {away}
🎯 {pin_odds[i]['name']}

📊 Pinnacle: {pin_price}
💰 Odds: {best_price} ({best_book})

📈 Edge: {round(edge*100,2)}%
"""

                    print(message)
                    send_telegram(message)

    print("\n⏳ Waiting for next scan...\n")

    time.sleep(60)

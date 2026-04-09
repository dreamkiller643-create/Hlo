import requests
import time

# ================= CONFIG =================
API_KEY = "15189eebbbae89f2e26e0e1cbe43cf5c"
TELEGRAM_TOKEN = "8341652276:AAF0MM-8PMaEUjcrgRh_nE68riYSj3e-ZaA"
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

ALLOWED_BOOKIES = ["1xBet",
    "Parimatch",
    "Stake",
    "Melbet",
    "4rabet",
    "1Win"]

EDGE_THRESHOLD = 0.001  # 2% edge

# ==========================================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


print("🚀 BOT STARTED...")

while True:
    print("\n🔄 Scanning...")

    all_matches = []

    # ===== FETCH DATA =====
    for sport in SPORTS:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"

        try:
            res = requests.get(url)

            if res.status_code != 200:
                print(f"❌ Error {res.status_code} for {sport}")
                continue

            data = res.json()
            print(f"✅ {sport}: {len(data)} matches")

            all_matches.extend(data)

        except Exception as e:
            print(f"❌ Fetch error: {e}")

    print("📊 TOTAL MATCHES SCANNED:", len(all_matches))

    # ===== VALUE BET LOGIC =====
    value_found = False

    for match in all_matches:
        home = match.get("home_team", "")
        away = match.get("away_team", "")
        match_name = f"{home} vs {away}"

        bookmakers = match.get("bookmakers", [])

        pin_odds = None
        best_odds = None
        best_bookmaker = None

        for book in bookmakers:
            title = book.get("title", "").lower()

            if not any(b in title for b in ALLOWED_BOOKIES) and "pinnacle" not in title:
                continue

            # Find Pinnacle
            if "pinnacle" in title:
                pin_odds = book["markets"][0]["outcomes"]

            # Find best odds from others
            for outcome in book["markets"][0]["outcomes"]:
                if not best_odds or outcome["price"] > best_odds:
                    best_odds = outcome["price"]
                    best_bookmaker = book.get("title")

        # Skip if no Pinnacle
        if not pin_odds or not best_odds:
            continue

        # Compare each selection
        for outcome in pin_odds:
            name = outcome["name"]
            pin_price = outcome["price"]

            # find same selection in other books
            for book in bookmakers:
                if "pinnacle" in book.get("title", "").lower():
                    continue

                for out in book["markets"][0]["outcomes"]:
                    if out["name"] == name:
                        other_price = out["price"]

                        true_prob = 1 / pin_price
                        edge = (other_price * true_prob) - 1

                        if edge > EDGE_THRESHOLD:
                            value_found = True

                            msg = f"""
🔥 VALUE BET FOUND!

🏟 Match: {match_name}
🎯 Selection: {name}

📊 Pinnacle: {pin_price}
💰 Other: {other_price} ({book.get('title')})

📈 Edge: {round(edge*100,2)}%
"""
                            print(msg)
                            send_telegram(msg)

    if not value_found:
        print("❌ No value bets found")

    print("⏳ Waiting for next scan...\n")
    time.sleep(60)

import requests
import json
import os
from datetime import datetime

# 🔐 Legge i segreti dal repository GitHub
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PRODOTTO = "Bull Brigade Perché non si sa mai vinile"
DATA_FILE = "prezzo.json"


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def get_serpapi_results():
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": PRODOTTO,
        "api_key": SERPAPI_KEY,
        "hl": "it",
        "gl": "it"
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []

    for field in ["shopping_results", "inline_shopping_results"]:
        for item in data.get(field, []):
            prezzo = item.get("price")
            link = item.get("link")

            if prezzo and link and "€" in prezzo:
                try:
                    valore = float(prezzo.replace("€", "").replace(",", "."))
                    results.append((valore, link))
                except:
                    pass

    return results


def load_previous():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return None


def save_price(price):
    with open(DATA_FILE, "w") as f:
        json.dump({"price": price, "date": str(datetime.now())}, f)


# ===== ESECUZIONE =====

results = get_serpapi_results()

if not results:
    print("Nessun prezzo trovato")
else:
    min_price = min(results, key=lambda x: x[0])[0]

    previous = load_previous()
    previous_price = previous.get("price") if previous else None

    if previous_price is None:
        send_telegram(f"📀 Primo prezzo trovato: {min_price}€")
    elif min_price < previous_price:
        send_telegram(
            f"📉 Prezzo sceso!\nPrima: {previous_price}€\nOra: {min_price}€"
        )

    save_price(min_price)

import os
import requests
import json
from datetime import datetime

# --- Secrets GitHub ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

prodotti = [
    {
        "nome": "Bull Brigade Perché non si sa mai vinile",
        "id": "Bull Brigade Perché non si sa mai vinile"
    }
]

# --- Funzioni ---
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    resp = requests.post(url, data=data)
    print("Telegram response:", resp.text)

def load_prices():
    try:
        with open("prezzi.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_prices(data):
    with open("prezzi.json", "w") as f:
        json.dump(data, f, indent=2)

# Ottieni risultati da Google Shopping (SerpAPI)
def get_google_shopping(q):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": q,
        "api_key": SERPAPI_KEY,
        "hl": "it",
        "gl": "it"
    }
    r = requests.get(url, params=params).json()
    res = []
    for item in r.get("shopping_results", []):
        prezzo = item.get("price", "")
        link = item.get("link", "")
        if "€" in prezzo and link:
            try:
                val = float(prezzo.replace("€", "").replace(",", "."))
                res.append((val, link))
            except:
                pass
    return res

# Ottieni risultati da Amazon (SerpAPI)
def get_amazon(q):
    url = "https://serpapi.com/search"
    params = {
        "engine": "amazon",
        "q": q,
        "api_key": SERPAPI_KEY,
        "domain": "amazon.it"
    }
    r = requests.get(url, params=params).json()
    res = []
    for item in r.get("shopping_results", []):
        prezzo = item.get("price", "")
        link = item.get("link", "")
        if "€" in prezzo and link:
            try:
                val = float(prezzo.replace("€","").replace(",","."))
                res.append((val, link))
            except:
                pass
    return res

# Ottieni risultati da Discogs (ricerca base)
def get_discogs(q):
    try:
        url = "https://api.discogs.com/database/search"
        headers = {"User-Agent": "vinile-monitor/1.0"}
        params = {"q": q, "format": "Vinyl", "type": "release"}
        r = requests.get(url, headers=headers, params=params).json()
        res = []
        for x in r.get("results", []):
            prezzo = x.get("price", None)
            link = x.get("uri", "")
            if prezzo and link:
                try:
                    val = float(prezzo)
                    url2 = f"https://www.discogs.com{link}"
                    res.append((val, url2))
                except:
                    pass
        return res
    except:
        return []

# --- ESECUZIONE ---
prezzi_storico = load_prices()
oggi = datetime.now().strftime("%d/%m/%Y %H:%M")
report = f"📊 *Monitor prezzi — {oggi}*\n\n"

for prodotto in prodotti:
    nome = prodotto["nome"]
    q = prodotto["id"]

    # Tutti i risultati
    risultati = []
    risultati += get_google_shopping(q)
    risultati += get_amazon(q)
    risultati += get_discogs(q)

    if not risultati:
        report += f"⚠️ Nessun risultato per *{nome}*\n\n"
        continue

    # Ordina per prezzo
    risultati.sort(key=lambda x: x[0])
    min_price = risultati[0][0]
    min_links = [link for price, link in risultati if price == min_price]

    # Prepara output dettagliato
    report += f"🎵 *{nome}*\n"
    report += f"➤ Prezzo più basso trovato: *{min_price}€*\n"
    report += f"➤ Storico minimo: "

    storico = prezzi_storico.get(nome, {})
    storico_min = storico.get("minimo", None)
    storico_last = storico.get("ultimo", None)

    if storico_min is None:
        report += "nessuno (prima esecuzione)\n"
    else:
        report += f"*{storico_min}€*\n"

    # Variazione rispetto all'ultimo
    if storico_last is not None:
        if min_price < storico_last:
            report += f"⬇️ Prezzo in calo rispetto a ultimo ({storico_last}€)\n"
        elif min_price > storico_last:
            report += f"⬆️ Prezzo aumentato rispetto a ultimo ({storico_last}€)\n"
        else:
            report += f"↔️ Prezzo invariato rispetto a ultimo ({storico_last}€)\n"
    else:
        report += "↔️ Nessun ultimo storico\n"

    # Link dei negozi al prezzo minimo
    report += "🔗 Link negozi:\n"
    for link in min_links:
        report += f"{link}\n"
    report += "\n"

    # Aggiorna storico nel JSON
    prezzi_storico[nome] = {
        "ultimo": min_price,
        "minimo": min(min_price, storico_min) if storico_min else min_price
    }

# Salva storico
save_prices(prezzi_storico)

# Invia Telegram
send_telegram(report)

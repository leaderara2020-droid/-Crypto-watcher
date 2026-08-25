#!/usr/bin/env python3
"""
Crypto Watcher — Analyse automatique du marché crypto envoyée sur Telegram.

Fonctionnement :
- Interroge CoinGecko (prix, volumes, dominance) et Alternative.me (Fear & Greed)
- Génère un résumé lisible de la situation du marché
- Envoie le tout sur Telegram via un bot

Installation :
    pip install requests

Configuration :
    1. Crée un bot Telegram via @BotFather sur Telegram -> tu obtiens un TOKEN
    2. Envoie un message à ton bot, puis va sur :
       https://api.telegram.org/bot<TON_TOKEN>/getUpdates
       -> récupère ton "chat_id" dans la réponse JSON
    3. Renseigne TELEGRAM_TOKEN et TELEGRAM_CHAT_ID ci-dessous

Exécution manuelle :
    python3 crypto_watcher.py

Exécution automatique toutes les 3h : voir instructions en bas de fichier.
"""

import os
import requests
from datetime import datetime

# ============ CONFIGURATION ============
# Les identifiants sont lus depuis les variables d'environnement
# (configurées comme "secrets" dans GitHub Actions)
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Cryptos à suivre (ids CoinGecko)
COINS = ["bitcoin", "ethereum", "solana"]
# ========================================


def get_market_data():
    """Récupère prix, variations et volumes depuis CoinGecko."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "eur",
        "ids": ",".join(COINS),
        "order": "market_cap_desc",
        "price_change_percentage": "1h,24h,7d",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def get_global_data():
    """Récupère la dominance BTC et le volume total du marché."""
    r = requests.get("https://api.coingecko.com/api/v3/global", timeout=15)
    r.raise_for_status()
    return r.json()["data"]


def get_fear_greed():
    """Récupère l'indice Fear & Greed."""
    r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=15)
    r.raise_for_status()
    data = r.json()["data"][0]
    return int(data["value"]), data["value_classification"]


def analyse_texte(coins, global_data, fng_value, fng_label):
    """Génère un résumé lisible basé sur des règles simples."""
    btc = next(c for c in coins if c["id"] == "bitcoin")
    var_1h = btc.get("price_change_percentage_1h_in_currency") or 0
    var_24h = btc.get("price_change_percentage_24h_in_currency") or 0
    var_7d = btc.get("price_change_percentage_7d_in_currency") or 0
    dominance = global_data["market_cap_percentage"].get("btc", 0)

    lignes = []

    # Tendance court terme
    if var_1h > 1.5:
        lignes.append("Mouvement haussier rapide sur la dernière heure.")
    elif var_1h < -1.5:
        lignes.append("Mouvement baissier rapide sur la dernière heure.")

    # Tendance 24h
    if var_24h > 5:
        lignes.append("Forte hausse sur 24h, marché en momentum positif.")
    elif var_24h < -5:
        lignes.append("Forte baisse sur 24h, prudence recommandée.")
    else:
        lignes.append("Marché relativement stable sur 24h.")

    # Tendance semaine
    if var_7d > 10:
        lignes.append("Tendance haussière soutenue sur 7 jours.")
    elif var_7d < -10:
        lignes.append("Tendance baissière marquée sur 7 jours.")

    # Sentiment
    if fng_value >= 75:
        lignes.append(f"Sentiment de marché : cupidité extrême ({fng_value}/100) — risque de correction.")
    elif fng_value <= 25:
        lignes.append(f"Sentiment de marché : peur extrême ({fng_value}/100) — zone historiquement propice aux rebonds.")
    else:
        lignes.append(f"Sentiment de marché neutre ({fng_value}/100 — {fng_label}).")

    # Dominance
    if dominance > 55:
        lignes.append(f"Dominance BTC élevée ({dominance:.1f}%) — capital concentré sur Bitcoin.")
    else:
        lignes.append(f"Dominance BTC : {dominance:.1f}%.")

    return " ".join(lignes)


def format_message(coins, global_data, fng_value, fng_label):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines = [f"📊 *Rapport Crypto — {now}*\n"]

    for c in coins:
        symbol = c["symbol"].upper()
        price = c["current_price"]
        var_1h = c.get("price_change_percentage_1h_in_currency") or 0
        var_24h = c.get("price_change_percentage_24h_in_currency") or 0
        var_7d = c.get("price_change_percentage_7d_in_currency") or 0
        emoji = "🟢" if var_24h >= 0 else "🔴"
        lines.append(
            f"{emoji} *{symbol}* : {price:,.0f} €  "
            f"(1h: {var_1h:+.1f}% | 24h: {var_24h:+.1f}% | 7j: {var_7d:+.1f}%)"
        )

    lines.append(f"\n🌐 Dominance BTC : {global_data['market_cap_percentage']['btc']:.1f}%")
    lines.append(f"😨 Fear & Greed Index : {fng_value}/100 ({fng_label})")
    lines.append(f"\n🧠 *Analyse* : {analyse_texte(coins, global_data, fng_value, fng_label)}")

    return "\n".join(lines)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    r = requests.post(url, data=payload, timeout=15)
    r.raise_for_status()


def main():
    try:
        coins = get_market_data()
        global_data = get_global_data()
        fng_value, fng_label = get_fear_greed()
        message = format_message(coins, global_data, fng_value, fng_label)
        send_telegram(message)
        print("Rapport envoyé avec succès.")
        print(message)
    except Exception as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    main()


# ============================================================
# Ce script est prévu pour tourner via GitHub Actions (cloud, gratuit).
# Voir le fichier .github/workflows/crypto-report.yml et le guide fourni.
# ============================================================

import os
import time
import json
import threading
import logging
import ccxt

# --- Configuration ---
SAVE_FILE = "bots.json"
POLL_INTERVAL = 5  # secondes entre vérifications
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# --- CCXT Exchange ---
api_key = os.environ.get("KRAKEN_KEY")
api_secret = os.environ.get("KRAKEN_SECRET")
if not api_key or not api_secret:
    raise SystemExit("Définir KRAKEN_KEY et KRAKEN_SECRET en variables d'environnement")

exchange = ccxt.kraken({
    "apiKey": api_key,
    "secret": api_secret,
    "enableRateLimit": True,
})

# Load markets and pick pair (prefer XRP/USDC)
try:
    exchange.load_markets()
except Exception as e:
    logging.warning(f"Impossible de charger les markets: {e}")

PAIR = None
for p in ("XRP/USDC", "XRP/USDT", "XRP/USD"):
    if p in exchange.markets:
        PAIR = p
        break
if PAIR is None:
    for m in exchange.markets:
        if m.upper().startswith("XRP/"):
            PAIR = m
            break
if PAIR is None:
    raise SystemExit("Aucune paire XRP disponible sur

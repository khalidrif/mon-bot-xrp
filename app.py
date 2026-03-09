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
for p in ("XRP/USDC", "XRP/USDT", "XRP/USD", "XRP/USD:USD"):
    if p in exchange.markets:
        PAIR = p
        break
if PAIR is None:
    # try case-insensitive search
    for m in exchange.markets:
        if m.upper().startswith("XRP/"):
            PAIR = m
            break
if PAIR is None:
    raise SystemExit("Aucune paire XRP disponible sur cet échange")

logging.info(f"Using market pair: {PAIR}")

# --- State persistence ---
_state_lock = threading.Lock()

def load_state():
    if not os.path.exists(SAVE_FILE):
        return []
    try:
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_state(bots):
    with _state_lock:
        with open(SAVE_FILE, "w") as f:
            json.dump(bots, f, indent=2)

# --- Helpers ---
def amount_precision(symbol, amount):
    try:
        return float(exchange.amount_to_precision(symbol, amount))
    except Exception:
        return round(amount, 4)

def price_precision(symbol, price):
    try:
        return float(exchange.price_to_precision(symbol, price))
    except Exception:
        return round(price, 5)

def is_order_filled(order):
    status = (order.get("status") or "").lower()
    filled = float(order.get("filled", 0) or 0)
    amount = float(order.get("amount", 0) or 0)
    remaining = float(order.get("remaining", 1) or 1)
    return status == "closed" or (amount > 0 and abs(filled - amount) < 1e-9) or remaining == 0

# --- Example bot structure ---
# {
#   "enabled": True/False,
#   "target_usdc": float,
#   "buy_price": float,
#   "sell_price": float,
#   "xrp_qty": float,
#   "snowball": True/False,
#   "gain": float,
#   "cycles": int,
#   "pair": "<PAIR>",
#   "buy_id": "",
#   "sell_id": "",
#   "mode": "CONFIG"/"BUY"/"SELL"
# }

# --- Load or create example bot if none ---
bots = load_state()
if not bots:
    bots = [{
        "enabled": False,
        "target_usdc": 10.0,
        "buy_price": 0.25,
        "sell_price": 0.27,
        "xrp_qty": 0.0,
        "snowball": True,
        "gain": 0.0,
        "cycles": 0,
        "pair": PAIR,
        "buy_id": "",
        "sell_id": "",
        "mode": "CONFIG"
    }]
    save_state(bots)
    logging.info("Fichier bots.json créé. Édite-le pour configurer et active le bot en mettant 'enabled': true.")

# --- Trading loop ---
def trading_loop():
    while True:
        for bot in bots:
            try:
                if not bot.get("enabled"):
                    continue
                pair = bot.get("pair", PAIR)

                # BUY waiting: check buy order filled and place sell
                if bot.get("mode") == "BUY" and bot.get("buy_id"):
                    buy_id = bot.get("buy_id")
                    try:
                        order = exchange.fetch

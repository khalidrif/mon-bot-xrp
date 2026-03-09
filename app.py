# ----------------------------------------------------
# AFFICHAGE STRUCTURÉ DES ORDRES KRAKEN
# ----------------------------------------------------
import pandas as pd

st.header("📑 Ordres Kraken")

try:
    open_orders = exchange.fetch_open_orders("XRP/USDC")
    closed_orders = exchange.fetch_closed_orders("XRP/USDC")
except:
    st.error("Impossible de récupérer les ordres Kraken.")
    open_orders = []
    closed_orders = []

# -------------------------
# ORDRES OUVERTS (OPEN)
# -------------------------
st.subheader("🟡 Ordres en attente")

if len(open_orders) == 0:
    st.info("Aucun ordre en attente.")
else:
    df_open = pd.DataFrame([{
        "ID": o["id"],
        "Type": o["side"],
        "Prix": o["price"],
        "Quantité": o["amount"],
        "Statut": o["status"]
    } for o in open_orders])

    st.dataframe(df_open, use_container_width=True)

# -------------------------
# ORDRES EXÉCUTÉS (CLOSED)
# -------------------------
st.subheader("🟢 Ordres exécutés")

if len(closed_orders) == 0:
    st.info("Aucun ordre exécuté.")
else:
    df_closed = pd.DataFrame([{
        "ID": o["id"],
        "Type": o["side"],
        "Prix": o["price"],
        "Quantité": o["amount"],
        "Statut": o["status"]
    } for o in closed_orders[-20:]])  # derniers 20 ordres

    st.dataframe(df_closed, use_container_width=True)

# --- INITIALISATION CRITIQUE ---
usdc = 0.0  # On force la création de la variable ici, quoi qu'il arrive

try:
    res_bal = k.query_private('Balance')
    # On vérifie si Kraken a bien répondu avec des données
    if res_bal and 'result' in res_bal:
        bal = res_bal['result']
        usdc = float(bal.get('USDC', 0))
    else:
        st.warning("⚠️ Kraken répond mais ne donne pas le solde. Mode attente...")
except Exception as e:
    st.error(f"❌ Connexion API impossible : {e}")

# --- UTILISATION SÉCURISÉE ---
# Maintenant 'usdc' est défini (soit 0.0, soit ton vrai solde)
# Le calcul suivant ne plantera plus jamais
p_in = st.number_input("Achat", value=1.3600, format="%.4f")
vol_calcul = (usdc * 0.98) / p_in if usdc > 0 else 22.0 # Valeur de secours pour tes 30$

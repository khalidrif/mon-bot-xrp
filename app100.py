# --- RÉCUPÉRATION DU SOLDE SÉCURISÉE ---
try:
    bal = k.query_private('Balance')['result']
    usdc = float(bal.get('USDC', 0))
except:
    usdc = 0.0  # Si Kraken ne répond pas, on met 0 au lieu de faire planter le script

# --- CALCUL DU VOLUME ---
if usdc > 0:
    # On calcule le volume max pour tes 1500$ (ou ce qu'il reste)
    vol_calcule = (usdc * 0.985) / p_in 
else:
    vol_calcule = 0.0

# Remplace ton champ 'vol' par celui-ci pour éviter l'erreur
vol = st.number_input("Volume XRP", value=max(vol_calcule, 10.0), format="%.1f")

import krakenex
import time

# --- CONFIGURATION ---
# Remplacez par vos clés API Kraken
API_KEY = 'VOTRE_CLE_API_PUBLIQUE'
API_SECRET = 'VOTRE_CLE_API_PRIVEE'

# Initialisation de l'API
k = krakenex.API()
k.key = API_KEY
k.secret = API_SECRET

def afficher_prix_xrp():
    """Récupère et affiche le dernier prix du XRP sur Kraken."""
    # Symbole Kraken pour XRP/USD (utilisez 'XXRPZEUR' pour l'Euro)
    paire = 'XXRPZUSD'
    
    try:
        # Requête publique pour le Ticker
        reponse = k.query_public('Ticker', {'pair': paire})
        
        if not reponse.get('error'):
            # Extraction du prix (champ 'c' = Last closed trade)
            # Structure : ['prix', 'volume du lot']
            dernier_prix = reponse['result'][paire]['c'][0]
            print(f"[{time.strftime('%H:%M:%S')}] Prix XRP: {dernier_prix} USD")
        else:
            print(f"Erreur API : {reponse['error']}")
            
    except Exception as e:
        print(f"Erreur de connexion : {e}")

if __name__ == "__main__":
    print("--- Démarrage du suivi XRP (Kraken) ---")
    try:
        while True:
            afficher_prix_xrp()
            time.sleep(10)  # Pause de 10 secondes entre chaque relevé
    except KeyboardInterrupt:
        print("\nArrêt du script par l'utilisateur.")

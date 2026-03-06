import krakenex
import os
import pandas as pd

# 1. Connexion sécurisée aux clés (qu'on va configurer juste après)
api_key = os.getenv('KRAKEN_KEY')
api_secret = os.getenv('KRAKEN_SECRET')

# 2. Initialisation de l'API
kraken = krakenex.API(key=api_key, secret=api_secret)

def check_account():
    print("Vérification du compte en cours...")
    try:
        # Demande le solde à Kraken
        response = kraken.query_private('Balance')
        
        if response.get('result'):
            # On transforme le résultat en tableau propre
            balance = response['result']
            df = pd.DataFrame.from_dict(balance, orient='index', columns=['Quantité'])
            print("--- TON SOLDE ACTUEL ---")
            print(df)
        else:
            print("Erreur Kraken :", response.get('error'))
            
    except Exception as e:
        print(f"Erreur de connexion : {e}")

if __name__ == "__main__":
    check_account()

import customtkinter as ctk
import ccxt
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TripleBotXRP(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DASHBOARD MULTI-STRATÉGIE XRP")
        self.geometry("1000x850")
        self.configure(fg_color="#0b0e11")

        # --- DONNÉES ---
        self.pair = "XRP/USDC"
        self.strats = {
            "Agressif (0.5%)": {"ecart": 0.005, "color": "#e74c3c", "orders": []},
            "Modéré (1.5%)": {"ecart": 0.015, "color": "#f1c40f", "orders": []},
            "Prudent (3.0%)": {"ecart": 0.030, "color": "#3498db", "orders": []}
        }
        self.historique_prix = []
        self.bot_actif = False

        # --- INTERFACE ---
        # 1. Graphique Central
        self.frame_graph = ctk.CTkFrame(self, fg_color="#1c1d22")
        self.frame_graph.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(5, 4), facecolor='#1c1d22')
        self.ax.set_facecolor('#1c1d22')
        self.ax.tick_params(colors='white')
        self.line_prix, = self.ax.plot([], [], color='#2ecc71', linewidth=2, label="Prix Live")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graph)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 2. Zone de Contrôle (3 colonnes pour les 3 bots)
        self.frame_bots = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bots.pack(fill="x", padx=10, pady=10)

        self.labels_prix = {}
        for name, config in self.strats.items():
            f = ctk.CTkFrame(self.frame_bots, fg_color="#1e2329", border_color=config['color'], border_width=1)
            f.pack(side="left", padx=5, expand=True, fill="both")
            ctk.CTkLabel(f, text=name, text_color=config['color'], font=("Arial", 14, "bold")).pack(pady=5)
            self.labels_prix[name] = ctk.CTkLabel(f, text="Attente...", font=("Arial", 16))
            self.labels_prix[name].pack(pady=10)

        # 3. Bouton Global
        self.btn_run = ctk.CTkButton(self, text="LANCER LES 3 STRATÉGIES", fg_color="#00c087", command=self.basculer_bots)
        self.btn_run.pack(pady=15)

    def basculer_bots(self):
        if not self.bot_actif:
            self.bot_actif = True
            self.btn_run.configure(text="STOP TOUT", fg_color="#e74c3c")
            threading.Thread(target=self.moteur_triple, daemon=True).start()
        else:
            self.bot_actif = False
            self.btn_run.configure(text="LANCER LES 3 STRATÉGIES", fg_color="#00c087")

    def moteur_triple(self):
        exchange = ccxt.kraken()
        ticker = exchange.fetch_ticker(self.pair)
        prix_depart = ticker['last']

        # Initialisation des ordres pour chaque bot
        for name, config in self.strats.items():
            config['orders'] = [
                {"side": "buy", "price": round(prix_depart * (1 - config['ecart']), 4)},
                {"side": "sell", "price": round(prix_depart * (1 + config['ecart']), 4)}
            ]

        while self.bot_actif:
            try:
                ticker = exchange.fetch_ticker(self.pair)
                prix = ticker['last']
                self.historique_prix.append(prix)
                if len(self.historique_prix) > 50: self.historique_prix.pop(0)
                
                self.after(0, self.maj_ui, prix)
                time.sleep(2)
            except:
                time.sleep(5)

    def maj_ui(self, prix):
        # Update du texte
        for name in self.strats:
            self.labels_prix[name].configure(text=f"{prix} $")
        
        # Update du Graphique
        self.line_prix.set_data(range(len(self.historique_prix)), self.historique_prix)
        self.ax.relim()
        self.ax.autoscale_view()

        # Effacer et Redessiner les lignes d'ordres des 3 bots
        for line in self.ax.get_lines()[1:]: line.remove()
        for name, config in self.strats.items():
            for o in config['orders']:
                self.ax.axhline(y=o['price'], color=config['color'], linestyle='--', alpha=0.5, linewidth=1)
        
        self.canvas.draw()

if __name__ == "__main__":
    app = TripleBotXRP()
    app.mainloop()

import customtkinter as ctk
import ccxt
import threading
import time
import json
import os

# --- CONFIGURATION STYLE ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paramètres techniques
FRAIS_KRAKEN = 0.0026 
SAVE_FILE = "empire_save.json"

class LigneBotPro(ctk.CTkFrame):
    def __init__(self, master, index, ecart, callback_harvest, **kwargs):
        super().__init__(master, fg_color="#1a1c22", height=50, corner_radius=8, **kwargs)
        
        self.index = index
        self.ecart = ecart
        self.callback_harvest = callback_harvest
        self.actif = False
        self.c_achat = 0
        self.c_vente = 0
        self.profit_bot = 0.0

        # UI : Bouton On/Off
        self.btn = ctk.CTkButton(self, text=f"STRAT {index+1}", width=90, height=30, 
                                 fg_color="#333333", font=("Arial", 11, "bold"), command=self.basculer)
        self.btn.pack(side="left", padx=15)

        # UI : Info Ecart et Prix
        self.lbl_ecart = ctk.CTkLabel(self, text=f"Grid: {round(ecart*100,2)}%", text_color="#848e9c", width=80)
        self.lbl_ecart.pack(side="left")

        self.lbl_prix = ctk.CTkLabel(self, text="---", font=("Consolas", 18, "bold"), text_color="#f0b90b", width=120)
        self.lbl_prix.pack(side="left", padx=10)

        # UI : Bouton Harvest
        self.btn_harvest = ctk.CTkButton(self, text="💰", width=35, fg_color="#2ecc71", 
                                         hover_color="#27ae60", command=self.recolter)
        self.btn_harvest.pack(side="right", padx=15)

        # UI : Zone Profit
        self.pnl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pnl_frame.pack(side="right", padx=10)
        self.lbl_pnl_val = ctk.CTkLabel(self.pnl_frame, text="+0.00$", text_color="#2ecc71", font=("Arial", 12, "bold"))
        self.lbl_pnl_val.pack()
        self.lbl_pnl_perc = ctk.CTkLabel(self.pnl_frame, text=f"Net: {round((ecart-(FRAIS_KRAKEN*2))*100,2)}%", text_color="#5dade2", font=("Arial", 10))
        self.lbl_pnl_perc.pack()

    def basculer(self, force_state=None):
        if force_state is not None: self.actif = force_state
        else: self.actif = not self.actif
        self.btn.configure(fg_color="#00c087" if self.actif else "#333333")
        if not self.actif: self.c_achat = 0

    def recolter(self):
        if self.profit_bot > 0:
            self.callback_harvest(self.profit_bot)
            self.profit_bot = 0.0
            self.flash_color("#2ecc71")

    def flash_color(self, color):
        orig = "#1a1c22"
        self.configure(fg_color=color)
        self.after(300, lambda: self.configure(fg_color=orig))

    def update_logic(self, prix, tendance_color):
        if not self.actif: return
        
        if self.c_achat == 0:
            self.c_achat = round(prix * (1 - self.ecart), 4)
            self.c_vente = round(prix * (1 + self.ecart), 4)

        if prix >= self.c_vente:
            gain = 10 * (self.ecart - (FRAIS_KRAKEN * 2))
            if gain > 0: 
                self.profit_bot += gain
                self.flash_color("#f1c40f")
            self.c_achat = round(prix * (1 - self.ecart), 4)
            self.c_vente = round(prix * (1 + self.ecart), 4)

        self.lbl_prix.configure(text=f"{prix}$", text_color=tendance_color)
        self.lbl_pnl_val.configure(text=f"+{round(self.profit_bot, 2)}$")

class EmpireTerminal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EMPIRE 2032 - ULTIMATE")
        self.geometry("950x850")
        self.configure(fg_color="#0b0e11")
        
        self.dernier_prix = 0
        self.coffre_fort = self.charger_sauvegarde()

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, fg_color="#1e2329", height=120)
        self.header.pack(fill="x", padx=20, pady=20)
        
        title_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        title_frame.pack(side="left", padx=30)
        ctk.CTkLabel(title_frame, text="🏛️ EMPIRE 2032", font=("Orbitron", 22, "bold"), text_color="#f0b90b").pack()
        self.lbl_coffre = ctk.CTkLabel(title_frame, text=f"COFFRE-FORT: {round(self.coffre_fort, 2)}$", font=("Arial", 14, "bold"), text_color="#2ecc71")
        self.lbl_coffre.pack()

        # Boutons Header
        self.btn_harvest_all = ctk.CTkButton(self.header, text="TOUT RÉCOLTER 💰", width=120, fg_color="#2ecc71", command=self.recolter_tout)
        self.btn_harvest_all.pack(side="right", padx=10)

        self.btn_all = ctk.CTkButton(self.header, text="RUN ALL", width=100, fg_color="#3498db", command=lambda: self.mass_action(True))
        self.btn_all.pack(side="right", padx=5)
        
        self.btn_stop = ctk.CTkButton(self.header, text="STOP ALL", width=100, fg_color="#f6465d", command=lambda: self.mass_action(False))
        self.btn_stop.pack(side="right", padx=5)

        # --- LISTE DES BOTS ---
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.bots = []
        for i in range(20):
            ecart = 0.006 + (i * 0.002)
            bot = LigneBotPro(self.scroll, i, ecart, self.ajouter_au_coffre)
            bot.pack(pady=5, fill="x")
            self.bots.append(bot)

        threading.Thread(target=self.moteur_master, daemon=True).start()

    def charger_sauvegarde(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                return data.get("coffre", 0.0)
        return 0.0

    def sauvegarder_donnees(self):
        with open(SAVE_FILE, 'w') as f:
            json.dump({"coffre": self.coffre_fort}, f)

    def ajouter_au_coffre(self, montant):
        self.coffre_fort += montant
        self.lbl_coffre.configure(text=f"COFFRE-FORT: {round(self.coffre_fort, 2)}$")
        self.sauvegarder_donnees()

    def recolter_tout(self):
        for bot in self.bots:
            bot.recolter()

    def mass_action(self, state):
        for bot in self.bots: bot.basculer(force_state=state)

    def moteur_master(self):
        exchange = ccxt.kraken()
        while True:
            try:
                ticker = exchange.fetch_ticker('XRP/USDC')
                prix = ticker['last']
                color = "#2ecc71" if prix >= self.dernier_prix else "#f6465d"
                self.dernier_prix = prix
                for bot in self.bots:
                    self.after(0, bot.update_logic, prix, color)
                time.sleep(1)
            except: time.sleep(5)

if __name__ == "__main__":
    app = EmpireTerminal()
    app.mainloop()

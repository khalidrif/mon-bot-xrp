# --- 5. INTERFACE (CORRIGÉE AVEC INDEX [0], [1]...) ---
st.title("🚀 Sniper Pro - Précision LIMIT")
st.caption(f"Dernier rafraîchissement : {time.strftime('%H:%M:%S')} (Intervalle : 40s)")

m1, m2, m3 = st.columns(3)
m1.metric("Prix XRP", f"{st.session_state.get('price',0):.5f}")
m2.metric("Solde USDC", f"{st.session_state.get('usdc',0):.2f}$")
m3.metric("Solde XRP", f"{st.session_state.get('xrp',0):.2f}")

st.divider()

# TABLEAU : On écrit dans chaque colonne individuellement
h = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6])
h[0].write("**ID**")
h[1].write("**St**")
h[2].write("**Achat**")
h[3].write("**Vente**")
h[4].write("**Mise**")
h[5].write("**Gain**")
h[6].write("**Qty**")
h[7].write("**Action**")
h[8].write("**Cy**")
h[9].write("**Go**")

for i in sorted(st.session_state.bots.keys()):
    bt = st.session_state.bots[i]
    r = st.columns([0.4, 0.4, 0.7, 0.7, 0.8, 0.8, 0.6, 1.2, 0.4, 0.6])
    
    r[0].write(f"#{i}")
    r[1].write("✅" if bt["actif"] else "⚪")
    r[2].write(f"{bt['p_achat']:.3f}")
    r[3].write(f"{bt['p_vente']:.3f}")
    
    mise_actu = float(bt["mise"] + bt["gain_cumule"])
    r[4].write(f"{mise_actu:.1f}$")
    
    # Gain
    g = bt["gain_cumule"]
    if g > 0: 
        r[5].markdown(f"**:green[+{g:.2f}$]**")
    else: 
        r[5].write(f"{g:.2f}$")
        
    r[6].write(f"{bt['qty']:.1f}")
    
    # Action (Achat VERT 🟢 / Vente ORANGE 🟠)
    if "ACHAT" in bt["etape"]: 
        r[7].markdown("🟢 **ACHAT**")
    elif "VENTE" in bt["etape"]:
        r[7].markdown("🟠 **VENTE**")
    else:
        r[7].write("⌛ ...")
        
    r[8].write(str(bt.get("cycles", 0)))
    
    if r[9].button("🚀" if not bt["actif"] else "🛑", key=f"btn{i}"):
        st.session_state.bots[i]["actif"] = not bt["actif"]
        st.rerun()

st.divider()
for m in reversed(st.session_state.logs[-10:]): 
    st.write(m)

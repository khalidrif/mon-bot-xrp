# ------------------------------
# TABLEAU RÉCAPITULATIF PRO (TRI + FILTRE + ACTIONS)
# ------------------------------
st.markdown("---")
st.subheader("📊 Tableau PRO des paliers")

import streamlit.components.v1 as components

if len(st.session_state.paliers) == 0:
    st.warning("Aucun palier.")
else:

    # --------- FILTRE ----------
    etat_filtre = st.selectbox(
        "Filtrer par état",
        ["TOUS", "WAIT BUY", "WAIT SELL", "EXEC SELL", "FINI", "OFF"]
    )

    # --------- TRI ----------
    tri = st.selectbox(
        "Trier par",
        ["Palier", "BUY", "SELL", "Montant", "Gain", "État"]
    )

    # construire tableau HTML
    html = "<div style='font-family:Arial;'><table style='width:100%; border-collapse:collapse;'>"

    # entête du tableau
    html += """
    <tr style='background:#222; color:white; font-size:16px;'>
        <th style='padding:8px; border-bottom:2px solid #444;'>Palier</th>
        <th style='padding:8px; border-bottom:2px solid #444;'>BUY</th>
        <th style='padding:8px; border-bottom:2px solid #444;'>SELL</th>
        <th style='padding:8px; border-bottom:2px solid #444;'>Montant</th>
        <th style='padding:8px; border-bottom:2px solid #444;'>État</th>
        <th style='padding:8px; border-bottom:2px solid #444;'>Cycle</th>
        <th style='padding:8px; border-bottom:2px solid #444;'>Gain</th>
        <th style='padding:8px; border-bottom:2px solid #444;'>Actions</th>
    </tr>
    """

    # préparer données
    rows = []
    for i, p in enumerate(st.session_state.paliers):

        # corriger clés manquantes
        for k, v in {
            "active": True,
            "done": False,
            "gain": 0.0,
            "buy_id": None,
            "sell_id": None,
        }.items():
            if k not in p:
                p[k] = v

        # état + couleurs
        if not p["active"]:
            etat = "OFF"
            color = "#661111"
        elif p["done"]:
            etat = "FINI"
            color = "#331144"
        elif p["buy_id"] is None:
            etat = "WAIT BUY"
            color = "#113311"
        elif p["sell_id"] is None:
            etat = "WAIT SELL"
            color = "#112244"
        else:
            etat = "EXEC SELL"
            color = "#443311"

        # filtre
        if etat_filtre != "TOUS" and etat_filtre != etat:
            continue

        rows.append({
            "i": i,
            "Palier": f"P{i+1}",
            "BUY": p["buy"],
            "SELL": p["sell"],
            "Montant": p["usdc"],
            "Etat": etat,
            "Couleur": color,
            "Gain": round(p["gain"], 4)
        })

    # tri dynamique
    rows.sort(key=lambda x: x[tri] if tri != "Palier" else x["i"])

    # construire lignes HTML
    for row in rows:

        i = row["i"]
        p = st.session_state.paliers[i]

        # barre progression cycle
        if row["Etat"] == "WAIT BUY":
            progress = 10
        elif row["Etat"] == "WAIT SELL":
            progress = 60
        elif row["Etat"] == "EXEC SELL":
            progress = 85
        elif row["Etat"] == "FINI":
            progress = 100
        else:
            progress = 0

        html += f"""
        <tr style='background:{row["Couleur"]}; color:white; font-size:14px;'>
            <td style='padding:8px;'>{row["Palier"]}</td>
            <td style='padding:8px;'>{row["BUY"]}</td>
            <td style='padding:8px;'>{row["SELL"]}</td>
            <td style='padding:8px;'>{row["Montant"]} USDC</td>
            <td style='padding:8px; font-weight:bold;'>{row["Etat"]}</td>

            <td style='padding:8px;'>
                <div style='background:#333; width:100%; height:10px; border-radius:5px;'>
                    <div style='background:#00FF00; height:10px; width:{progress}%; border-radius:5px;'></div>
                </div>
            </td>

            <td style='padding:8px;'>{row["Gain"]} USDC</td>

            <td style='padding:8px;'>
                <form action='' method='get'>
                    <button name='ON{i}' style='padding:5px 8px;'>ON</button>
                    <button name='OFF{i}' style='padding:5px 8px;'>OFF</button>
                    <button name='CB{i}' style='padding:5px 8px;'>C.BUY</button>
                    <button name='CS{i}' style='padding:5px 8px;'>C.SELL</button>
                    <button name='DEL{i}' style='padding:5px 8px;'>DEL</button>
                </form>
            </td>
        </tr>
        """

    html += "</table></div>"

    components.html(html, height=500, scrolling=True)

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

paliers = [
    {"buy":1.33607,"sell":1.37607,"usdc":10,"gain":0},
    {"buy":1.33000,"sell":1.37000,"usdc":10,"gain":0},
]

for i,p in enumerate(paliers):

    etat = "WAIT BUY"
    couleur = "#00aa44"

    components.html(f"""
    <div style="
    background:#101010;
    width:680px;
    height:34px;
    margin:auto;
    margin-top:6px;
    border-radius:6px;
    border-left:4px solid {couleur};
    font-family:Consolas, monospace;
    font-size:13px;
    color:#e6e6e6;
    display:grid;
    grid-template-columns:50px 130px 130px 80px 120px 90px 70px 70px;
    align-items:center;
    padding-left:10px;
    ">

    <div style="color:#aaaaaa;">P{i+1}</div>

    <div style="color:#00ff88;font-weight:bold;">
    BUY {p['buy']}
    </div>

    <div style="color:#ff4d4d;font-weight:bold;">
    SELL {p['sell']}
    </div>

    <div style="color:#dddddd;">
    ${p['usdc']}
    </div>

    <div style="color:#ffaa00;">
    {etat}
    </div>

    <div style="color:#00ffaa;">
    +{p['gain']:.4f}
    </div>

    <button style="
    width:60px;
    height:24px;
    background:#cc0000;
    color:white;
    border:none;
    border-radius:4px;
    font-size:11px;
    cursor:pointer;">
    OFF
    </button>

    <button style="
    width:60px;
    height:24px;
    background:#550000;
    color:white;
    border:none;
    border-radius:4px;
    font-size:11px;
    cursor:pointer;">
    DEL
    </button>

    </div>
    """,height=40)

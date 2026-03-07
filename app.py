import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

paliers = [
    {"buy":1.33607,"sell":1.37607,"usdc":10,"gain":0},
    {"buy":1.33000,"sell":1.37000,"usdc":10,"gain":0},
]

for i,p in enumerate(paliers):

    components.html(f"""
    <div style="
    background:#101010;
    width:95%;
    height:30px;
    margin:auto;
    margin-top:6px;
    border-radius:5px;
    font-family:Arial;
    font-size:12px;
    color:white;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding-left:6px;
    padding-right:6px;
    ">

    <span>P{i+1}</span>

    <span style="color:#00ff88;">
    B:{p['buy']}
    </span>

    <span style="color:#ff4d4d;">
    S:{p['sell']}
    </span>

    <span>${p['usdc']}</span>

    <span>WAIT</span>

    <span>+{p['gain']}</span>

    <button style="
    height:20px;
    font-size:10px;
    ">OFF</button>

    <button style="
    height:20px;
    font-size:10px;
    ">DEL</button>

    </div>
    """, height=35)

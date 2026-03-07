import streamlit as st
import streamlit.components.v1 as components

components.html("""
<div style='
    background-color:#111;
    padding:15px;
    margin-top:10px;
    border-radius:10px;
    border-left:8px solid #00FF00;
    color:white;
    font-size:18px;
'>
    TEST : Ceci est une bande avec une barre verte ✔
</div>
""", height=100)

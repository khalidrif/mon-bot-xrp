import streamlit as st
import ccxt
import time
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="XRP Multi-Grid Pro", layout="wide")
DB_FILE = "config_bots_xrp_v3.json"


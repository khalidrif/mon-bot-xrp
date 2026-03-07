components.html(f"""
<div style='
background:#101010;
width:100%;
max-width:390px;
padding:6px 8px;
margin:auto;
margin-top:6px;
border-radius:6px;
border-left:5px solid {couleur};
font-family:Consolas, monospace;
font-size:12px;
color:white;
display:flex;
align-items:center;
justify-content:space-between;
gap:6px;
'>

<div style="min-width:25px;">P{i+1}</div>

<div style="color:#00ff88;">BUY {p['buy']}</div>

<div style="color:#ff4d4d;">SELL {p['sell']}</div>

<div>{p['usdc']} USDC</div>

<div>{etat}</div>

<div>G:{p['gain']:.4f}</div>

<div style="display:flex; gap:4px;">

<a href='/?off={i}'>
<button style='
padding:2px 6px;
background:#bb0000;
color:white;
border:none;
border-radius:4px;
font-size:11px;
'>OFF</button>
</a>

<a href='/?del={i}'>
<button style='
padding:2px 6px;
background:#660000;
color:white;
border:none;
border-radius:4px;
font-size:11px;
'>DEL</button>
</a>

</div>

</div>
""", height=40)

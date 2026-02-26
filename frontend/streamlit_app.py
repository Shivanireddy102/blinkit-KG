"""
streamlit_app.py
================
E-Commerce Analytics Hub — full rewrite with:
  - Single clean Neo4j Aura connection (no duplicates)
  - Fixed CYPHER_SYSTEM_PROMPT (no more [:PLACED*2..] bug)
  - All pages working: Dashboard, Knowledge Graph, Graph Query,
    Product Search, Customers, Orders, Products, Stores,
    Delivery Partners, Analytics, Hora Chatbot
"""

import os
import json
import random
import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── Optional imports ────────────────────────────────────────
try:
    from neo4j import GraphDatabase, exceptions as neo4j_exc
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================
# PAGE CONFIG  (must be first Streamlit call)
# ============================================================
st.set_page_config(
    page_title="E-Commerce Analytics Hub",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
:root {
  --forest:#005F02; --sage:#427A43; --olive:#C0B87A;
  --cream:#F2E3BB;  --cream-dk:#e8d4a0; --ink:#1a2e1a;
  --white:#ffffff;
  --shadow-md:0 6px 20px rgba(0,95,2,.13);
  --shadow-lg:0 12px 36px rgba(0,95,2,.16);
  --r-sm:10px; --r-md:16px; --r-lg:24px;
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:var(--ink);}
.main .block-container{background:var(--cream)!important;padding-top:1.5rem!important;}
@keyframes fadeSlide{from{opacity:0;transform:translateY(-18px)}to{opacity:1;transform:translateY(0)}}
.header-box{background:linear-gradient(135deg,var(--forest) 0%,var(--sage) 60%,#5a9e5c 100%);
  padding:36px 40px;border-radius:var(--r-lg);text-align:center;color:var(--cream);
  box-shadow:var(--shadow-lg);margin-bottom:28px;animation:fadeSlide .9s ease;}
.header-box h1{font-family:'DM Serif Display',serif;font-size:2.4rem;color:var(--cream)!important;margin:0 0 6px;}
.header-box h4{color:var(--olive)!important;font-weight:400;font-size:1rem;margin:0;}
.kpi-card{padding:22px 16px;border-radius:var(--r-md);text-align:center;
  animation:fadeSlide 1.1s ease;transition:transform .25s,box-shadow .25s;
  border:1px solid rgba(0,95,2,.10);}
.kpi-card:hover{transform:translateY(-5px) scale(1.03);box-shadow:var(--shadow-lg);}
.kpi-card h2{font-family:'DM Serif Display',serif;font-size:2rem;margin:0 0 4px;}
.kpi-card p{font-size:.82rem;font-weight:600;letter-spacing:.8px;text-transform:uppercase;margin:0;opacity:.75;}
.kpi1{background:linear-gradient(135deg,#d4edda,#b8ddb8);color:var(--forest);}
.kpi2{background:linear-gradient(135deg,var(--cream),#e8d4a0);color:#5a3e00;}
.kpi3{background:linear-gradient(135deg,#c8e0c8,#a8cfa8);color:var(--forest);}
.kpi4{background:linear-gradient(135deg,#f0e8c8,var(--cream-dk));color:#6b5000;}
.kpi5{background:linear-gradient(135deg,var(--forest),var(--sage));color:var(--cream);}
.section{background:var(--white);padding:28px 30px;border-radius:var(--r-lg);
  box-shadow:var(--shadow-md);margin-bottom:22px;animation:fadeSlide 1.3s ease;
  border:1px solid rgba(66,122,67,.12);border-top:3px solid var(--sage);}
.section-neo4j{background:var(--white);padding:28px 30px;border-radius:var(--r-lg);
  box-shadow:var(--shadow-md);margin-bottom:22px;
  border:1px solid rgba(26,107,138,.2);border-top:3px solid #1a6b8a;}
.graph-legend-pill{display:inline-flex;align-items:center;gap:6px;
  background:rgba(242,227,187,0.7);border:1px solid rgba(66,122,67,.2);
  border-radius:20px;padding:4px 12px;font-size:12px;margin:3px;}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block;}
.cypher-box{background:#1a2e1a;border-radius:var(--r-md);padding:16px 20px;
  font-family:'Courier New',monospace;font-size:13px;color:#6fcf6f;
  border:1px solid rgba(66,122,67,.3);white-space:pre-wrap;word-break:break-all;margin:8px 0;}
.result-card{background:rgba(242,227,187,0.4);border-radius:var(--r-sm);
  padding:12px 16px;border-left:3px solid var(--sage);margin:6px 0;font-size:13px;}
.product-card{background:linear-gradient(135deg,rgba(242,227,187,.5),rgba(255,255,255,.8));
  border-radius:var(--r-md);padding:16px;border:1px solid rgba(192,184,122,.35);
  transition:all .2s;margin-bottom:10px;}
.product-card:hover{transform:translateY(-2px);box-shadow:var(--shadow-md);}
.status-badge{display:inline-block;padding:2px 10px;border-radius:20px;
  font-size:11px;font-weight:600;letter-spacing:.5px;}
.badge-connected{background:#d4edda;color:#005F02;}
.badge-demo{background:#fff3cd;color:#856404;}
.badge-error{background:#f8d7da;color:#721c24;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,var(--forest),#003a02)!important;}
section[data-testid="stSidebar"] *{color:var(--cream)!important;}
section[data-testid="stSidebar"] .stButton>button{
  background:rgba(242,227,187,.10)!important;color:var(--cream)!important;
  border:1px solid rgba(192,184,122,.25)!important;border-radius:var(--r-sm)!important;
  font-weight:500!important;transition:all .2s!important;}
section[data-testid="stSidebar"] .stButton>button:hover{
  background:rgba(192,184,122,.25)!important;transform:translateX(3px)!important;}
section[data-testid="stSidebar"] .stButton>button[kind="primary"]{
  background:linear-gradient(135deg,var(--olive),#a8a060)!important;
  color:var(--ink)!important;border-color:transparent!important;font-weight:600!important;}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{color:var(--olive)!important;font-family:'DM Serif Display',serif!important;}
section[data-testid="stSidebar"] hr{border-color:rgba(192,184,122,.2)!important;}
.chat-header{background:linear-gradient(135deg,var(--forest),var(--sage));
  padding:18px 20px;border-radius:var(--r-md) var(--r-md) 0 0;
  color:var(--cream);margin-bottom:0;border-bottom:2px solid var(--olive);}
.chat-header h3{margin:0;font-family:'DM Serif Display',serif;font-size:1.2rem;}
.chat-header p{margin:4px 0 0;font-size:12px;opacity:.85;}
h2,h3{font-family:'DM Serif Display',serif!important;color:var(--forest)!important;}
h4,h5,h6{font-family:'DM Sans',sans-serif!important;color:var(--sage)!important;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================
def initialize_session():
    defaults = {
        "initialized":       True,
        "chat_open":         False,
        "current_page":      "Dashboard",
        "chat_messages":     [{"role":"assistant",
                               "content":"Hello! I am **Hora** 👋 How can I help you?",
                               "time":datetime.datetime.now().strftime("%H:%M")}],
        "cypher_result":     None,
        "cypher_query":      "",
        "cypher_error":      None,
        "search_results":    [],
        # Neo4j creds stored here after Connect click
        "neo4j_uri":         os.getenv("NEO4J_URI", ""),
        "neo4j_user":        os.getenv("NEO4J_USER", "neo4j"),
        "neo4j_password":    os.getenv("NEO4J_PASSWORD", ""),
        "neo4j_connected":   False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# NEO4J — single clean connection layer
# ============================================================

@st.cache_resource(show_spinner=False)
def _build_driver(uri: str, user: str, password: str):
    """
    Cached driver factory. Returns (driver, None) or (None, error_str).
    Only called when credentials actually change.
    """
    if not NEO4J_AVAILABLE:
        return None, "neo4j package not installed — run: pip install neo4j"
    if not uri or not password:
        return None, "URI and password required."
    # Fix scheme for Aura
    for old in ("bolt://", "neo4j://"):
        if uri.startswith(old):
            uri = "neo4j+s://" + uri.split("://", 1)[1]
    if not uri.startswith("neo4j+s://"):
        uri = "neo4j+s://" + uri.lstrip("/")
    try:
        driver = GraphDatabase.driver(
            uri, auth=(user, password),
            max_connection_lifetime=3600,
            max_connection_pool_size=10,
            connection_acquisition_timeout=30,
        )
        driver.verify_connectivity()
        return driver, None
    except neo4j_exc.AuthError:
        return None, "Authentication failed — wrong username or password."
    except neo4j_exc.ServiceUnavailable as e:
        return None, f"Cannot reach Neo4j Aura: {e}"
    except Exception as e:
        return None, f"Connection error: {e}"


def get_driver():
    """Return cached driver using current session_state credentials."""
    return _build_driver(
        st.session_state.get("neo4j_uri", ""),
        st.session_state.get("neo4j_user", "neo4j"),
        st.session_state.get("neo4j_password", ""),
    )


def run_cypher(cypher: str):
    """Execute a Cypher query. Returns (rows, error)."""
    driver, err = get_driver()
    if driver is None:
        return [], err
    try:
        with driver.session(database="neo4j") as session:
            result = session.run(cypher)
            rows = []
            for rec in result:
                row = {}
                for k, v in rec.items():
                    row[k] = dict(v) if hasattr(v, "items") else v
                rows.append(row)
            return rows, None
    except Exception as e:
        return [], str(e)


# ============================================================
# DEMO DATA
# ============================================================
@st.cache_data(ttl=60)
def load_data():
    np.random.seed(42)
    n_c, n_o, n_p, n_s, n_dp = 120, 350, 60, 8, 15
    cities   = ["Mumbai","Delhi","Bengaluru","Hyderabad","Chennai","Pune","Kolkata"]
    states   = ["Maharashtra","Delhi","Karnataka","Telangana","Tamil Nadu","West Bengal"]
    brands   = ["Nike","Adidas","Samsung","Apple","LG","Sony","Puma","Zara"]
    cats     = ["Electronics","Clothing","Footwear","Home & Kitchen","Sports","Books"]
    vehicles = ["Bike","Scooter","Bicycle","Car"]
    statuses = ["Delivered","Pending","Shipped","Cancelled","Returned"]

    customers = pd.DataFrame({
        "customer_id": [f"C{i:03d}" for i in range(1,n_c+1)],
        "name":  [f"Customer {i}" for i in range(1,n_c+1)],
        "email": [f"customer{i}@email.com" for i in range(1,n_c+1)],
        "city":  np.random.choice(cities, n_c),
        "state": np.random.choice(states, n_c),
        "phone": [f"98{np.random.randint(10000000,99999999)}" for _ in range(n_c)],
    })
    products = pd.DataFrame({
        "product_id":   [f"P{i:03d}" for i in range(1,n_p+1)],
        "product_name": [f"Product {i}" for i in range(1,n_p+1)],
        "brand":    np.random.choice(brands, n_p),
        "category": np.random.choice(cats,   n_p),
        "price":    np.round(np.random.uniform(199, 9999, n_p), 2),
        "rating":   np.round(np.random.uniform(3.0, 5.0,  n_p), 1),
        "stock":    np.random.randint(0, 500, n_p),
    })
    stores = pd.DataFrame({
        "store_id":   [f"S{i:02d}" for i in range(1,n_s+1)],
        "store_name": [f"Store {i}" for i in range(1,n_s+1)],
        "city":    np.random.choice(cities, n_s),
        "state":   np.random.choice(states, n_s),
        "manager": [f"Manager {i}" for i in range(1,n_s+1)],
    })
    delivery_partners = pd.DataFrame({
        "partner_id":   [f"DP{i:02d}" for i in range(1,n_dp+1)],
        "name":         [f"Partner {i}" for i in range(1,n_dp+1)],
        "vehicle_type": np.random.choice(vehicles, n_dp),
        "rating":       np.round(np.random.uniform(3.5, 5.0, n_dp), 1),
        "city":         np.random.choice(cities, n_dp),
    })
    orders = pd.DataFrame({
        "order_id":            [f"O{i:04d}" for i in range(1,n_o+1)],
        "customer_id":         np.random.choice(customers["customer_id"], n_o),
        "store_id":            np.random.choice(stores["store_id"],       n_o),
        "delivery_partner_id": np.random.choice(delivery_partners["partner_id"], n_o),
        "status":              np.random.choice(statuses, n_o, p=[.55,.15,.15,.10,.05]),
        "total_amount":        np.round(np.random.uniform(299, 14999, n_o), 2),
        "order_date":          pd.to_datetime(
            np.random.choice(pd.date_range("2024-01-01","2025-12-31"), n_o)),
    })
    order_items = pd.DataFrame({
        "order_id":   np.random.choice(orders["order_id"],   n_o*2),
        "product_id": np.random.choice(products["product_id"], n_o*2),
        "quantity":   np.random.randint(1, 6, n_o*2),
        "unit_price": np.round(np.random.uniform(199, 9999, n_o*2), 2),
    })
    return {"customers":customers,"orders":orders,"products":products,
            "stores":stores,"delivery_partners":delivery_partners,"order_items":order_items}


# ============================================================
# NL-TO-CYPHER  — fixed prompt, no [:REL*N..] ever generated
# ============================================================
CYPHER_SYSTEM_PROMPT = """
You are a Neo4j 5 Cypher expert for an e-commerce graph database.

Return ONLY a valid Cypher query. No explanation. No markdown. No backticks.

Node Labels and Properties:
  Customer        (id, name)
  Order           (id, date, status)
  Product         (id, name, price, category)
  Store           (id, name)
  DeliveryPartner (id, name)

Relationships — single hop only, EXACT syntax:
  (Customer)-[:PLACED]->(Order)
  (Order)-[:CONTAINS]->(Product)
  (Order)-[:FROM]->(Store)
  (Order)-[:DELIVERED_BY]->(DeliveryPartner)
  (Customer)-[:ORDERED_PRODUCT]->(Product)
  (Customer)-[:ORDERED_FROM]->(Store)
  (Customer)-[:SERVICED_BY]->(DeliveryPartner)
  (Store)-[:SOLD_PRODUCT]->(Product)
  (DeliveryPartner)-[:DELIVERED_PRODUCT]->(Product)
  (DeliveryPartner)-[:DELIVERED_TO_STORE]->(Store)

STRICT RULES:
  1. NEVER use variable-length paths like [:PLACED*] or [:PLACED*2..] — single hop only
  2. NEVER use size() with pattern expressions — use count() with WITH instead
  3. NEVER invent properties — use only the ones listed above
  4. Order has NO price/amount/total — use sum(p.price) via CONTAINS for revenue
  5. Always RETURN something meaningful
  6. Default LIMIT 25

Correct count pattern:
  MATCH (c:Customer)-[:PLACED]->(o:Order)
  WITH c, count(o) AS order_count
  RETURN c.name AS customer, order_count
  ORDER BY order_count DESC LIMIT 25

Revenue pattern:
  MATCH (s:Store)<-[:FROM]-(o:Order)-[:CONTAINS]->(p:Product)
  RETURN s.name AS store, sum(p.price) AS revenue
  ORDER BY revenue DESC LIMIT 10
"""


def nl_to_cypher(question: str) -> str:
    if not GROQ_AVAILABLE:
        return "// groq not installed\nRETURN 'pip install groq' AS message"
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return "// GROQ_API_KEY not set\nRETURN 'Set GROQ_API_KEY in .env' AS message"
    try:
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": CYPHER_SYSTEM_PROMPT},
                {"role": "user",   "content": f"Question: {question}\n\nCypher query:"},
            ],
            temperature=0,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip any markdown fences the model still adds
        raw = raw.replace("```cypher","").replace("```","").strip()
        return raw
    except Exception as e:
        return f"// Error: {e}"


# ============================================================
# GRAPH VISUALISATION
# ============================================================
REL_COLORS = {
    "PLACED":"#005F02","CONTAINS":"#C0B87A",
    "FROM":"#8B4513","DELIVERED_BY":"#1a6b8a",
}

def generate_demo_graph(filter_type="All", view_mode="Core Path", max_nodes=40):
    random.seed(42)
    styles = {
        "Customer":        {"color":"#005F02","size":20},
        "Order":           {"color":"#427A43","size":16},
        "Product":         {"color":"#C0B87A","size":14},
        "Store":           {"color":"#8B4513","size":13},
        "DeliveryPartner": {"color":"#1a6b8a","size":13},
    }
    customers = [f"C{i:03d}" for i in range(1,7)]
    orders    = [f"O{i:04d}" for i in range(1,11)]
    products  = [f"P{i:03d}" for i in range(1,9)]
    stores    = [f"S{i:02d}" for i in range(1,4)]
    partners  = [f"DP{i:02d}" for i in range(1,4)]

    include = ({"Customer","Order","Product"} if "Core" in view_mode
               else {"Customer","Order","Product","Store","DeliveryPartner"})
    if filter_type != "All":
        include = {filter_type}

    all_nodes = ([(c,"Customer") for c in customers]+[(o,"Order") for o in orders]+
                 [(p,"Product")  for p in products]+[(s,"Store")  for s in stores]+
                 [(d,"DeliveryPartner") for d in partners])
    nodes = [{"id":nid,"type":ntype,"color":styles[ntype]["color"],"size":styles[ntype]["size"]}
             for nid,ntype in all_nodes if ntype in include]

    rels = []
    for o in orders:
        c=random.choice(customers); s=random.choice(stores)
        d=random.choice(partners);  p1=random.choice(products); p2=random.choice(products)
        rels+=[(c,o,"PLACED"),(o,p1,"CONTAINS"),(o,p2,"CONTAINS"),(o,s,"FROM"),(o,d,"DELIVERED_BY")]

    node_ids = {n["id"] for n in nodes}
    edges = [{"source":src,"target":tgt,"rel":rel}
             for src,tgt,rel in rels if src in node_ids and tgt in node_ids]
    return nodes[:max_nodes], edges


def _layout_positions(nodes):
    random.seed(77)
    col_x  = {"Customer":0.08,"Order":0.50,"Product":0.92,"Store":0.28,"DeliveryPartner":0.72}
    band_y = {"Customer":(0.55,0.95),"Order":(0.30,0.95),"Product":(0.55,0.95),
               "Store":(0.05,0.28),"DeliveryPartner":(0.05,0.28)}
    buckets: dict = {}
    for n in nodes:
        buckets.setdefault(n["type"],[]).append(n["id"])
    pos = {}
    for ntype,ids in buckets.items():
        cx=col_x.get(ntype,0.5); ylo,yhi=band_y.get(ntype,(0.2,0.8)); n_ids=len(ids)
        for i,nid in enumerate(ids):
            y=(ylo+(yhi-ylo)*(i/max(n_ids-1,1))) if n_ids>1 else (ylo+yhi)/2
            pos[nid]=(cx+random.uniform(-0.035,0.035), y)
    return pos


def build_graph_figure(nodes, edges, title="Knowledge Graph"):
    if not nodes:
        fig=go.Figure(); fig.update_layout(title="No data",height=500); return fig
    pos=_layout_positions(nodes)
    annotations=[]
    for e in edges:
        src,tgt,rel=e["source"],e["target"],e["rel"]
        if src not in pos or tgt not in pos: continue
        x0,y0=pos[src]; x1,y1=pos[tgt]; color=REL_COLORS.get(rel,"#999")
        annotations.append(dict(x=x1,y=y1,ax=x0,ay=y0,xref="x",yref="y",axref="x",ayref="y",
            showarrow=True,arrowhead=3,arrowsize=1.5,arrowwidth=1.8,arrowcolor=color,opacity=0.72))
        annotations.append(dict(x=(x0+x1)/2,y=(y0+y1)/2,text=f"<b>{rel}</b>",showarrow=False,
            font=dict(size=8,color=color),bgcolor="rgba(255,255,255,0.85)",
            bordercolor=color,borderwidth=1,borderpad=2,opacity=0.9))
    for cx,lbl,lc in [(0.08,"👤 Customers","#005F02"),(0.50,"📦 Orders","#427A43"),(0.92,"🛍️ Products","#b8a050")]:
        annotations.append(dict(x=cx,y=1.04,xref="x",yref="paper",text=f"<b>{lbl}</b>",
            showarrow=False,font=dict(size=11,color=lc),bgcolor="rgba(242,227,187,0.75)",
            bordercolor=lc,borderwidth=1,borderpad=4))
    icons={"Customer":"👤","Order":"📦","Product":"🛍️","Store":"🏪","DeliveryPartner":"🚚"}
    buckets: dict = {}
    for n in nodes: buckets.setdefault(n["type"],[]).append(n)
    traces=[]
    for ntype,ns in buckets.items():
        xs=[pos[n["id"]][0] for n in ns if n["id"] in pos]
        ys=[pos[n["id"]][1] for n in ns if n["id"] in pos]
        texts=[n["id"] for n in ns if n["id"] in pos]
        traces.append(go.Scatter(x=xs,y=ys,mode="markers+text",
            name=f"{icons.get(ntype,'')} {ntype}",
            marker=dict(size=ns[0]["size"],color=ns[0]["color"],
                        line=dict(color="white",width=2.5),opacity=0.93),
            text=texts,textposition="top center",
            textfont=dict(size=8,color="#1a2e1a"),
            hovertemplate=f"<b>%{{text}}</b><br>Type:{ntype}<extra></extra>"))
    fig=go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=title,font=dict(family="DM Serif Display",size=18,color="#005F02")),
        showlegend=True,
        legend=dict(orientation="h",yanchor="bottom",y=-0.14,xanchor="center",x=0.5,
                    font=dict(size=11),bgcolor="rgba(242,227,187,0.7)",
                    bordercolor="#C0B87A",borderwidth=1),
        xaxis=dict(showgrid=False,zeroline=False,showticklabels=False,range=[-0.05,1.05]),
        yaxis=dict(showgrid=False,zeroline=False,showticklabels=False,range=[-0.05,1.10]),
        height=620,paper_bgcolor="rgba(242,227,187,0.18)",
        plot_bgcolor="rgba(255,255,255,0.55)",
        margin=dict(l=20,r=20,t=70,b=70),annotations=annotations)
    return fig


# ============================================================
# CHATBOT
# ============================================================
def get_offline_response(msg: str) -> str:
    m=msg.lower(); d=load_data()
    cust=d["customers"]; ords=d["orders"]; prods=d["products"]
    stores=d["stores"]; dps=d["delivery_partners"]; items=d["order_items"]
    tc=len(cust); to=len(ords); tp=len(prods); ts=len(stores); tdp=len(dps)
    rev=ords["total_amount"].sum()
    if any(w in m for w in ["hello","hi","hey","start"]):
        return "Hello! I am **Hora** 👋 your E-Commerce AI Assistant!\n\nAsk me about customers, orders, products, revenue, or the Neo4j graph!"
    if any(w in m for w in ["neo4j","graph","cypher","relationship"]):
        return "🕸️ **Neo4j Knowledge Graph**\n\nExplore entity relationships on the **Knowledge Graph** page!\n\n• Customer → PLACED → Order\n• Order → CONTAINS → Product\n• Order → FROM → Store\n• Order → DELIVERED_BY → DeliveryPartner"
    if "customer" in m:
        if any(w in m for w in ["how many","total","count"]):
            return f"👥 **Total Customers**: **{tc}**"
        top=cust["city"].value_counts().head(3)
        return f"👥 **Customers**: **{tc}**\n\nTop Cities:\n"+"\n".join(f"• {c}: {n}" for c,n in top.items())
    if "order" in m:
        if "status" in m:
            sc=ords["status"].value_counts()
            return "📦 **Order Status**\n\n"+"\n".join(f"• {s}: {n}" for s,n in sc.items())
        avg=rev/to if to else 0
        return f"📦 **Orders**: **{to}** | Revenue: **₹{rev:,.2f}** | Avg: **₹{avg:,.2f}**"
    if "product" in m:
        if any(w in m for w in ["top","best","popular"]):
            merged=items.merge(prods,on="product_id")
            top=merged.groupby("product_name")["quantity"].sum().sort_values(ascending=False).head(5)
            return "🛍️ **Top 5 Products**\n\n"+"\n".join(f"{i+1}. {p}: {q} units" for i,(p,q) in enumerate(top.items()))
        return f"🛍️ **Products**: **{tp}** | Categories: **{prods['category'].nunique()}** | Avg Rating: **{prods['rating'].mean():.1f}** ⭐"
    if "store" in m:
        return f"🏪 **Stores**: **{ts}**"
    if any(w in m for w in ["delivery","partner"]):
        return f"🚚 **Delivery Partners**: **{tdp}** | Avg Rating: **{dps['rating'].mean():.1f}** ⭐"
    if any(w in m for w in ["revenue","sales","money"]):
        return f"💰 **Revenue**: **₹{rev:,.2f}** from **{to}** orders"
    if any(w in m for w in ["stats","overview","summary","everything"]):
        return (f"📊 **Overview**\n\n• Customers: **{tc}**\n• Orders: **{to}**\n"
                f"• Products: **{tp}**\n• Stores: **{ts}**\n• Partners: **{tdp}**\n"
                f"• Revenue: **₹{rev:,.2f}**")
    if any(w in m for w in ["thank","thanks"]):
        return "You're welcome! 😊"
    if any(w in m for w in ["bye","goodbye"]):
        return "Goodbye! 👋"
    return "I'm **Hora** 🤖 Try: *show statistics*, *top products*, *order status*, *revenue*, or *graph*"


# ============================================================
# PAGES
# ============================================================

def display_header():
    st.markdown("""
    <div class='header-box'>
      <h1>🛒 E-Commerce Analytics Hub</h1>
      <h4>Real-Time Business Intelligence · Knowledge Graph · AI Search</h4>
    </div>""", unsafe_allow_html=True)


def display_kpis():
    d=load_data()
    vals=[len(d["customers"]),len(d["orders"]),len(d["products"]),
          len(d["stores"]),len(d["delivery_partners"])]
    lbls=["Total Customers","Total Orders","Total Products","Total Stores","Delivery Partners"]
    stys=["kpi1","kpi2","kpi3","kpi4","kpi5"]
    icos=["👥","📦","🛍️","🏪","🚚"]
    cols=st.columns(5)
    for col,val,lbl,sty,ico in zip(cols,vals,lbls,stys,icos):
        with col:
            st.markdown(f"<div class='kpi-card {sty}'><h2>{ico} {val}</h2><p>{lbl}</p></div>",
                        unsafe_allow_html=True)


def display_analytics():
    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("📊 Business Analytics")
    d=load_data(); orders=d["orders"]; items=d["order_items"]
    products=d["products"]; stores=d["stores"]; dps=d["delivery_partners"]

    st.markdown("### 📅 Daily Order Trends")
    opd=orders.groupby(orders["order_date"].dt.date).size().reset_index(name="Orders")
    opd.columns=["Date","Orders"]
    fig1=px.line(opd,x="Date",y="Orders",markers=True,title="Daily Orders",
                 color_discrete_sequence=["#427A43"])
    fig1.update_layout(height=350,paper_bgcolor="rgba(242,227,187,0.3)",
                       plot_bgcolor="rgba(242,227,187,0.3)",
                       font=dict(family="DM Sans",color="#1a2e1a"),
                       title_font=dict(family="DM Serif Display",color="#005F02"))
    st.plotly_chart(fig1,use_container_width=True)

    c1,c2=st.columns(2)
    with c1:
        st.markdown("### 🏆 Top 10 Products by Units Sold")
        merged=items.merge(products,on="product_id")
        top=merged.groupby("product_name")["quantity"].sum().sort_values(ascending=False).head(10)
        fig2=px.bar(x=top.values,y=top.index,orientation="h",
                    labels={"x":"Quantity","y":"Product"},
                    color=top.values,color_continuous_scale=["#C0B87A","#427A43","#005F02"])
        fig2.update_layout(height=380,showlegend=False,
                           paper_bgcolor="rgba(242,227,187,0.3)",plot_bgcolor="rgba(242,227,187,0.3)",
                           font=dict(family="DM Sans",color="#1a2e1a"))
        st.plotly_chart(fig2,use_container_width=True)
    with c2:
        st.markdown("### 💰 Revenue by Store")
        sr=orders.groupby("store_id")["total_amount"].sum().reset_index()
        sr=sr.merge(stores[["store_id","store_name"]],on="store_id",how="left")
        fig3=px.pie(sr,values="total_amount",names="store_name",title="Revenue Distribution",
                    color_discrete_sequence=["#005F02","#427A43","#C0B87A","#F2E3BB",
                                             "#5a9e5c","#8ab88b","#e8d4a0","#003a02"])
        fig3.update_layout(height=380,paper_bgcolor="rgba(242,227,187,0.3)",
                           font=dict(family="DM Sans",color="#1a2e1a"))
        st.plotly_chart(fig3,use_container_width=True)

    st.markdown("### 🚚 Delivery Partner — Orders vs Rating")
    po=orders.groupby("delivery_partner_id").size().reset_index(name="total_orders")
    pd_data=dps.merge(po,left_on="partner_id",right_on="delivery_partner_id",how="left")
    pd_data["total_orders"]=pd_data["total_orders"].fillna(0)
    fig4=go.Figure()
    fig4.add_trace(go.Scatter(x=pd_data["total_orders"],y=pd_data["rating"],
        mode="markers+text",
        marker=dict(size=pd_data["total_orders"]*2+8,color=pd_data["rating"],
                    colorscale=[[0,"#C0B87A"],[0.5,"#427A43"],[1,"#005F02"]],showscale=True),
        text=pd_data["name"],textposition="top center",
        hovertemplate="<b>%{text}</b><br>Orders:%{x}<br>Rating:%{y}<extra></extra>"))
    fig4.update_layout(title="Orders vs Rating",xaxis_title="Total Orders",yaxis_title="Rating",
                       height=380,paper_bgcolor="rgba(242,227,187,0.3)",
                       plot_bgcolor="rgba(242,227,187,0.3)",
                       font=dict(family="DM Sans",color="#1a2e1a"))
    st.plotly_chart(fig4,use_container_width=True)
    st.markdown("</div>",unsafe_allow_html=True)


def page_knowledge_graph():
    st.markdown("<div class='section-neo4j'>",unsafe_allow_html=True)
    st.subheader("🕸️ Knowledge Graph — Entity Relationships")

    driver, err = get_driver()
    neo4j_ok = driver is not None
    st.session_state["neo4j_connected"] = neo4j_ok

    if neo4j_ok:
        st.markdown("<span class='status-badge badge-connected'>● Connected to Neo4j Aura</span>",
                    unsafe_allow_html=True)
    else:
        st.markdown("<span class='status-badge badge-demo'>● Demo Mode — connect via sidebar</span>",
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='margin-bottom:16px;'>
      <b style='font-family:DM Serif Display,serif;color:#005F02;'>Node Types:</b><br>
      <span class='graph-legend-pill'><span class='dot' style='background:#005F02'></span> Customer</span>
      <span class='graph-legend-pill'><span class='dot' style='background:#427A43'></span> Order</span>
      <span class='graph-legend-pill'><span class='dot' style='background:#C0B87A'></span> Product</span>
      <span class='graph-legend-pill'><span class='dot' style='background:#8B4513'></span> Store</span>
      <span class='graph-legend-pill'><span class='dot' style='background:#1a6b8a'></span> Delivery Partner</span>
    </div>""", unsafe_allow_html=True)

    cf1,cf2,cf3=st.columns([2,2,1])
    with cf1:
        view_mode=st.selectbox("🗺️ View Mode",
                               ["Core Path (Customer→Order→Product)","Full Graph"])
    with cf2:
        filter_type=st.selectbox("🔍 Highlight Node Type",
                                 ["All","Customer","Order","Product","Store","DeliveryPartner"])
    with cf3:
        max_nodes=st.slider("Max Nodes",10,80,40)

    nodes,edges=[],[]
    if neo4j_ok:
        try:
            if "Core" in view_mode:
                q="""
                MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
                WITH c,o,p LIMIT 150
                RETURN 'Customer' AS src_type,c.id AS src_id,'PLACED' AS rel,
                       'Order' AS tgt_type,o.id AS tgt_id
                UNION
                MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
                WITH o,p LIMIT 150
                RETURN 'Order' AS src_type,o.id AS src_id,'CONTAINS' AS rel,
                       'Product' AS tgt_type,p.id AS tgt_id
                """
            else:
                q="""
                MATCH (n)-[r]->(m)
                WHERE n.id IS NOT NULL AND m.id IS NOT NULL
                RETURN labels(n)[0] AS src_type,n.id AS src_id,
                       type(r) AS rel,labels(m)[0] AS tgt_type,m.id AS tgt_id
                LIMIT 300
                """
            rows, err2 = run_cypher(q)
            tc={"Customer":"#005F02","Order":"#427A43","Product":"#C0B87A",
                "Store":"#8B4513","DeliveryPartner":"#1a6b8a"}
            ts={"Customer":20,"Order":16,"Product":14,"Store":13,"DeliveryPartner":13}
            nodes_set: set = set()
            for rec in rows:
                st_=str(rec.get("src_type") or ""); tt=str(rec.get("tgt_type") or "")
                si=str(rec.get("src_id") or "");   ti=str(rec.get("tgt_id") or "")
                if not si or not ti: continue
                if filter_type!="All" and filter_type not in (st_,tt): continue
                nodes_set.add((si,st_)); nodes_set.add((ti,tt))
                edges.append({"source":si,"target":ti,"rel":rec.get("rel","")})
            nodes=[{"id":nid,"type":ntype,"color":tc.get(ntype,"#999"),"size":ts.get(ntype,12)}
                   for nid,ntype in nodes_set]
            if not nodes:
                st.info("No data in Neo4j — run entity_extractor.py and relationship_extractor.py first.")
                nodes,edges=generate_demo_graph(filter_type,view_mode,max_nodes)
        except Exception as e:
            st.warning(f"Graph fetch error: {e}")
            nodes,edges=generate_demo_graph(filter_type,view_mode,max_nodes)
    else:
        nodes,edges=generate_demo_graph(filter_type,view_mode,max_nodes)

    fig=build_graph_figure(nodes[:max_nodes],edges,title="E-Commerce Knowledge Graph")
    st.plotly_chart(fig,use_container_width=True)

    if edges:
        st.markdown("### 📋 Relationship Summary")
        rc: dict={}
        for e in edges: rc[e["rel"]]=rc.get(e["rel"],0)+1
        rel_df=pd.DataFrame(list(rc.items()),columns=["Relationship","Count"]).sort_values("Count",ascending=False)
        ct1,ct2=st.columns([1,2])
        with ct1: st.dataframe(rel_df,use_container_width=True,hide_index=True)
        with ct2:
            fig_r=px.bar(rel_df,x="Count",y="Relationship",orientation="h",
                         color="Count",color_continuous_scale=["#C0B87A","#427A43","#005F02"],
                         title="Relationship Distribution")
            fig_r.update_layout(height=250,showlegend=False,
                                paper_bgcolor="rgba(242,227,187,0.3)",
                                plot_bgcolor="rgba(242,227,187,0.3)")
            st.plotly_chart(fig_r,use_container_width=True)
    st.markdown("</div>",unsafe_allow_html=True)


def page_graph_query():
    st.markdown("<div class='section-neo4j'>",unsafe_allow_html=True)
    st.subheader("🔮 Natural Language → Cypher Query")
    st.caption("Ask in plain English — powered by LLaMA 3.3 via Groq · Results from Neo4j Aura")

    groq_ok  = bool(os.getenv("GROQ_API_KEY")) and GROQ_AVAILABLE
    driver,_ = get_driver()
    neo4j_ok = driver is not None
    st.session_state["neo4j_connected"] = neo4j_ok

    c1,c2=st.columns(2)
    with c1:
        st.markdown(f"<span class='status-badge {'badge-connected' if groq_ok else 'badge-error'}'>"
                    f"{'● Groq LLM Ready' if groq_ok else '● Groq Not Configured'}</span>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"<span class='status-badge {'badge-connected' if neo4j_ok else 'badge-demo'}'>"
                    f"{'● Neo4j Connected' if neo4j_ok else '● Neo4j Not Connected'}</span>",
                    unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("📐 Graph Schema Reference"):
        st.markdown("""
**Nodes:** `Customer(id,name)` · `Order(id,date,status)` · `Product(id,name,price,category)` · `Store(id,name)` · `DeliveryPartner(id,name)`

**Relationships:**
```
(Customer)-[:PLACED]->(Order)
(Order)-[:CONTAINS]->(Product)
(Order)-[:FROM]->(Store)
(Order)-[:DELIVERED_BY]->(DeliveryPartner)
(Customer)-[:ORDERED_PRODUCT]->(Product)
(Customer)-[:ORDERED_FROM]->(Store)
(Customer)-[:SERVICED_BY]->(DeliveryPartner)
(Store)-[:SOLD_PRODUCT]->(Product)
(DeliveryPartner)-[:DELIVERED_PRODUCT]->(Product)
(DeliveryPartner)-[:DELIVERED_TO_STORE]->(Store)
```
> **Note:** Order has no price/amount — revenue = `sum(p.price)` via CONTAINS
        """)

    st.markdown("**💡 Try these questions:**")
    samples=[
        "Which customers placed the most orders?",
        "Which stores have the highest revenue?",
        "Which delivery partner handled the most deliveries?",
        "What are the top 10 products by order count?",
        "How much has each customer spent in total?",
        "What are the most popular product categories?",
    ]
    cols=st.columns(3)
    for i,q in enumerate(samples):
        with cols[i%3]:
            if st.button(f"💬 {q[:38]}…",key=f"sq_{i}",use_container_width=True):
                st.session_state["nl_query_input"]=q

    nl_query=st.text_area("🗣️ Your Question:",
                          value=st.session_state.get("nl_query_input",""),
                          height=80,placeholder="e.g. Which customers placed the most orders?",
                          key="nl_query_area")

    cr,cc=st.columns([1,4])
    with cr:
        run_btn=st.button("🚀 Generate & Run",use_container_width=True,type="primary")
    with cc:
        if st.button("🗑️ Clear",use_container_width=True):
            for k in ("cypher_result","cypher_query","cypher_error","nl_query_input"):
                st.session_state.pop(k,None)
            st.rerun()

    if run_btn and nl_query.strip():
        if not neo4j_ok:
            st.error("❌ Neo4j not connected — fill in credentials in the sidebar first.")
        elif not groq_ok:
            st.error("❌ GROQ_API_KEY not set in .env file.")
        else:
            with st.spinner("🤖 Generating Cypher…"):
                cypher=nl_to_cypher(nl_query.strip())
                st.session_state["cypher_query"]=cypher
            with st.spinner("🔍 Running against Neo4j Aura…"):
                rows,err=run_cypher(cypher)
                st.session_state["cypher_result"]=rows
                st.session_state["cypher_error"]=err

    if st.session_state.get("cypher_query"):
        st.markdown("**🧬 Generated Cypher:**")
        st.markdown(f"<div class='cypher-box'>{st.session_state['cypher_query']}</div>",
                    unsafe_allow_html=True)
        st.download_button("⬇️ Download Cypher",st.session_state["cypher_query"],
                           file_name="query.cypher",mime="text/plain")

    if st.session_state.get("cypher_error"):
        st.warning(f"⚠️ {st.session_state['cypher_error']}")

    if st.session_state.get("cypher_result") is not None:
        rows=st.session_state["cypher_result"]
        if rows:
            st.success(f"✅ {len(rows)} row{'s' if len(rows)!=1 else ''} returned")
            try:
                st.dataframe(pd.DataFrame(rows),use_container_width=True,height=300)
            except Exception:
                for row in rows[:20]:
                    st.markdown(f"<div class='result-card'>{json.dumps(row,default=str)}</div>",
                                unsafe_allow_html=True)
        else:
            st.info("Query ran but returned no results — check your data or rephrase the question.")

    st.markdown("</div>",unsafe_allow_html=True)


def page_product_search():
    st.markdown("<div class='section'>",unsafe_allow_html=True)
    st.subheader("🔍 Product Search")
    d=load_data(); products=d["products"]
    suggestions=["electronics","Nike","Samsung","sports","books"]
    scols=st.columns(5)
    for i,sug in enumerate(suggestions):
        with scols[i]:
            if st.button(sug,key=f"sug_{i}",use_container_width=True):
                st.session_state["search_input"]=sug
    search_q=st.text_input("🛒 Search Products:",
                           value=st.session_state.get("search_input",""),
                           placeholder="e.g. electronics under ₹2000",
                           key="search_input_box")
    cr,ck=st.columns([3,1])
    with cr: search_btn=st.button("🔍 Search",use_container_width=True,type="primary")
    with ck: top_k=st.selectbox("Top K",[3,5,10],index=1)

    if search_btn and search_q.strip():
        q_lower=search_q.lower()
        mask=(products["product_name"].str.lower().str.contains(q_lower,na=False)|
              products["brand"].str.lower().str.contains(q_lower,na=False)|
              products["category"].str.lower().str.contains(q_lower,na=False))
        filtered=products[mask].head(top_k)
        st.session_state["search_sources"]=filtered.to_dict("records")
        st.session_state["search_answer"]=(f"Found {len(filtered)} product(s) matching '{search_q}'."
                                           if len(filtered) else f"No products found for '{search_q}'.")

    if st.session_state.get("search_answer"):
        st.info(st.session_state["search_answer"])
    for i,src in enumerate(st.session_state.get("search_sources",[]),1):
        name=src.get("product_name",f"Product {i}"); price=src.get("price","N/A")
        cat=src.get("category","");  brand=src.get("brand","")
        rating=src.get("rating",""); stock=src.get("stock",0)
        stars="⭐"*int(float(rating)) if rating else ""
        in_stock="In Stock" if int(stock or 0)>0 else "Out of Stock"
        stock_color="#005F02" if int(stock or 0)>50 else "#856404"
        st.markdown(f"""
        <div class='product-card'>
          <div style='display:flex;justify-content:space-between;align-items:start'>
            <div>
              <b style='font-size:15px'>{i}. {name}</b>
              <div style='color:#5a7a5a;font-size:12px;margin-top:2px'>{brand} · {cat}</div>
              <div>{stars} {rating}</div>
            </div>
            <div style='text-align:right'>
              <div style='font-size:18px;font-weight:700;color:#005F02'>₹{price}</div>
              <div style='font-size:11px;color:{stock_color};font-weight:600'>{in_stock}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)


def page_customers():
    st.markdown("<div class='section'>",unsafe_allow_html=True)
    st.subheader("👥 Customers")
    df=load_data()["customers"]
    c1,c2,c3=st.columns(3)
    with c1: nq=st.text_input("🔍 Search Name","")
    with c2: cf=st.multiselect("🏙️ City",df["city"].unique())
    with c3: sf=st.multiselect("📍 State",df["state"].unique())
    out=df.copy()
    if nq:  out=out[out["name"].str.contains(nq,case=False,na=False)]
    if cf:  out=out[out["city"].isin(cf)]
    if sf:  out=out[out["state"].isin(sf)]
    st.dataframe(out,use_container_width=True,height=420)
    st.caption(f"Showing {len(out)} of {len(df)} customers")
    st.markdown("</div>",unsafe_allow_html=True)


def page_orders():
    st.markdown("<div class='section'>",unsafe_allow_html=True)
    st.subheader("📦 Orders")
    df=load_data()["orders"]
    c1,c2,c3=st.columns(3)
    with c1: sf=st.multiselect("📊 Status",df["status"].unique())
    with c2: cuf=st.multiselect("👤 Customer",df["customer_id"].unique())
    with c3: dr=st.date_input("📅 Date Range",value=[])
    out=df.copy()
    if sf:  out=out[out["status"].isin(sf)]
    if cuf: out=out[out["customer_id"].isin(cuf)]
    if len(dr)==2:
        out=out[(out["order_date"].dt.date>=dr[0])&(out["order_date"].dt.date<=dr[1])]
    st.dataframe(out,use_container_width=True,height=420)
    st.caption(f"Showing {len(out)} of {len(df)} orders | Revenue: ₹{out['total_amount'].sum():,.2f}")
    st.markdown("</div>",unsafe_allow_html=True)


def page_products():
    st.markdown("<div class='section'>",unsafe_allow_html=True)
    st.subheader("🛍️ Products")
    df=load_data()["products"]
    c1,c2,c3,c4=st.columns(4)
    with c1: pq=st.text_input("🔍 Search","")
    with c2: bf=st.multiselect("🏷️ Brand",df["brand"].unique())
    with c3: cf=st.multiselect("📂 Category",df["category"].unique())
    with c4: mr=st.slider("⭐ Min Rating",0.0,5.0,0.0,0.1)
    out=df.copy()
    if pq: out=out[out["product_name"].str.contains(pq,case=False,na=False)]
    if bf: out=out[out["brand"].isin(bf)]
    if cf: out=out[out["category"].isin(cf)]
    if mr: out=out[out["rating"]>=mr]
    st.dataframe(out,use_container_width=True,height=420)
    st.caption(f"Showing {len(out)} of {len(df)} products")
    st.markdown("</div>",unsafe_allow_html=True)


def page_stores():
    st.markdown("<div class='section'>",unsafe_allow_html=True)
    st.subheader("🏪 Stores")
    df=load_data()["stores"]
    c1,c2=st.columns(2)
    with c1: cf=st.multiselect("🏙️ City",df["city"].unique())
    with c2: sf=st.multiselect("📍 State",df["state"].unique())
    out=df.copy()
    if cf: out=out[out["city"].isin(cf)]
    if sf: out=out[out["state"].isin(sf)]
    st.dataframe(out,use_container_width=True,height=420)
    st.caption(f"Showing {len(out)} of {len(df)} stores")
    st.markdown("</div>",unsafe_allow_html=True)


def page_delivery_partners():
    st.markdown("<div class='section'>",unsafe_allow_html=True)
    st.subheader("🚚 Delivery Partners")
    df=load_data()["delivery_partners"]
    c1,c2=st.columns(2)
    with c1: vf=st.multiselect("🚗 Vehicle",df["vehicle_type"].unique())
    with c2: mr=st.slider("⭐ Min Rating",0.0,5.0,0.0,0.1)
    out=df.copy()
    if vf: out=out[out["vehicle_type"].isin(vf)]
    if mr: out=out[out["rating"]>=mr]
    avg=out["rating"].mean() if len(out) else 0
    st.dataframe(out,use_container_width=True,height=420)
    st.caption(f"Showing {len(out)} of {len(df)} partners | Avg Rating: {avg:.2f}/5.0")
    st.markdown("</div>",unsafe_allow_html=True)


# ============================================================
# CHATBOT PANEL
# ============================================================
def display_chatbot_panel():
    st.markdown("""
    <div class='chat-header'>
      <h3>🌿 Hora – ChatBot</h3>
      <p><span style='display:inline-block;width:8px;height:8px;background:#6fcf6f;
         border-radius:50%;margin-right:5px;'></span>Online · Ready to Help!</p>
    </div>""", unsafe_allow_html=True)

    if st.button("✕ Close Chat",key="close_chat",use_container_width=True):
        st.session_state.chat_open=False; st.rerun()

    with st.container(height=360):
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                st.caption(f"🕐 {msg.get('time','')}")

    st.markdown("**Quick Actions:**")
    quick=[("📊 Overview","show me complete statistics overview"),
           ("👥 Customers","how many customers do we have"),
           ("📦 Orders","tell me about our orders"),
           ("🛍️ Top Products","what are the top products"),
           ("💰 Revenue","show revenue summary"),
           ("🕸️ Graph Info","tell me about the neo4j knowledge graph")]
    cols=st.columns(2)
    for idx,(lbl,q) in enumerate(quick):
        with cols[idx%2]:
            if st.button(lbl,key=f"quick_{idx}",use_container_width=True):
                now=datetime.datetime.now().strftime("%H:%M")
                st.session_state.chat_messages.append({"role":"user","content":q,"time":now})
                st.session_state.chat_messages.append({"role":"assistant",
                                                        "content":get_offline_response(q),"time":now})
                st.rerun()

    user_input=st.chat_input("💬 Type your message…",key="chat_input_main")
    if user_input and user_input.strip():
        now=datetime.datetime.now().strftime("%H:%M")
        st.session_state.chat_messages.append({"role":"user","content":user_input,"time":now})
        st.session_state.chat_messages.append({"role":"assistant",
                                                "content":get_offline_response(user_input),"time":now})
        st.rerun()

    c1,c2=st.columns(2)
    with c1:
        if st.button("🗑️ Clear",key="clear_chat",use_container_width=True):
            st.session_state.chat_messages=[{"role":"assistant",
                "content":"Hello! I am **Hora** 👋","time":datetime.datetime.now().strftime("%H:%M")}]
            st.rerun()
    with c2:
        if st.button("🔄 Restart",key="restart_chat",use_container_width=True):
            st.session_state.chat_messages=[{"role":"assistant",
                "content":"I'm back! 😊","time":datetime.datetime.now().strftime("%H:%M")}]
            st.rerun()


# ============================================================
# SIDEBAR
# ============================================================
def display_sidebar():
    with st.sidebar:
        st.header("🧭 Navigation")
        pages={"Dashboard":"📊","Knowledge Graph":"🕸️","Graph Query":"🔮",
               "Product Search":"🔍","Customers":"👥","Orders":"📦",
               "Products":"🛍️","Stores":"🏪","Delivery Partners":"🚚","Analytics":"📈"}
        for page,icon in pages.items():
            active=st.session_state.current_page==page
            if st.button(f"{icon} {page}",key=f"nav_{page}",use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.current_page=page; st.rerun()

        st.divider()
        st.header("🔌 Neo4j Aura")

        ss=st.session_state
        if ss.get("neo4j_connected"):
            st.success("✅ Connected!")
            st.caption(f"🌐 {ss.get('neo4j_uri','')[:45]}…")
            if st.button("🔌 Disconnect",use_container_width=True,key="neo4j_disconnect"):
                ss["neo4j_uri"]=""; ss["neo4j_password"]=""
                ss["neo4j_connected"]=False
                _build_driver.clear(); st.rerun()
        else:
            uri_val  = st.text_input("URI",value=ss.get("neo4j_uri",""),
                                     placeholder="neo4j+s://xxxxxxxx.databases.neo4j.io",
                                     key="neo4j_uri_inp")
            user_val = st.text_input("Username",value=ss.get("neo4j_user","neo4j"),
                                     key="neo4j_user_inp")
            pwd_val  = st.text_input("Password",value="",type="password",
                                     placeholder="Aura password",key="neo4j_pwd_inp")

            if st.button("🚀 Connect",use_container_width=True,type="primary",key="neo4j_connect_btn"):
                if not uri_val.strip():
                    st.error("Enter your Neo4j Aura URI.")
                elif not pwd_val.strip():
                    st.error("Enter your password.")
                else:
                    ss["neo4j_uri"]      = uri_val.strip()
                    ss["neo4j_user"]     = user_val.strip() or "neo4j"
                    ss["neo4j_password"] = pwd_val.strip()
                    _build_driver.clear()   # force fresh connection
                    with st.spinner("Connecting…"):
                        driver, err = get_driver()
                    if driver:
                        ss["neo4j_connected"]=True
                        st.success("✅ Connected!"); st.rerun()
                    else:
                        ss["neo4j_connected"]=False
                        st.error(f"❌ {err}")

        st.divider()
        st.header("⚙️ Platform Health")
        st.success("✅ Data Layer  : Active")
        st.success("✅ Charts      : Active")
        st.success("✅ Hora Bot    : Active")
        groq_st="🟢 Ready" if (GROQ_AVAILABLE and os.getenv("GROQ_API_KEY")) else "🟡 Not Set"
        st.info(f"Groq LLM  : {groq_st}")

        if st.button("🔄 Refresh Data",use_container_width=True):
            st.cache_data.clear(); st.rerun()

        st.divider()
        with st.expander("📖 About"):
            st.info("**E-Commerce Analytics Hub**\n\n"
                    "• 📊 Dashboard\n• 🕸️ Neo4j Graph\n• 🔮 NL→Cypher\n"
                    "• 🔍 Product Search\n• 🌿 Hora Chatbot\n\n")


# ============================================================
# ROUTING
# ============================================================
def route_page():
    p=st.session_state.current_page
    if   p=="Dashboard":        display_header(); display_kpis(); display_analytics()
    elif p=="Knowledge Graph":  page_knowledge_graph()
    elif p=="Graph Query":      page_graph_query()
    elif p=="Product Search":   page_product_search()
    elif p=="Customers":        page_customers()
    elif p=="Orders":           page_orders()
    elif p=="Products":         page_products()
    elif p=="Stores":           page_stores()
    elif p=="Delivery Partners":page_delivery_partners()
    elif p=="Analytics":        display_analytics()


# ============================================================
# MAIN
# ============================================================
def main():
    initialize_session()
    display_sidebar()

    if st.session_state.chat_open:
        mc,cc=st.columns([2.2,1])
        with mc: route_page()
        with cc: display_chatbot_panel()
    else:
        route_page()
        _,_,bc=st.columns([10,1,1])
        with bc:
            if st.button("💬",key="open_chat_btn",help="Chat with Hora"):
                st.session_state.chat_open=True; st.rerun()

    st.markdown(
        "<center style='color:#427A43;margin-top:30px;font-family:DM Sans,sans-serif;font-size:.85rem;'>"
        "© 2026 E-Commerce Analytics Hub &nbsp;|&nbsp; Powered by 🌿 Hora AI &nbsp;|&nbsp;"
        " 🕸️ Neo4j &nbsp;|&nbsp; 🔮 Groq LLaMA &nbsp;|&nbsp; Developed by Sriram"
        "</center>", unsafe_allow_html=True)


if __name__=="__main__":
    main()
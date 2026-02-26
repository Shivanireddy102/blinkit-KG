# ============================================================
# ✅ NEO4J AURA CONNECTION FIX
# ============================================================
# ISSUES FIXED:
#   1. Use neo4j+s:// scheme (required for Aura, NOT bolt://)
#   2. Single connection attempt per page load (no duplicate calls)
#   3. Proper session caching in st.session_state
#   4. Correct Aura Free instance URI format
#   5. Driver/session lifecycle managed safely
#   6. .env support with correct variable names
# ============================================================

import os
import streamlit as st

# ── Try importing the Neo4j driver ──────────────────────────
try:
    from neo4j import GraphDatabase, exceptions as neo4j_exc
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


# ============================================================
# CONNECTION HELPER  — returns (driver, session) or (None, err_str)
# ============================================================
@st.cache_resource(show_spinner=False)          # ← cache so we don't reconnect on every rerun
def get_neo4j_driver(uri: str, user: str, password: str):
    """
    Create and verify a Neo4j Aura driver.
    Aura Free URIs look like:  neo4j+s://<uid>.databases.neo4j.io
    Never use bolt:// for Aura — it requires encrypted neo4j+s://.
    Returns (driver, None) on success or (None, error_message) on failure.
    """
    if not NEO4J_AVAILABLE:
        return None, "neo4j Python package not installed. Run: pip install neo4j"

    if not uri or not password:
        return None, "Neo4j URI and password are required."

    # ── Normalise URI — enforce neo4j+s:// for Aura ───────
    # Aura REQUIRES neo4j+s:// (TLS + routing).
    # bolt://, neo4j://, or bolt+s:// all cause "Unable to retrieve routing information".
    uri = uri.strip().rstrip("/")

    if "databases.neo4j.io" in uri:
        # Strip any existing scheme and force neo4j+s://
        for scheme in ("bolt+s://", "bolt+routing://", "bolt://", "neo4j+s://", "neo4j://"):
            if uri.startswith(scheme):
                uri = uri[len(scheme):]
                break
        uri = f"neo4j+s://{uri}"

    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            # Aura-specific settings to avoid routing / timeout issues
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60,
        )
        driver.verify_connectivity()              # ← Aura Free may take ~2-3 s on cold start
        return driver, None
    except neo4j_exc.AuthError:
        return None, "Authentication failed — check your Neo4j username and password."
    except neo4j_exc.ServiceUnavailable as e:
        return None, (
            f"Cannot reach Neo4j Aura.\n"
            f"• Check the instance is running in console.neo4j.io\n"
            f"• URI used: {uri}\n"
            f"Detail: {e}"
        )
    except Exception as e:
        err = str(e)
        if "routing" in err.lower():
            return None, (
                f"Routing error — URI scheme is likely wrong.\n"
                f"URI used: {uri}\n"
                f"Make sure it starts with neo4j+s://\n"
                f"Detail: {err}"
            )
        return None, f"Neo4j connection error: {err}"


def get_neo4j_session():
    """
    Resolve credentials (sidebar form → env vars → fallback) and return
    (driver, session) or (None, error_str).

    Priority order for credentials:
      1. Values typed in the sidebar Connect panel (session_state)
      2. Environment variables / .env file
      3. Nothing → return (None, explanation)
    """
    # ── 1. Sidebar / form credentials ────────────────────
    uri      = st.session_state.get("neo4j_uri",      "").strip()
    user     = st.session_state.get("neo4j_user",     "neo4j").strip()
    password = st.session_state.get("neo4j_password", "").strip()

    # ── 2. Fall back to environment variables ────────────
    if not uri:
        uri = os.getenv("NEO4J_URI", "").strip()
    if not password:
        password = os.getenv("NEO4J_PASSWORD", "").strip()
    if not user or user == "neo4j":
        user = os.getenv("NEO4J_USER", "neo4j").strip()

    if not uri or not password:
        return None, (
            "No Neo4j credentials found.\n"
            "Either fill in the 🔌 Connect panel in the sidebar, or set "
            "NEO4J_URI / NEO4J_PASSWORD in your .env file.\n\n"
            "Your Aura Free URI looks like:\n"
            "  neo4j+s://<uid>.databases.neo4j.io"
        )

    driver, err = get_neo4j_driver(uri, user, password)
    if driver is None:
        return None, err

    try:
        session = driver.session(database="neo4j")   # Aura Free only has "neo4j" DB
        return driver, session
    except Exception as e:
        return None, f"Could not open Neo4j session: {e}"


def run_cypher(cypher: str) -> tuple[list, str | None]:
    """
    Run a Cypher query and return (rows, error).
    Opens a fresh session for each query to avoid stale-session issues on Aura.
    """
    driver, session_or_err = get_neo4j_session()
    if driver is None:
        return [], session_or_err

    try:
        result = session_or_err.run(cypher)
        rows = [dict(r) for r in result]
        return rows, None
    except Exception as e:
        return [], str(e)
    finally:
        try:
            session_or_err.close()
        except Exception:
            pass
        # NOTE: Don't close driver here — it's cached by @st.cache_resource


# ============================================================
# SIDEBAR CONNECT PANEL  — call this from your main sidebar
# ============================================================
def sidebar_neo4j_connect():
    """
    Renders the 🔌 Connect panel.
    Saves credentials to st.session_state so get_neo4j_session() picks them up.
    """
    with st.sidebar.expander("🔌 Neo4j Aura Connect", expanded=not st.session_state.get("neo4j_connected", False)):
        st.caption("Paste your **Aura Free** connection details below.")
        st.markdown(
            "URI format: `neo4j+s://<uid>.databases.neo4j.io`",
            help="Find this in the Neo4j Aura console under your instance's 'Connect' tab.",
        )

        uri_input = st.text_input(
            "URI",
            value=st.session_state.get("neo4j_uri", os.getenv("NEO4J_URI", "")),
            placeholder="neo4j+s://xxxxxxxx.databases.neo4j.io",
            key="_neo4j_uri_input",
        )
        user_input = st.text_input(
            "Username",
            value=st.session_state.get("neo4j_user", os.getenv("NEO4J_USER", "neo4j")),
            key="_neo4j_user_input",
        )
        pwd_input = st.text_input(
            "Password",
            value="",
            type="password",
            placeholder="Your Aura instance password",
            key="_neo4j_pwd_input",
        )

        if st.button("🔗 Connect", use_container_width=True, type="primary"):
            # Persist to session_state so get_neo4j_session() uses them
            st.session_state["neo4j_uri"]      = uri_input.strip()
            st.session_state["neo4j_user"]     = user_input.strip() or "neo4j"
            st.session_state["neo4j_password"] = pwd_input.strip()

            # Clear cached driver so it reconnects with new creds
            get_neo4j_driver.clear()

            # Test connection immediately
            with st.spinner("Connecting to Aura…"):
                driver, err = get_neo4j_driver(
                    st.session_state["neo4j_uri"],
                    st.session_state["neo4j_user"],
                    st.session_state["neo4j_password"],
                )

            if driver:
                st.session_state["neo4j_connected"] = True
                st.success("✅ Connected to Neo4j Aura!")
            else:
                st.session_state["neo4j_connected"] = False
                st.error(f"❌ Connection failed:\n{err}")

        # Show current status
        if st.session_state.get("neo4j_connected"):
            st.markdown("<span style='color:#005F02;font-weight:600'>● Connected</span>", unsafe_allow_html=True)
            if st.button("Disconnect", use_container_width=True):
                st.session_state["neo4j_connected"] = False
                st.session_state.pop("neo4j_uri", None)
                st.session_state.pop("neo4j_password", None)
                get_neo4j_driver.clear()
                st.rerun()


# ============================================================
# FIXED page_knowledge_graph  — single connection, no double-call
# ============================================================
def page_knowledge_graph():
    import pandas as pd
    import plotly.express as px

    st.markdown("<div class='section-neo4j'>", unsafe_allow_html=True)
    st.subheader("🕸️ Knowledge Graph — Entity Relationships")

    # ── ONE connection attempt per render ─────────────────
    driver, session_or_err = get_neo4j_session()
    neo4j_connected = driver is not None

    # Keep session_state in sync
    st.session_state["neo4j_connected"] = neo4j_connected

    if neo4j_connected:
        st.markdown(
            "<span class='status-badge badge-connected'>● Connected to Neo4j Aura</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<span class='status-badge badge-demo'>● Demo Mode — fill in the 🔌 Connect panel in the sidebar to use live data</span>",
            unsafe_allow_html=True,
        )
        if isinstance(session_or_err, str) and session_or_err:
            with st.expander("ℹ️ Connection details"):
                st.code(session_or_err, language="text")

    st.markdown("---")

    # Legend
    st.markdown("""
    <div style='margin-bottom:16px;'>
      <b style='font-family:DM Serif Display,serif;color:#005F02;'>Node Types:</b><br>
      <span class='graph-legend-pill'><span class='dot' style='background:#005F02'></span> Customer</span>
      <span class='graph-legend-pill'><span class='dot' style='background:#427A43'></span> Order</span>
      <span class='graph-legend-pill'><span class='dot' style='background:#C0B87A'></span> Product</span>
      <span class='graph-legend-pill'><span class='dot' style='background:#8B4513'></span> Store</span>
      <span class='graph-legend-pill'><span class='dot' style='background:#1a6b8a'></span> Delivery Partner</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Controls ──────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        view_mode = st.selectbox(
            "🗺️ View Mode",
            ["Core Path (Customer→Order→Product)", "Full Graph"],
        )
    with col_f2:
        filter_type = st.selectbox(
            "🔍 Highlight Node Type",
            ["All", "Customer", "Order", "Product", "Store", "DeliveryPartner"],
        )
    with col_f3:
        max_nodes = st.slider("Max Nodes", 10, 80, 40)

    # ── Fetch data ────────────────────────────────────────
    nodes, edges = [], []

    if neo4j_connected:
        try:
            if view_mode == "Core Path (Customer→Order→Product)":
                live_cypher = """
                MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
                WITH c, o, p LIMIT 150
                RETURN
                  'Customer' AS src_type, c.id AS src_id,
                  'PLACED'   AS rel,
                  'Order'    AS tgt_type, o.id  AS tgt_id
                UNION
                MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
                WITH o, p LIMIT 150
                RETURN
                  'Order'    AS src_type, o.id AS src_id,
                  'CONTAINS' AS rel,
                  'Product'  AS tgt_type, p.id AS tgt_id
                """
            else:
                live_cypher = """
                MATCH (n)-[r]->(m)
                WHERE n.id IS NOT NULL AND m.id IS NOT NULL
                RETURN labels(n)[0] AS src_type, n.id AS src_id,
                       type(r)      AS rel,
                       labels(m)[0] AS tgt_type, m.id AS tgt_id
                LIMIT 300
                """

            result  = session_or_err.run(live_cypher)
            records = list(result)

            type_colors = {
                "Customer": "#005F02", "Order": "#427A43", "Product": "#C0B87A",
                "Store": "#8B4513",    "DeliveryPartner": "#1a6b8a",
            }
            type_sizes = {
                "Customer": 20, "Order": 16, "Product": 14,
                "Store": 13,    "DeliveryPartner": 13,
            }

            nodes_set: set = set()
            for rec in records:
                s_type = rec.get("src_type") or ""
                t_type = rec.get("tgt_type") or ""
                s_id   = str(rec.get("src_id") or "")
                t_id   = str(rec.get("tgt_id") or "")
                if not s_id or not t_id:
                    continue
                if filter_type != "All" and filter_type not in (s_type, t_type):
                    continue
                nodes_set.add((s_id, s_type))
                nodes_set.add((t_id, t_type))
                edges.append({"source": s_id, "target": t_id, "rel": rec.get("rel", "")})

            nodes = [
                {
                    "id":    nid,
                    "type":  ntype,
                    "color": type_colors.get(ntype, "#999"),
                    "size":  type_sizes.get(ntype, 12),
                }
                for nid, ntype in nodes_set
            ]

            if not nodes:
                st.info("No data returned from Neo4j Aura — make sure the database has been populated.")
                nodes, edges = generate_demo_graph(filter_type, view_mode, max_nodes)

        except Exception as e:
            st.warning(f"Could not fetch live graph: {e}\nShowing demo data.")
            nodes, edges = generate_demo_graph(filter_type, view_mode, max_nodes)
        finally:
            # Close session but NOT driver (driver is cached)
            try:
                session_or_err.close()
            except Exception:
                pass
    else:
        nodes, edges = generate_demo_graph(filter_type, view_mode, max_nodes)

    # ── Build and render ──────────────────────────────────
    fig = build_graph_figure(nodes[:max_nodes], edges, title="E-Commerce Knowledge Graph")
    st.plotly_chart(fig, use_container_width=True)

    # Relationship summary table
    if edges:
        st.markdown("### 📋 Relationship Summary")
        rel_counts: dict = {}
        for e in edges:
            rel_counts[e["rel"]] = rel_counts.get(e["rel"], 0) + 1

        rel_df = (
            pd.DataFrame(list(rel_counts.items()), columns=["Relationship Type", "Count"])
            .sort_values("Count", ascending=False)
        )
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            st.dataframe(rel_df, use_container_width=True, hide_index=True)
        with col_t2:
            fig_rel = px.bar(
                rel_df, x="Count", y="Relationship Type", orientation="h",
                color="Count", color_continuous_scale=["#C0B87A", "#427A43", "#005F02"],
                title="Relationship Distribution",
            )
            fig_rel.update_layout(
                height=250, showlegend=False,
                paper_bgcolor="rgba(242,227,187,0.3)", plot_bgcolor="rgba(242,227,187,0.3)",
                font=dict(family="DM Sans", color="#1a2e1a"),
                title_font=dict(family="DM Serif Display", color="#005F02"),
            )
            st.plotly_chart(fig_rel, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# FIXED page_graph_query  — consistent credential resolution
# ============================================================
def page_graph_query():
    import json
    import pandas as pd

    st.markdown("<div class='section-neo4j'>", unsafe_allow_html=True)
    st.subheader("🔮 Natural Language → Cypher Query")
    st.caption("Ask questions in plain English — powered by LLaMA 3.3 via Groq · Results run against Neo4j")

    groq_ok     = bool(os.getenv("GROQ_API_KEY")) and GROQ_AVAILABLE
    neo4j_ok    = st.session_state.get("neo4j_connected", False)

    # If not yet connected, do a quick check (e.g. env vars were set but page
    # was opened before the user clicked Connect)
    if not neo4j_ok:
        d, _ = get_neo4j_session()
        neo4j_ok = d is not None
        st.session_state["neo4j_connected"] = neo4j_ok

    c1, c2 = st.columns(2)
    with c1:
        badge = "badge-connected" if groq_ok else "badge-error"
        label = "● Groq LLM Ready" if groq_ok else "● Groq Not Configured"
        st.markdown(f"<span class='status-badge {badge}'>{label}</span>", unsafe_allow_html=True)
    with c2:
        badge2 = "badge-connected" if neo4j_ok else "badge-demo"
        label2 = "● Neo4j Connected"  if neo4j_ok else "● Neo4j Demo Mode"
        st.markdown(f"<span class='status-badge {badge2}'>{label2}</span>", unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("📐 Graph Schema Reference"):
        st.markdown("""
        **Nodes:** `Customer(id, name)` · `Order(id)` · `Product(id)` · `Store(id)` · `DeliveryPartner(id)`

        **Relationships:**
        ```
        (Customer)-[:PLACED]->(Order)
        (Order)-[:CONTAINS]->(Product)
        (Order)-[:FROM]->(Store)
        (Order)-[:DELIVERED_BY]->(DeliveryPartner)
        ```
        """)

    st.markdown("**💡 Try these questions:**")
    sample_qs = [
        "Which customers placed the most orders?",
        "What products are most frequently ordered together?",
        "Which delivery partner handled the most orders?",
        "Show me all orders from Store S01",
        "Which stores have the highest number of deliveries?",
    ]
    cols = st.columns(3)
    for i, q in enumerate(sample_qs):
        with cols[i % 3]:
            if st.button(f"💬 {q[:35]}…", key=f"sample_q_{i}", use_container_width=True):
                st.session_state["nl_query_input"] = q

    nl_query = st.text_area(
        "🗣️ Your Question:",
        value=st.session_state.get("nl_query_input", ""),
        height=80,
        placeholder="e.g. Which customers placed the most orders?",
        key="nl_query_area",
    )

    col_run, col_clear = st.columns([1, 4])
    with col_run:
        run_btn = st.button("🚀 Generate & Run", use_container_width=True, type="primary")
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            for k in ("cypher_result", "cypher_query", "cypher_error", "nl_query_input"):
                st.session_state.pop(k, None)
            st.rerun()

    if run_btn and nl_query.strip():
        with st.spinner("🤖 Generating Cypher query…"):
            cypher = nl_to_cypher(nl_query.strip())
            st.session_state["cypher_query"] = cypher

        if neo4j_ok:
            with st.spinner("🔍 Running against Neo4j Aura…"):
                rows, err = run_cypher(cypher)
                st.session_state["cypher_result"] = rows
                st.session_state["cypher_error"]  = err
        else:
            st.session_state["cypher_result"] = None
            st.session_state["cypher_error"]  = (
                "Neo4j not connected — use the 🔌 Connect panel in the sidebar."
            )

    if st.session_state.get("cypher_query"):
        st.markdown("**🧬 Generated Cypher:**")
        st.markdown(
            f"<div class='cypher-box'>{st.session_state['cypher_query']}</div>",
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇️ Download Cypher",
            st.session_state["cypher_query"],
            file_name="query.cypher",
            mime="text/plain",
        )

    if st.session_state.get("cypher_error"):
        st.warning(f"⚠️ {st.session_state['cypher_error']}")

    if st.session_state.get("cypher_result") is not None:
        rows = st.session_state["cypher_result"]
        if rows:
            st.success(f"✅ {len(rows)} record(s) returned")
            try:
                df_result = pd.DataFrame(rows)
                st.dataframe(df_result, use_container_width=True, height=300)
            except Exception:
                for row in rows[:20]:
                    st.markdown(
                        f"<div class='result-card'>{json.dumps(row, default=str)}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info("⚠️ Query ran successfully but returned no results.")

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# .env SETUP GUIDE (print to terminal on first run)
# ============================================================
# Create a .env file in your project root with:
#
#   NEO4J_URI=neo4j+s://<uid>.databases.neo4j.io
#   NEO4J_USER=neo4j
#   NEO4J_PASSWORD=<your-aura-password>
#   GROQ_API_KEY=<your-groq-key>
#
# Then load it at the top of your app.py:
#   from dotenv import load_dotenv
#   load_dotenv()
#
# Install dependencies if not already:
#   pip install neo4j python-dotenv
# ============================================================
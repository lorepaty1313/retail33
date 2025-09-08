import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Retail 33 - Demo Visual", page_icon="🛍️", layout="wide")

# ---- CSS Global: fondo blanco + texto gris ----
css_global = """
<style>
body, .stApp { background:#ffffff !important; color:#4a4a4a !important; font-family:"Helvetica Neue", sans-serif; }
h1, h2, h3, h4, h5, h6 { color:#4a4a4a !important; }
.stTextInput, .stNumberInput, .stSelectbox, .stTextArea, .stDateInput { background:#ffffff !important; color:#4a4a4a !important; }
label, .stMarkdown, .stCaption { color:#4a4a4a !important; }
.stButton>button { background:#f6bd60; color:#4a4a4a !important; border-radius:8px; border:none; font-weight:700; }
.stButton>button:hover { background:#f28482; color:#fff !important; }
[data-testid="stMetricValue"]{ color:#4a4a4a !important; font-weight:800; }
[data-testid="stMetricLabel"]{ color:#6d6d6d !important; }
.dataframe, .stDataFrame, .stTable { background:#ffffff !important; color:#4a4a4a !important; }
.stDataFrame div { color:#4a4a4a !important; }

/* Tarjetas del grid */
.store{ border-radius:10px; padding:12px; font-weight:700; text-align:center; color:#444; }
.store small{ display:block; font-weight:400; }
</style>
"""
st.markdown(css_global, unsafe_allow_html=True)

# ---- CSS: colores pastel por expander usando ANCLAS adyacentes ----
css_expand = """
<style>
/* Base del header del expander dentro del panel de captura */
#cap-panel [data-testid="stExpander"] summary,
#cap-panel .streamlit-expanderHeader{
  color:#4a4a4a !important;
  font-weight:700;
  border-radius:8px;
  border:1px solid #e8e8e8;
}

/* Pintamos cada expander según su ancla previa (#exp-<key>) */
#exp-pasarela + div [data-testid="stExpander"] summary,
#exp-pasarela + div .streamlit-expanderHeader { background:#A7C7E7 !important; }  /* azul */
#exp-acomodo + div [data-testid="stExpander"] summary,
#exp-acomodo + div .streamlit-expanderHeader { background:#C6E2B5 !important; }   /* verde */
#exp-producto_nuevo + div [data-testid="stExpander"] summary,
#exp-producto_nuevo + div .streamlit-expanderHeader { background:#F7C6C7 !important; } /* rosa */
#exp-producto_rebaja + div [data-testid="stExpander"] summary,
#exp-producto_rebaja + div .streamlit-expanderHeader { background:#D9C2E9 !important; } /* lila */
#exp-display + div [data-testid="stExpander"] summary,
#exp-display + div .streamlit-expanderHeader { background:#FFF3B0 !important; }   /* amarillo */
#exp-maniquies + div [data-testid="stExpander"] summary,
#exp-maniquies + div .streamlit-expanderHeader { background:#FFB5A7 !important; } /* coral */
#exp-zona_impulso + div [data-testid="stExpander"] summary,
#exp-zona_impulso + div .streamlit-expanderHeader { background:#B5EAD7 !important; } /* menta */
#exp-area_ropa + div [data-testid="stExpander"] summary,
#exp-area_ropa + div .streamlit-expanderHeader { background:#FFDAB9 !important; } /* durazno */

/* Cuerpo del expander blanco para inputs */
#cap-panel [data-testid="stExpander"] > div[role="region"],
#cap-panel .streamlit-expanderContent{
  background:#ffffff !important;
  border:1px solid #f0f0f0;
  border-radius:8px;
  padding-bottom:8px;
}
</style>
"""
st.markdown(css_expand, unsafe_allow_html=True)

# ---------- Datos demo ----------
TIENDAS_COLS = ["tienda_id","nombre","ciudad","gerente","estatus"]
CATEGORIAS = [
    ("pasarela",       "Pasarela de la moda"),
    ("acomodo",        "Acomodo guía visual"),
    ("producto_nuevo", "Producto nuevo"),
    ("producto_rebaja","Producto rebaja"),
    ("display",        "Display"),
    ("maniquies",      "Maniquíes"),
    ("zona_impulso",   "Zona impulso"),
    ("area_ropa",      "Área ropa"),
]
BOOL_COLS = [f"{k}_si" for k,_ in CATEGORIAS]

def demo_data():
    df_t = pd.DataFrame([
        {"tienda_id":"T01","nombre":"Perisur","ciudad":"CDMX","gerente":"Ana","estatus":"abierta"},
        {"tienda_id":"T02","nombre":"Santa Fe","ciudad":"CDMX","gerente":"Luis","estatus":"abierta"},
        {"tienda_id":"T03","nombre":"Centro","ciudad":"CDMX","gerente":"Marta","estatus":"abierta"},
        {"tienda_id":"T04","nombre":"Universidad","ciudad":"CDMX","gerente":"Paco","estatus":"abierta"},
        {"tienda_id":"T05","nombre":"Puebla","ciudad":"PUE","gerente":"Sofía","estatus":"cerrada"},
    ])[TIENDAS_COLS]
    hoy = dt.date.today()
    base = [
        {"fecha":hoy,"tienda_id":"T01","notas":"Todo ok",
         "pasarela_si":True,"acomodo_si":True,"producto_nuevo_si":True,"producto_rebaja_si":True,
         "display_si":True,"maniquies_si":True,"zona_impulso_si":True,"area_ropa_si":True},
        {"fecha":hoy,"tienda_id":"T02","notas":"Faltan en zona impulso",
         "pasarela_si":True,"acomodo_si":True,"producto_nuevo_si":False,"producto_rebaja_si":True,
         "display_si":False,"maniquies_si":True,"zona_impulso_si":False,"area_ropa_si":True},
        {"fecha":hoy,"tienda_id":"T03","notas":"Requiere acomodo",
         "pasarela_si":False,"acomodo_si":False,"producto_nuevo_si":False,"producto_rebaja_si":True,
         "display_si":False,"maniquies_si":True,"zona_impulso_si":False,"area_ropa_si":True},
    ]
    df_c = pd.DataFrame(base)
    return df_t, df_c

df_t, df_c = demo_data()

# ------------------- UI -------------------
st.title("🛍️ Retail 33 — Demo Visual (sin Sheets)")

# Filtros
st.sidebar.header("Filtros")
ciudad_sel = st.sidebar.selectbox("Ciudad", ["Todas"] + sorted(df_t["ciudad"].unique()))
estatus_sel = st.sidebar.selectbox("Estatus", ["Todos"] + sorted(df_t["estatus"].unique()))
df_t_filt = df_t.copy()
if ciudad_sel != "Todas": df_t_filt = df_t_filt[df_t_filt["ciudad"] == ciudad_sel]
if estatus_sel != "Todos": df_t_filt = df_t_filt[df_t_filt["estatus"] == estatus_sel]

# Tabs
tab_dash, tab_captura, tab_tareas, tab_conf = st.tabs(["📊 Dashboard", "📝 Captura diaria", "✅ Tareas", "⚙️ Configuración"])

# ==================== DASHBOARD ====================
with tab_dash:
    st.subheader("Resumen visual (hoy)")
    hoy = dt.date.today()

    df_hoy = df_t[["tienda_id","nombre","ciudad","estatus"]].merge(
        df_c[df_c["fecha"] == hoy], on="tienda_id", how="left"
    )

    def score_row(r):
        vals = [(1.0 if bool(r.get(col)) else 0.0) for col in BOOL_COLS]
        return np.mean(vals) if len(vals) else 0.0

    df_hoy["score_visual"] = df_hoy.apply(score_row, axis=1)

    def color_from_score(score, has_data):
        if not has_data: return "#E5E5E5"
        if score >= 0.8: return "#A8D5BA"
        if score >= 0.5: return "#FFF3B0"
        return "#FFB5A7"

    has_data = df_hoy[BOOL_COLS].notna().any(axis=1)
    df_hoy["color"] = [color_from_score(s, d) for s, d in zip(df_hoy["score_visual"], has_data)]

    tiendas_total = len(df_t_filt)
    cobertura = int(has_data.sum()) / max(len(df_hoy), 1)
    score_prom = float(df_hoy["score_visual"].mean())

    c1, c2, c3 = st.columns(3)
    c1.metric("Visita (hoy)", f"{cobertura*100:,.0f}%")
    c2.metric("Score promedio", f"{score_prom*100:,.1f}%")
    c3.metric("Tiendas (filtro)", f"{tiendas_total}")

    st.markdown("### 🛍️ Tiendas (color por score)")
    grid_cols = 3
    df_grid = df_t_filt.sort_values("tienda_id")
    blocks = [df_grid.iloc[i:i+grid_cols] for i in range(0, len(df_grid), grid_cols)]
    for block in blocks:
        cols = st.columns(len(block))
        for j, (_, r) in enumerate(block.iterrows()):
            row_hoy = df_hoy[df_hoy["tienda_id"] == r["tienda_id"]]
            if row_hoy.empty:
                color, sc = "#E5E5E5", 0
            else:
                color = row_hoy["color"].values[0]
                sc = float(row_hoy["score_visual"].values[0]) * 100
            cols[j].markdown(
                f"""<div class="store" style="background:{color}">
                {r['tienda_id']}<small>{r['nombre']}</small>
                <small>Score: {sc:,.0f}%</small>
                </div>""",
                unsafe_allow_html=True
            )

    st.markdown("### 🔍 Detalle de hoy")
    st.dataframe(df_hoy[["tienda_id","nombre","ciudad","estatus","score_visual","notas"]]
                 .rename(columns={"score_visual":"score_visual_0_1"}),
                 use_container_width=True)

# ==================== CAPTURA (demo) ====================
with tab_captura:
    st.subheader("Visita (demo)")
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", dt.date.today())
    tienda_id = c2.selectbox("Tienda", df_t_filt["tienda_id"].tolist() or df_t["tienda_id"].tolist())
    st.text_area("Notas generales")

    st.markdown("Visual (Sí/No, notas y foto opcional)")

    # Panel scopeado para aplicar las reglas CSS
    st.markdown('<div id="cap-panel">', unsafe_allow_html=True)

    # ANCLA + expander por categoría (el CSS apunta a '#exp-<key> + div ...')
    for key, label in CATEGORIAS:
        st.markdown(f'<div id="exp-{key}"></div>', unsafe_allow_html=True)
        with st.expander(label):
            st.radio("¿Cumple?", ["No","Sí"], horizontal=True, key=f"{key}_si_demo")
            st.text_area("Notas", key=f"{key}_notas_demo")
            st.file_uploader("Foto (opcional)", type=["jpg","jpeg","png"], key=f"{key}_foto_demo")

    st.markdown('</div>', unsafe_allow_html=True)
    st.info("Demo: este modo no guarda datos (solo visualiza el layout).")

# ==================== TAREAS (placeholder) ====================
with tab_tareas:
    st.subheader("Gestión de tareas (demo)")
    st.write("Aquí irán las tareas (no implementado en demo).")

# ==================== CONFIGURACIÓN ====================
with tab_conf:
    st.subheader("Tiendas (demo)")
    st.dataframe(df_t, use_container_width=True)


import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import io, base64
from PIL import Image

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Retail 33 - Demo Visual", page_icon="🛍️", layout="wide")

# ---- CSS Global: fondo blanco + texto gris (incluye tablas) y estilos base ----
css_global = """
<style>
/* Fondo y tipografía global */
body, .stApp {
  background-color: #ffffff !important;
  color: #4a4a4a !important;
  font-family: "Helvetica Neue", sans-serif;
}

/* Títulos */
h1, h2, h3, h4, h5, h6 {
  color: #4a4a4a !important;
}

/* Widgets (inputs, select, textarea, date) */
.stTextInput, .stNumberInput, .stSelectbox, .stTextArea, .stDateInput {
  background-color: #ffffff !important;
  color: #4a4a4a !important;
}

/* Labels / textos secundarios */
label, .stMarkdown, .stCaption {
  color: #4a4a4a !important;
}

/* Botones */
.stButton>button {
  background-color: #f6bd60; /* amarillo pastel */
  color: #4a4a4a !important;
  border-radius: 8px;
  border: none;
  font-weight: bold;
}
.stButton>button:hover {
  background-color: #f28482; /* coral pastel */
  color: #ffffff !important;
}

/* Métricas */
[data-testid="stMetricValue"] {
  color: #4a4a4a !important;
  font-weight: 800;
}
[data-testid="stMetricLabel"] {
  color: #6d6d6d !important;
}

/* Tablas / DataFrames */
.dataframe, .stDataFrame, .stTable {
  background-color: #ffffff !important;
  color: #4a4a4a !important;
}
.stDataFrame div {
  color: #4a4a4a !important;
}

/* Grid de tiendas (cuadritos) */
.store {
  border-radius: 10px;
  padding: 12px;
  font-weight: 700;
  text-align: center;
  color: #444; /* texto gris oscuro */
}
.store small {
  display: block;
  font-weight: 400;
}
</style>
"""
st.markdown(css_global, unsafe_allow_html=True)

# ---- CSS para expanders pastel en Captura (scoped por contenedor) ----
css_expand = """
<style>
/* Base del header en versiones nuevas/viejas */
#cap-expanders details > summary,
#cap-expanders .streamlit-expanderHeader {
  color: #4a4a4a !important;
  font-weight: 700;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

/* 1..8 por orden dentro de #cap-expanders */
#cap-expanders details:nth-of-type(1) > summary,
#cap-expanders .streamlit-expander:nth-of-type(1) > .streamlit-expanderHeader {
  background: #A7C7E7 !important; /* azul pastel */
}
#cap-expanders details:nth-of-type(2) > summary,
#cap-expanders .streamlit-expander:nth-of-type(2) > .streamlit-expanderHeader {
  background: #C6E2B5 !important; /* verde pastel */
}
#cap-expanders details:nth-of-type(3) > summary,
#cap-expanders .streamlit-expander:nth-of-type(3) > .streamlit-expanderHeader {
  background: #F7C6C7 !important; /* rosa pastel */
}
#cap-expanders details:nth-of-type(4) > summary,
#cap-expanders .streamlit-expander:nth-of-type(4) > .streamlit-expanderHeader {
  background: #D9C2E9 !important; /* lila pastel */
}
#cap-expanders details:nth-of-type(5) > summary,
#cap-expanders .streamlit-expander:nth-of-type(5) > .streamlit-expanderHeader {
  background: #FFF3B0 !important; /* amarillo pastel */
}
#cap-expanders details:nth-of-type(6) > summary,
#cap-expanders .streamlit-expander:nth-of-type(6) > .streamlit-expanderHeader {
  background: #FFB5A7 !important; /* coral pastel */
}
#cap-expanders details:nth-of-type(7) > summary,
#cap-expanders .streamlit-expander:nth-of-type(7) > .streamlit-expanderHeader {
  background: #B5EAD7 !important; /* menta pastel */
}
#cap-expanders details:nth-of-type(8) > summary,
#cap-expanders .streamlit-expander:nth-of-type(8) > .streamlit-expanderHeader {
  background: #FFDAB9 !important; /* durazno pastel */
}

/* Cuerpo del expander: blanco limpio para inputs */
#cap-expanders details[open] > div,
#cap-expanders .streamlit-expanderContent {
  background: #ffffff;
  border-left: 1px solid #f0f0f0;
  border-right: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  border-radius: 0 0 8px 8px;
  padding-bottom: 8px;
}
</style>
"""
st.markdown(css_expand, unsafe_allow_html=True)

# ---------- Modelo de datos ----------
TIENDAS_COLS = [
    "tienda_id","nombre","ciudad","gerente","estatus"
]

# Captura centrada en auditoría visual (sin ventas)
CAPTURAS_COLS = [
    "fecha","tienda_id","notas",
    "pasarela_si","pasarela_notas",
    "acomodo_si","acomodo_notas",
    "producto_nuevo_si","producto_nuevo_notas",
    "producto_rebaja_si","producto_rebaja_notas",
    "display_si","display_notas",
    "maniquies_si","maniquies_notas",
    "zona_impulso_si","zona_impulso_notas",
    "area_ropa_si","area_ropa_notas"
]

FOTOS_COLS = [
    "fecha","tienda_id","categoria","filename","mime","img_base64"
]

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
LABEL_MAP = dict(CATEGORIAS)
BOOL_COLS = [f"{k}_si" for k, _ in CATEGORIAS]

# ---------- Datos demo ----------
def demo_data():
    df_t = pd.DataFrame([
        {"tienda_id":"T01","nombre":"Perisur","ciudad":"CDMX","gerente":"Ana","estatus":"abierta"},
        {"tienda_id":"T02","nombre":"Santa Fe","ciudad":"CDMX","gerente":"Luis","estatus":"abierta"},
        {"tienda_id":"T03","nombre":"Centro","ciudad":"CDMX","gerente":"Marta","estatus":"abierta"},
        {"tienda_id":"T04","nombre":"Universidad","ciudad":"CDMX","gerente":"Paco","estatus":"abierta"},
        {"tienda_id":"T05","nombre":"Puebla","ciudad":"PUE","gerente":"Sofía","estatus":"cerrada"},
    ])[TIENDAS_COLS]

    hoy = dt.date.today()
    base = []
    base.append({
        "fecha":hoy,"tienda_id":"T01","notas":"Todo ok",
        "pasarela_si":True, "pasarela_notas":"",
        "acomodo_si":True, "acomodo_notas":"",
        "producto_nuevo_si":True, "producto_nuevo_notas":"",
        "producto_rebaja_si":True, "producto_rebaja_notas":"",
        "display_si":True, "display_notas":"",
        "maniquies_si":True, "maniquies_notas":"",
        "zona_impulso_si":True, "zona_impulso_notas":"",
        "area_ropa_si":True, "area_ropa_notas":""
    })
    base.append({
        "fecha":hoy,"tienda_id":"T02","notas":"Faltan productos en zona impulso",
        "pasarela_si":True, "pasarela_notas":"",
        "acomodo_si":True, "acomodo_notas":"",
        "producto_nuevo_si":False, "producto_nuevo_notas":"No señalado",
        "producto_rebaja_si":True, "producto_rebaja_notas":"",
        "display_si":False, "display_notas":"Desorden",
        "maniquies_si":True, "maniquies_notas":"",
        "zona_impulso_si":False, "zona_impulso_notas":"Sin material",
        "area_ropa_si":True, "area_ropa_notas":""
    })
    base.append({
        "fecha":hoy,"tienda_id":"T03","notas":"Requiere acomodo",
        "pasarela_si":False, "pasarela_notas":"Sin montaje",
        "acomodo_si":False, "acomodo_notas":"Guía no seguida",
        "producto_nuevo_si":False, "producto_nuevo_notas":"No visible",
        "producto_rebaja_si":True, "producto_rebaja_notas":"",
        "display_si":False, "display_notas":"Faltan etiquetas",
        "maniquies_si":True, "maniquies_notas":"",
        "zona_impulso_si":False, "zona_impulso_notas":"",
        "area_ropa_si":True, "area_ropa_notas":""
    })
    df_c = pd.DataFrame(base)[CAPTURAS_COLS]
    df_f = pd.DataFrame(columns=FOTOS_COLS)
    return df_t, df_c, df_f

df_t, df_c, df_f = demo_data()

# ------------------- UI -------------------
st.title("🛍️ Retail 33 — Demo Visual (sin Sheets)")

# --------- Sidebar filtros ----------
st.sidebar.header("Filtros")
ciudades = ["Todas"] + sorted(df_t["ciudad"].dropna().unique().tolist())
ciudad_sel = st.sidebar.selectbox("Ciudad", ciudades, index=0)

estatuses = ["Todos"] + sorted(df_t["estatus"].dropna().unique().tolist())
estatus_sel = st.sidebar.selectbox("Estatus", estatuses, index=0)

df_t_filt = df_t.copy()
if ciudad_sel != "Todas":
    df_t_filt = df_t_filt[df_t_filt["ciudad"] == ciudad_sel]
if estatus_sel != "Todos":
    df_t_filt = df_t_filt[df_t_filt["estatus"] == estatus_sel]

# --------- Tabs ---------
tab_dash, tab_captura, tab_tareas, tab_conf = st.tabs(["📊 Dashboard", "📝 Captura diaria", "✅ Tareas", "⚙️ Configuración"])

# ==================== DASHBOARD ====================
with tab_dash:
    st.subheader("Resumen visual (hoy)")
    hoy = dt.date.today()

    # Merge capturas de hoy a tiendas
    df_hoy = df_t[["tienda_id","nombre","ciudad","estatus"]].merge(
        df_c[df_c["fecha"] == hoy], on="tienda_id", how="left"
    )

    # Score visual = promedio de checks (True=1, False/NaN=0)
    def score_row(r):
        vals = [(1.0 if bool(r.get(col)) else 0.0) for col in BOOL_COLS]
        return np.mean(vals) if len(vals) else 0.0

    df_hoy["score_visual"] = df_hoy.apply(score_row, axis=1)

    # Color pastel por score (gris si no hay captura)
    def color_from_score(score, has_data):
        if not has_data:
            return "#E5E5E5"  # gris pastel
        if score >= 0.8:
            return "#A8D5BA"  # verde menta pastel
        if score >= 0.5:
            return "#FFF3B0"  # amarillo mantequilla
        return "#FFB5A7"      # coral pastel

    has_data = df_hoy[BOOL_COLS].notna().any(axis=1)
    df_hoy["color"] = [color_from_score(s, d) for s, d in zip(df_hoy["score_visual"], has_data)]

    # KPIs
    tiendas_total = len(df_t_filt)
    cobertura = int(has_data.sum()) / max(len(df_hoy), 1)
    score_prom = float(df_hoy["score_visual"].mean())

    colA, colB, colC = st.columns(3)
    colA.metric("Visita (hoy)", f"{cobertura*100:,.0f}%")
    colB.metric("Score promedio", f"{score_prom*100:,.1f}%")
    colC.metric("Tiendas (filtro)", f"{tiendas_total}")

    # Grid por tiendas
    st.markdown("### 🛍️ Tiendas (color por score)")

    grid_cols = 3
    df_grid = df_t_filt.copy().sort_values("tienda_id")
    blocks = [df_grid.iloc[i:i+grid_cols] for i in range(0, len(df_grid), grid_cols)]

    for block in blocks:
        cols = st.columns(len(block))
        for j, (_, r) in enumerate(block.iterrows()):
            row_hoy = df_hoy[df_hoy["tienda_id"] == r["tienda_id"]]
            if row_hoy.empty:
                color = "#E5E5E5"; sc = 0
            else:
                color = row_hoy["color"].values[0]
                sc = float(row_hoy["score_visual"].values[0])*100
            cols[j].markdown(
                f"""<div class="store" style="background:{color}">
                {r['tienda_id']}<small>{r['nombre']}</small>
                <small>Score: {sc:,.0f}%</small>
                </div>""",
                unsafe_allow_html=True
            )

    st.markdown("### 🔍 Detalle de hoy")
    st.dataframe(
        df_hoy[["tienda_id","nombre","ciudad","estatus","score_visual","notas"]]
        .rename(columns={"score_visual":"score_visual_0_1"}),
        use_container_width=True
    )

# ==================== CAPTURA (demo) ====================
with tab_captura:
    st.subheader("Visita (demo)")
    col1, col2 = st.columns(2)
    fecha = col1.date_input("Fecha", dt.date.today())
    tienda_id = col2.selectbox("Tienda", df_t_filt["tienda_id"].tolist() or df_t["tienda_id"].tolist())
    notas = st.text_area("Notas generales")

    st.markdown("Visual (Sí/No, notas y foto opcional)")

    # Contenedor scropeado para colorear cada expander por orden
    st.markdown('<div id="cap-expanders">', unsafe_allow_html=True)
    for key, label in CATEGORIAS:
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

import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import io, base64
from PIL import Image

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Retail 33 - Demo ", page_icon="🛍️", layout="wide")

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

# ---------- Fake data para demo (incluye algunos checks) ----------
def demo_data():
    # 5 tiendas de ejemplo
    df_t = pd.DataFrame([
        {"tienda_id":"T01","nombre":"Perisur","ciudad":"CDMX","gerente":"Ana","estatus":"abierta"},
        {"tienda_id":"T02","nombre":"Santa Fe","ciudad":"CDMX","gerente":"Luis","estatus":"abierta"},
        {"tienda_id":"T03","nombre":"Centro","ciudad":"CDMX","gerente":"Marta","estatus":"abierta"},
        {"tienda_id":"T04","nombre":"Universidad","ciudad":"CDMX","gerente":"Paco","estatus":"abierta"},
        {"tienda_id":"T05","nombre":"Puebla","ciudad":"PUE","gerente":"Sofía","estatus":"cerrada"},
    ])[TIENDAS_COLS]

    hoy = dt.date.today()
    # Tres tiendas con auditoría de ejemplo para que se vea el color del grid
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

    # Sin tareas ni fotos persistidas en demo
    df_x = pd.DataFrame(columns=["tarea_id","tienda_id","titulo","detalle","prioridad","estado","responsable","fecha_creacion","fecha_vencimiento"])
    df_f = pd.DataFrame(columns=FOTOS_COLS)
    return df_t, df_c, df_x, df_f

df_t, df_c, df_x, df_f = demo_data()

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

    # Une capturas de hoy a tiendas para calcular score por tienda
    df_hoy = df_t[["tienda_id","nombre","ciudad","estatus"]].merge(
        df_c[df_c["fecha"] == hoy], on="tienda_id", how="left"
    )

    # Score visual = promedio de checks (True=1, False/NaN=0)
    def score_row(r):
        vals = [(1.0 if bool(r.get(col)) else 0.0) for col in BOOL_COLS]
        if len(vals) == 0:
            return 0.0
        return np.mean(vals)

    df_hoy["score_visual"] = df_hoy.apply(score_row, axis=1)

    # Color por score (gris si no hay captura)
    def color_from_score(score, has_data):
        if not has_data:
            return "#9E9E9E"  # sin captura
        if score >= 0.8:
            return "#4CAF50"  # verde
        if score >= 0.5:
            return "#FFC107"  # ámbar
        return "#F44336"      # rojo

    has_data = df_hoy[BOOL_COLS].notna().any(axis=1)
    df_hoy["color"] = [
        color_from_score(s, d) for s, d in zip(df_hoy["score_visual"], has_data)
    ]

    # KPIs
    tiendas_total = len(df_t_filt)
    cobertura = int(has_data.sum()) / max(len(df_hoy), 1)
    score_prom = float(df_hoy["score_visual"].mean())

    colA, colB, colC = st.columns(3)
    colA.metric("Visita (hoy)", f"{cobertura*100:,.0f}%")
    colB.metric("Score", f"{score_prom*100:,.1f}%")
    colC.metric("Tiendas)", f"{tiendas_total}")

    # Grid por tiendas
    st.markdown(" Tiendas (color por score)")
    grid_cols = 3
    df_grid = df_t_filt.copy().sort_values("tienda_id")
    blocks = [df_grid.iloc[i:i+grid_cols] for i in range(0, len(df_grid), grid_cols)]
    css = """
    <style>
    .store { border-radius:10px; padding:10px; color:white; font-weight:700; text-align:center; }
    .store small { display:block; font-weight:400; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    for block in blocks:
        cols = st.columns(len(block))
        for j, (_, r) in enumerate(block.iterrows()):
            row_hoy = df_hoy[df_hoy["tienda_id"] == r["tienda_id"]]
            if row_hoy.empty:
                color = "#9E9E9E"; sc = 0
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

# ==================== CAPTURA (solo layout demo) ====================
with tab_captura:
    st.subheader("Visita (demo)")
    col1, col2 = st.columns(2)
    fecha = col1.date_input("Fecha", dt.date.today())
    tienda_id = col2.selectbox("Tienda", df_t_filt["tienda_id"].tolist() or df_t["tienda_id"].tolist())

    notas = st.text_area("Notas generales")

    st.markdown("Visual (Sí/No, notas y foto opcional)")
    for key, label in CATEGORIAS:
        with st.expander(label):
            st.radio("¿Cumple?", ["No","Sí"], horizontal=True, key=f"{key}_si_demo")
            st.text_area("Notas", key=f"{key}_notas_demo")
            st.file_uploader("Foto (opcional)", type=["jpg","jpeg","png"], key=f"{key}_foto_demo")
    st.info("Demo: este modo no guarda datos (solo visualiza el layout).")

# ==================== TAREAS (placeholder) ====================
with tab_tareas:
    st.subheader("Gestión de tareas (demo)")
    st.write("Aquí irán las tareas (no implementado en demo).")

# ==================== CONFIGURACIÓN ====================
with tab_conf:
    st.subheader("Tiendas (dejemplo)")
    st.dataframe(df_t, use_container_width=True)

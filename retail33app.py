import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import io, base64
from PIL import Image

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Retail 33 - Demo", page_icon="🛍️", layout="wide")

# ---------- Modelo de datos ----------
TIENDAS_COLS = [
    "tienda_id","nombre","ciudad","gerente","estatus"
]

CAPTURAS_COLS = [
    "fecha","tienda_id","ventas","tickets","conversion","ticket_prom","merma_alerta","notas",
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

# ---------- Fake data para demo ----------
def demo_data():
    # 5 tiendas de ejemplo
    df_t = pd.DataFrame([
        {"tienda_id":"T01","nombre":"Perisur","ciudad":"CDMX","gerente":"Ana","estatus":"abierta"},
        {"tienda_id":"T02","nombre":"Santa Fe","ciudad":"CDMX","gerente":"Luis","estatus":"abierta"},
        {"tienda_id":"T03","nombre":"Centro ","ciudad":"CDMX","gerente":"Marta","estatus":"abierta"},
        {"tienda_id":"T04","nombre":"Universidad","ciudad":"CDMX","gerente":"Paco","estatus":"abierta"},
        {"tienda_id":"T05","nombre":"Puebla","ciudad":"PUE","gerente":"Sofía","estatus":"cerrada"},
    ])[TIENDAS_COLS]

    hoy = dt.date.today()
    df_c = pd.DataFrame([
        {"fecha":hoy,"tienda_id":"T01","notas":"Todo ok"},
        {"fecha":hoy,"tienda_id":"T02","notas":"Faltan productos"},
        {"fecha":hoy,"tienda_id":"T03","notas":"acomodar"},
    ])[CAPTURAS_COLS[:8]]  # sin auditoría visual por ahora
    return df_t, df_c, pd.DataFrame(columns=TAREAS_COLS), pd.DataFrame(columns=FOTOS_COLS)

df_t, df_c, df_x, df_f = demo_data()

# ------------------- UI -------------------
st.title("🛍️ Retail 33 — Demo Layout (sin Sheets)")

# --------- Sidebar filtros ----------
st.sidebar.header("Filtros")
ciudades = ["Todas"] + sorted(df_t["ciudad"].dropna().unique().tolist())
ciudad_sel = st.sidebar.selectbox("Ciudad", ciudades, index=0)

estatuses = ["Todos"] + sorted(df_t["estatus"].dropna().unique().tolist())
estatus_sel = st.sidebar.selectbox("Estatus", estatuses, index=0)

meta_ref = st.sidebar.number_input("Meta diaria de referencia ($)", min_value=0, value=int(df_t["meta_diaria"].median()))

df_t_filt = df_t.copy()
if ciudad_sel != "Todas":
    df_t_filt = df_t_filt[df_t_filt["ciudad"] == ciudad_sel]
if estatus_sel != "Todos":
    df_t_filt = df_t_filt[df_t_filt["estatus"] == estatus_sel]

# --------- Tabs ---------
tab_dash, tab_captura, tab_tareas, tab_conf = st.tabs(["📊 Dashboard", "📝 Captura diaria", "✅ Tareas", "⚙️ Configuración"])

# ==================== DASHBOARD ====================
with tab_dash:
    st.subheader("Resumen de hoy")
    hoy = dt.date.today()

    df_hoy = df_c[df_c["fecha"] == hoy].merge(df_t[["tienda_id","meta_diaria","nombre","ciudad"]], on="tienda_id", how="right")
    df_hoy["ventas"] = pd.to_numeric(df_hoy["ventas"], errors="coerce").fillna(0)
    df_hoy["avance"] = (df_hoy["ventas"] / df_hoy["meta_diaria"]).replace([np.inf, -np.inf], 0)
    df_hoy["color"] = np.where(df_hoy["avance"] >= 1.0, "#4CAF50",
                        np.where(df_hoy["avance"] >= 0.7, "#FFC107", "#F44336"))

    colA, colB, colC, colD = st.columns(4)
    total_ventas = float(df_hoy["ventas"].sum())
    avance_prom = float(df_hoy["avance"].mean())
    colA.metric("Ventas totales (hoy)", f"${total_ventas:,.0f}")
    colB.metric("Avance promedio", f"{avance_prom*100:,.1f}%")
    colC.metric("Tiendas abiertas", len(df_t_filt))
    colD.metric("Meta referencia", f"${meta_ref:,.0f}")

    st.markdown("### 🗺️ Grid de tiendas")
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
                color = "#9E9E9E"; vtas = 0; av = 0
            else:
                color = row_hoy["color"].values[0]
                vtas = float(row_hoy["ventas"].values[0])
                av = float(row_hoy["avance"].values[0])
            cols[j].markdown(
                f"""<div class="store" style="background:{color}">
                {r['tienda_id']}<small>{r['nombre']}</small>
                <small>${vtas:,.0f} • {av*100:,.0f}%</small>
                </div>""",
                unsafe_allow_html=True
            )

# ==================== CAPTURA (solo layout) ====================
with tab_captura:
    st.subheader("Captura diaria (demo)")
    col1, col2, col3, col4 = st.columns(4)
    fecha = col1.date_input("Fecha", dt.date.today())
    tienda_id = col2.selectbox("Tienda", df_t_filt["tienda_id"].tolist())
    ventas = col3.number_input("Ventas ($)", min_value=0.0, step=100.0)
    tickets = col4.number_input("Tickets", min_value=0, step=1)

    st.markdown("### 👀 Auditoría visual (checklist demo)")
    for key, label in CATEGORIAS:
        with st.expander(label):
            st.radio("¿Cumple?", ["No","Sí"], horizontal=True, key=f"{key}_si")
            st.text_area("Notas", key=f"{key}_notas")
            st.file_uploader("Foto (opcional)", type=["jpg","jpeg","png"], key=f"{key}_foto")

    st.button("💾 Guardar captura (demo)")

# ==================== TAREAS ====================
with tab_tareas:
    st.subheader("Gestión de tareas (demo)")
    st.write("Aquí irán las tareas de tiendas.")

# ==================== CONFIGURACIÓN ====================
with tab_conf:
    st.subheader("Configuración (demo)")
    st.dataframe(df_t, use_container_width=True)

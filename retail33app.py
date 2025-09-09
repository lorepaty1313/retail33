import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
from streamlit_extras.stylable_container import stylable_container

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Retail 33 - Demo Visual", page_icon="🛍️", layout="wide")

# ---- CSS Global ----
st.markdown("""
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
.store-card{ border-radius:12px; padding:10px; border:1px solid #e8e8e8; }
.store-card small{ display:block; font-weight:400; }
</style>
""", unsafe_allow_html=True)

# ---------- Datos demo / modelo ----------
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

# Paleta pastel por categoría (para el wrapper)
PASTEL = {
    "pasarela":        "#A7C7E7",  # azul
    "acomodo":         "#C6E2B5",  # verde
    "producto_nuevo":  "#F7C6C7",  # rosa
    "producto_rebaja": "#D9C2E9",  # lila
    "display":         "#FFF3B0",  # amarillo
    "maniquies":       "#FFB5A7",  # coral
    "zona_impulso":    "#B5EAD7",  # menta
    "area_ropa":       "#FFDAB9",  # durazno
}

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

# ---------------- Utilidades ----------------
def score_row(r):
    vals = [(1.0 if bool(r.get(col)) else 0.0) for col in BOOL_COLS]
    return np.mean(vals) if len(vals) else 0.0

def color_from_score(score, has_data):
    if not has_data: return "#E5E5E5"
    if score >= 0.8: return "#A8D5BA"
    if score >= 0.5: return "#FFF3B0"
    return "#FFB5A7"

def safe_index(vals, target, default=0):
    try:
        return next(i for i, v in enumerate(vals) if v == target)
    except StopIteration:
        return default
    except Exception:
        return default

# ---------------- Routing robusto por query params ----------------
# (compatibles con versiones anteriores)
params = st.experimental_get_query_params()
view = params.get("view", ["dashboard"])[0]
tienda_sel = params.get("tienda", [None])[0]

# ------------------- UI -------------------
st.title("🛍️ Retail 33 — Demo Visual")

# Filtros
st.sidebar.header("Filtros")
ciudad_sel = st.sidebar.selectbox("Ciudad", ["Todas"] + sorted(df_t["ciudad"].unique()))
estatus_sel = st.sidebar.selectbox("Estatus", ["Todos"] + sorted(df_t["estatus"].unique()))

# Navegación por botones (cada botón cambia params y corta el ciclo)
st.sidebar.header("Secciones")
if st.sidebar.button("📊 Dashboard"):
    st.experimental_set_query_params(view="dashboard", tienda=tienda_sel or "")
    st.stop()

if st.sidebar.button("📝 Captura diaria"):
    if tienda_sel:
        st.experimental_set_query_params(view="captura", tienda=tienda_sel)
    else:
        st.experimental_set_query_params(view="captura")
    st.stop()

# Aplica filtros a tiendas
df_t_filt = df_t.copy()
if ciudad_sel != "Todas": df_t_filt = df_t_filt[df_t_filt["ciudad"] == ciudad_sel]
if estatus_sel != "Todos": df_t_filt = df_t_filt[df_t_filt["estatus"] == estatus_sel]

# ==================== DASHBOARD ====================
if view == "dashboard":
    st.subheader("Resumen visual (hoy)")
    hoy = dt.date.today()

    df_hoy = df_t[["tienda_id","nombre","ciudad","estatus"]].merge(
        df_c[df_c["fecha"] == hoy], on="tienda_id", how="left"
    )
    df_hoy["score_visual"] = df_hoy.apply(score_row, axis=1)
    has_data = df_hoy[BOOL_COLS].notna().any(axis=1)
    df_hoy["color"] = [color_from_score(s, d) for s, d in zip(df_hoy["score_visual"], has_data)]

    c1, c2, c3 = st.columns(3)
    cobertura = (has_data.sum() / max(len(df_hoy), 1)) * 100
    score_prom = float(df_hoy["score_visual"].mean()) * 100
    c1.metric("Visita (hoy)", f"{cobertura:,.0f}%")
    c2.metric("Score promedio", f"{score_prom:,.1f}%")
    c3.metric("Tiendas (filtro)", f"{len(df_t_filt)}")

    st.markdown("### 🛍️ Tiendas (clic para ir a Captura)")
    grid_cols = 3
    df_grid = df_t_filt.sort_values("tienda_id")
    blocks = [df_grid.iloc[i:i+grid_cols] for i in range(0, len(df_grid), grid_cols)]

    for block in blocks:
        cols = st.columns(len(block))
        for j, (_, r) in enumerate(block.iterrows()):
            row_hoy = df_hoy[df_hoy["tienda_id"] == r["tienda_id"]]
            if row_hoy.empty:
                color, sc = "#E5E5E5", 0.0
            else:
                try:
                    color = row_hoy["color"].iloc[0]
                    sc = float(row_hoy["score_visual"].iloc[0]) * 100.0
                except Exception:
                    color, sc = "#E5E5E5", 0.0

            with stylable_container(
                key=f"card_{r['tienda_id']}",
                css_styles="{ padding:0; }"
            ):
                cols[j].markdown(
                    f"""<div class="store-card" style="background:{color}">
                    <b>{r['tienda_id']} — {r['nombre']}</b>
                    <small>Score: {sc:,.0f}%</small>
                    </div>""",
                    unsafe_allow_html=True
                )
                # Botón: setea params y corta ejecución (evita error del primer clic)
                if cols[j].button("Capturar aquí", key=f"btn_{r['tienda_id']}"):
                    st.experimental_set_query_params(view="captura", tienda=r["tienda_id"])
                    st.stop()

    st.markdown("### 🔍 Detalle de hoy")
    st.dataframe(
        df_hoy[["tienda_id","nombre","ciudad","estatus","score_visual","notas"]]
        .rename(columns={"score_visual":"score_visual_0_1"}),
        use_container_width=True
    )

# ==================== CAPTURA ====================
elif view == "captura":
    st.subheader("📝 Captura diaria")

    # Opciones de tienda seguras contra filtros vacíos
    opciones = df_t_filt["tienda_id"].tolist() or df_t["tienda_id"].tolist()
    default_tienda = tienda_sel or (opciones[0] if opciones else None)
    idx = safe_index(opciones, default_tienda, default=0)
    idx = max(0, min(idx, max(len(opciones)-1, 0)))

    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", dt.date.today())
    tienda_id = c2.selectbox("Tienda", opciones, index=idx if opciones else 0)
    st.caption(f"Tienda seleccionada: **{tienda_id}**")

    st.text_area("Notas generales")

    st.markdown("Visual (Sí/No, notas y foto opcional)")
    for key, label in CATEGORIAS:
        bg = PASTEL[key]
        with stylable_container(
            key=f"wrap_{key}",
            css_styles=f"""
                {{
                    background: {bg};
                    border: 1px solid #e8e8e8;
                    border-radius: 12px;
                    margin-bottom: 12px;
                    padding: 0;
                    overflow: hidden;
                }}
                [data-testid="stExpander"] summary {{
                    background: transparent !important;
                    color: #4a4a4a !important;
                    font-weight: 700;
                    margin: 0 !important;
                    padding: 12px 14px !important;
                    border: none !important;
                }}
                [data-testid="stExpander"] > div[role="region"] {{
                    background: #ffffff !important;
                    border-top: 1px solid #f0f0f0;
                    border-radius: 0 0 12px 12px;
                    padding: 12px 14px 16px 14px;
                }}
                [data-testid="stExpander"] summary:focus {{ outline: none !important; }}
            """
        ):
            with st.expander(label, expanded=False):
                st.radio("¿Cumple?", ["No","Sí"], horizontal=True, key=f"{key}_si_demo")
                st.text_area("Notas", key=f"{key}_notas_demo")
                st.file_uploader("Foto (opcional)", type=["jpg","jpeg","png"], key=f"{key}_foto_demo")

    # Volver al dashboard (manteniendo tienda en la URL si quieres)
    if st.button("⬅️ Volver al Dashboard"):
        st.experimental_set_query_params(view="dashboard", tienda=tienda_id)
        st.stop()

# ==================== TAREAS / CONFIG ====================
elif view == "tareas":
    st.subheader("✅ Gestión de tareas (demo)")
    st.write("Aquí irán las tareas (no implementado en demo).")

elif view == "config":
    st.subheader("⚙️ Tiendas (demo)")
    st.dataframe(df_t, use_container_width=True)

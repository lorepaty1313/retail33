import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
from streamlit_extras.stylable_container import stylable_container

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Retail 33 - Demo Visual", page_icon="🛍️", layout="wide")

# ---- CSS ----
st.markdown("""
<style>
body, .stApp { background:#ffffff !important; color:#4a4a4a !important; font-family:"Helvetica Neue", sans-serif; }
h1, h2, h3, h4, h5, h6 { color:#4a4a4a !important; }
.stButton>button { background:#f6bd60; color:#4a4a4a !important; border-radius:8px; border:none; font-weight:700; }
.stButton>button:hover { background:#f28482; color:#fff !important; }
[data-testid="stMetricValue"]{ color:#4a4a4a !important; font-weight:800; }
[data-testid="stMetricLabel"]{ color:#6d6d6d !important; }
.store-card{ border-radius:12px; padding:10px; border:1px solid #e8e8e8; }
.store-card small{ display:block; font-weight:400; }
</style>
""", unsafe_allow_html=True)

# ---------- Datos demo / modelo ----------
TIENDAS_COLS = ["tienda_id","nombre","ciudad","gerente","estatus"]

# 33 tiendas (T01..T33)
def demo_data():
    ciudades = ["CDMX","PUE","GDL","MTY","QRO","MEX"]
    gerentes = ["Ana","Luis","Marta","Paco","Sofía","Diego","Lucía","Carlos"]
    rows = []
    for i in range(1, 34):
        tid = f"T{i:02d}"
        rows.append({
            "tienda_id": tid,
            "nombre": f"Tienda {i:02d}",
            "ciudad": ciudades[(i-1) % len(ciudades)],
            "gerente": gerentes[(i-1) % len(gerentes)],
            "estatus": "abierta" if (i % 7) else "cerrada"
        })
    df_t = pd.DataFrame(rows)[TIENDAS_COLS]

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
        {"fecha":hoy,"tienda_id":"T10","notas":"Bien vitrina",
         "pasarela_si":True,"acomodo_si":True,"producto_nuevo_si":True,"producto_rebaja_si":False,
         "display_si":True,"maniquies_si":True,"zona_impulso_si":True,"area_ropa_si":True},
        {"fecha":hoy,"tienda_id":"T15","notas":"Reponer maniquí",
         "pasarela_si":True,"acomodo_si":False,"producto_nuevo_si":True,"producto_rebaja_si":True,
         "display_si":True,"maniquies_si":False,"zona_impulso_si":True,"area_ropa_si":True},
        {"fecha":hoy,"tienda_id":"T22","notas":"Área ropa con huecos",
         "pasarela_si":True,"acomodo_si":True,"producto_nuevo_si":True,"producto_rebaja_si":True,
         "display_si":True,"maniquies_si":True,"zona_impulso_si":True,"area_ropa_si":False},
    ]
    df_c = pd.DataFrame(base)
    return df_t, df_c

df_t, df_c = demo_data()

# Categorías y colores
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
PASTEL = {
    "pasarela": "#A7C7E7", "acomodo": "#C6E2B5", "producto_nuevo": "#F7C6C7",
    "producto_rebaja": "#D9C2E9", "display": "#FFF3B0", "maniquies": "#FFB5A7",
    "zona_impulso": "#B5EAD7", "area_ropa": "#FFDAB9",
}

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

def rerun_compat():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            st.stop()

def set_params_and_rerun(**kwargs):
    """Prefiere la API nueva (st.query_params); fallback a experimental."""
    # limpia claves con None
    params = {k: v for k, v in kwargs.items() if v is not None}
    try:
        # API nueva
        st.query_params.clear()
        st.query_params.update(params)
    except Exception:
        # Fallback API vieja
        st.experimental_set_query_params(**{k: v for k, v in params.items()})
    rerun_compat()

def get_params():
    """Lee query params preferentemente con la API nueva."""
    try:
        return dict(st.query_params)
    except Exception:
        qp = st.experimental_get_query_params()
        return {k:(v[0] if isinstance(v, list) and v else v) for k,v in qp.items()}

# ---------------- Routing por query params ----------------
params = get_params()
view = params.get("view", "dashboard") or "dashboard"
tienda_qp = params.get("tienda", None)

st.title("🛍️ Retail 33 — Demo Visual")

# Filtros
st.sidebar.header("Filtros")
ciudad_sel = st.sidebar.selectbox("Ciudad", ["Todas"] + sorted(df_t["ciudad"].unique()))
estatus_sel = st.sidebar.selectbox("Estatus", ["Todos"] + sorted(df_t["estatus"].unique()))

# Navegación (radio) que escribe params y rerun
nav_labels = {"dashboard":"📊 Dashboard", "captura":"📝 Captura diaria", "tareas":"✅ Tareas", "config":"⚙️ Configuración"}
keys_list = list(nav_labels.keys())
try:
    current_index = keys_list.index(view)
except ValueError:
    current_index = 0

choice = st.sidebar.radio("Secciones", [nav_labels[k] for k in keys_list], index=current_index)
for k, lbl in nav_labels.items():
    if lbl == choice and k != view:
        set_params_and_rerun(view=k, tienda=tienda_qp)

# Aplica filtros a tiendas
df_t_filt = df_t.copy()
if ciudad_sel != "Todas":
    df_t_filt = df_t_filt[df_t_filt["ciudad"] == ciudad_sel]
if estatus_sel != "Todos":
    df_t_filt = df_t_filt[df_t_filt["estatus"] == estatus_sel]

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
    grid_cols = 6  # Para que quepan 33 en menos filas
    df_grid = df_t_filt.sort_values("tienda_id")
    blocks = [df_grid.iloc[i:i+grid_cols] for i in range(0, len(df_grid), grid_cols)]

    for block in blocks:
        cols = st.columns(len(block))
        for j, (_, r) in enumerate(block.iterrows()):
            # color/score seguro
            try:
                row_hoy = df_hoy[df_hoy["tienda_id"] == r["tienda_id"]]
                if row_hoy.empty:
                    raise ValueError("Sin datos")
                color = str(row_hoy["color"].iloc[0])
                sc = float(row_hoy["score_visual"].iloc[0]) * 100.0
            except Exception:
                color, sc = "#E5E5E5", 0.0

            with stylable_container(key=f"card_{r['tienda_id']}",
                                    css_styles=f"{{ background:{color}; border-radius:12px; padding:10px; border:1px solid #e8e8e8; }}"):
                cols[j].markdown(f"**{r['tienda_id']} — {r['nombre']}**  \n<small>Score: {sc:,.0f}%</small>", unsafe_allow_html=True)
                if cols[j].button("Capturar aquí", key=f"btn_{r['tienda_id']}"):
                    set_params_and_rerun(view="captura", tienda=r["tienda_id"])

    st.markdown("### 🔍 Detalle de hoy")
    st.dataframe(
        df_hoy[["tienda_id","nombre","ciudad","estatus","score_visual","notas"]]
        .rename(columns={"score_visual":"score_visual_0_1"}),
        use_container_width=True
    )

# ==================== CAPTURA ====================
elif view == "captura":
    st.subheader("📝 Captura diaria")

    opciones = df_t_filt["tienda_id"].tolist() or df_t["tienda_id"].tolist()
    default_tienda = tienda_qp or (opciones[0] if opciones else None)
    idx = safe_index(opciones, default_tienda, default=0)
    idx = max(0, min(idx, max(len(opciones)-1, 0)))

    c1, c2 = st.columns(2)
    _fecha = c1.date_input("Fecha", dt.date.today())
    tienda_id = c2.selectbox("Tienda", opciones, index=idx)
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

    # Volver al dashboard (usa API nueva; fallback ya está en set_params_and_rerun)
    if hasattr(st, "link_button"):
        st.link_button("⬅️ Volver al Dashboard", url=f"?view=dashboard&tienda={tienda_id}")
    else:
        if st.button("⬅️ Volver al Dashboard"):
            set_params_and_rerun(view="dashboard", tienda=tienda_id)

# ==================== TAREAS / CONFIG ====================
elif view == "tareas":
    st.subheader("✅ Gestión de tareas (demo)")
    st.write("Aquí irán las tareas (no implementado en demo).")

elif view == "config":
    st.subheader("⚙️ Tiendas (demo)")
    st.dataframe(df_t, use_container_width=True)

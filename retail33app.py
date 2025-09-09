# ------------------- UI (con navegación programática) -------------------
# Estado inicial
if "view" not in st.session_state: st.session_state.view = "dashboard"  # "dashboard" | "captura" | "tareas" | "config"
if "tienda_sel" not in st.session_state: st.session_state.tienda_sel = None

st.title("🛍️ Retail 33 — Demo Visual (sin Sheets)")

# Filtros
st.sidebar.header("Filtros")
ciudad_sel = st.sidebar.selectbox("Ciudad", ["Todas"] + sorted(df_t["ciudad"].unique()))
estatus_sel = st.sidebar.selectbox("Estatus", ["Todos"] + sorted(df_t["estatus"].unique()))

# Control de navegación (sidebar)
nav_map = {"📊 Dashboard": "dashboard", "📝 Captura diaria": "captura", "✅ Tareas": "tareas", "⚙️ Configuración": "config"}
nav_label = {v:k for k,v in nav_map.items()}
nav_choice = st.sidebar.radio(
    "Secciones",
    list(nav_map.keys()),
    index=list(nav_map.values()).index(st.session_state.view),
)
st.session_state.view = nav_map[nav_choice]

# Aplicar filtros a tiendas
df_t_filt = df_t.copy()
if ciudad_sel != "Todas": df_t_filt = df_t_filt[df_t_filt["ciudad"] == ciudad_sel]
if estatus_sel != "Todos": df_t_filt = df_t_filt[df_t_filt["estatus"] == estatus_sel]

# ---------- Funciones de apoyo ----------
def score_row(r):
    vals = [(1.0 if bool(r.get(col)) else 0.0) for col in BOOL_COLS]
    return np.mean(vals) if len(vals) else 0.0

def color_from_score(score, has_data):
    if not has_data: return "#E5E5E5"
    if score >= 0.8: return "#A8D5BA"
    if score >= 0.5: return "#FFF3B0"
    return "#FFB5A7"

def store_card(col, r, color, sc):
    # Botón con estilo de tarjeta; al hacer clic cambia a la vista de captura
    with stylable_container(
        key=f"card_{r['tienda_id']}",
        css_styles=f"""
            {{
                background: {color};
                border: 1px solid #e8e8e8;
                border-radius: 12px;
                padding: 10px;
            }}
            button[kind="secondary"] {{
                width: 100%;
                background: transparent;
                border: none;
                text-align: left;
                color: #444;
                font-weight: 700;
                padding: 6px 2px;
            }}
        """
    ):
        clicked = col.button(
            f"{r['tienda_id']} — {r['nombre']}\nScore: {sc:,.0f}%",
            key=f"btn_{r['tienda_id']}",
        )
    if clicked:
        st.session_state.tienda_sel = r["tienda_id"]
        st.session_state.view = "captura"
        st.experimental_rerun()

# ==================== VISTA: DASHBOARD ====================
if st.session_state.view == "dashboard":
    st.subheader("Resumen visual (hoy)")
    hoy = dt.date.today()

    df_hoy = df_t[["tienda_id","nombre","ciudad","estatus"]].merge(
        df_c[df_c["fecha"] == hoy], on="tienda_id", how="left"
    )
    df_hoy["score_visual"] = df_hoy.apply(score_row, axis=1)
    has_data = df_hoy[BOOL_COLS].notna().any(axis=1)
    df_hoy["color"] = [color_from_score(s, d) for s, d in zip(df_hoy["score_visual"], has_data)]

    tiendas_total = len(df_t_filt)
    cobertura = int(has_data.sum()) / max(len(df_hoy), 1)
    score_prom = float(df_hoy["score_visual"].mean())

    c1, c2, c3 = st.columns(3)
    c1.metric("Visita (hoy)", f"{cobertura*100:,.0f}%")
    c2.metric("Score promedio", f"{score_prom*100:,.1f}%")
    c3.metric("Tiendas (filtro)", f"{tiendas_total}")

    st.markdown("### 🛍️ Tiendas (clic para ir a captura)")
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
            store_card(cols[j], r, color, sc)

    st.markdown("### 🔍 Detalle de hoy")
    st.dataframe(
        df_hoy[["tienda_id","nombre","ciudad","estatus","score_visual","notas"]]
        .rename(columns={"score_visual":"score_visual_0_1"}),
        use_container_width=True
    )

# ==================== VISTA: CAPTURA ====================
elif st.session_state.view == "captura":
    st.subheader("📝 Captura diaria")
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", dt.date.today())
    # Si venimos desde un clic, usar esa tienda como default
    default_tienda = st.session_state.tienda_sel or (df_t_filt["tienda_id"].tolist() or df_t["tienda_id"].tolist())[0]
    tienda_id = c2.selectbox(
        "Tienda",
        df_t_filt["tienda_id"].tolist() or df_t["tienda_id"].tolist(),
        index=lambda opts: opts.index(default_tienda) if default_tienda in opts else 0
        (df_t_filt["tienda_id"].tolist() or df_t["tienda_id"].tolist())
    )
    st.session_state.tienda_sel = tienda_id
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
                [data-testid="stExpander"] > div[role=\"region\"] {{
                    background: #ffffff !important;
                    border-top: 1px solid #f0f0f0;
                    border-radius: 0 0 12px 12px;
                    padding: 12px 14px 16px 14px;
                }}
            """
        ):
            with st.expander(label, expanded=False):
                st.radio("¿Cumple?", ["No","Sí"], horizontal=True, key=f"{key}_si_demo")
                st.text_area("Notas", key=f"{key}_notas_demo")
                st.file_uploader("Foto (opcional)", type=["jpg","jpeg","png"], key=f"{key}_foto_demo")

    st.info("Demo: este modo no guarda datos (solo visualiza el layout).")
    st.button("⬅️ Volver al Dashboard", on_click=lambda: st.session_state.update(view="dashboard"))

# ==================== VISTA: TAREAS ====================
elif st.session_state.view == "tareas":
    st.subheader("✅ Gestión de tareas (demo)")
    st.write("Aquí irán las tareas (no implementado en demo).")

# ==================== VISTA: CONFIGURACIÓN ====================
elif st.session_state.view == "config":
    st.subheader("⚙️ Tiendas (demo)")
    st.dataframe(df_t, use_container_width=True)


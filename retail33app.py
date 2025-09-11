# app.py
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import io
from datetime import datetime
from supabase import create_client
from streamlit_extras.stylable_container import stylable_container

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Retail 33", page_icon="🛍️", layout="wide")

# ---- CSS simple (fondo blanco + texto gris) ----
st.markdown("""
<style>
body, .stApp { background:#ffffff !important; color:#4a4a4a !important; font-family:"Helvetica Neue", sans-serif; }
h1, h2, h3, h4, h5, h6 { color:#4a4a4a !important; }
.stButton>button { background:#f6bd60; color:#4a4a4a !important; border-radius:8px; border:none; font-weight:700; }
.stButton>button:hover { background:#f28482; color:#fff !important; }
.store{ border-radius:10px; padding:12px; font-weight:700; text-align:center; color:#444; }
.store small{ display:block; font-weight:400; }
</style>
""", unsafe_allow_html=True)

# ---------- Supabase ----------
@st.cache_resource
def get_sb():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["anon_key"])
sb = get_sb()

def login_ui():
    st.subheader("Acceso")
    email = st.text_input("Email")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        try:
            res = sb.auth.sign_in_with_password({"email": email, "password": pwd})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.error(f"No pude iniciar sesión: {e}")

def load_profile():
    uid = st.session_state.user.id
    data = sb.table("users_profile").select("*").eq("id", uid).single().execute()
    st.session_state.profile = data.data
    return data.data

def require_login():
    if "user" not in st.session_state:
        login_ui()
        st.stop()

def role_and_store():
    prof = st.session_state.get("profile") or load_profile()
    role = prof["role"]
    store_code = prof.get("store_code")
    return role, store_code

# ---------- Constantes ----------
CATEGORIAS = [
    ("pasarela","Pasarela de la moda"),
    ("acomodo","Acomodo guía visual"),
    ("producto_nuevo","Producto nuevo"),
    ("producto_rebaja","Producto rebaja"),
    ("display","Display"),
    ("maniquies","Maniquíes"),
    ("zona_impulso","Zona impulso"),
    ("area_ropa","Área ropa"),
]
BOOL_COLS = [f"{k}_si" for k,_ in CATEGORIAS]

PASTEL = {
    "pasarela":        "#A7C7E7",  "acomodo":         "#C6E2B5",
    "producto_nuevo":  "#F7C6C7",  "producto_rebaja": "#D9C2E9",
    "display":         "#FFF3B0",  "maniquies":       "#FFB5A7",
    "zona_impulso":    "#B5EAD7",  "area_ropa":       "#FFDAB9",
}

# ---------- Helpers ----------
def get_stores():
    resp = sb.table("stores").select("code,name,city,status").order("code").execute()
    return pd.DataFrame(resp.data)

def upload_photo(file, bucket, path):
    buf = io.BytesIO(file.read())
    sb.storage.from_(bucket).upload(path, buf.getvalue(),
                                    {"content-type": file.type, "upsert": True})
    return sb.storage.from_(bucket).create_signed_url(path, 60*60*24)["signedURL"]

def list_latest(bucket, prefix):
    items = sb.storage.from_(bucket).list(path=prefix)
    if not items:
        return None, None
    items = sorted(items, key=lambda x: (x.get("updated_at") or x.get("created_at") or x["name"]))
    name = items[-1]["name"]
    url = sb.storage.from_(bucket).create_signed_url(prefix + name, 60*60*24)["signedURL"]
    return name, url

def delete_latest(bucket, prefix):
    name, _ = list_latest(bucket, prefix)
    if name:
        sb.storage.from_(bucket).remove([prefix + name])
        return True
    return False

def upsert_capture(date_val, store_code, notes, form_vals, created_by):
    """Busca captura por (date, store_code). Si existe, actualiza; si no, inserta."""
    sel = sb.table("captures").select("id").eq("date", str(date_val)).eq("store_code", store_code).execute()
    payload = {
        "date": str(date_val),
        "store_code": store_code,
        "notes": notes,
        "created_by": created_by
    }
    payload.update(form_vals)
    if sel.data:
        cid = sel.data[0]["id"]
        sb.table("captures").update(payload).eq("id", cid).execute()
        return "update"
    else:
        sb.table("captures").insert(payload).execute()
        return "insert"

# ---------- App ----------
require_login()
role, my_store = role_and_store()
is_admin = role in ("jefe","andrea")
st.caption(f"Conectado como **{role}** — tienda: **{my_store or 'todas'}**")

tab_dash, tab_captura, tab_reportes = st.tabs(["📊 Dashboard", "📝 Captura", "📤 Reportes"])

# ==================== DASHBOARD ====================
with tab_dash:
    st.subheader("Resumen visual (por fecha)")
    df_stores = get_stores()
    fecha_dash = st.date_input("Fecha", dt.date.today(), key="fecha_dash")

    # Capturas de esa fecha
    resp = sb.table("captures").select("*").eq("date", str(fecha_dash)).execute()
    df_cap = pd.DataFrame(resp.data) if resp.data else pd.DataFrame()

    # Merge tiendas + captura del día
    df = df_stores.merge(df_cap, how="left", left_on="code", right_on="store_code")
    def score_row(r):
        vals = [(1.0 if bool(r.get(f"{k}_si")) else 0.0) for k,_ in CATEGORIAS]
        return float(np.mean(vals)) if vals else 0.0
    df["score_visual"] = df.apply(score_row, axis=1)

    def color_from_score(has_data, score):
        if not has_data: return "#E5E5E5"
        if score >= 0.8: return "#A8D5BA"
        if score >= 0.5: return "#FFF3B0"
        return "#FFB5A7"
    has_data = df[[f"{k}_si" for k,_ in CATEGORIAS]].notna().any(axis=1)
    df["color"] = [color_from_score(h, s) for h, s in zip(has_data, df["score_visual"])]

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tiendas", len(df_stores))
    c2.metric("Capturas hoy", int(has_data.sum()))
    c3.metric("Score promedio", f"{df['score_visual'].mean()*100:,.1f}%")

    st.markdown("### 🛍️ Tiendas (color por score)")
    grid_cols = 3
    blocks = [df.iloc[i:i+grid_cols] for i in range(0, len(df), grid_cols)]
    for block in blocks:
        cols = st.columns(len(block))
        for j, (_, r) in enumerate(block.iterrows()):
            sc = r["score_visual"] * 100
            cols[j].markdown(
                f"""<div class="store" style="background:{r['color']}">
                {r['code']}<small>{r['name']}</small>
                <small>Score: {sc:,.0f}%</small>
                </div>""",
                unsafe_allow_html=True
            )

    st.markdown("### 🔍 Detalle")
    show_cols = ["code","name","city","status","score_visual","notes"]
    if not df.empty:
        st.dataframe(df[show_cols].rename(columns={"code":"tienda","name":"nombre","score_visual":"score_0_1"}),
                     use_container_width=True)
    else:
        st.info("Sin capturas para esa fecha.")

# ==================== CAPTURA ====================
with tab_captura:
    st.subheader("Visita (captura + fotos)")
    df_stores = get_stores()
    if is_admin:
        _store = st.selectbox("Tienda", df_stores["code"].tolist(), index=0)
    else:
        _store = my_store
        st.info(f"Tu tienda: **{_store}**")

    col1, col2 = st.columns(2)
    fecha = col1.date_input("Fecha", dt.date.today(), key="fecha_cap")
    notas = col2.text_input("Notas generales", "")

    # --- Checklist + Foto Guía vs Actual por categoría ---
    form_vals = {}
    st.markdown("### Guía vs Actual por categoría")
    for key, label in CATEGORIAS:
        bg = PASTEL[key]
        with stylable_container(
            key=f"wrap_{key}",
            css_styles=f"""
                {{
                    background:{bg};
                    border: 1px solid #e8e8e8;
                    border-radius: 12px; margin-bottom: 12px;
                    padding:0; overflow:hidden;
                }}
                [data-testid="stExpander"] summary {{
                    background: transparent !important;
                    color:#4a4a4a !important; font-weight:700;
                    margin:0 !important; padding:12px 14px !important; border:none !important;
                }}
                [data-testid="stExpander"] > div[role="region"] {{
                    background:#ffffff !important; border-top:1px solid #f0f0f0;
                    border-radius:0 0 12px 12px; padding:12px 14px 16px 14px;
                }}
            """
        ):
            with st.expander(label, expanded=False):
                # Sí/No + Notas (se guardan en captures)
                val = st.radio("¿Cumple?", ["No","Sí"], horizontal=True, key=f"{key}_si_ui")
                form_vals[f"{key}_si"] = (val == "Sí")
                form_vals[f"{key}_notas"] = st.text_area("Notas", key=f"{key}_notas_ui")

                # Fotos
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Foto guía**")
                    prefix_g = f"org1/store_{_store}/{key}/guide/"
                    name_g, url_g = list_latest("guides", prefix_g)
                    if url_g: st.image(url_g, use_container_width=True)
                    else: st.info("Sin guía aún")
                    if is_admin:
                        gfile = st.file_uploader("Subir/actualizar guía", type=["jpg","jpeg","png"], key=f"g_{_store}_{key}")
                        if gfile:
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            path = f"{prefix_g}{ts}.jpg"
                            upload_photo(gfile, "guides", path)
                            st.success("Guía actualizada"); st.rerun()
                        if name_g and st.button("Eliminar guía (última)", key=f"delg_{key}"):
                            if delete_latest("guides", prefix_g):
                                st.success("Eliminada"); st.rerun()

                with c2:
                    st.markdown("**Foto actual**")
                    prefix_c = f"org1/store_{_store}/{key}/current/"
                    name_c, url_c = list_latest("current", prefix_c)
                    if url_c: st.image(url_c, use_container_width=True)
                    afile = st.file_uploader("Subir foto actual", type=["jpg","jpeg","png"], key=f"c_{_store}_{key}")
                    if afile:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"{prefix_c}{ts}.jpg"
                        upload_photo(afile, "current", path)
                        st.success("Foto actual subida"); st.rerun()

    # Guardar CAPTURA (upsert por fecha+tienda)
    if st.button("💾 Guardar captura"):
        who = st.session_state.user.id
        action = upsert_capture(fecha, _store, notas, form_vals, who)
        st.success("Captura actualizada" if action=="update" else "Captura guardada")

# ==================== REPORTES ====================
with tab_reportes:
    st.subheader("Exportar capturas")
    colA, colB = st.columns(2)
    d1 = colA.date_input("Desde", dt.date.today().replace(day=1))
    d2 = colB.date_input("Hasta", dt.date.today())
    btn = st.button("🔎 Consultar")
    if btn:
        q = sb.table("captures").select("*").gte("date", str(d1)).lte("date", str(d2))
        if not is_admin and my_store:
            q = q.eq("store_code", my_store)
        resp = q.order("date").execute()
        df = pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
        if df.empty:
            st.info("Sin capturas en el rango.")
        else:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Descargar CSV", data=csv, file_name="capturas.csv", mime="text/csv")
            # Excel opcional
            try:
                import xlsxwriter
                buff = io.BytesIO()
                with pd.ExcelWriter(buff, engine="xlsxwriter") as w:
                    df.to_excel(w, index=False, sheet_name="capturas")
                st.download_button("⬇️ Descargar Excel", data=buff.getvalue(),
                                   file_name="capturas.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception:
                pass

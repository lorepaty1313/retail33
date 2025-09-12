# retail33app.py
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import io, hashlib, time
from datetime import datetime
from supabase import create_client
from streamlit_extras.stylable_container import stylable_container
from PIL import Image, ImageOps
import httpx

# =========== Ajustes de compresión (rápida) ===========
FAST_TARGET_KB = 300
FAST_MAX_DIM   = 1280
FAST_PREFER_WEBP = True   # intenta WebP primero

# =========== Streamlit ===========
st.set_page_config(page_title="Retail 33", page_icon="🛍️", layout="wide")

# ---- CSS base ----
st.markdown("""
<style>
.card {background:#f6f8fb; border:1px solid #e7ecf3; border-radius:12px; padding:12px;}
.card h4{margin:0 0 8px 0}
.ph { background:#eaf0fa; border:1px dashed #c9d6ea; border-radius:10px;
      height:180px; display:flex; align-items:center; justify-content:center;
      color:#6b7280; font-weight:600; }
[data-testid="stFileUploader"] { background:white; border:1px solid #e7ecf3; border-radius:10px; padding:10px; }
body, .stApp { background:#ffffff !important; color:#4a4a4a !important; font-family:"Helvetica Neue", sans-serif; }
h1, h2, h3, h4, h5, h6 { color:#4a4a4a !important; }
.stButton>button { background:#f6bd60; color:#4a4a4a !important; border-radius:8px; border:none; font-weight:700; }
.stButton>button:hover { background:#f28482; color:#fff !important; }
.store{ border-radius:10px; padding:12px; font-weight:700; text-align:center; color:#444; }
.store small{ display:block; font-weight:400; }
</style>
""", unsafe_allow_html=True)

# =========== Supabase ===========
@st.cache_resource
def get_sb():
    supa = st.secrets.get("supabase", {})
    url = supa.get("url"); key = supa.get("anon_key")
    if not url or not key:
        st.error('Faltan secrets de Supabase. Crea .streamlit/secrets.toml con [supabase] url y anon_key.')
        st.stop()
    # Opciones con timeouts (compatibles)
    try:
        from supabase import ClientOptions
        opts = ClientOptions(
            postgrest_client_timeout=30,
            storage_client_timeout=60,
            retries=3
        )
        return create_client(url, key, options=opts)
    except Exception:
        return create_client(url, key)

sb = get_sb()

# =========== Login / Perfil ===========
def login_ui():
    st.subheader("Acceso")
    email = st.text_input("Email")
    pwd   = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        try:
            res = sb.auth.sign_in_with_password({"email": email, "password": pwd})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.error(f"No pude iniciar sesión: {e}")

def require_login():
    if "user" not in st.session_state:
        login_ui()
        st.stop()

def load_profile():
    uid = st.session_state.user.id
    resp = (sb.table("users_profile")
              .select("id,email,role,store_code")
              .eq("id", uid)
              .maybe_single()
              .execute())
    prof = resp.data
    if prof is None:
        st.error("Tu usuario no tiene perfil en users_profile. Crea esa fila (id, email, role, store_code).")
        st.stop()
    st.session_state.profile = prof
    return prof

def role_and_store():
    prof = st.session_state.get("profile") or load_profile()
    return prof["role"], prof.get("store_code")

# =========== Constantes ===========
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

# Catálogo (para Configuración / Upsert)
STORES_32 = [
    {"code":"T01","name":"Lázaro Cárdenas","city":"CDMX","status":"abierta"},
    {"code":"T05","name":"Zona Rosa","city":"CDMX","status":"abierta"},
    {"code":"T22","name":"Perisur","city":"CDMX","status":"abierta"},
    {"code":"T24","name":"Aeropuerto Nacional","city":"CDMX","status":"abierta"},
    {"code":"T40","name":"Centro Comercial Chimalhuacán","city":"Edomex","status":"abierta"},
    {"code":"T41","name":"Plaza Lindavista","city":"CDMX","status":"abierta"},
    {"code":"T43","name":"Galerías Coapa","city":"CDMX","status":"abierta"},
    {"code":"T44","name":"Parques Tepeyac","city":"CDMX","status":"abierta"},
    {"code":"T45","name":"Plaza Satélite","city":"Edomex","status":"abierta"},
    {"code":"T46","name":"Santa Fe","city":"CDMX","status":"abierta"},
    {"code":"T48","name":"Parque Las Antenas","city":"CDMX","status":"abierta"},
    {"code":"T49","name":"Melchor Ocampo","city":"CDMX","status":"abierta"},
    {"code":"T51","name":"Plaza Cuicuilco","city":"CDMX","status":"abierta"},
    {"code":"T53","name":"Outlet Lerma","city":"Edomex","status":"abierta"},
    {"code":"T54","name":"Universidad","city":"CDMX","status":"abierta"},
    {"code":"T56","name":"Punta Norte","city":"Edomex","status":"abierta"},
    {"code":"T57","name":"Parque Delta","city":"CDMX","status":"abierta"},
    {"code":"T58","name":"Las Américas","city":"Edomex","status":"abierta"},
    {"code":"T60","name":"Tepeyac","city":"CDMX","status":"abierta"},
    {"code":"T61","name":"Parque Lindavista","city":"CDMX","status":"abierta"},
    {"code":"T62","name":"La Cúspide","city":"Edomex","status":"abierta"},
    {"code":"T63","name":"Tezontle","city":"CDMX","status":"abierta"},
    {"code":"T64","name":"Plaza Oriente","city":"CDMX","status":"abierta"},
    {"code":"T69","name":"Parque Vía Vallejo","city":"CDMX","status":"abierta"},
    {"code":"T71","name":"Parque Toreo","city":"Edomex","status":"abierta"},
    {"code":"T73","name":"Ciudad Jardín","city":"Edomex","status":"abierta"},
    {"code":"T75","name":"Plaza del Sol","city":"Jalisco","status":"abierta"},
    {"code":"T26","name":"La Perla Guadalajara","city":"Jalisco","status":"abierta"},
    {"code":"T27","name":"Galerías Guadalajara","city":"Jalisco","status":"abierta"},
    {"code":"T39","name":"Centro Comercial Mulza","city":"Guanajuato","status":"abierta"},
    {"code":"T47","name":"Parques Puebla","city":"Puebla","status":"abierta"},
    {"code":"T55","name":"Angelópolis","city":"Puebla","status":"abierta"},
]

# =========== Helpers de DB / Storage ===========
def get_stores():
    resp = sb.table("stores").select("code,name,city,status").order("code").execute()
    return pd.DataFrame(resp.data)

def _resize_keep_aspect(im: Image.Image, max_side: int) -> Image.Image:
    w, h = im.size
    side = max(w, h)
    if side <= max_side:
        return im
    scale = max_side / float(side)
    return im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

def _encode(im: Image.Image, fmt: str, quality: int) -> bytes:
    buf = io.BytesIO()
    if fmt.upper() == "WEBP":
        im.save(buf, format="WEBP", quality=quality, method=6)
    elif fmt.upper() == "JPEG":
        im.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    else:
        raise ValueError("Formato no soportado")
    return buf.getvalue()

def compress_image_adaptive(file, target_kb=FAST_TARGET_KB, max_dim=FAST_MAX_DIM, prefer_webp=FAST_PREFER_WEBP):
    """Devuelve (bytes, mime) <= target_kb aprox, probando WebP y luego JPEG."""
    try:
        file.seek(0)
    except Exception:
        pass
    img = Image.open(file)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    img = _resize_keep_aspect(img, max_dim)
    target_bytes = int(target_kb * 1024)

    def _search(fmt):
        lo, hi = 35, 92
        best = None
        while lo <= hi:
            q = (lo + hi) // 2
            data = _encode(img, fmt, q)
            if len(data) <= target_bytes:
                best = data
                lo = q + 1
            else:
                hi = q - 1
        return best

    if prefer_webp:
        try:
            data = _search("WEBP")
            if data:
                return data, "image/webp"
        except Exception:
            pass
    data = _search("JPEG")
    if not data:
        data = _encode(img, "JPEG", 35)
    return data, "image/jpeg"

def file_sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()

# --- Naming policy: sobrescribir siempre la última ---
LATEST_MODE = True
def make_path(store_code: str, categoria_key: str, typ: str) -> str:
    # typ: "guide" o "current"
    if LATEST_MODE:
        return f"org1/store_{store_code}/{categoria_key}/{typ}/latest.jpg"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"org1/store_{store_code}/{categoria_key}/{typ}/{ts}.jpg"

def upload_photo(file, bucket, path, target_kb=FAST_TARGET_KB):
    """Comprime y sube a Supabase Storage. Devuelve URL firmada (24h)."""
    try:
        data, mime = compress_image_adaptive(file, target_kb=target_kb)
    except Exception:
        try:
            file.seek(0)
        except Exception:
            pass
        data = file.read()
        if isinstance(data, str):
            data = data.encode("utf-8")
        mime = getattr(file, "type", None) or "application/octet-stream"

    # Cache-control MUY corto para evitar imagen vieja
    try:
        from supabase.storage import FileOptions
        opts = FileOptions(content_type=str(mime), cache_control="max-age=5, must-revalidate", upsert=True)
        sb.storage.from_(bucket).upload(path, data, file_options=opts)
    except Exception:
        sb.storage.from_(bucket).upload(
            path, data,
            file_options={"contentType": str(mime), "cacheControl": "5", "upsert": "true"}
        )
    return sb.storage.from_(bucket).create_signed_url(path, 60*60*24)["signedURL"]

def list_latest(bucket, prefix):
    items = sb.storage.from_(bucket).list(path=prefix)
    if not items:
        return None, None
    items = sorted(items, key=lambda x: (x.get("updated_at") or x.get("created_at") or x["name"]))
    name = items[-1]["name"]
    url = sb.storage.from_(bucket).create_signed_url(prefix + name, 60*60*24)["signedURL"]
    return name, url

def delete_photo(bucket: str, store_code: str, categoria_key: str, typ: str) -> int:
    """
    Borra la foto 'del día' / 'última' según la estrategia:
    - LATEST_MODE=True: borra latest.jpg
    - LATEST_MODE=False: borra archivos cuyo nombre empiece por YYYYMMDD_ (hoy)
    Devuelve cuántos archivos borró.
    """
    prefix = f"org1/store_{store_code}/{categoria_key}/{typ}/"
    if LATEST_MODE:
        # Borrar latest.jpg si existe
        items = sb.storage.from_(bucket).list(path=prefix) or []
        targets = [it["name"] for it in items if it["name"] == "latest.jpg"]
    else:
        today = dt.date.today().strftime("%Y%m%d")
        items = sb.storage.from_(bucket).list(path=prefix) or []
        targets = [it["name"] for it in items if it["name"].startswith(today)]
    if not targets:
        return 0
    sb.storage.from_(bucket).remove([prefix + n for n in targets])
    return len(targets)

def delete_latest(bucket, prefix):
    name, _ = list_latest(bucket, prefix)
    if name:
        sb.storage.from_(bucket).remove([prefix + name])
        return True
    return False

def get_guide_url(store_code, categoria_key):
    _, url = list_latest("guides", f"org1/store_{store_code}/{categoria_key}/guide/")
    return url

def get_current_url(store_code, categoria_key):
    _, url = list_latest("current", f"org1/store_{store_code}/{categoria_key}/current/")
    return url

def upsert_capture(date_val, store_code, notes, form_vals, created_by):
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

def with_retries(fn, *args, **kwargs):
    last_err = None
    for i in range(3):
        try:
            return fn(*args, **kwargs)
        except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException) as e:
            last_err = e
            time.sleep(0.8 * (i + 1))
    raise last_err

def nocache(url: str) -> str:
    if not url:
        return url
    sep = '&' if '?' in url else '?'
    return f"{url}{sep}cb={int(time.time())}"

# =========== App ===========
require_login()
role, my_store = role_and_store()
is_admin = role in ("jefe","andrea")
st.caption(f"Conectado como **{role}** — tienda: **{my_store or 'todas'}**")

# --- Navegación ---
TABS = ["📊 Dashboard", "📝 Captura", "📤 Reportes", "⚙️ Configuración"]
st.session_state.setdefault("active_tab", "📊 Dashboard")
active_tab = st.radio(
    "Navegación", TABS, horizontal=True,
    index=TABS.index(st.session_state["active_tab"]),
    label_visibility="collapsed", key="nav_radio"
)
st.session_state["active_tab"] = active_tab

# ==================== DASHBOARD ====================
if st.session_state["active_tab"] == "📊 Dashboard":
    st.subheader("Resumen visual (por fecha)")
    df_stores = get_stores()
    fecha_dash = st.date_input("Fecha", dt.date.today(), key="fecha_dash")

    # Capturas del día
    resp = sb.table("captures").select("*").eq("date", str(fecha_dash)).execute()
    df_cap = pd.DataFrame(resp.data or [])

    # Asegura columnas
    if "store_code" not in df_cap.columns:
        df_cap["store_code"] = pd.Series(dtype="object")
    if "notes" not in df_cap.columns:
        df_cap["notes"] = pd.Series(dtype="object")
    for k, _ in CATEGORIAS:
        col = f"{k}_si"
        if col not in df_cap.columns:
            df_cap[col] = pd.Series(dtype="float")

    # Merge tiendas + capturas
    df = df_stores.merge(df_cap, how="left", left_on="code", right_on="store_code")

    # Score + color
    for k, _ in CATEGORIAS:
        if f"{k}_si" not in df.columns:
            df[f"{k}_si"] = pd.NA

    has_data = df[[f"{k}_si" for k, _ in CATEGORIAS]].notna().any(axis=1)

    def score_row(r):
        vals = [(1.0 if bool(r.get(f"{k}_si")) else 0.0) for k, _ in CATEGORIAS]
        return float(np.mean(vals)) if vals else 0.0

    df["score_visual"] = df.apply(score_row, axis=1)

    def color_from_score(have, score):
        if not have: return "#E5E5E5"
        if score >= 0.8: return "#A8D5BA"
        if score >= 0.5: return "#FFF3B0"
        return "#FFB5A7"

    df["color"] = [color_from_score(h, s) for h, s in zip(has_data, df["score_visual"])]
    # Si la tienda está cerrada, fuerza gris
    df.loc[df["status"].str.lower() == "cerrada", "color"] = "#E0E0E0"

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Tiendas", len(df_stores))
    c2.metric("Capturas hoy", int(has_data.sum()))
    c3.metric("Score promedio", f"{df['score_visual'].mean()*100:,.1f}%")

    # Grid clickeable
    st.markdown("### 🛍️ Tiendas (clic para capturar)")
    TILE_STYLE = "min-height:110px; display:flex; flex-direction:column; justify-content:center;"
    st.session_state.setdefault("selected_store", None)
    grid_cols = 3
    blocks = [df.iloc[i:i+grid_cols] for i in range(0, len(df), grid_cols)]

    for block in blocks:
        cols = st.columns(len(block), gap="medium")
        for j, (_, r) in enumerate(block.iterrows()):
            sc = int(round(float(r.get("score_visual") or 0) * 100))
            can_click = is_admin or (my_store == r["code"])
            cols[j].markdown(
                f"""<div class="store" style="background:{r['color']}; {TILE_STYLE}">
                {r['code']}<small>{r['name']}</small>
                <small>Score: {sc}%</small>
                </div>""",
                unsafe_allow_html=True
            )
            clicked = cols[j].button("📸 Capturar", key=f"cap_{r['code']}",
                                     use_container_width=True, disabled=not can_click)
            if clicked:
                st.session_state["selected_store"] = r["code"]
                st.session_state["active_tab"] = "📝 Captura"
                st.rerun()

    # Detalle (solo admins)
    if is_admin:
        st.markdown("### 🔍 Detalle")
        show_cols = ["code","name","city","status","score_visual","notes"]
        if not df.empty:
            st.dataframe(
                df[show_cols].rename(columns={"code":"tienda","name":"nombre","score_visual":"score_0_1"}),
                use_container_width=True
            )
        else:
            st.info("Sin capturas para esa fecha.")

# ==================== CAPTURA ====================
elif st.session_state["active_tab"] == "📝 Captura":
    st.subheader("Visita (captura + fotos)")
    df_stores = get_stores()
    if is_admin:
        codes = df_stores["code"].tolist()
        default_ix = codes.index(st.session_state["selected_store"]) if st.session_state.get("selected_store") in codes else 0
        _store = st.selectbox("Tienda", codes, index=default_ix)
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
                # fila: cumple + notas (empleado)
                col_check, col_notes = st.columns([1,3], gap="medium")
                val = col_check.radio("¿Cumple?", ["No","Sí"], horizontal=True, key=f"{key}_si_ui")
                notas_cat = col_notes.text_area("Notas (empleado)", key=f"{key}_notas_ui")
                form_vals[f"{key}_si"] = (val == "Sí")
                form_vals[f"{key}_notas"] = notas_cat

                # hedonía + notas management (solo admin)
                hedo_opts = [1, 2, 3, 4, 5]
                hedo_labels = {1:"😣 1", 2:"🙁 2", 3:"😐 3", 4:"🙂 4", 5:"🤩 5"}
                hedo_val = st.radio("Calificación (1-5) (solo admin)", hedo_opts,
                                    format_func=lambda x: hedo_labels[x], horizontal=True,
                                    key=f"{key}_hedo_ui", disabled=not is_admin)
                form_vals[f"{key}_hedo"] = int(hedo_val) if is_admin else None

                notas_mgmt = st.text_area("Notas management (solo admin)",
                                          key=f"{key}_notas_mgmt_ui", disabled=not is_admin)
                form_vals[f"{key}_notas_mgmt"] = notas_mgmt if is_admin else None

                target_store = _store if is_admin else my_store

                # fila: fotos lado a lado
                g, a = st.columns(2, gap="large")

                # ---- Foto guía (solo admin) ----
                with g:
                    st.markdown("#### Foto guía")
                    url_g = get_guide_url(target_store, key)
                    if url_g:
                        st.image(nocache(url_g), use_container_width=True)
                    else:
                        st.markdown('<div class="ph">Sin guía aún</div>', unsafe_allow_html=True)

                    c1, c2 = st.columns(2)
                    if is_admin and c1.button("🗑️ Eliminar guía (hoy/última)", key=f"del_g_{target_store}_{key}"):
                        deleted = delete_photo("guides", target_store, key, "guide")
                        if deleted:
                            st.success("Guía eliminada.")
                            st.rerun()
                        else:
                            st.info("No hay guía para eliminar.")

                    if is_admin:
                        gfile = c2.file_uploader("Subir/actualizar guía", type=["jpg","jpeg","png","heic","heif","webp"],
                                                 key=f"g_{target_store}_{key}")
                        if gfile:
                            path = make_path(target_store, key, "guide")
                            upload_photo(gfile, "guides", path)
                            st.success("Guía actualizada.")
                            st.rerun()

                # ---- Foto actual (empleado/admin) ----
                with a:
                    st.markdown("#### Foto actual")
                    url_c = get_current_url(target_store, key)
                    if url_c:
                        st.image(nocache(url_c), use_container_width=True)
                    else:
                        st.markdown('<div class="ph">Sin foto actual</div>', unsafe_allow_html=True)

                    c3, c4 = st.columns(2)
                    can_manage_current = is_admin or (my_store == target_store)
                    if can_manage_current and c3.button("🗑️ Eliminar actual (hoy/última)", key=f"del_c_{target_store}_{key}"):
                        deleted = delete_photo("current", target_store, key, "current")
                        if deleted:
                            st.success("Foto actual eliminada.")
                            st.rerun()
                        else:
                            st.info("No hay foto actual para eliminar.")

                    if can_manage_current:
                        cfile = c4.file_uploader("Subir foto actual", type=["jpg","jpeg","png","heic","heif","webp"],
                                                 key=f"c_{target_store}_{key}")
                        if cfile:
                            path = make_path(target_store, key, "current")
                            upload_photo(cfile, "current", path)
                            st.success("Foto actual subida.")
                            st.rerun()

    # Guardar CAPTURA (upsert por fecha+tienda)
    if st.button("💾 Guardar captura"):
        who = st.session_state.user.id
        action = with_retries(upsert_capture, fecha, _store, notas, form_vals, who)
        st.success("Captura actualizada" if action=="update" else "Captura guardada")

# ==================== REPORTES ====================
elif st.session_state["active_tab"] == "📤 Reportes":
    st.subheader("Exportar capturas")
    df = pd.DataFrame()
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

    st.markdown("---")
    show_photos = st.checkbox("👀 Mostrar fotos guía y actuales por sección")
    if show_photos:
        if df.empty:
            st.info("No hay capturas en el rango para mostrar fotos.")
        else:
            stores_in_df = sorted(df["store_code"].dropna().unique().tolist()) if "store_code" in df.columns else []
            if not stores_in_df:
                st.info("No hay tiendas identificadas en el resultado.")
            else:
                for scode in stores_in_df:
                    st.markdown(f"### 🏪 Tienda {scode}")
                    for key, label in CATEGORIAS:
                        gcol, ccol = st.columns(2)
                        with gcol:
                            st.caption(f"Guía — {label}")
                            url_g = get_guide_url(scode, key)
                            if url_g: st.image(nocache(url_g), use_container_width=True)
                            else:     st.write("Sin guía")
                        with ccol:
                            st.caption(f"Actual — {label}")
                            url_c = get_current_url(scode, key)
                            if url_c: st.image(nocache(url_c), use_container_width=True)
                            else:     st.write("Sin foto actual")

# ==================== CONFIGURACIÓN ====================
elif st.session_state["active_tab"] == "⚙️ Configuración":
    st.subheader("Catálogo de tiendas (DB vs. lista local)")
    col_left, col_right = st.columns(2)

    # Ver tiendas en la DB
    if col_left.button("🔍 Ver tiendas en la DB"):
        resp_db = sb.table("stores").select("code,name,city,status").order("code").execute()
        df_db = pd.DataFrame(resp_db.data or [])
        st.info(f"Tiendas en DB: {len(df_db)}")
        st.dataframe(df_db, use_container_width=True)
    else:
        st.caption("Usa el botón para listar lo que hay en Supabase → stores.")

    # Vista previa lista local
    col_right.write("Lista local (lo que subiríamos):")
    col_right.dataframe(pd.DataFrame(STORES_32), use_container_width=True)

    st.markdown("---")
    c1, c2, _ = st.columns([1,2,2])
    confirm = c1.checkbox("Confirmo vaciar", value=False)
    if c2.button("🗑️ Vaciar tabla stores (admin)") and confirm:
        if is_admin:
            sb.table("stores").delete().neq("code","").execute()
            st.success("Tabla 'stores' vaciada.")
        else:
            st.error("Necesitas rol jefe/andrea para vaciar.")

    if st.button("⬆️ Subir/actualizar catálogo (upsert)"):
        try:
            sb.table("stores").upsert(STORES_32, on_conflict="code").execute()
            resp_db = sb.table("stores").select("code,name,city,status").order("code").execute()
            df_db = pd.DataFrame(resp_db.data or [])
            st.success(f"Listo. Tiendas en DB ahora: {len(df_db)}")
            st.dataframe(df_db, use_container_width=True)
        except Exception as e:
            st.error(f"No pude hacer upsert: {e}")

    # --- Limpieza de fotos (mantener pocas por sección) ---
    st.markdown("---")
    st.subheader("🧹 Limpieza de fotos (mantén solo la última si usas timestamps)")
    def cleanup_bucket(bucket: str, keep:int=1):
        total_deleted = 0
        try:
            stores = get_stores()["code"].tolist()
        except Exception:
            stores = []
        for store_code in stores:
            for key, _ in CATEGORIAS:
                for typ in ["guide", "current"]:
                    prefix = f"org1/store_{store_code}/{key}/{typ}/"
                    try:
                        items = sb.storage.from_(bucket).list(path=prefix) or []
                    except Exception:
                        items = []
                    if not items:
                        continue
                    items_sorted = sorted(
                        items,
                        key=lambda x: x.get("updated_at") or x.get("created_at") or x["name"]
                    )
                    to_delete = items_sorted[:-keep] if len(items_sorted) > keep else []
                    if to_delete:
                        paths = [prefix + it["name"] for it in to_delete]
                        sb.storage.from_(bucket).remove(paths)
                        total_deleted += len(paths)
        return total_deleted

    colL, colR = st.columns(2)
    keep_n = colL.number_input("Conservar últimas N por sección", 1, 10, 1)
    if colR.button("Eliminar excedentes ahora"):
        deleted_guides = cleanup_bucket("guides", keep=int(keep_n))
        deleted_current = cleanup_bucket("current", keep=int(keep_n))
        st.success(f"Listo. Borradas {deleted_guides + deleted_current} fotos "
                   f"(guides: {deleted_guides}, current: {deleted_current}).")

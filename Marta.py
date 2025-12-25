import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    .logo-container { text-align: center; margin-top: -65px !important; margin-bottom: 30px !important; padding-bottom: 5px; }
    .logo-container img { width: 200px; cursor: pointer; }
    .sticky-user-badge { position: fixed; bottom: 15px; left: 15px; width: 270px; background-color: #eab308; color: #1e293b !important; padding: 5px 10px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; text-align: center; z-index: 999999; box-shadow: 0 4px 10px rgba(0,0,0,0.4); border: 1px solid white; }
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; font-size: 0.85rem !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 5px 10px !important; }
    button[data-baseweb="tab"] { font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; margin-right: 5px; padding: 10px 25px !important; border: 1px solid #cbd5e1 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }
    .term-box { background: #334155; padding: 6px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 5px; color: white; font-size: 0.72rem; }
    .sidebar-header-nav { color: #eab308; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; margin-top: -12px !important; margin-bottom: 5px !important; }
    .sidebar-header { color: #eab308; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. BAZA UŻYTKOWNIKÓW
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_param = st.query_params.get("u", "")
k_param = st.query_params.get("k", "")
if u_param in USERS and USERS[u_param] == k_param: zalogowany = u_param
else: st.error("BŁĄD AUTORYZACJI"); st.stop()

# ==========================================================
# 3. FUNKCJE TECHNICZNE (STABILNY ODCZYT)
# ==========================================================
def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=60) # Cache danych na 60 sekund, aby uniknąć zerowania
def pobierz_df_stabilnie(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df[df.iloc[:, 0].astype(str).str.strip() != ""].copy()
    except:
        return pd.DataFrame()

def generuj_kalendarz_html(df_zadania, user):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dni_z_terminami = []
    if not df_zadania.empty and 'DEADLINE' in df_zadania.columns:
        df_f = df_zadania if user == "Andrzej" else df_zadania[df_zadania['OSOBA'].str.contains(user, na=False)]
        df_f['DT_TMP'] = pd.to_datetime(df_f['DEADLINE'], dayfirst=True, errors='coerce')
        dni_z_terminami = df_f[df_f['DT_TMP'].dt.month == now.month]['DT_TMP'].dt.day.tolist()
    html = f'<div style="background:white; padding:8px; border-radius:8px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1.2; font-size:11px;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; border-bottom:1px solid #eee; padding-bottom:5px;">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    for week in cal:
        html += '<tr style="height:22px;">'
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                bg = "#eab308" if day == now.day else "transparent"
                color = "#ef4444" if day in dni_z_terminami else "#1e293b"
                border = "1px solid #ef4444" if day in dni_z_terminami else "none"
                html += f'<td style="text-align:center; padding:2px; font-weight:700; background-color:{bg}; color:{color}; border:{border}; border-radius:4px;">{day}</td>'
        html += "</tr>"
    return html + "</tbody></table></div>"

# ==========================================================
# 4. SIDEBAR
# ==========================================================
df_biez = pobierz_df_stabilnie("Zadania bieżące")
df_zreal = pobierz_df_stabilnie("Zadania zrealizowane")
df_chat = pobierz_df_stabilnie("CZAT")
has_new = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty if not df_chat.empty and 'ODBIORCA' in df_chat.columns else False

st.markdown(f'<div class="sticky-user-badge">👤 ZALOGOWANO: {zalogowany.upper()}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.markdown(f'<div class="logo-container"><a href="?u={u_param}&k={k_param}" target="_self"><img src="{LOGO_URL}"></a></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header-nav">🧭 Nawigacja</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): 
            st.cache_data.clear() # Ręczne wymuszenie pobrania świeżych danych
            st.rerun()
    st.markdown('<div style="border-top: 1px solid #334155; margin: 8px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">📅 Twoje Terminy</div>', unsafe_allow_html=True)
    st.components.v1.html(generuj_kalendarz_html(df_biez, zalogowany), height=175)
    st.markdown('<div class="sidebar-header">🕒 Nadchodzące Twoje</div>', unsafe_allow_html=True)
    if not df_biez.empty:
        df_side = df_biez if zalogowany == "Andrzej" else df_biez[df_biez['OSOBA'].str.contains(zalogowany, na=False)]
        for _, r in df_side.head(5).iterrows():
            try:
                dni_val = pd.to_numeric(r.get('DNI', 0), errors='coerce')
                status_icon = "🔴" if dni_val >= -2 else "🟢"
            except: status_icon = "⚪"
            st.markdown(f'<div class="term-box">{status_icon} <b>{r.get("DEADLINE","")}</b>: {str(r.get("TREŚĆ ZADANIA",""))[:32]}...</div>', unsafe_allow_html=True)

# ==========================================================
# 5. WIDOK GŁÓWNY
# ==========================================================
chat_label = "💬 CZAT 🔴" if has_new else "💬 CZAT"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", chat_label])
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))
for i, kat in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_df_stabilnie(kat)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📋 Razem", len(df))
        if not df.empty and 'DNI' in df.columns:
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
        else: m2.metric("🔥 Pilne (-2+)", 0)
        m3.metric("✅ Zrealizowane", len(df_zreal))
        m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
        if not df.empty: st.data_editor(df, use_container_width=True, hide_index=True, height=550)
        else: st.info("Brak aktywnych zadań w tej sekcji.")

st.markdown(f'<div style="margin-top: 15px; padding: 5px 15px; background-color: #1e293b; border-top: 3px solid #eab308; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; color: white;"><div style="color:#eab308; font-weight:800; font-size:0.8rem;">UZDROWISKO CIECHOCINEK S.A.</div><div>{now_pl.strftime("%d.%m.%Y | %H:%M:%S")}</div></div>', unsafe_allow_html=True)

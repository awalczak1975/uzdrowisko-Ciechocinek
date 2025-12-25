import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (NAPRAWA WIDOCZNOŚCI)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=15000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    .logo-container { text-align: center; margin-top: -35px !important; margin-bottom: 10px !important; }
    .logo-container img { width: 190px; cursor: pointer; }

    /* --- NOWY PŁYWAJĄCY PASEK ZALOGOWANIA (ZAWSZE NA WIERZCHU) --- */
    .sticky-user-badge {
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 260px; /* Dopasowane do szerokości sidebaru */
        background-color: #eab308;
        color: #1e293b !important;
        padding: 12px;
        border-radius: 10px;
        font-weight: 900;
        font-size: 0.9rem;
        text-align: center;
        z-index: 999999;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        border: 2px solid white;
    }

    .sidebar-divider { border-top: 1px solid #334155; margin: 8px 0; }
    .sidebar-header { color: #eab308; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; }
    
    /* ODSTĘP NA DOLE SIDEBARA, ŻEBY BADGE NICZEGO NIE ZASŁANIAŁ */
    .sidebar-content-spacer { height: 100px; }

    .term-box { background: #334155; padding: 6px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 5px; color: white; font-size: 0.72rem; }
    
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; }

    button[data-baseweb="tab"] { font-size: 1.1rem !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE TECHNICZNE
# ==========================================================
def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

def pobierz_df(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df[df.iloc[:, 0].astype(str).str.strip() != ""].copy()
    except: return pd.DataFrame()

def generuj_kalendarz_html(df_zadania):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dni_z_terminami = []
    if not df_zadania.empty and 'DEADLINE' in df_zadania.columns:
        df_zadania['DT_TMP'] = pd.to_datetime(df_zadania['DEADLINE'], dayfirst=True, errors='coerce')
        dni_z_terminami = df_zadania[df_zadania['DT_TMP'].dt.month == now.month]['DT_TMP'].dt.day.tolist()

    html = f'<div style="background:white; padding:8px; border-radius:8px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1.2; font-size:11px;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; border-bottom:1px solid #eee; padding-bottom:5px;">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    for week in cal:
        html += '<tr style="height:22px;">'
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                bg = "#eab308" if day == now.day else "transparent"
                color = "#ef4444" if day in dni_z_terminami else "#1e293b"
                html += f'<td style="text-align:center; font-weight:700; background-color:{bg}; color:{color}; border-radius:4px;">{day}</td>'
        html += "</tr>"
    return html + "</tbody></table></div>"

# ==========================================================
# 3. LOGIKA I SIDEBAR (Z FIXOWANYM BADGEM)
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = "Andrzej Walczak"
else: st.error("BŁĄD LOGOWANIA"); st.stop()

df_biez = pobierz_df("Zadania bieżące")
df_chat = pobierz_df("CZAT")
has_new = not df_chat[(df_chat['ODBIORCA'] == "Andrzej") & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty if not df_chat.empty and 'ODBIORCA' in df_chat.columns else False

# --- PŁYWAJĄCA ETYKIETA (WYWOŁANA POZA SIDEBAREM DLA PEWNOŚCI) ---
st.markdown(f'<div class="sticky-user-badge">👤 ZALOGOWANO: {zalogowany.upper()}</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f'<div class="logo-container"><a href="?u={u}&k={k}" target="_self"><img src="{LOGO_URL}"></a></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-header">🧭 Nawigacja</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ DODAJ", use_container_width=True): st.session_state.show_form = True
    with c2:
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">📅 Kalendarz</div>', unsafe_allow_html=True)
    st.components.v1.html(generuj_kalendarz_html(df_biez), height=175)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">🕒 Nadchodzące (5)</div>', unsafe_allow_html=True)
    if not df_biez.empty:
        for _, r in df_biez.head(5).iterrows():
            st.markdown(f'<div class="term-box"><span style="color:#eab308; font-weight:bold;">{r.get("DEADLINE","")}</span>: {str(r.get("TREŚĆ ZADANIA",""))[:35]}...</div>', unsafe_allow_html=True)
    
    # Miejsce na dole sidebaru, aby pływająca etykieta nic nie zakryła
    st.markdown('<div class="sidebar-content-spacer"></div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
chat_tab_label = "💬 CZAT 🔴" if has_new else "💬 CZAT"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", chat_tab_label])

df_zrealizowane = pobierz_df("Zadania zrealizowane")
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, kat in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_df(kat)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📋 Razem", len(df))
        if not df.empty and 'DNI' in df.columns:
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
        m3.metric("✅ Zrealizowane", len(df_zrealizowane))
        m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
        if not df.empty:
            st.data_editor(df, use_container_width=True, hide_index=True, height=550)

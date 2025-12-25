import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (ZOPTYMALIZOWANE ODSTĘPY)
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

    /* NAGŁÓWKI SIDEBARA - ZREDUKOWANE ODSTĘPY */
    .sidebar-divider { border-top: 1px solid #334155; margin: 5px 0; } /* Zmniejszony margines z 10 na 5 */
    .sidebar-header { color: #eab308; font-size: 0.8rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 3px; } /* Zmniejszony margines z 5 na 3 */

    /* KOMPAKTOWE BOX ZADANIA */
    .term-box {
        background: #334155; 
        padding: 4px 8px; 
        border-radius: 6px; 
        border-left: 4px solid #ef4444; 
        margin-bottom: 3px; 
        color: white; 
        font-size: 0.7rem;
        line-height: 1.1;
    }
    .term-date { color: #eab308; font-weight: bold; margin-right: 3px; }

    /* METRYKI WYŚRODKOWANE */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 10px !important; }

    /* ZAKŁADKI */
    button[data-baseweb="tab"] { font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; margin-right: 5px; padding: 10px 25px !important; border: 1px solid #cbd5e1 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }

    /* STOPKA SYSTEMOWA W SIDEBARZE */
    .sidebar-footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.75rem;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #334155;
    }

    /* BELKA DOLNA ARKUSZA */
    .main-sheet-footer { margin-top: 15px; padding: 5px 15px; background-color: #1e293b; border-top: 3px solid #eab308; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; color: white; }
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

def generuj_kalendarz_html():
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    html = f'<div style="background:white; padding:4px; border-radius:8px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1; font-size:10px;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; border-bottom:1px solid #eee; padding-bottom:1px;">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    for week in cal:
        html += "<tr>"
        for day in week:
            bg = "#eab308" if day == now.day else "transparent"
            html += f'<td style="text-align:center; padding:1px; font-weight:700; background-color:{bg}; border-radius:4px;">{day if day != 0 else ""}</td>'
        html += "</tr>"
    return html + "</tbody></table></div>"

# ==========================================================
# 3. LOGIKA I SIDEBAR (ZREDUKOWANE ODSTĘPY)
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = "Andrzej Walczak"
else: st.error("BŁĄD LOGOWANIA"); st.stop()

df_biez_side = pobierz_df("Zadania bieżące")
df_chat = pobierz_df("CZAT")

has_new = False
if not df_chat.empty and 'ODBIORCA' in df_chat.columns:
    has_new = not df_chat[(df_chat['ODBIORCA'] == "Andrzej") & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty

with st.sidebar:
    st.markdown(f'<div class="logo-container"><a href="?u={u}&k={k}" target="_self"><img src="{LOGO_URL}"></a></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-header" style="margin-top:-5px;">🧭 Nawigacja</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ DODAJ", use_container_width=True): st.session_state.show_form = True
    with c2:
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">📅 Kalendarz</div>', unsafe_allow_html=True)
    st.components.v1.html(generuj_kalendarz_html(), height=125) # Obniżono wysokość ramki z 135 na 125
    
    # TUTAJ ZMNIEJSZONO ODLEGŁOŚĆ O 3MM (poprzez redukcję marginesów w dividerze)
    st.markdown('<div class="sidebar-divider" style="margin:2px 0;"></div>', unsafe_allow_html=True) 
    
    st.markdown('<div class="sidebar-header">🕒 Nadchodzące (5)</div>', unsafe_allow_html=True)
    if not df_biez_side.empty:
        for _, r in df_biez_side.head(5).iterrows():
            st.markdown(f'<div class="term-box"><span class="term-date">{r.get("DEADLINE","")}</span>: {str(r.get("TREŚĆ ZADANIA",""))[:35]}...</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="sidebar-footer">
            Zalogowany: <b>{zalogowany}</b><br>
            System Zarządzania &copy; 2025
        </div>
    """, unsafe_allow_html=True)

    if has_new:
        st.markdown('<p style="color:#ef4444; font-weight:900; text-align:center; animation: blinker 1.5s linear infinite; margin-top:2px;">🔔 NOWA WIADOMOŚĆ!</p>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
chat_tab_label = "💬 CZAT 🔴" if has_new else "💬 CZAT"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", chat_tab_label])

now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))
df_zrealizowane = pobierz_df("Zadania zrealizowane")

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

st.markdown(f'<div class="main-sheet-footer"><div style="color:#eab308; font-weight:800; font-size:0.8rem;">UZDROWISKO CIECHOCINEK S.A.</div><div style="font-size:0.7rem; color:#94a3b8;">{now_pl.strftime("%d.%m.%Y | %H:%M:%S")}</div></div>', unsafe_allow_html=True)

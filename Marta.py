import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. STYLIZACJA I KONFIGURACJA
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

APP_URL = "https://uzdrowisko-ciechocinek-nex3rfaat9fpxlpug35urd.streamlit.app/"
LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }}
    .logo-link {{ display: block; text-align: center; margin-top: -65px !important; margin-bottom: 15px !important; cursor: pointer; }}
    .logo-link img {{ width: 185px; }}
    .cal-container {{ background: white; padding: 10px; border-radius: 8px; border: 2px solid #eab308; width: 100%; margin-bottom: 15px; }}
    .cal-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 11px; color: #1e293b; }}
    .cal-table td {{ text-align: center; padding: 5px 1px; font-weight: 700; border-radius: 3px; }}
    .day-today {{ background-color: #eab308 !important; }}
    .day-task {{ color: #ef4444 !important; border: 1px solid #ef4444 !important; }}
    .term-box {{ background: #334155; padding: 12px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 10px; color: white; font-size: 0.75rem; }}
    .sidebar-header {{ color: #eab308; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; margin-top: 15px; }}
    .user-info-footer {{ background-color: #eab308 !important; color: #1e293b !important; padding: 10px; border-radius: 8px; font-weight: 900; font-size: 0.85rem; text-align: center; margin-top: 10px; margin-bottom: 20px; border: 2px solid white; }}
    
    [data-testid="stMetricValue"] > div {{ display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }}
    [data-testid="stMetricLabel"] > div {{ display: flex !important; justify-content: center !important; color: white !important; font-weight: 700 !important; text-transform: uppercase; }}
    [data-testid="stMetric"] {{ background-color: #1e293b !important; border-top: 5px solid #eab308 !important; border-radius: 12px !important; padding: 15px !important; text-align: center !important; }}
    
    button[data-baseweb="tab"] {{ font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 30px !important; border: none !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. LOGIKA DANYCH (5 KOLUMN + EMOTKI)
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_p, k_p = st.query_params.get("u", ""), st.query_params.get("k", "")

if u_p in USERS and USERS[u_p] == k_p:
    zalogowany = u_p
else:
    st.error("BŁĄD LOGOWANIA"); st.stop()

def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=15)
def pobierz_arkusz(nazwa, filtruj_dla_uzytkownika=True):
    try:
        sh = polacz().open("Marta-Dział Techniczny")
        ws = sh.worksheet(nazwa)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        
        df = pd.DataFrame(dane[1:], columns=dane[0])
        df = df.iloc[:, :5].copy() # 5 kolumn zgodnie z umową
        
        col_tresc = df.columns[2]
        df = df[df[col_tresc].str.strip() != ""].copy()
        
        # DODAWANIE EMOTEK NA POCZĄTEK TREŚCI
        def dodaj_ikone(row):
            dni = pd.to_numeric(row[df.columns[4]], errors='coerce')
            # Jeśli arkusz to zrealizowane
            if "zrealizowane" in nazwa.lower():
                return "✅ " + str(row[col_tresc])
            # Jeśli pilne (dni >= -2 wg Twojej instrukcji)
            if not pd.isna(dni) and dni >= -2:
                return "🔥 " + str(row[col_tresc])
            return "⏳ " + str(row[col_tresc])

        df[col_tresc] = df.apply(dodaj_ikone, axis=1)

        if filtruj_dla_uzytkownika:
            col_osoba = df.columns[1]
            if zalogowany == "Sławek":
                return df[df[col_osoba].str.contains("Sławek", case=False, na=False)].copy()
            elif zalogowany in ["Rafał", "Agata"]:
                return df[~df[col_osoba].str.contains("Sławek", case=False, na=False)].copy()
        return df 
    except: return pd.DataFrame()

# ==========================================================
# 3. SIDEBAR (LOGO, KALENDARZ, ZADANIA)
# ==========================================================
df_sidebar = pobierz_arkusz("Zadania bieżące", filtruj_dla_uzytkownika=True)
PERSONAL_URL = f"{APP_URL}?u={zalogowany}&k={USERS[zalogowany]}"

with st.sidebar:
    st.markdown(f'<a href="{PERSONAL_URL}" target="_self" class="logo-link"><img src="{LOGO_URL}"></a>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.markdown('<div class="sidebar-header">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dni_z_zadaniem = set()
    if not df_sidebar.empty:
        col_deadline = df_sidebar.columns[3]
        dt_deadlines = pd.to_datetime(df_sidebar[col_deadline], errors='coerce', dayfirst=True)
        dni_z_zadaniem = set(dt_deadlines[(dt_deadlines.dt.month == now.month) & (dt_deadlines.dt.year == now.year)].dt.day.dropna().astype(int))

    html_cal = f'<div class="cal-container"><table class="cal-table"><thead><tr><th colspan="7">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    for week in cal:
        html_cal += '<tr>'
        for day in week:
            if day == 0: html_cal += '<td></td>'
            else:
                cls = "day-today" if day == now.day else ""
                if day in dni_z_zadaniem: cls += " day-task"
                html_cal += f'<td class="{cls}">{day}</td>'
        html_cal += '</tr>'
    st.markdown(html_cal + '</tbody></table></div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-header">🕒 NADCHODZĄCE TWOJE</div>', unsafe_allow_html=True)
    if not df_sidebar.empty:
        col_deadline = df_sidebar.columns[3]
        col_tresc = df_sidebar.columns[2]
        for _, r in df_sidebar.head(4).iterrows():
            st.markdown(f'<div class="term-box"><b>{r[col_deadline]}</b>: {str(r[col_tresc])[:28]}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {zalogowany.upper()}</div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY (5 KOLUMN Z EMOTKAMI)
# ==========================================================
df_zreal_global = pobierz_arkusz("Zadania zrealizowane", filtruj_dla_uzytkownika=False)
count_zreal_total = len(df_zreal_global)

lista_zakladek = ["Zadania bieżące", "Zadania zrealizowane"]
if zalogowany == "Andrzej": lista_zakladek.append("Terminy Sławka")
lista_zakladek.append("CZAT 🔴")

tabs = st.tabs(lista_zakladek)
for i, nazwa in enumerate(lista_zakladek):
    if nazwa == "CZAT 🔴":
        with tabs[i]: st.info("Komunikator firmowy aktywny.")
        continue
        
    with tabs[i]:
        df_tab = pobierz_arkusz(nazwa, filtruj_dla_uzytkownika=True)
        m1, m2, m3, m4 = st.columns(4)
        
        count_razem = len(df_tab)
        pilne = 0
        if not df_tab.empty:
            col_dni = df_tab.columns[4]
            dni_val = pd.to_numeric(df_tab[col_dni].astype(str).str.extract(r'(-?\d+)')[0], errors='coerce').fillna(-999)
            pilne = len(df_tab[dni_val >= -2])
        
        m1.metric("📋 Razem", count_razem)
        m2.metric("🔥 Pilne (-2+)", pilne)
        m3.metric("✅ Zrealizowane", count_zreal_total)
        m4.metric("🕒 Aktualizacja", now.strftime("%H:%M"))
        
        st.markdown("---")
        if not df_tab.empty:
            st.data_editor(df_tab, use_container_width=True, hide_index=True, height=700)
        else:
            st.info("Brak zadań.")

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now.strftime("%d.%m.%Y")}</span></div>', unsafe_allow_html=True)

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I ZOPTYMALIZOWANA STYLIZACJA
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 0.5rem !important; }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-right: 5px solid #eab308 !important; min-width: 310px !important; }}
    .logo-link {{ display: block; text-align: center; margin-top: -65px !important; margin-bottom: 5px !important; }}
    .logo-link img {{ width: 160px; }}
    .cal-container {{ background: white; padding: 4px; border-radius: 8px; border: 2px solid #eab308; margin-bottom: 8px; }}
    .cal-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 9px; color: #1e293b; }}
    .cal-table td {{ text-align: center; padding: 2px 1px; font-weight: 700; border-radius: 3px; }}
    .day-today {{ background-color: #eab308 !important; }}
    .day-task {{ color: #ef4444 !important; border: 1.5px solid #ef4444 !important; font-weight: 900 !important; background-color: #fee2e2 !important; }}
    .term-box {{ background: #334155; padding: 6px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 5px; color: white; font-size: 0.65rem; }}
    .sidebar-header {{ color: #eab308; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; margin-top: 8px; }}
    .user-info-footer {{ background-color: #eab308 !important; color: #1e293b !important; padding: 6px; border-radius: 8px; font-weight: 900; font-size: 0.75rem; text-align: center; margin-top: 10px; margin-bottom: 5px; border: 2px solid white; }}
    button[data-baseweb="tab"] {{ font-size: 1.0rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #cbd5e1 !important; border-radius: 8px 8px 0 0 !important; padding: 8px 25px !important; margin-right: 4px !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: white !important; background-color: #0f172a !important; border-bottom: 5px solid #ef4444 !important; }}
    [data-testid="stMetricValue"] > div {{ display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.0rem !important; }}
    [data-testid="stMetricLabel"] > div {{ display: flex !important; justify-content: center !important; color: white !important; font-weight: 700 !important; text-transform: uppercase; font-size: 0.8rem !important; }}
    [data-testid="stMetric"] {{ background-color: #1e293b !important; border-top: 5px solid #eab308 !important; border-radius: 12px !important; padding: 10px !important; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. LOGIKA UWIERZYTELNIANIA
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_p, k_p = st.query_params.get("u", ""), st.query_params.get("k", "")

if u_p in USERS and USERS[u_p] == k_p: zalogowany = u_p
else: st.error("BŁĄD LOGOWANIA"); st.stop()

def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=10)
def pobierz_arkusz(nazwa, filtruj=True):
    try:
        sh = polacz().open("Marta-Dział Techniczny")
        ws = sh.worksheet(nazwa)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0]).iloc[:, :5].copy()
        df = df[df.iloc[:, 0].str.strip() != ""].copy()
        def wstaw_emotke(row):
            try:
                dni = pd.to_numeric(str(row.iloc[3]).replace(',', '.').strip(), errors='coerce')
                tresc = str(row.iloc[0])
                if "zrealizowane" in nazwa.lower(): return f"✅ {tresc}"
                if not pd.isna(dni) and dni >= -2: return f"🔥 {tresc}"
                return f"⏳ {tresc}"
            except: return str(row.iloc[0])
        df.iloc[:, 0] = df.apply(wstaw_emotke, axis=1)
        if filtruj:
            col_osoba = df.iloc[:, 4].str.lower()
            if zalogowany == "Sławek": return df[col_osoba.str.contains("sławek", na=False)].copy()
            elif zalogowany in ["Rafał", "Agata"]: return df[~col_osoba.str.contains("sławek", na=False)].copy()
        return df 
    except: return pd.DataFrame()

# ==========================================================
# 3. NAPRAWIONY FORMULARZ DODAWANIA
# ==========================================================
@st.dialog("➕ DODAJ NOWE ZADANIE")
def otworz_formularz():
    with st.form("form_global"):
        tresc = st.text_input("Co jest do zrobienia?")
        uwagi = st.text_area("Szczegóły / Uwagi")
        deadline = st.date_input("Termin (Deadline)", datetime.now())
        osoba = st.selectbox("Dla kogo?", list(USERS.keys()), index=list(USERS.keys()).index(zalogowany))
        submit = st.form_submit_button("✅ ZAPISZ W ARKUSZU")
        
        if submit:
            if tresc:
                try:
                    sh = polacz().open("Marta-Dział Techniczny")
                    ws = sh.worksheet("Zadania bieżące")
                    # Tworzymy wiersz (DNI zostawiamy puste, arkusz sam policzy)
                    ws.append_row([tresc, uwagi, deadline.strftime("%Y-%m-%d"), "", osoba])
                    st.success("Zadanie zapisane pomyślnie!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Problem z arkuszem: {e}")
            else:
                st.warning("Musisz podać treść zadania!")

# ==========================================================
# 4. LEWY PANEL (SIDEBAR)
# ==========================================================
df_side = pobierz_arkusz("Zadania bieżące", filtruj=True)
with st.sidebar:
    st.markdown(f'<a href="https://uzdrowisko-ciechocinek-nex3rfaat9fpxlpug35urd.streamlit.app/?u={zalogowany}&k={USERS[zalogowany]}" target="_self" class="logo-link"><img src="{LOGO_URL}"></a>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: 
        # Wywołanie okna dialogowego
        if st.button("➕ DODAJ", use_container_width=True, key="btn_dodaj"):
            otworz_formularz()
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown('<div class="sidebar-header">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dni_z_zadaniem = set()
    if not df_side.empty:
        dt_deadlines = pd.to_datetime(df_side.iloc[:, 2], errors='coerce', dayfirst=True)
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
    if not df_side.empty:
        for _, r in df_side.head(3).iterrows():
            st.markdown(f'<div class="term-box"><b>{r.iloc[2]}</b>: {r.iloc[0]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="user-info-footer">👤 ZALOGOWANO: {zalogowany.upper()}</div>', unsafe_allow_html=True)

# ==========================================================
# 5. WIDOK GŁÓWNY
# ==========================================================
df_zreal_full = pobierz_arkusz("Zadania zrealizowane", filtruj=False)
lista_zakladek = ["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "CZAT 🔴"]
tabs = st.tabs(lista_zakladek)

for i, nazwa in enumerate(lista_zakladek):
    if nazwa == "CZAT 🔴":
        with tabs[i]: st.info("Czat aktywny.")
        continue
    with tabs[i]:
        df_tab = pobierz_arkusz(nazwa, filtruj=(nazwa != "Zadania zrealizowane"))
        m1, m2, m3, m4 = st.columns(4)
        pilne_count = 0
        if not df_tab.empty:
            num_dni = pd.to_numeric(df_tab.iloc[:, 3].astype(str).str.replace(',', '.').str.strip(), errors='coerce').fillna(-999)
            pilne_count = len(df_tab[num_dni >= -2])
        m1.metric("RAZEM", len(df_tab))
        m2.metric("PILNE 🔥", pilne_count)
        m3.metric("ZREALIZOWANE", len(df_zreal_full))
        m4.metric("AKTUALIZACJA", now.strftime("%H:%M"))
        st.markdown("---")
        if not df_tab.empty: st.data_editor(df_tab, use_container_width=True, hide_index=True, height=700)

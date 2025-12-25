import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (NAPRAWA WIZUALNA)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=10000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0px !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    .logo-container { text-align: center; margin-top: -35px !important; margin-bottom: 15px !important; }
    .logo-container img { width: 190px; cursor: pointer; }

    /* METRYKI WYŚRODKOWANE - POWRÓT DO FAJNEGO STYLU */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 10px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }

    /* ZAKŁADKI */
    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; margin-right: 5px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }

    /* STOPKA DOLNA */
    .main-sheet-footer { margin-top: 15px; padding: 5px 15px; background-color: #1e293b; border-top: 3px solid #eab308; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; color: white; }
    
    .term-box { background: #334155; padding: 5px 8px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 4px; color: white; font-size: 0.7rem; line-height: 1.2; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE TECHNICZNE (POPRAWIONE FILTROWANIE KOLUMNY A)
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
        # FILTR: Bierzemy tylko wiersze, gdzie pierwsza kolumna (index 0) nie jest pusta
        return df[df.iloc[:, 0].astype(str).str.strip() != ""]
    except: return pd.DataFrame()

def dodaj_zadanie_do_arkusza(tresc, osoba, deadline, uwagi):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("Zadania bieżące")
        ws.append_row(["●", tresc, uwagi, deadline, "", osoba, "W trakcie", "FALSE"])
        return True
    except: return False

def generuj_kalendarz_html():
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    html = f'<div style="background:white; padding:8px; border-radius:8px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1; font-size:10px;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; border-bottom:1px solid #eee; padding-bottom:3px;">{calendar.month_name[now.month].upper()}</th></tr><tr style="color:#64748b; font-size:8px;"><th>PN</th><th>WT</th><th>ŚR</th><th>CZ</th><th>PT</th><th>SO</th><th>ND</th></tr></thead><tbody>'
    for week in cal:
        html += "<tr>"
        for day in week:
            bg = "#eab308" if day == now.day else "transparent"
            html += f'<td style="text-align:center; padding:3px; font-weight:700; background-color:{bg}; border-radius:4px;">{day if day != 0 else ""}</td>'
        html += "</tr>"
    return html + "</tbody></table></div>"

# ==========================================================
# 3. LOGIKA I SIDEBAR
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = u
else: st.error("BŁĄD LOGOWANIA"); st.stop()

# Pobieranie danych dla kafelków
df_biez_raw = pobierz_df("Zadania bieżące")
df_zreal_raw = pobierz_df("Zadania zrealizowane")

with st.sidebar:
    st.markdown(f'<div class="logo-container"><a href="?u={u}&k={k}" target="_self"><img src="{LOGO_URL}"></a></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ DODAJ", use_container_width=True): st.session_state.show_form = True
    with col2:
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.components.v1.html(generuj_kalendarz_html(), height=155)
    
    st.markdown("<p style='color:white; font-size:0.85rem; font-weight:bold; margin-top:10px;'>📅 Nadchodzące:</p>", unsafe_allow_html=True)
    if not df_biez_raw.empty:
        for _, r in df_biez_raw.head(8).iterrows():
            st.markdown(f'<div class="term-box"><b>{r.get("DEADLINE","")}</b>: {str(r.get("TREŚĆ ZADANIA",""))[:35]}...</div>', unsafe_allow_html=True)

# ==========================================================
# 4. FORMULARZ DODAWANIA
# ==========================================================
if st.session_state.get('show_form', False):
    with st.expander("📝 NOWE ZADANIE", expanded=True):
        with st.form("new_task"):
            f_col1, f_col2 = st.columns(2)
            tresc = f_col1.text_input("Zadanie:")
            osoba = f_col1.selectbox("Osoba:", ["Marta", "Sławek", "Agata", "Rafał", "Andrzej", "Pola"])
            deadline = f_col2.date_input("Termin:")
            uwagi = f_col2.text_area("Uwagi:")
            
            if st.form_submit_button("✅ ZAPISZ ZADANIE"):
                if tresc and dodaj_zadanie_do_arkusza(tresc, osoba, deadline.strftime("%d.%m.%Y"), uwagi):
                    st.success("Zadanie dodane!"); st.session_state.show_form = False; st.cache_data.clear(); st.rerun()
        if st.button("❌ ANULUJ"): st.session_state.show_form = False; st.rerun()

# ==========================================================
# 5. WIDOK GŁÓWNY (POPRAWIONE KAFELKI)
# ==========================================================
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "💬 CZAT"])
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, kat in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_df(kat)
        m1, m2, m3, m4 = st.columns(4)
        
        # LICZENIE TYLKO REKORDÓW Z KOLUMNY A
        m1.metric("📋 Razem", len(df))
        
        if not df.empty and 'DNI' in df.columns:
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
        else:
            m2.metric("🔥 Pilne (-2+)", 0)
            
        m3.metric("✅ Zrealizowane", len(df_zreal_raw))
        m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
        
        if not df.empty:
            st.data_editor(df, use_container_width=True, hide_index=True, height=550)
        else:
            st.info("Brak aktywnych zadań w tej sekcji.")

# --- ULTRA KOMPAKTOWA BELKA DOLNA ---
st.markdown(f"""
    <div class="main-sheet-footer">
        <div style="color:#eab308; font-weight:800; font-size:0.8rem;">UZDROWISKO CIECHOCINEK S.A.</div>
        <div style="font-size:0.75rem; color:#94a3b8;">{now_pl.strftime('%d.%m.%Y | %H:%M:%S')} | Dział Techniczny</div>
    </div>
""", unsafe_allow_html=True)

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (PANEL BEZ PRZEWIJANIA)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="globalrefresh")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    
    /* LEWY PANEL BOCZNY */
    [data-testid="stSidebar"] { 
        background-color: #1e293b !important; 
        border-right: 5px solid #eab308 !important; 
    }
    
    /* PRZYCISKI W PANELU - ZWARTY UKŁAD */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-weight: 600 !important;
        height: 40px !important; margin-bottom: 5px !important;
        font-size: 0.8rem !important;
    }

    /* KALENDARZ - KOMPAKTOWY */
    .cal-container {
        background-color: white;
        padding: 8px;
        border-radius: 10px;
        border: 2px solid #eab308;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        margin-top: 10px;
    }
    .cal-table { width: 100%; border-collapse: collapse; font-family: sans-serif; line-height: 1.1; }
    .cal-header { color: #1e293b; text-align: center; font-weight: 800; font-size: 0.75rem; padding-bottom: 5px; }
    .cal-day-name { color: #64748b; font-size: 0.6rem; text-align: center; font-weight: bold; }
    .cal-day { text-align: center; padding: 4px 1px; font-size: 0.75rem; color: #1e293b; font-weight: 600; }
    .cal-today { background-color: #eab308 !important; color: #1e293b !important; border-radius: 4px; }
    .cal-task-urgent { color: #ef4444 !important; font-weight: 900 !important; border: 1px solid #ef4444; border-radius: 4px; }

    /* METRYKI */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; border-top: 4px solid #eab308 !important; 
        border-radius: 10px !important; text-align: center !important; 
    }
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }

    /* INFO O UŻYTKOWNIKU NA DOLE */
    .sidebar-footer { position: fixed; bottom: 10px; width: 240px; text-align: center; color: #94a3b8; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE TECHNICZNE
# ==========================================================
def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], 
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def pobierz_df(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        if not dane: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df[df.iloc[:, 0].str.strip() != ""]
    except: return pd.DataFrame()

def generuj_kalendarz_html(df_zadania):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    rok, miesiac = now.year, now.month
    cal = calendar.monthcalendar(rok, miesiac)
    
    pilne_daty = []
    if not df_zadania.empty:
        df_zadania['DT'] = pd.to_datetime(df_zadania['DEADLINE'], dayfirst=True, errors='coerce')
        df_zadania['DNI_N'] = pd.to_numeric(df_zadania['DNI'], errors='coerce').fillna(-999)
        mask = (df_zadania['DT'].dt.month == miesiac) & (df_zadania['DT'].dt.year == rok) & (df_zadania['DNI_N'] >= -2)
        pilne_daty = df_zadania[mask]['DT'].dt.day.unique().tolist()

    html = f"""
    <div class="cal-container">
        <table class="cal-table">
            <thead>
                <tr><th colspan="7" class="cal-header">{calendar.month_name[miesiac].upper()} {rok}</th></tr>
                <tr class="cal-day-name"><th>PN</th><th>WT</th><th>ŚR</th><th>CZ</th><th>PT</th><th>SO</th><th>ND</th></tr>
            </thead>
            <tbody>
    """
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                style = ""
                cl = "cal-day"
                if day == now.day: cl += " cal-today"
                if day in pilne_daty: cl += " cal-task-urgent"
                html += f'<td class="{cl}">{day}</td>'
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

# ==========================================================
# 3. LOGIKA SIDEBARU (GÓRA: LOGO -> PRZYCISKI -> KALENDARZ)
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800":
    zalogowany = u
else:
    st.error("BŁĄD LOGOWANIA"); st.stop()

# Pobranie danych
df_biezace = pobierz_df("Zadania bieżące")
df_slawek = pobierz_df("Terminy Sławka")
df_total = pd.concat([df_biezace, df_slawek])

with st.sidebar:
    # 1. LOGO UZDROWISKA
    st.markdown("""
        <div style="text-align:center; padding-bottom:10px;">
            <h2 style="color:#0ea5e9; margin:0; font-weight:900; letter-spacing:1px;">UZDROWISKO</h2>
            <h4 style="color:#eab308; margin:0; font-weight:700; letter-spacing:2px; line-height:1;">CIECHOCINEK</h4>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 2. KAFFELKI PRZYCISKÓW
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True):
        st.info("Dodaj zadanie bezpośrednio w Arkuszu Google.")
    
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # 3. KALENDARZ (KOMPAKTOWY)
    st.components.v1.html(generuj_kalendarz_html(df_total), height=210)
    
    # 4. INFO NA DOLE
    st.markdown(f'<div class="sidebar-footer">Zalogowany: <b>{zalogowany}</b></div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY (ZAKŁADKI)
# ==========================================================
kat_list = ["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "🔴 CZAT"]
tabs = st.tabs(kat_list)

for i, kat in enumerate(kat_list[:-1]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Razem", len(df))
            m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
            m3.metric("🕒 Godzina", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))
            
            df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))
            
            st.data_editor(df, use_container_width=True, hide_index=True, height=700, key=f"ed_{kat}")

# BELKA DOLNA
st.markdown("""
    <div style="display:flex; justify-content:center; background:white; border-radius:10px; padding:10px; margin-top:30px; border:1px solid #eee;">
        <a style="margin:0 15px; text-decoration:none; color:#1e293b; font-weight:700; font-size:0.8rem;" href="https://uzdrowiskociechocinek.pl/kontakt/">KONTAKT</a>
    </div>
""", unsafe_allow_html=True)

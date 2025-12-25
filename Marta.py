import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (SIATKA KALENDARZA)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="globalrefresh")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* STYLIZACJA WŁASNEJ SIATKI KALENDARZA */
    .cal-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; font-family: sans-serif; }
    .cal-header { background: #334155; color: white; text-align: center; font-weight: bold; padding: 5px; font-size: 0.8rem; }
    .cal-day-name { background: #f1f5f9; color: #475569; font-size: 0.7rem; text-align: center; padding: 5px; }
    .cal-day { text-align: center; padding: 8px; font-size: 0.8rem; border: 1px solid #f1f5f9; color: #1e293b; }
    .cal-today { background: #eab308 !important; color: white !important; font-weight: bold; border-radius: 50%; }
    .cal-task-urgent { background: #ef4444 !important; color: white !important; font-weight: bold; cursor: pointer; }
    
    /* KAFELKI I RESZTA */
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; text-align: center !important; }
    [data-testid="stMetricValue"] > div { color: #eab308 !important; font-weight: 900; font-size: 2.5rem !important; justify-content: center !important; display: flex !important; }
    [data-testid="stMetricLabel"] > div { color: white !important; font-size: 1.1rem !important; justify-content: center !important; display: flex !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE DANYCH
# ==========================================================
def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

def pobierz_df(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        df = pd.DataFrame(dane[1:], columns=dane[0]).iloc[:, :5]
        return df[df.iloc[:, 0].str.strip() != ""]
    except: return pd.DataFrame()

# ==========================================================
# 3. GENERATOR WIDOKU KALENDARZA (HTML)
# ==========================================================
def generuj_kalendarz_html(df_zadania):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    rok, miesiac = now.year, now.month
    cal = calendar.monthcalendar(rok, miesiac)
    
    # Pobierz daty, które mają pilne terminy (DNI >= -2)
    df_zadania['DT'] = pd.to_datetime(df_zadania['DEADLINE'], dayfirst=True, errors='coerce')
    df_zadania['DNI_N'] = pd.to_numeric(df_zadania['DNI'], errors='coerce').fillna(-999)
    pilne_daty = df_zadania[df_zadania['DNI_N'] >= -2]['DT'].dt.day.tolist()

    html = f"<table class='cal-table'><tr class='cal-header'><td colspan='7'>{calendar.month_name[miesiac].upper()} {rok}</td></tr>"
    html += "<tr class='cal-day-name'><td>Pn</td><td>Wt</td><td>Śr</td><td>Cz</td><td>Pt</td><td>So</td><td>Nd</td></tr>"
    
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td class='cal-day'></td>"
            else:
                css_class = "cal-day"
                if day == now.day: css_class += " cal-today"
                if day in pilne_daty: css_class += " cal-task-urgent"
                html += f"<td class='{css_class}'>{day}</td>"
        html += "</tr>"
    html += "</table>"
    return html

# ==========================================================
# 4. WERYFIKACJA I PANEL BOCZNY (SIDEBAR)
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800":
    zalogowany = u
else:
    st.error("BŁĄD LOGOWANIA"); st.stop()

# Pobranie danych do kalendarza
df_biezace = pobierz_df("Zadania bieżące")
df_slawek = pobierz_df("Terminy Sławka")
df_total = pd.concat([df_biezace, df_slawek])

with st.sidebar:
    st.markdown("<h3 style='text-align:center; color:white;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h3>", unsafe_allow_html=True)
    st.divider()
    
    # WSTAWIANIE STAŁEJ SIATKI KALENDARZA
    st.markdown("📅 **TERMINY W TYM MIESIĄCU**")
    st.components.v1.html(generuj_kalendarz_html(df_total), height=230)
    st.caption("🔴 - Dni z pilnymi zadaniami (DNI >= -2)")
    
    st.divider()
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): 
        st.cache_data.clear(); st.rerun()
    st.write(f"Zalogowany: **{zalogowany}**")

# ==========================================================
# 5. WIDOK GŁÓWNY (ZAKŁADKI I TABELA)
# ==========================================================
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "🔴 CZAT"])

with tabs[0]:
    if not df_biezace.empty:
        df_biezace['DNI_N'] = pd.to_numeric(df_biezace['DNI'], errors='coerce').fillna(-999)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("📋 Razem", len(df_biezace))
        m2.metric("🔥 Pilne (-2+)", len(df_biezace[df_biezace['DNI_N'] >= -2]))
        m3.metric("🕒 Godzina", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))
        
        df_biezace.insert(0, "S", df_biezace['DNI_N'].apply(lambda x: "🚨" if x >= -2 else "✅"))
        st.data_editor(df_biezace, use_container_width=True, hide_index=True, height=600,
                       column_config={"DNI_N": None, "S": st.column_config.TextColumn(" ", width="small")})

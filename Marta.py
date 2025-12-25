import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (POWRÓT DO ELEGANCKIEGO WYGLĄDU)
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
    
    /* POWIĘKSZONE PRZYCISKI W PANELU */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-weight: 600 !important;
        height: 46px !important; margin-bottom: 8px !important;
        font-size: 0.9rem !important;
    }

    /* BIAŁA KARTA KALENDARZA - STYL INLINE DLA KONTRASTU */
    .cal-card {
        background-color: white;
        padding: 12px;
        border-radius: 12px;
        border: 2px solid #eab308;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 15px;
    }

    /* ZAKŁADKI (TABS) - KOLOR LEWEGO PANELU */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important; font-weight: 700 !important;
        color: #475569 !important; background-color: #f1f5f9 !important;
        border-radius: 8px 8px 0 0 !important; margin-right: 5px !important;
        padding: 10px 25px !important; border: 1px solid #e2e8f0 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important;
        background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }

    /* METRYKI PODSUMOWANIA */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; border-top: 4px solid #eab308 !important; 
        border-radius: 10px !important; text-align: center !important; 
    }
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }

    /* INFO O UŻYTKOWNIKU */
    .sidebar-footer { position: fixed; bottom: 10px; width: 240px; text-align: center; color: #94a3b8; font-size: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE DANYCH
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
    <div style="background-color: white; padding: 12px; border-radius: 10px; border: 2px solid #eab308; font-family: sans-serif;">
        <table style="width: 100%; border-collapse: collapse; line-height: 1.3;">
            <thead>
                <tr><th colspan="7" style="color: #1e293b; text-align: center; font-weight: 800; font-size: 15px; padding-bottom: 8px; border-bottom: 1px solid #eee;">{calendar.month_name[miesiac].upper()} {rok}</th></tr>
                <tr style="color: #64748b; font-size: 10px; text-align: center; font-weight: bold;">
                    <th style="padding: 4px 0;">PN</th><th style="padding: 4px 0;">WT</th><th style="padding: 4px 0;">ŚR</th><th style="padding: 4px 0;">CZ</th><th style="padding: 4px 0;">PT</th><th style="padding: 4px 0;">SO</th><th style="padding: 4px 0;">ND</th>
                </tr>
            </thead>
            <tbody style="color: #1e293b;">
    """
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                bg = "transparent"
                color = "#1e293b"
                border = "none"
                if day == now.day: bg = "#eab308"
                if day in pilne_daty:
                    color = "#ef4444"
                    border = "1px solid #ef4444"
                html += f'<td style="text-align: center; padding: 6px 1px; font-size: 13px; font-weight: 700; color: {color}; background-color: {bg}; border-radius: 4px; border: {border};">{day}</td>'
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

# ==========================================================
# 3. LOGIKA SIDEBARU
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = u
else: st.error("BŁĄD LOGOWANIA"); st.stop()

df_biezace = pobierz_df("Zadania bieżące")
df_slawek = pobierz_df("Terminy Sławka")
df_total = pd.concat([df_biezace, df_slawek])

with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding-bottom: 10px;">
            <div style="color:#eab308; font-size: 24px; font-weight: 900; line-height: 0.8;">UZDROWISKO</div>
            <div style="color:#0ea5e9; font-size: 16px; font-weight: 700; letter-spacing: 2px;">CIECHOCINEK</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True): st.info("Dodaj w Arkuszu Google.")
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    # POWRÓT DO GRAFICZNEGO KALENDARZA
    st.components.v1.html(generuj_kalendarz_html(df_total), height=230)
    
    # LISTA TERMINÓW NA DZIŚ POD KALENDARZEM
    now_dt = datetime.now(pytz.timezone('Europe/Warsaw')).date()
    df_total['DT'] = pd.to_datetime(df_total['DEADLINE'], dayfirst=True, errors='coerce')
    zadania_dzis = df_total[df_total['DT'].dt.date == now_dt]
    
    if not zadania_dzis.empty:
        st.markdown(f"📅 **Terminy na dziś ({now_dt.strftime('%d.%m')}):**")
        for _, r in zadania_dzis.iterrows():
            st.markdown(f"<small>🚨 {r['TREŚĆ ZADANIA']}</small>", unsafe_allow_html=True)
    
    st.markdown(f'<div class="sidebar-user" style="text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:20px;">Zalogowany: <b>{zalogowany}</b></div>', unsafe_allow_html=True)

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
            st.data_editor(df, use_container_width=True, hide_index=True, height=750, key=f"ed_{kat}")

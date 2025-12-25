import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (AKTYWNA ZAKŁADKA I KALENDARZ)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="globalrefresh")

# Inicjalizacja stanu dla wybranej daty w kalendarzu
if 'selected_day' not in st.session_state:
    st.session_state.selected_day = datetime.now(pytz.timezone('Europe/Warsaw')).day

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* POWIĘKSZONE PRZYCISKI */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-weight: 600 !important;
        height: 46px !important; margin-bottom: 8px !important; font-size: 0.9rem !important;
    }

    /* AKTYWNA ZAKŁADKA - KOLOR PANELU */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important; font-weight: 700 !important;
        color: #475569 !important; background-color: #f1f5f9 !important;
        border-radius: 8px 8px 0 0 !important; margin-right: 5px !important;
        padding: 10px 25px !important; border: 1px solid #e2e8f0 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important; background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }

    /* KAFELKI PODSUMOWANIA */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; border-top: 4px solid #eab308 !important; 
        border-radius: 10px !important; text-align: center !important; 
    }
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }

    /* KALENDARZ - STYL PRZYCISKÓW DAT */
    .cal-btn {
        background: none; border: none; color: #1e293b; font-weight: 700;
        width: 100%; cursor: pointer; padding: 5px 0; border-radius: 4px;
    }
    .cal-btn:hover { background-color: #f1f5f9; }
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
        if not dane: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df[df.iloc[:, 0].str.strip() != ""]
    except: return pd.DataFrame()

# ==========================================================
# 3. LOGIKA SIDEBARU (LOGO -> PRZYCISKI -> KALENDARZ -> LISTA)
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = u
else: st.error("BŁĄD LOGOWANIA"); st.stop()

df_biezace = pobierz_df("Zadania bieżące")
df_slawek = pobierz_df("Terminy Sławka")
df_total = pd.concat([df_biezace, df_slawek])

with st.sidebar:
    st.markdown('<div style="text-align:center; padding-bottom: 10px;"><div style="color:#eab308; font-size: 24px; font-weight: 900; line-height: 0.8;">UZDROWISKO</div><div style="color:#0ea5e9; font-size: 16px; font-weight: 700; letter-spacing: 2px;">CIECHOCINEK</div></div>', unsafe_allow_html=True)
    st.divider()
    
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True): st.info("Dodaj w Arkuszu Google.")
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): st.cache_data.clear(); st.rerun()

    # GENEROWANIE KALENDARZA JAKO PRZYCISKI (WŁASNA IMPLEMENTACJA)
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    rok, miesiac = now.year, now.month
    cal_obj = calendar.Calendar(firstweekday=0)
    
    # Przygotowanie dat z terminami
    df_total['DT'] = pd.to_datetime(df_total['DEADLINE'], dayfirst=True, errors='coerce')
    df_total['DNI_N'] = pd.to_numeric(df_total['DNI'], errors='coerce').fillna(-999)
    pilne_daty = df_total[df_total['DNI_N'] >= -2]['DT'].dt.day.unique().tolist()

    st.markdown(f'<div style="background:white; padding:10px; border-radius:10px; border:2px solid #eab308; color:#1e293b;"><div style="text-align:center; font-weight:800; font-size:14px; margin-bottom:5px;">{calendar.month_name[miesiac].upper()} {rok}</div>', unsafe_allow_html=True)
    
    cols = st.columns(7)
    days = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
    for i, d in enumerate(days): cols[i].markdown(f"<center><small><b>{d}</b></small></center>", unsafe_allow_html=True)

    month_days = cal_obj.monthdayscalendar(rok, miesiac)
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                style = "color:#1e293b;"
                if day in pilne_daty: style = "color:#ef4444; font-weight:900; border-bottom:2px solid #ef4444;"
                if day == now.day: style += "background:#eab308; border-radius:4px;"
                
                if cols[i].button(str(day), key=f"day_{day}"):
                    st.session_state.selected_day = day
    st.markdown('</div>', unsafe_allow_html=True)

    # WYŚWIETLANIE TERMINÓW DLA KLIKNIĘTEGO DNIA
    st.markdown(f"📅 **Terminy: {st.session_state.selected_day}.{miesiac}**")
    wybrana_data_dt = datetime(rok, miesiac, st.session_state.selected_day).date()
    zadania_dnia = df_total[df_total['DT'].dt.date == wybrana_data_dt]
    
    if not zadania_dnia.empty:
        for _, r in zadania_dnia.iterrows():
            emoji = "🚨" if r['DNI_N'] >= -2 else "✅"
            st.markdown(f"<small>{emoji} {r['TREŚĆ ZADANIA']}</small>", unsafe_allow_html=True)
    else:
        st.caption("Brak zadań na ten dzień.")

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
            m2.metric("🔥 Pilne", len(df[df['DNI_N'] >= -2]))
            m3.metric("🕒 Godzina", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))
            
            df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))
            st.data_editor(df, use_container_width=True, hide_index=True, height=700, key=f"ed_{kat}")

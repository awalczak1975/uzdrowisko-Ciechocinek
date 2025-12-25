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
st_autorefresh(interval=30000, key="globalrefresh")

# Inicjalizacja stanu dla wybranej daty
if 'selected_day' not in st.session_state:
    st.session_state.selected_day = datetime.now(pytz.timezone('Europe/Warsaw')).day

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* Stylizacja przycisków-dni w kalendarzu */
    div[data-testid="column"] button {
        padding: 2px !important;
        height: 35px !important;
        width: 100% !important;
        min-width: 0px !important;
        font-size: 0.8rem !important;
        background-color: white !important;
        color: #1e293b !important;
        border: 1px solid #f1f5f9 !important;
        border-radius: 4px !important;
    }
    
    /* Przycisk aktywnego/wybranego dnia */
    div[data-testid="column"] button:focus, div[data-testid="column"] button:active {
        border: 2px solid #eab308 !important;
        background-color: #f1f5f9 !important;
    }

    /* AKTYWNA ZAKŁADKA */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important;
        background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }

    /* OBNIŻENIE INFO O UŻYTKOWNIKU */
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

# ==========================================================
# 3. LOGIKA SIDEBARU (NOWY INTERAKTYWNY KALENDARZ)
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

    # --- INTERAKTYWNA SIATKA KALENDARZA ---
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    rok, miesiac = now.year, now.month
    
    st.markdown(f'<div style="color:white; text-align:center; font-weight:bold; margin-bottom:5px;">{calendar.month_name[miesiac].upper()} {rok}</div>', unsafe_allow_html=True)
    
    # Nagłówki dni tygodnia
    cols_h = st.columns(7)
    days_names = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
    for i, d in enumerate(days_names):
        cols_h[i].markdown(f"<center><small style='color:#94a3b8'>{d}</small></center>", unsafe_allow_html=True)

    # Budowanie siatki dni
    cal_obj = calendar.Calendar(firstweekday=0)
    for week in cal_obj.monthdayscalendar(rok, miesiac):
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                # Oznaczenie dni z terminami
                df_total['DT'] = pd.to_datetime(df_total['DEADLINE'], dayfirst=True, errors='coerce')
                df_total['DNI_N'] = pd.to_numeric(df_total['DNI'], errors='coerce').fillna(-999)
                pilne = day in df_total[df_total['DNI_N'] >= -2]['DT'].dt.day.unique().tolist()
                
                label = f"{day}🔴" if pilne else str(day)
                if day == now.day: label = f"⭐{day}"
                
                if cols[i].button(label, key=f"d_{day}"):
                    st.session_state.selected_day = day
            else:
                cols[i].write("")

    st.divider()
    
    # --- WYŚWIETLANIE ZADAŃ DLA KLIKNIĘTEGO DNIA ---
    st.markdown(f"📅 **Zadania na dzień: {st.session_state.selected_day}.{miesiac}**")
    wybrana_data_dt = datetime(rok, miesiac, st.session_state.selected_day).date()
    zadania_dnia = df_total[df_total['DT'].dt.date == wybrana_data_dt]
    
    if not zadania_dnia.empty:
        for _, r in zadania_dnia.iterrows():
            emoji = "🚨" if r['DNI_N'] >= -2 else "✅"
            st.markdown(f"<div style='background:#334155; padding:5px; border-radius:5px; margin-bottom:5px;'><small>{emoji} {r['TREŚĆ ZADANIA']}</small></div>", unsafe_allow_html=True)
    else:
        st.caption("Brak zadań na ten dzień.")

    st.markdown(f'<div class="sidebar-footer">Zalogowany: <b>{zalogowany}</b></div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY (ZAKŁADKI I TABELE)
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

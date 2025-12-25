import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (MESSENGER STYLE)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=10000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    /* OGÓLNE I SIDEBAR */
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    .logo-container { text-align: center; margin-top: -35px !important; margin-bottom: 15px !important; }
    .logo-container img { width: 190px; cursor: pointer; }

    /* METRYKI WYŚRODKOWANE */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 10px !important; }

    /* MESSENGER CHAT UI */
    .messenger-container { background-color: #f0f2f5; padding: 15px; border-radius: 15px; border: 1px solid #ddd; }
    .msg-row { display: flex; margin-bottom: 10px; width: 100%; }
    .msg-mine { justify-content: flex-end; }
    .msg-theirs { justify-content: flex-start; }
    
    .bubble {
        padding: 10px 15px;
        border-radius: 18px;
        max-width: 70%;
        font-family: sans-serif;
        font-size: 0.95rem;
        position: relative;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .bubble-mine { background-color: #eab308; color: #1e293b; border-bottom-right-radius: 4px; }
    .bubble-theirs { background-color: #1e293b; color: white; border-bottom-left-radius: 4px; }
    
    .msg-info { font-size: 0.7rem; color: #888; margin: 2px 5px; }
    
    /* BELKA DOLNA */
    .main-sheet-footer { margin-top: 15px; padding: 5px 15px; background-color: #1e293b; border-top: 3px solid #eab308; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; color: white; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE TECHNICZNE (POPRAWIONE LICZENIE I CZAT)
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
        # Filtrujemy tylko wiersze, gdzie Kolumna A (index 0) nie jest pusta
        return df[df.iloc[:, 0].astype(str).str.strip() != ""]
    except: return pd.DataFrame()

def wyslij_wiadomosc(nadawca, odbiorca, tresc):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("CZAT")
        czas = datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M")
        ws.append_row([czas, nadawca, odbiorca, tresc, "NIEPRZECZYTANE"])
        return True
    except: return False

def generuj_kalendarz_html():
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    html = f'<div style="background:white; padding:8px; border-radius:8px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1; font-size:10px;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; border-bottom:1px solid #eee; padding-bottom:3px;">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
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

# Bezpieczne pobranie czatu
df_chat = pobierz_df("CZAT")
has_new = False
if not df_chat.empty and 'ODBIORCA' in df_chat.columns:
    has_new = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty

with st.sidebar:
    st.markdown(f'<div class="logo-container"><a href="?u={u}&k={k}" target="_self"><img src="{LOGO_URL}"></a></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ DODAJ", use_container_width=True): st.session_state.show_form = True
    with c2:
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.components.v1.html(generuj_kalendarz_html(), height=155)
    
    if has_new:
        st.markdown('<p style="color:#ef4444; font-weight:900; text-align:center; animation: blinker 1.5s linear infinite;">🔔 NOWA WIADOMOŚĆ!</p>', unsafe_allow_html=True)
        st.markdown('<audio autoplay><source src="https://www.soundjay.com/buttons/beep-07a.mp3"></audio>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY (KAFELKI + MESSENGER CHAT)
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

# --- WIDOK MESSENGERA ---
with tabs[3]:
    st.write("### 💬 Messenger Działu Technicznego")
    pracownicy = ["Marta", "Sławek", "Agata", "Rafał", "Andrzej"]
    wybrany = st.selectbox("Rozmowa z:", [p for p in pracownicy if p != zalogowany])
    
    # Okno rozmowy
    chat_container = st.container(height=450, border=False)
    with chat_container:
        if not df_chat.empty and 'TREŚĆ' in df_chat.columns:
            # Filtrowanie rozmowy
            history = df_chat[((df_chat['NADAWCA'] == zalogowany) & (df_chat['ODBIORCA'] == wybrany)) | 
                             ((df_chat['NADAWCA'] == wybrany) & (df_chat['ODBIORCA'] == zalogowany))]
            
            for _, msg in history.tail(20).iterrows():
                is_mine = msg['NADAWCA'] == zalogowany
                row_class = "msg-mine" if is_mine else "msg-theirs"
                bubble_class = "bubble-mine" if is_mine else "bubble-theirs"
                
                st.markdown(f"""
                    <div class="msg-row {row_class}">
                        <div class="bubble {bubble_class}">
                            <div style="font-size:0.75rem; font-weight:bold; margin-bottom:2px;">{msg['NADAWCA']}</div>
                            {msg['TREŚĆ']}
                            <div class="msg-info">{msg['CZAS']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # Pole wpisywania
    t_input = st.chat_input(f"Napisz do: {wybrany}...")
    if t_input:
        if wyslij_wiadomosc(zalogowany, wybrany, t_input):
            st.rerun()

# BELKA DOLNA
st.markdown(f'<div class="main-sheet-footer"><div style="color:#eab308; font-weight:800; font-size:0.8rem;">UZDROWISKO CIECHOCINEK S.A.</div><div style="font-size:0.75rem; color:#94a3b8;">{now_pl.strftime("%d.%m.%Y | %H:%M:%S")}</div></div>', unsafe_allow_html=True)

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
st_autorefresh(interval=10000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0px !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    .logo-container { text-align: center; margin-top: -35px !important; margin-bottom: 15px !important; }
    .logo-container img { width: 190px; cursor: pointer; }

    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 10px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }

    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; margin-right: 5px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }

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
        if len(dane) < 1: return pd.DataFrame()
        return pd.DataFrame(dane[1:], columns=dane[0])
    except: return pd.DataFrame()

def dodaj_zadanie_do_arkusza(tresc, osoba, deadline, uwagi):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("Zadania bieżące")
        ws.append_row(["", tresc, uwagi, deadline, "", osoba, "W trakcie", "FALSE"])
        return True
    except: return False

def generuj_kalendarz_html():
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    html = f'<div style="background:white; padding:8px; border-radius:8px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1; font-size:10px;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; border-bottom:1px solid #eee; padding-bottom:3px;">{calendar.month_name[now.month].upper()}</th></tr><tr style="color:#64748b; font-size:8px;"><th>PN</th><th>WT</th><th>ŚR</th><th>CZ</th><th>PT</th><th>SO</th><th>ND</th></tr></thead><tbody>'
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                bg = "#eab308" if day == now.day else "transparent"
                html += f'<td style="text-align:center; padding:3px; font-weight:700; background-color:{bg}; border-radius:4px;">{day}</td>'
        html += "</tr>"
    return html + "</tbody></table></div>"

# ==========================================================
# 3. LOGIKA I SIDEBAR (PRZYWRÓCONY KALENDARZ)
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = u
else: st.error("BŁĄD LOGOWANIA"); st.stop()

df_chat = pobierz_df("CZAT")
has_new = False
if not df_chat.empty and 'ODBIORCA' in df_chat.columns:
    has_new = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty

with st.sidebar:
    st.markdown(f'<div class="logo-container"><a href="?u={u}&k={k}" target="_self"><img src="{LOGO_URL}"></a></div>', unsafe_allow_html=True)
    st.markdown('<div style="border-bottom:1px solid #334155; margin:10px 0;"></div>', unsafe_allow_html=True)
    
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True):
        st.session_state.show_form = True

    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    # --- PRZYWRÓCONY KALENDARZ ---
    st.components.v1.html(generuj_kalendarz_html(), height=155)
    
    # TERMINY W SIDEBARZE
    st.markdown("<p style='color:white; font-size:0.8rem; font-weight:bold; margin-bottom:5px;'>📅 Nadchodzące:</p>", unsafe_allow_html=True)
    df_biez = pobierz_df("Zadania bieżące")
    if not df_biez.empty:
        for _, r in df_biez.head(2).iterrows():
            st.markdown(f"<div style='background:#334155; padding:5px; border-radius:5px; border-left:3px solid #ef4444; margin-bottom:3px; color:white; font-size:0.7rem;'>{r['DEADLINE']}: {r['TREŚĆ ZADANIA'][:25]}...</div>", unsafe_allow_html=True)

    if has_new:
        st.markdown('<p style="color:#ef4444; font-weight:900; text-align:center; animation: blinker 1.5s linear infinite;">🔔 NOWA WIADOMOŚĆ!</p>', unsafe_allow_html=True)
        st.markdown('<audio autoplay><source src="https://www.soundjay.com/buttons/beep-07a.mp3"></audio>', unsafe_allow_html=True)

# ==========================================================
# 4. FORMULARZ DODAWANIA
# ==========================================================
if st.session_state.get('show_form', False):
    with st.expander("📝 NOWE ZADANIE", expanded=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            n_tresc = st.text_input("Zadanie:")
            n_osoba = st.selectbox("Osoba:", ["Marta", "Sławek", "Agata", "Rafał", "Andrzej", "Pola"])
        with f_col2:
            n_deadline = st.date_input("Termin:")
            n_uwagi = st.text_area("Uwagi:")
        
        c1, c2 = st.columns(2)
        if c1.button("✅ ZAPISZ", use_container_width=True):
            if n_tresc:
                if dodaj_zadanie_do_arkusza(n_tresc, n_osoba, n_deadline.strftime("%d.%m.%Y"), n_uwagi):
                    st.success("Zadanie dodane!"); st.session_state.show_form = False; st.cache_data.clear(); st.rerun()
        if c2.button("❌ ANULUJ", use_container_width=True):
            st.session_state.show_form = False; st.rerun()

# ==========================================================
# 5. WIDOK GŁÓWNY
# ==========================================================
chat_label = "💬 CZAT (NOWY!)" if has_new else "💬 CZAT"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", chat_label])

now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))
df_zrealizowane = pobierz_df("Zadania zrealizowane")

for i, kat in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📋 Razem", len(df))
            if 'DNI' in df.columns:
                df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
                m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
            m3.metric("✅ Zrealizowane", len(df_zrealizowane))
            m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))
            st.data_editor(df, use_container_width=True, hide_index=True, height=500)

with tabs[3]:
    if df_chat.empty or 'ODBIORCA' not in df_chat.columns:
        st.warning("Brak nagłówków w arkuszu CZAT")
    else:
        odbiorca = st.selectbox("Adresat:", ["Marta", "Sławek", "Agata", "Rafał", "Andrzej"])
        chat_box = st.container(height=350, border=True)
        history = df_chat[((df_chat['NADAWCA'] == zalogowany) & (df_chat['ODBIORCA'] == odbiorca)) | 
                         ((df_chat['NADAWCA'] == odbiorca) & (df_chat['ODBIORCA'] == zalogowany))]
        for _, msg in history.tail(10).iterrows():
            cls = "chat-mine" if msg['NADAWCA'] == zalogowany else "chat-theirs"
            chat_box.markdown(f'<div style="padding:10px; border-radius:12px; margin-bottom:8px; font-size:0.9rem;" class="{cls}"><b>{msg["NADAWCA"]}</b>: {msg["TREŚĆ"]}</div>', unsafe_allow_html=True)
        t_input = st.chat_input("Napisz...")
        if t_input and wyslij_wiadomosc(zalogowany, odbiorca, t_input): st.rerun()

# --- BELKA DOLNA ---
st.markdown(f'<div class="main-sheet-footer"><div style="color:#eab308; font-weight:800; font-size:0.8rem;">UZDROWISKO CIECHOCINEK S.A.</div><div style="font-size:0.7rem; color:#94a3b8;">{now_pl.strftime("%d.%m.%Y | %H:%M:%S")}</div></div>', unsafe_allow_html=True)

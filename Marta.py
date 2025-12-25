import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (NAPRAWA ZASŁANIANIA)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="global_refresh")

LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"

st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* LOGO */
    .logo-container { text-align: center; margin-top: -65px !important; margin-bottom: 25px !important; }
    .logo-container img { width: 200px; }
    
    /* --- NOWA ETYKIETA ZALOGOWANEGO (ZINTEGROWANA, NIE ZASŁANIA) --- */
    .user-info-box {
        background-color: #eab308;
        color: #1e293b !important;
        padding: 10px;
        border-radius: 8px;
        font-weight: 900;
        font-size: 0.85rem;
        text-align: center;
        margin-top: 20px;
        border: 2px solid white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* METRYKI */
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }
    [data-testid="stMetric"] { background-color: #1e293b !important; border-top: 4px solid #eab308 !important; border-radius: 10px !important; padding: 5px 10px !important; }
    
    /* ZAKŁADKI */
    button[data-baseweb="tab"] { font-size: 1.1rem !important; font-weight: 700 !important; color: #1e293b !important; background-color: #e2e8f0 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 25px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: white !important; background-color: #1e293b !important; border-bottom: 4px solid #eab308 !important; }
    
    .term-box { background: #334155; padding: 6px 10px; border-radius: 6px; border-left: 4px solid #ef4444; margin-bottom: 5px; color: white; font-size: 0.72rem; }
    .sidebar-header { color: #eab308; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; margin-top: 10px; }
    
    /* CZAT */
    .chat-bubble-container { display: flex; flex-direction: column; gap: 8px; padding: 15px; background: #f1f5f9; border-radius: 12px; margin-bottom: 20px; border: 1px solid #cbd5e1; }
    .bubble { padding: 10px 15px; border-radius: 15px; font-size: 13px; max-width: 80%; color: black !important; }
    .bubble-me { align-self: flex-end; background-color: #eab308; }
    .bubble-other { align-self: flex-start; background-color: white; border: 1px solid #cbd5e1; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. LOGOWANIE I DANE
# ==========================================================
USERS = {"Andrzej": "8800", "Marta": "1111", "Sławek": "2222", "Agata": "3333", "Rafał": "4444", "Dagmara": "5555", "Ewelina": "6666", "Ireneusz": "7777"}
u_p, k_p = st.query_params.get("u", ""), st.query_params.get("k", "")
if u_p in USERS and USERS[u_p] == k_p: zalogowany = u_p
else: st.error("BŁĄD LOGOWANIA"); st.stop()

def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

@st.cache_data(ttl=20)
def pobierz_df(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        if len(dane) < 2: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df[df.iloc[:, 0].astype(str).str.strip() != ""].copy()
    except: return pd.DataFrame()

# ==========================================================
# 3. FUNKCJA KALENDARZA
# ==========================================================
def generuj_kalendarz_html(df_zadania, user):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    cal = calendar.monthcalendar(now.year, now.month)
    dni_z_terminami = []
    if not df_zadania.empty and 'DEADLINE' in df_zadania.columns:
        df_f = df_zadania if user == "Andrzej" else df_zadania[df_zadania['OSOBA'].str.contains(user, na=False)]
        df_f['DT_TMP'] = pd.to_datetime(df_f['DEADLINE'], dayfirst=True, errors='coerce')
        dni_z_terminami = df_f[df_f['DT_TMP'].dt.month == now.month]['DT_TMP'].dt.day.tolist()

    html = f'<div style="background:white; padding:8px; border-radius:8px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1.2; font-size:11px;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; border-bottom:1px solid #eee; padding-bottom:5px;">{calendar.month_name[now.month].upper()}</th></tr></thead><tbody>'
    for week in cal:
        html += '<tr style="height:22px;">'
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                bg = "#eab308" if day == now.day else "transparent"
                color = "#ef4444" if day in dni_z_terminami else "#1e293b"
                html += f'<td style="text-align:center; padding:2px; font-weight:700; background-color:{bg}; color:{color}; border:{"1px solid #ef4444" if day in dni_z_terminami else "none"}; border-radius:4px;">{day}</td>'
        html += "</tr>"
    return html + "</tbody></table></div>"

# ==========================================================
# 4. SIDEBAR (BEZ ZASŁANIANIA)
# ==========================================================
df_biez = pobierz_df("Zadania bieżące")
df_chat = pobierz_df("CZAT")
has_new = not df_chat[(df_chat['ODBIORCA'] == zalogowany) & (df_chat['STATUS'] == "NIEPRZECZYTANE")].empty if not df_chat.empty else False

with st.sidebar:
    st.markdown(f'<div class="logo-container"><img src="{LOGO_URL}"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">🧭 Nawigacja</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.button("➕ DODAJ", use_container_width=True)
    with c2: 
        if st.button("🔄 ODSW", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.markdown('<div style="border-top:1px solid #334155; margin:10px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">📅 TWOJE TERMINY</div>', unsafe_allow_html=True)
    st.components.v1.html(generuj_kalendarz_html(df_biez, zalogowany), height=175)
    st.markdown('<div class="sidebar-header">🕒 NADCHODZĄCE TWOJE</div>', unsafe_allow_html=True)
    if not df_biez.empty:
        df_side = df_biez if zalogowany == "Andrzej" else df_biez[df_biez['OSOBA'].str.contains(zalogowany, na=False)]
        for _, r in df_side.head(5).iterrows():
            dni = pd.to_numeric(r.get('DNI', 0), errors='coerce')
            st.markdown(f'<div class="term-box">{"🔥" if dni >= -2 else "🟢"} <b>{r.get("DEADLINE","")}</b>: {str(r.get("TREŚĆ ZADANIA",""))[:30]}...</div>', unsafe_allow_html=True)
    
    # --- ETYKIETA ZALOGOWANEGO NA KOŃCU LISTY W SIDEBARZE ---
    display_name = f"{zalogowany.upper()} Walczak" if zalogowany == "Andrzej" else zalogowany.upper()
    st.markdown(f'<div class="user-info-box">👤 ZALOGOWANO: {display_name}</div>', unsafe_allow_html=True)

# ==========================================================
# 5. WIDOK GŁÓWNY (CZYSTY I CZYTELNY)
# ==========================================================
chat_tab_label = f"💬 CZAT {'🔴' if has_new else ''}"
tabs = st.tabs(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", chat_tab_label])
now_pl = datetime.now(pytz.timezone('Europe/Warsaw'))

for i, kat in enumerate(["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka"]):
    with tabs[i]:
        df = pobierz_df(kat)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📋 Razem", len(df))
        if not df.empty and 'DNI' in df.columns:
            df['D_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            m2.metric("🔥 Pilne (-2+)", len(df[df['D_N'] >= -2]))
            df_view = df.copy()
            df_view['TREŚĆ ZADANIA'] = df_view.apply(lambda r: f"{('🔥 ' if pd.to_numeric(r['DNI'], errors='coerce') >= -2 else '🟢 ')}{r['TREŚĆ ZADANIA']}", axis=1)
            st.data_editor(df_view.drop(columns=['D_N']), use_container_width=True, hide_index=True, height=800)
        m4.metric("🕒 Aktualizacja", now_pl.strftime("%H:%M"))

with tabs[3]:
    st.subheader("💬 Messenger Firmowy")
    if not df_chat.empty:
        chat_html = '<div class="chat-bubble-container">'
        historia = df_chat[(df_chat['NADAWCA'] == zalogowany) | (df_chat['ODBIORCA'] == zalogowany)].tail(15)
        for _, r in historia.iterrows():
            is_me = r['NADAWCA'] == zalogowany
            align = "bubble-me" if is_me else "bubble-other"
            chat_html += f'<div class="bubble {align}"><b>{r["NADAWCA"]}</b><br>{r["TREŚĆ"]}</div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    
    with st.form("msg_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        target = col1.selectbox("Odbiorca:", [u for u in USERS.keys() if u != zalogowany])
        msg_text = col1.text_area("Wpisz wiadomość...", height=70)
        if col2.form_submit_button("WYŚLIJ 🚀", use_container_width=True) and msg_text:
            polacz().open("Marta-Dział Techniczny").worksheet("CZAT").append_row([now_pl.strftime("%Y-%m-%d %H:%M"), zalogowany, target, msg_text, "NIEPRZECZYTANE"])
            st.cache_data.clear(); st.rerun()

st.markdown(f'<div style="margin-top:20px; padding:10px; background:#1e293b; color:white; border-radius:5px; display:flex; justify-content:space-between;"><b>UZDROWISKO CIECHOCINEK S.A.</b> <span>{now_pl.strftime("%d.%m.%Y | %H:%M")}</span></div>', unsafe_allow_html=True)

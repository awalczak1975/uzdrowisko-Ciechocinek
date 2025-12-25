import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I DOPRACOWANA STYLIZACJA
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
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* PRZYCISKI W PANELU */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-weight: 600 !important;
    }

    /* STYLIZACJA ZAKŁADEK (TABS) - POPRAWKA CZYTELNOŚCI */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #475569 !important; /* Wyraźny szary dla nieaktywnych */
        background-color: #f1f5f9 !important; /* Jasne tło dla nieaktywnych */
        border-radius: 8px 8px 0 0 !important;
        margin-right: 5px !important;
        padding: 10px 25px !important;
        transition: 0.3s !important;
        border: 1px solid #e2e8f0 !important;
    }

    /* AKTYWNA ZAKŁADKA - KOLOR LEWEGO PANELU */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important;
        background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }

    /* KAFELKI PODSUMOWANIA (CIEMNE) */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; 
        border-top: 4px solid #eab308 !important; 
        border-radius: 10px !important; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricValue"] > div { color: #eab308 !important; font-weight: 900 !important; font-size: 2.5rem !important; }
    [data-testid="stMetricLabel"] > div { color: white !important; font-weight: 600 !important; font-size: 1.2rem !important; }

    /* STYL CZATU */
    .chat-bubble {
        padding: 12px 18px; border-radius: 10px; margin-bottom: 8px;
        border-left: 5px solid #0ea5e9; background-color: #f8fafc;
    }
    .chat-to { color: #eab308; font-weight: bold; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE GOOGLE SHEETS
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
        df = pd.DataFrame(dane[1:], columns=dane[0]).iloc[:, :5]
        return df[df.iloc[:, 0].str.strip() != ""]
    except: return pd.DataFrame()

def zapisz_df(df, zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())
        return True
    except: return False

def wyslij_chat(autor, adresat, tekst):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("Czat")
        now = datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M (%d.%m)")
        ws.append_row([now, autor, adresat, tekst])
        return True
    except: return False

# ==========================================================
# 3. WERYFIKACJA I SIDEBAR
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
uzytkownicy = {"Andrzej": "8800", "Marta": "1234", "Rafał": "5566", "Agata": "9911", "Sławek": "4422"}

if u in uzytkownicy and uzytkownicy[u] == k:
    zalogowany = u
    czy_admin = u in ["Andrzej", "Marta"]
else:
    st.error("❌ BŁĄD DOSTĘPU"); st.stop()

with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h2>", unsafe_allow_html=True)
    st.divider()
    if st.button("🔄 ODŚWIEŻ DANE", use_container_width=True): 
        st.cache_data.clear()
        st.rerun()
    st.write(f"Zalogowany: **{zalogowany}**")

# ==========================================================
# 4. WIDOK GŁÓWNY
# ==========================================================
kat_list = ["Zadania bieżące", "Zadania zrealizowane"]
if zalogowany == "Andrzej": kat_list.append("Terminy Sławka")
kat_list.append("🔴 CZAT")

tabs = st.tabs(kat_list)

for i, kat in enumerate(kat_list[:-1]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            
            # KAFELKI PODSUMOWANIA
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Razem zadań", len(df))
            m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
            m3.metric("🕒 Godzina", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))
            
            # Ikony statusu
            df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))
            
            edytowane = st.data_editor(
                df, use_container_width=True, hide_index=True, height=450,
                disabled=not czy_admin, key=f"ed_{kat}",
                column_config={"DNI_N": None, "S": st.column_config.TextColumn(" ", width="small")}
            )
            
            if czy_admin:
                if st.button(f"💾 ZAPISZ ZMIANY: {kat.upper()}", key=f"btn_{kat}"):
                    if zapisz_df(edytowane.drop(columns=["S", "DNI_N"]), kat):
                        st.success("Zapisano pomyślnie!"); st.cache_data.clear(); st.rerun()

# CZAT Z WYBOREM ADRESATA
with tabs[-1]:
    st.subheader("🔴 Komunikacja pracownicza")
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        do_kogo = st.selectbox("Do kogo:", ["Wszyscy"] + [n for n in uzytkownicy.keys() if n != zalogowany])
    with c2:
        msg = st.text_input("Twoja wiadomość...", key="chat_msg")
    with c3:
        st.write(" ")
        if st.button("WYŚLIJ 📩", use_container_width=True):
            if msg and wyslij_chat(zalogowany, do_kogo, msg):
                st.rerun()
    
    st.divider()
    df_c = pobierz_df("Czat")
    if not df_c.empty:
        for _, r in df_c.iloc[::-1].iterrows():
            # Widzisz wiadomości do Ciebie, do Wszystkich lub Twoje własne
            if r['Adresat'] in [zalogowany, "Wszyscy"] or r['Autor'] == zalogowany:
                st.markdown(f"""
                    <div class="chat-bubble">
                        <div class="chat-meta">{r['Autor']} • {r['Data']}</div>
                        <div class="chat-to">DO: {r['Adresat']}</div>
                        <div style="color:#1e293b;">{r['Wiadomość']}</div>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================================
# 5. DOLNA BELKA WWW
# ==========================================================
st.markdown("""
    <div style="display: flex; justify-content: center; background-color: white; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-top: 40px;">
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/oferta/">Oferta</a>
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/sanatoria/">Sanatoria</a>
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/teznia-i-inne-atrakcje/">Tężnie</a>
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/o-uzdrowisku/">O nas</a>
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/zabiegi/">Zabiegi</a>
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/kontakt/">Kontakt</a>
    </div>
    """, unsafe_allow_html=True)

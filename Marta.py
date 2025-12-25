import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide")
st_autorefresh(interval=30000, key="globalrefresh")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* Stylizacja zakładek - powiększenie i wyróżnienie */
    button[data-baseweb="tab"] { font-size: 1.1rem !important; font-weight: 700 !important; }
    
    /* Styl czatu */
    .chat-bubble {
        padding: 12px 18px; border-radius: 15px; margin-bottom: 10px;
        border: 1px solid #e2e8f0; background-color: white;
    }
    .chat-meta { font-size: 0.75rem; color: #64748b; }

    /* Belka WWW na dole */
    .nav-bar {
        display: flex; justify-content: center; background-color: white;
        border: 1px solid #e2e8f0; border-radius: 10px; padding: 0;
        overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 40px;
    }
    .nav-item {
        flex: 1; text-align: center; padding: 18px 10px;
        text-decoration: none !important; color: #334155 !important;
        font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9;
        text-transform: uppercase;
    }
    .nav-item:hover { background-color: #f8fafc; color: #0ea5e9 !important; }
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
        df = pd.DataFrame(dane[1:], columns=dane[0])
        return df
    except: return pd.DataFrame()

def zapisz_df(df, zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())
        return True
    except: return False

def wyslij_wiadomosc_chat(autor, tekst):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("Czat")
        now = datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M (%d.%m)")
        ws.append_row([now, autor, tekst])
        return True
    except: return False

# ==========================================================
# 3. WERYFIKACJA
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
uzytkownicy = {"Andrzej": "8800", "Marta": "1234", "Rafał": "5566", "Agata": "9911", "Sławek": "4422"}

if u in uzytkownicy and uzytkownicy[u] == k:
    zalogowany = u
    czy_admin = u in ["Andrzej", "Marta"]
else:
    st.error("BŁĄD DOSTĘPU"); st.stop()

# ==========================================================
# 4. WIDOK GŁÓWNY (ZAKŁADKI)
# ==========================================================
# Tytuly zakładek z kropką przy Czacie
kat_list = ["Zadania bieżące", "Zadania zrealizowane"]
if zalogowany == "Andrzej": kat_list.append("Terminy Sławka")
kat_list.append("🔴 CZAT") # TUTAJ JEST TWOJA KROPKA

tabs = st.tabs(kat_list)

# Obsługa Zadań
for i, kat in enumerate(kat_list[:-1]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))
            
            edytowane = st.data_editor(
                df, use_container_width=True, hide_index=True, height=450,
                disabled=not czy_admin, key=f"ed_{kat}",
                column_config={"DNI_N": None, "S": st.column_config.TextColumn(" ", width="small")}
            )
            
            if czy_admin:
                if st.button(f"💾 ZAPISZ: {kat.upper()}", key=f"btn_{kat}"):
                    if zapisz_df(edytowane.drop(columns=["S", "DNI_N"]), kat):
                        st.success("Zapisano!"); st.cache_data.clear(); st.rerun()

# Obsługa Czatu
with tabs[-1]:
    st.subheader("Komunikacja pracownicza")
    msg = st.text_input("Napisz wiadomość i naciśnij Enter lub przycisk...", key="chat_input")
    if st.button("WYŚLIJ 📩"):
        if msg:
            if wyslij_wiadomosc_chat(zalogowany, msg):
                st.rerun()

    st.divider()
    df_chat = pobierz_df("Czat")
    if not df_chat.empty:
        for _, row in df_chat.iloc[::-1].iterrows():
            st.markdown(f"""
                <div class="chat-bubble">
                    <div class="chat-meta"><b>{row['Autor']}</b> • {row['Data']}</div>
                    <div class="chat-text">{row['Wiadomość']}</div>
                </div>
            """, unsafe_allow_html=True)

# ==========================================================
# 5. DOLNE MENU WWW
# ==========================================================
st.markdown("""
    <div class="nav-bar">
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/oferta/">Oferta</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/sanatoria/">Sanatoria</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/teznia-i-inne-atrakcje/">Tężnie</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/o-uzdrowisku/">O nas</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/zabiegi/">Zabiegi</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/kontakt/">Kontakt</a>
    </div>
    """, unsafe_allow_html=True)

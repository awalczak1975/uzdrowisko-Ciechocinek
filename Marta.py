]import streamlit as st
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
# Odświeżanie co 30 sekund dla płynności czatu
st_autorefresh(interval=30000, key="globalrefresh")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* Przyciski systemowe */
    div.stButton > button {
        background-color: #334155 !important; color: white !important;
        font-weight: 600 !important; height: 45px !important;
    }

    /* Stylizacja czatu */
    .chat-bubble {
        padding: 12px 18px; border-radius: 15px; margin-bottom: 10px;
        border: 1px solid #e2e8f0; background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .chat-meta { font-size: 0.75rem; color: #64748b; margin-bottom: 4px; }
    .chat-text { font-size: 0.95rem; color: #1e293b; }

    /* Profesjonalna Belka WWW na dole */
    .nav-bar {
        display: flex; justify-content: center; background-color: white;
        border: 1px solid #e2e8f0; border-radius: 10px; padding: 0;
        overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 40px;
    }
    .nav-item {
        flex: 1; text-align: center; padding: 18px 10px;
        text-decoration: none !important; color: #334155 !important;
        font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9;
        text-transform: uppercase; transition: 0.3s;
    }
    .nav-item:hover { background-color: #f8fafc; color: #0ea5e9 !important; }
    .nav-home { background-color: #f8fafc; flex: 0.3; color: #0ea5e9 !important; font-size: 1.1rem; }
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

def wyslij_wiadomosc_chat(autor, tekst):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("Czat")
        # Formatowanie godziny dla Polski
        now = datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M (%d.%m)")
        ws.append_row([now, autor, tekst])
        return True
    except: return False

# ==========================================================
# 3. WERYFIKACJA UŻYTKOWNIKA
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
uzytkownicy = {"Andrzej": "8800", "Marta": "1234", "Rafał": "5566", "Agata": "9911", "Sławek": "4422"}

if u in uzytkownicy and uzytkownicy[u] == k:
    zalogowany = u
    czy_admin = u in ["Andrzej", "Marta"]
else:
    st.error("❌ BŁĄD DOSTĘPU"); st.stop()

with st.sidebar:
    st.markdown("<h2 style='color:#0ea5e9; text-align:center;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h2>", unsafe_allow_html=True)
    st.divider()
    if st.button("🔄 ODŚWIEŻ DANE", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.write(f"Zalogowany: **{zalogowany}**")

# ==========================================================
# 4. WIDOK GŁÓWNY (ZAKŁADKI)
# ==========================================================
kategorie = ["Zadania bieżące", "Zadania zrealizowane"]
if zalogowany == "Andrzej": kategorie.append("Terminy Sławka")
kategorie.append("💬 CZAT")

tabs = st.tabs(kategorie)

# Obsługa Zadań
for i, kat in enumerate(kategorie[:-1]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            # Logika ikon: -2 i więcej to alarm 🚨
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))
            
            edytowane = st.data_editor(
                df, use_container_width=True, hide_index=True, height=450,
                disabled=not czy_admin, key=f"ed_{kat}",
                column_config={"DNI_N": None, "S": st.column_config.TextColumn(" ", width="small")}
            )
            
            if czy_admin:
                if st.button(f"💾 ZAPISZ ZMIANY: {kat.upper()}", key=f"btn_{kat}"):
                    # Usuwamy kolumny pomocnicze przed zapisem do Google
                    df_final = edytowane.drop(columns=["S", "DNI_N"])
                    if zapisz_df(df_final, kat):
                        st.success("Zapisano!"); st.cache_data.clear(); st.rerun()
        else:
            st.info("Brak zadań w tej sekcji.")

# Obsługa Czatu
with tabs[-1]:
    st.subheader("Komunikacja wewnętrzna")
    c1, c2 = st.columns([4, 1])
    with c1:
        msg = st.text_input("Twoja wiadomość...", key="chat_input", label_visibility="collapsed")
    with c2:
        if st.button("WYŚLIJ 📩", use_container_width=True):
            if msg:
                if wyslij_wiadomosc_chat(zalogowany, msg):
                    st.rerun()

    st.divider()
    df_chat = pobierz_df("Czat")
    if not df_chat.empty:
        # Wyświetlamy wiadomości od najnowszych na górze
        for _, row in df_chat.iloc[::-1].iterrows():
            st.markdown(f"""
                <div class="chat-bubble">
                    <div class="chat-meta"><b>{row['Autor']}</b> • {row['Data']}</div>
                    <div class="chat-text">{row['Wiadomość']}</div>
                </div>
            """, unsafe_allow_html=True)

# ==========================================================
# 5. DOLNE MENU WWW (GRAFICZNE)
# ==========================================================
st.markdown("""
    <div class="nav-bar">
        <a class="nav-item nav-home" href="https://uzdrowiskociechocinek.pl/">🏠</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/oferta/">Oferta</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/sanatoria/">Sanatoria</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/teznia-i-inne-atrakcje/">Tężnie</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/o-uzdrowisku/">O nas</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/zabiegi/">Zabiegi</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/kontakt/">Kontakt</a>
    </div>
    <div style='text-align:center; color:#94a3b8; font-size: 0.75rem; margin-top:20px;'>
        Panel Operacyjny Uzdrowisko Ciechocinek S.A. | 2025
    </div>
    """, unsafe_allow_html=True)

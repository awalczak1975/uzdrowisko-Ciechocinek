import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I PRZYWRÓCENIE ORYGINALNEGO STYLU
# ==========================================================
st.set_page_config(
    page_title="System Uzdrowisko", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=30000, key="globalrefresh")

st.markdown("""
    <style>
    /* PRZYWRÓCENIE CIEMNEGO PANELU BOCZNEGO */
    [data-testid="stSidebar"] { 
        background-color: #1e293b !important; 
        border-right: 5px solid #eab308 !important; 
    }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-weight: 600 !important;
    }

    /* NAGŁÓWKI ZAKŁADEK */
    button[data-baseweb="tab"] { font-size: 1.1rem !important; font-weight: 700 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #eab308 !important; border-bottom-color: #eab308 !important; }

    /* METRYKI (GÓRNE PODSUMOWANIE) */
    [data-testid="stMetric"] { 
        background-color: white !important; border-top: 4px solid #eab308 !important; 
        border-radius: 8px !important; padding: 15px !important; text-align: center !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; font-weight: 900 !important; font-size: 2.2rem !important; color: #1e293b !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; font-size: 1.1rem !important; font-weight: 600 !important; color: #64748b !important; }

    /* STYL CZATU */
    .chat-bubble {
        padding: 12px 18px; border-radius: 10px; margin-bottom: 8px;
        border-left: 5px solid #0ea5e9; background-color: #f8fafc;
    }
    .chat-to { color: #eab308; font-weight: bold; font-size: 0.8rem; }
    
    /* BELKA WWW DOLNA */
    .nav-bar {
        display: flex; justify-content: center; background-color: white;
        border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-top: 40px;
    }
    .nav-item {
        flex: 1; text-align: center; padding: 18px 10px;
        text-decoration: none !important; color: #1e293b !important;
        font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9;
        text-transform: uppercase;
    }
    .nav-item:hover { background-color: #f8fafc; color: #eab308 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE
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
    st.markdown("<h2 style='text-align:center;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h2>", unsafe_allow_html=True)
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
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Razem", len(df))
            m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
            m3.metric("🕒 Godzina", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))
            
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

# CZAT Z WYBOREM ADRESATA
with tabs[-1]:
    st.subheader("Komunikacja w dziale")
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        do_kogo = st.selectbox("Do kogo:", ["Wszyscy"] + [name for name in uzytkownicy.keys() if name != zalogowany])
    with c2:
        msg = st.text_input("Treść wiadomości...", key="chat_in")
    with c3:
        st.write(" ") # wyrównanie
        if st.button("WYŚLIJ 📩", use_container_width=True):
            if msg and wyslij_chat(zalogowany, do_kogo, msg): st.rerun()
    
    st.divider()
    # Zakładka Czat musi mieć kolumny: Data, Autor, Adresat, Wiadomość
    df_c = pobierz_df("Czat")
    if not df_c.empty:
        for _, r in df_c.iloc[::-1].iterrows():
            # Filtrowanie: widzisz wiadomości do Ciebie lub do Wszystkich
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
    <div class="nav-bar">
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/oferta/">Oferta</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/sanatoria/">Sanatoria</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/teznia-i-inne-atrakcje/">Tężnie</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/o-uzdrowisku/">O nas</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/zabiegi/">Zabiegi</a>
        <a class="nav-item" href="https://uzdrowiskociechocinek.pl/kontakt/">Kontakt</a>
    </div>
    """, unsafe_allow_html=True)

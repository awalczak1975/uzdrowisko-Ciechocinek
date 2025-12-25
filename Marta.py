import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA STRONY
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=300000, key="datarefresh")

# ==========================================================
# 2. DANE DOSTĘPOWE
# ==========================================================
KLUCZE_DOSTEPU = {"Andrzej": "8800", "Marta": "1234", "Rafał": "5566", "Agata": "9911", "Sławek": "4422"}
NAZWA_ARKUSZA = "Marta-Dział Techniczny"
LISTA_OSOB = list(KLUCZE_DOSTEPU.keys())

# ==========================================================
# 3. WERYFIKACJA UŻYTKOWNIKA
# ==========================================================
user_url = st.query_params.get("u", "")
key_url = st.query_params.get("k", "")

if user_url in KLUCZE_DOSTEPU and KLUCZE_DOSTEPU[user_url] == key_url:
    zalogowany_uzytkownik = user_url
    czy_andrzej = (user_url == "Andrzej")
    czy_admin = (user_url in ["Andrzej", "Marta"])
else:
    st.error("❌ BŁĄD DOSTĘPU")
    st.stop()

# ==========================================================
# 4. FUNKCJE GOOGLE SHEETS
# ==========================================================
def polacz_z_google():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], 
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def pobierz_dane_final(nazwa_zakladki):
    try:
        client = polacz_z_google()
        ws = client.open(NAZWA_ARKUSZA).worksheet(nazwa_zakladki)
        dane_raw = ws.get_all_values()
        if not dane_raw: return pd.DataFrame()
        df = pd.DataFrame(dane_raw[1:], columns=dane_raw[0])
        df = df.iloc[:, :5] 
        df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
        return df
    except:
        return pd.DataFrame()

def aktualizuj_arkusz(df_nowy, nazwa_zakladki):
    try:
        client = polacz_z_google()
        ws = client.open(NAZWA_ARKUSZA).worksheet(nazwa_zakladki)
        naglowki = df_nowy.columns.tolist()
        wartosci = df_nowy.values.tolist()
        dane_do_zapisu = [naglowki] + wartosci
        ws.clear()
        ws.update("A1", dane_do_zapisu)
        return True
    except:
        return False

# ==========================================================
# 5. STYLIZACJA CSS
# ==========================================================
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-size: 0.85rem !important;
        font-weight: 600 !important; width: 100% !important; height: 50px !important;
    }
    [data-testid="stMetric"] { 
        background-color: white !important; border-top: 4px solid #eab308 !important; 
        border-radius: 8px !important; padding: 15px !important; text-align: center !important; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 6. DIALOG I PANEL BOCZNY
# ==========================================================
@st.dialog("➕ Dodaj nowe zadanie")
def dodaj_zadanie_dialog():
    with st.form("form_nowe"):
        tresc = st.text_area("Treść zadania:")
        osoba = st.selectbox("Osoba odpowiedzialna:", ["Brak"] + LISTA_OSOB)
        termin = st.date_input("Termin realizacji:", datetime.now())
        if st.form_submit_button("ZAPISZ ZADANIE"):
            try:
                client = polacz_z_google()
                zakl = "Terminy Sławka" if osoba == "Sławek" else "Zadania bieżące"
                ws = client.open(NAZWA_ARKUSZA).worksheet(zakl)
                ws.append_row([tresc, osoba if osoba != "Brak" else "", termin.strftime("%d.%m.%Y"), "", ""])
                st.success("Dodano!"); st.cache_data.clear(); st.rerun()
            except: st.error("Błąd zapisu")

with st.sidebar:
    st.markdown("<h2 style='color: #0ea5e9; text-align:center;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h2>", unsafe_allow_html=True)
    st.divider()
    if czy_admin:
        if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True): dodaj_zadanie_dialog()
    if st.button("🔄 ODŚWIEŻ DANE", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.markdown(f"<div style='text-align:center; color:#94a3b8; margin-top:20px;'>Zalogowany: <b>{zalogowany_uzytkownik}</b></div>", unsafe_allow_html=True)

# ==========================================================
# 7. WIDOK GŁÓWNY
# ==========================================================
if 'widok' not in st.session_state: st.session_state['widok'] = 'biezace'

# Nawigacja górna
cols = st.columns(3) if czy_andrzej else st.columns([1, 1, 0.01])
if cols[0].button("📋 BIEŻĄCE", use_container_width=True): st.session_state['widok'] = 'biezace'
if cols[1].button("✅ ZREALIZOWANE", use_container_width=True): st.session_state['widok'] = 'zrealizowane'
if czy_andrzej and cols[2].button("🔧 SŁAWEK", use_container_width=True): st.session_state['widok'] = 'slawek'

mapa = {'biezace': "Zadania bieżące", 'zrealizowane': "Zadania zrealizowane", 'slawek': "Terminy Sławka"}
zakladka_aktualna = mapa[st.session_state['widok']]
df = pobierz_dane_final(zakladka_aktualna)

if not df.empty:
    # Przygotowanie Danych
    kol_data = "DEADLINE" if "DEADLINE" in df.columns else "TERMIN"
    if kol_data in df.columns:
        df['tmp'] = pd.to_datetime(df[kol_data], dayfirst=True, errors='coerce')
        df = df.sort_values(by='tmp', ascending=True).drop(columns=['tmp'])
    if 'DNI' in df.columns:
        df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
        df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))

    # Metryki
    m1, m2, m3 = st.columns(3)
    m1.metric("📋 Razem", len(df))
    m2.metric("🔥 Pilne", len(df[df['DNI_N'] >= -2]) if 'DNI_N' in df.columns else "0")
    m3.metric("🕒 Godzina", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))

    # TABELA
    edytowane_df = st.data_editor(
        df, use_container_width=True, hide_index=True, height=400, 
        disabled=not czy_admin, key=f"ed_{st.session_state['widok']}",
        column_config={"DNI_N": None, "S": st.column_config.TextColumn(" ", width="small")}
    )

    # PRZYCISK ZAPISU - teraz bardziej widoczny
    if czy_admin:
        st.write("")
        if st.button("💾 ZAPISZ ZMIANY W ARKUSZU", use_container_width=True, type="primary"):
            if aktualizuj_arkusz(edytowane_df.drop(columns=["S", "DNI_N"]), zakladka_aktualna):
                st.success("Zapisano pomyślnie!"); st.cache_data.clear(); st.rerun()
            else: st.error("Błąd połączenia z Google Sheets")

# ==========================================================
# 8. MENU DOLNE (AKTYWNE LINKI)
# ==========================================================
st.markdown("---")
st.markdown("### 🌐 SZYBKI DOSTĘP: UZDROWISKOCIECHOCINEK.PL")
m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
with m1: st.link_button("🏠 OFERTA", "https://uzdrowiskociechocinek.pl/oferta/")
with m2: st.link_button("🏨 SANATORIA", "https://uzdrowiskociechocinek.pl/sanatoria/")
with m3: st.link_button("⛲ TĘŻNIE", "https://uzdrowiskociechocinek.pl/teznia-i-inne-atrakcje/")
with m4: st.link_button("👥 O NAS", "https://uzdrowiskociechocinek.pl/o-uzdrowisku/")
with m5: st.link_button("💆 ZABIEGI", "https://uzdrowiskociechocinek.pl/zabiegi/")
with m6: st.link_button("🛒 SKLEP", "https://uzdrowiskociechocinek.pl/produkty-zdrojowe/")
with m7: st.link_button("📞 KONTAKT", "https://uzdrowiskociechocinek.pl/kontakt/")

st.markdown(f"<div style='text-align:center; color:grey; font-size: 0.8rem; margin-top:20px;'>System Zarządzania Uzdrowisko Ciechocinek S.A. | {datetime.now().year}</div>", unsafe_allow_html=True)

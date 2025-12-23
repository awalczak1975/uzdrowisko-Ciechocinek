import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLIK_KLUCZA = os.path.join(BASE_DIR, "klucz.json")  # lokalny JSON z kontem serwisowym
PLIK_LOGO = os.path.join(BASE_DIR, "logo.png")
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko - Andrzej", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")  # odświeżanie co 5 minut

# --- 2. PARAMETRY UŻYTKOWNIKA ---
query_params = st.query_params
user_url = query_params.get("user", ["Andrzej"])[0]

# --- 3. CSS ---
st.markdown("""
<style>
.block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
[data-testid="stHeader"] { display: none !important; }
.top-bar { background-color: #1e293b; height: 30px; width: 100%; position: fixed; top: 0; left: 0; z-index: 1000; display: flex; align-items: center; justify-content: flex-end; padding-right: 20px; border-bottom: 2px solid #facc15; }
.top-bar p { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; margin: 0; }
.sticky-wrapper { position: sticky; top: 30px; z-index: 999; background-color: #ffffff; padding-top: 0px; padding-bottom: 0px; }
.main-content { margin-top: 25px; }
h4 { margin-top: -15px !important; margin-bottom: 10px !important; font-size: 1.7rem !important; font-weight: bold !important; color: #1e293b !important; }
.html-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.9rem; }
.html-table th { background-color: #f1f5f9; color: #475569; text-align: left; padding: 12px; border-bottom: 2px solid #eab308; }
.html-table td { padding: 12px; border-bottom: 1px solid #e2e8f0; white-space: normal !important; word-wrap: break-word; vertical-align: top; }
.html-table tr:nth-child(even) { background-color: rgba(30, 41, 59, 0.05); }
[data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #facc15 !important; }
.stButton { margin-bottom: 12px !important; }
.stButton button { background-color: #334155 !important; color: white !important; border: 1px solid #475569 !important; width: 100% !important; height: 32px !important; font-weight: bold !important; text-align: left !important; padding-left: 12px !important; font-size: 0.75rem !important; border-radius: 4px !important; }
.metric-card { background-color: #1e293b; border-radius: 8px; padding: 5px 5px; border-top: 4px solid #facc15 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; height: 70px; }
.metric-card h3 { margin: 0px 0 0 0; color: #ffffff; font-size: 1.5rem; }
.metric-card p { margin: 0; color: #facc15; font-size: 0.75rem; font-weight: bold; }
.metric-row-wrapper { margin-bottom: 15px !important; }
.user-footer { text-align: center; color: #94a3b8; font-size: 0.7rem; margin-top: 20px; padding-top: 10px; border-top: 1px solid #334155; }
</style>
""", unsafe_allow_html=True)

# --- 4. FUNKCJE ---
def pobierz_polaczenie():
    if not os.path.exists(PLIK_KLUCZA):
        st.error("❌ Brak pliku klucz.json! Umieść go w folderze z Marta.py")
        st.stop()
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        PLIK_KLUCZA, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def pobierz_dane(zakladka):
    try:
        client = pobierz_polaczenie()
        sheet = client.open(NAZWA_ARKUSZA).worksheet(zakladka)
        dane = sheet.get_all_values()
        if not dane: return pd.DataFrame(), "", 0
        df_full = pd.DataFrame(dane[1:], columns=dane[0])
        aktualizacja = datetime.now().strftime("%H:%M")
        liczba_wpisow = len(df_full[df_full.iloc[:, 0].str.strip() != ""])
        df_view = df_full.iloc[:, :5].copy()
        if 'DNI' in df_view.columns:
            df_view['DNI_N'] = pd.to_numeric(df_view['DNI'], errors='coerce').fillna(0)
            def ustaw_ikonke(row):
                if zakladka == "Zadania zrealizowane": return "✅"
                if row['DNI_N'] > 0: return "🔥"
                if row['DNI_N'] >= -3: return "⏳"
                return "✅"
            df_view[' '] = df_view.apply(ustaw_ikonke, axis=1)
        else:
            df_view[' '] = "✅" if zakladka == "Zadania zrealizowane" else "📋"

        # filtrowanie dla użytkowników
        if user_url == "Slawek":
            df_view = df_view[df_view['OSOBA'].str.contains("Sławek", case=False, na=False)]
        elif user_url in ["Marta", "Agata", "Rafal"]:
            df_view = df_view[~df_view['OSOBA'].str.contains("Sławek", case=False, na=False)]

        return df_view, aktualizacja, liczba_wpisow
    except Exception as e:
        st.error(f"❌ Błąd: {e}")
        return pd.DataFrame(), "", 0

def stworz_tabele_html(df):
    if df.empty:
        return "<p style='text-align:center; padding:20px;'>Brak zadań do wyświetlenia.</p>"
    kol_merytoryczne = [c for c in df.columns if c not in [' ', 'DNI_N']]
    wys_kol = [' '] + kol_merytoryczne[:5]
    html = '<table class="html-table"><thead><tr>'
    for k in wys_kol:
        html += f'<th>{k if k != " " else ""}</th>'
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for k in wys_kol: html += f'<td>{row[k]}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

# --- 5. DANE ---
df_biezace, czas_synchro, liczba_biezacych = pobierz_dane("Zadania bieżące")
df_zrealizowane, _, liczba_zrealizowanych = pobierz_dane("Zadania zrealizowane")
df_slawka, _, _ = pobierz_dane("Terminy Sławka")

# --- 6. SIDEBAR ---
with st.sidebar:
    if os.path.exists(PLIK_LOGO): st.image(PLIK_LOGO, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if user_url == "Andrzej":
        st.button("➕ DODAJ ZADANIE", use_container_width=True)
        st.button("📄 RAPORTY PDF", use_container_width=True)
        st.button("💾 ZAPISZ ZMIANY", use_container_width=True)
        if st.button("🔄 SYNCHRONIZUJ", use_container_width=True): st.experimental_rerun()
        st.button("📢 TELEGRAM", use_container_width=True)
    else:
        st.info(f"Witaj, {user_url}!")
        if st.button("🔄 ODŚWIEŻ", use_container_width=True): st.experimental_rerun()
    st.markdown(f'<div class="user-footer">Zalogowany: {user_url}</div>', unsafe_allow_html=True)

# --- 7. WIDOK GŁÓWNY ---
st.markdown(f'<div class="top-bar"><p>OSTATNIA AKTUALIZACJA: {czas_synchro}</p></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.markdown('<div class="sticky-wrapper">', unsafe_allow_html=True)
st.markdown('<h4 style="text-align:center;">Centrum Zarządzania Administracją</h4>', unsafe_allow_html=True)

st.markdown('<div class="metric-row-wrapper">', unsafe_allow_html=True)
if not df_biezace.empty:
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="metric-card"><p>📋 MOJE ZADANIA</p><h3>{liczba_biezacych}</h3></div>', unsafe_allow_html=True)
    with m2:
        pilne = len(df_biezace[(df_biezace['DNI_N'] >= -3) & (df_biezace['DNI_N'] <= 0)]) if 'DNI_N' in df_biezace.columns else 0
        st.markdown(f'<div class="metric-card"><p>⏳ PILNE</p><h3>{pilne}</h3></div>', unsafe_allow_html=True)
    with m3:
        spoznione = len(df_biezace[df_biezace['DNI_N'] > 0]) if 'DNI_N' in df_biezace.columns else 0
        st.markdown(f'<div class="metric-card"><p>🔥 PO CZASIE</p><h3>{spoznione}</h3></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="metric-card"><p>✅ ZREALIZOWANE</p><h3>{liczba_zrealizowanych}</h3></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 8. TABS ---
lista_zakladek = ["📋 MOJE BIEŻĄCE", "✅ MOJE ZREALIZOWANE"]
if user_url in ["Slawek", "Andrzej"]: lista_zakladek.append("📅 TERMINY SŁAWKA")
tabs = st.tabs(lista_zakladek)
st.markdown('</div>', unsafe_allow_html=True)

with tabs[0]: st.markdown(stworz_tabele_html(df_biezace), unsafe_allow_html=True)
with tabs[1]: st.markdown(stworz_tabele_html(df_zrealizowane), unsafe_allow_html=True)
if len(tabs) > 2: 
    with tabs[2]: st.markdown(stworz_tabele_html(df_slawka), unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

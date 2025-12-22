import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA ---
# USTAWIŁEM DOKŁADNĄ NAZWĘ Z TWOJEGO ZDJĘCIA NR 10
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko - Andrzej", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

user_url = st.query_params.get("user", "Andrzej")

# --- 2. STYLIZACJA CSS ---
st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; }
    [data-testid="stHeader"] { display: none !important; }
    .top-bar { background-color: #1e293b; height: 30px; border-bottom: 2px solid #facc15; display: flex; align-items: center; justify-content: flex-end; padding-right: 20px; }
    .top-bar p { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; margin: 0; }
    .metric-card { background-color: #1e293b; border-radius: 8px; padding: 10px; border-top: 4px solid #facc15; text-align: center; color: white; }
    .metric-card h3 { margin: 0; font-size: 1.5rem; }
    .metric-card p { margin: 0; color: #facc15; font-size: 0.75rem; font-weight: bold; }
    .html-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.9rem; }
    .html-table th { background-color: #f1f5f9; color: #475569; text-align: left; padding: 12px; border-bottom: 2px solid #eab308; }
    .html-table td { padding: 12px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
    .html-table tr:nth-child(even) { background-color: rgba(30, 41, 59, 0.05); }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #facc15 !important; color: white !important; }
    .stButton button { background-color: #334155 !important; color: white !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNKCJE ---
def pobierz_polaczenie():
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
    return None

def pobierz_dane(zakladka):
    client = pobierz_polaczenie()
    if not client: return pd.DataFrame(), "", 0
    try:
        sheet = client.open(NAZWA_ARKUSZA).worksheet(zakladka)
        dane = sheet.get_all_values()
        if not dane: return pd.DataFrame(), "", 0
        
        df_full = pd.DataFrame(dane[1:], columns=dane[0])
        aktualizacja = datetime.now().strftime("%H:%M")
        
        # Licznik z kolumny A
        liczba_wpisow = len(df_full[df_full.iloc[:, 0].str.strip() != ""])
        df_view = df_full.iloc[:, :5].copy()
        
        if 'DNI' in df_view.columns:
            df_view['DNI_N'] = pd.to_numeric(df_view['DNI'], errors='coerce').fillna(0)
            def ustaw_ikonke(row):
                if zakladka == "Zadania zrealizowane": return "✅"
                return "🔥" if row['DNI_N'] > 0 else "⏳" if row['DNI_N'] >= -3 else "✅"
            df_view[' '] = df_view.apply(ustaw_ikonke, axis=1)
        else:
            df_view[' '] = "✅" if zakladka == "Zadania zrealizowane" else "📋"

        return df_view, aktualizacja, liczba_wpisow
    except:
        return pd.DataFrame(), "", 0

def stworz_tabele_html(df):
    if df.empty: return "<p style='text-align:center;'>Brak zadań.</p>"
    kol_merytoryczne = [c for c in df.columns if c not in [' ', 'DNI_N']]
    wys_kol = [' '] + kol_merytoryczne[:5]
    html = '<table class="html-table"><thead><tr>'
    for k in wys_kol: html += f"<th>{k if k != ' ' else ''}</th>"
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for k in wys_kol: html += f'<td>{row[k]}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

# --- 4. START ---
# DOPASOWANE DO TWOJEGO ARKUSZA (ZDJĘCIE 10)
df_biezace, czas_synchro, liczba_biezacych = pobierz_dane("1 Zadania bieżące")
df_zrealizowane, _, liczba_zrealizowanych = pobierz_dane("Zadania zrealizowane")
df_slawka, _, _ = pobierz_dane("Terminy Sławka")

# WIDOK
with st.sidebar:
    st.title("System Uzdrowisko")
    st.info(f"Zalogowany: {user_url}")
    if st.button("🔄 ODŚWIEŻ"): st.rerun()

st.markdown(f'<div class="top-bar"><p>AKTUALIZACJA: {czas_synchro}</p></div>', unsafe_allow_html=True)
st.markdown('<h4 style="text-align:center;">Centrum Zarządzania Administracją</h4>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f'<div class="metric-card"><p>📋 BIEŻĄCE (A)</p><h3>{liczba_biezacych}</h3></div>', unsafe_allow_html=True)
with c2: 
    pilne = len(df_biezace[df_biezace['DNI_N'].between(-3, 0)]) if 'DNI_N' in df_biezace.columns else 0
    st.markdown(f'<div class="metric-card"><p>⏳ PILNE</p><h3>{pilne}</h3></div>', unsafe_allow_html=True)
with c3:
    spoz = len(df_biezace[df_biezace['DNI_N'] > 0]) if 'DNI_N' in df_biezace.columns else 0
    st.markdown(f'<div class="metric-card"><p>🔥 PO TERMINIE</p><h3>{spoz}</h3></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-card"><p>✅ ZREALIZOWANE (A)</p><h3>{liczba_zrealizowanych}</h3></div>', unsafe_allow_html=True)

tabs = st.tabs(["📋 BIEŻĄCE", "✅ ZREALIZOWANE", "📅 TERMINY SŁAWKA"])
with tabs[0]: st.markdown(stworz_tabele_html(df_biezace), unsafe_allow_html=True)
with tabs[1]: st.markdown(stworz_tabele_html(df_zrealizowane), unsafe_allow_html=True)
with tabs[2]: st.markdown(stworz_tabele_html(df_slawka), unsafe_allow_html=True)

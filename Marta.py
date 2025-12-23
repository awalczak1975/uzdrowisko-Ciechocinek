import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from streamlit_autorefresh import st_autorefresh
import io

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="System Uzdrowisko - Andrzej", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

# --- 2. WYBÓR PLIKU JSON ---
st.sidebar.header("Ustawienia")
uploaded_file = st.sidebar.file_uploader("Wybierz plik JSON konta serwisowego Google", type="json")

if uploaded_file is None:
    st.error("❌ Brak pliku JSON! Wgraj plik aby kontynuować.")
    st.stop()

# --- 3. PARAMETRY UŻYTKOWNIKA Z LINKU ---
query_params = st.query_params
user_url = query_params.get("user", ["Andrzej"])[0]

# --- 4. FUNKCJE ---
def pobierz_polaczenie(json_file):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        pd.read_json(json_file, typ='dict'),
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def pobierz_dane(client, arkusz, zakladka):
    try:
        sheet = client.open(arkusz).worksheet(zakladka)
        dane = sheet.get_all_values()
        if not dane: return pd.DataFrame(), "", 0
        df_full = pd.DataFrame(dane[1:], columns=dane[0])
        aktualizacja = datetime.now().strftime("%H:%M")
        liczba_wpisow = len(df_full[df_full.iloc[:,0].str.strip() != ""])
        df_view = df_full.iloc[:, :5].copy()
        if 'DNI' in df_view.columns:
            df_view['DNI_N'] = pd.to_numeric(df_view['DNI'], errors='coerce').fillna(0)
        return df_view, aktualizacja, liczba_wpisow
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame(), "", 0

def stworz_tabele_html(df):
    if df.empty: return "<p style='text-align:center; padding:20px;'>Brak zadań do wyświetlenia.</p>"
    html = '<table style="width:100%;border-collapse:collapse;">'
    html += '<tr>' + ''.join([f'<th>{col}</th>' for col in df.columns]) + '</tr>'
    for _, row in df.iterrows():
        html += '<tr>' + ''.join([f'<td>{row[col]}</td>' for col in df.columns]) + '</tr>'
    html += '</table>'
    return html

# --- 5. ŁĄCZENIE Z GOOGLE SHEETS ---
try:
    json_data = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    client = pobierz_polaczenie(json_data)
except Exception as e:
    st.error(f"❌ Błąd autoryzacji: {e}")
    st.stop()

# --- 6. POBIERANIE DANYCH ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"
df_biezace, czas_synchro, liczba_biezacych = pobierz_dane(client, NAZWA_ARKUSZA, "Zadania bieżące")
df_zrealizowane, _, liczba_zrealizowanych = pobierz_dane(client, NAZWA_ARKUSZA, "Zadania zrealizowane")

# --- 7. WIDOK ---
st.markdown(f"**OSTATNIA AKTUALIZACJA:** {czas_synchro}")
st.markdown("### Zadania bieżące")
st.markdown(stworz_tabele_html(df_biezace), unsafe_allow_html=True)
st.markdown("### Zadania zrealizowane")
st.markdown(stworz_tabele_html(df_zrealizowane), unsafe_allow_html=True)


import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import io

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="System Uzdrowisko - Andrzej", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

# --- 2. WYBÓR PLIKU JSON ---
st.sidebar.header("Ustawienia")
uploaded_file = st.sidebar.file_uploader("Wgraj plik JSON konta serwisowego Google", type="json")

if uploaded_file is None:
    st.error("❌ Brak pliku JSON! Wgraj plik, aby kontynuować.")
    st.stop()

# --- 3. PARAMETRY UŻYTKOWNIKA Z LINKU ---
query_params = st.query_params
user_url = query_params.get("user", ["Andrzej"])[0]

# --- 4. FUNKCJE ---
def pobierz_polaczenie(json_file):
    json_dict = pd.read_json(json_file, typ='dict')
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json_dict,
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
            # ustawienie ikonki
            def ustaw_ikonke(row):
                if zakladka == "Zadania zrealizowane": return "✅"
                if row['DNI_N'] > 0: return "🔥"
                if row['DNI_N'] >= -3: return "⏳"
                return "✅"
            df_view[' '] = df_view.apply(ustaw_ikonke, axis=1)
        else:
            df_view[' '] = "✅" if zakladka == "Zadania zrealizowane" else "📋"
        # filtrowanie użytkowników
        if user_url == "Slawek":
            df_view = df_view[df_view['OSOBA'].str.contains("Sławek", case=False, na=False)]
        elif user_url in ["Marta", "Agata", "Rafal"]:
            df_view = df_view[~df_view['OSOBA'].str.contains("Sławek", case=False, na=False)]
        return df_view, aktualizacja, liczba_wpisow
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame(), "", 0

def stworz_tabele_html(df):
    if df.empty: return "<p style='text-align:center; padding:20px;'>Brak zadań do wyświetlenia.</p>"
    kol_merytoryczne = [c for c in df.columns if c not in [' ', 'DNI_N']]
    wys_kol = [' '] + kol_merytoryczne[:5]
    html = '<table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:0.9rem;">'
    html += '<tr>' + ''.join([f'<th>{k if k != " " else ""}</th>' for k in wys_kol]) + '</tr>'
    for _, row in df.iterrows():
        html += '<tr>' + ''.join([f'<td>{row[k]}</td>' for k in wys_kol]) + '</tr>'
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
df_slawka, _, _ = pobierz_dane(client, NAZWA_ARKUSZA, "Terminy Sławka")

# --- 7. WIDOK GŁÓWNY ---
st.markdown(f"**OSTATNIA AKTUALIZACJA:** {czas_synchro}")

# metryki
if not df_biezace.empty:
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("📋 MOJE ZADANIA", liczba_biezacych)
    with col2:
        pilne = len(df_biezace[(df_biezace['DNI_N'] >= -3) & (df_biezace['DNI_N'] <= 0)]) if 'DNI_N' in df_biezace.columns else 0
        st.metric("⏳ PILNE", pilne)
    with col3:
        spoznione = len(df_biezace[df_biezace['DNI_N'] > 0]) if 'DNI_N' in df_biezace.columns else 0
        st.metric("🔥 PO CZASIE", spoznione)
    with col4: st.metric("✅ ZREALIZOWANE", liczba_zrealizowanych)

# zakładki
lista_zakladek = ["📋 MOJE BIEŻĄCE", "✅ MOJE ZREALIZOWANE"]
if user_url in ["Slawek", "Andrzej"]:
    lista_zakladek.append("📅 TERMINY SŁAWKA")

tabs = st.tabs(lista_zakladek)

with tabs[0]: st.markdown(stworz_tabele_html(df_biezace), unsafe_allow_html=True)
with tabs[1]: st.markdown(stworz_tabele_html(df_zrealizowane), unsafe_allow_html=True)
if len(tabs) > 2:
    with tabs[2]: st.markdown(stworz_tabele_html(df_slawka), unsafe_allow_html=True)

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA GŁÓWNA ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

def pobierz_polaczenie():
    """Łączy się z Google Sheets i naprawia błędy formatowania klucza."""
    try:
        if "gcp_service_account" in st.secrets:
            # Pobieramy dane z sekcji Tajniki (Secrets)
            info = dict(st.secrets["gcp_service_account"])
            
            # PANCERNA POPRAWKA: Jeśli klucz został wklejony ze znakami '\n',
            # zamieniamy je na prawdziwe znaki nowej linii.
            if "private_key" in info:
                info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Błąd konfiguracji połączenia: {e}")
    return None

def pobierz_dane_po_indeksie(numer_arkusza):
    """Pobiera dane z arkusza na podstawie jego pozycji (indeksu)."""
    client = pobierz_polaczenie()
    if not client: return pd.DataFrame(), 0, "Błąd"
    try:
        doc = client.open(NAZWA_ARKUSZA)
        arkusze = doc.worksheets()
        if len(arkusze) > numer_arkusza:
            sheet = arkusze[numer_arkusza]
            dane = sheet.get_all_values()
            if len(dane) < 2: return pd.DataFrame(), 0, sheet.title
            df = pd.DataFrame(dane[1:], columns=dane[0])
            # Liczymy rzędy z danymi
            liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
            return df, liczba, sheet.title
        return pd.DataFrame(), 0, "Brak"
    except Exception as e:
        return pd.DataFrame(), 0, f"Błąd wczytywania: {e}"

# --- 2. START ---
df_biezace, liczba_b, nazwa_b = pobierz_dane_po_indeksie(0)
df_zrealizowane, liczba_z, nazwa_z = pobierz_dane_po_indeksie(1)
df_slawka, _, nazwa_s = pobierz_dane_po_indeksie(4)

# --- 3. WYGLĄD ---
st.markdown("<h2 style='text-align:center;'>Centrum Zarządzania Administracją</h2>", unsafe_allow_html=True)
st.write(f"Aktualizacja: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

kol1, kol2 = st.columns(2)
kol1.metric(label=f"📋 {nazwa_b.upper()}", value=liczba_b)
kol2.metric(label=f"✅ {nazwa_z.upper()}", value=liczba_z)

st.divider()

zakladki_ui = st.tabs([f"📋 {nazwa_b}", f"✅ {nazwa_z}", f"📅 {nazwa_s}"])

with zakladki_ui[0]:
    if not df_biezace.empty: st.dataframe(df_biezace, use_container_width=True, hide_index=True)
    else: st.info("Brak aktywnych zadań.")

with zakladki_ui[1]:
    if not df_zrealizowane.empty: st.dataframe(df_zrealizowane, use_container_width=True, hide_index=True)
    else: st.info("Brak zadań.")

with zakladki_ui[2]:
    if not df_slawka.empty: st.dataframe(df_slawka, use_container_width=True, hide_index=True)
    else: st.info("Brak danych.")

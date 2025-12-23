import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA GŁÓWNA ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")
# Automatyczne odświeżanie co 5 minut
st_autorefresh(interval=300000, key="datarefresh")

def pobierz_polaczenie():
    """Łączy się z arkuszem, naprawiając błędy w kluczu prywatnym."""
    try:
        if "gcp_service_account" in st.secrets:
            # Pobieramy dane z Secrets jako zwykły słownik
            info = dict(st.secrets["gcp_service_account"])
            
            # KLUCZOWA POPRAWKA: Jeśli klucz został wklejony jako tekst z '\n',
            # zamieniamy go na prawdziwe znaki nowej linii wymagane przez Google.
            if "private_key" in info:
                info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Błąd konfiguracji klucza: {e}")
    return None

def pobierz_dane_po_indeksie(numer_arkusza):
    """Pobiera dane z arkusza na podstawie jego kolejności (indeksu)."""
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
            # Liczymy rzędy z danymi (niepuste w kolumnie A)
            liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
            return df, liczba, sheet.title
        return pd.DataFrame(), 0, "Brak"
    except Exception as e:
        return pd.DataFrame(), 0, f"Błąd: {e}"

# --- 2. POBIERANIE DANYCH ---
# 0 = pierwsza zakładka od lewej, 1 = druga, 4 = piąta (Terminy Sławka)
df_biezace, liczba_b, nazwa_b = pobierz_dane_po_indeksie(0)
df_zrealizowane, liczba_z, nazwa_z = pobierz_dane_po_indeksie(1)
df_slawka, _, nazwa_s = pobierz_dane_po_indeksie(4)

# --- 3. WYGLĄD APLIKACJI ---
st.markdown("<h3 style='text-align:center;'>Centrum Zarządzania Administracją</h3>", unsafe_allow_html=True)
st.write(f"Aktualizacja: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

# Kafelki z sumami
c1, c2 = st.columns(2)
with c1: st.metric(f"📋 {nazwa_b}", liczba_b)
with c2: st.metric(f"✅ {nazwa_z}", liczba_z)

# Przełącznik zakładek
tabs = st.tabs([f"📋 {nazwa_b}", f"✅ {nazwa_z}", f"📅 {nazwa_s}"])

with tabs[0]:
    if not df_biezace.empty:
        st.dataframe(df_biezace, use_container_width=True, hide_index=True)
    else:
        st.info("Brak aktywnych zadań.")

with tabs[1]:
    if not df_zrealizowane.empty:
        st.dataframe(df_zrealizowane, use_container_width=True, hide_index=True)
    else:
        st.info("Brak zrealizowanych zadań.")

with tabs[2]:
    if not df_slawka.empty:
        st.dataframe(df_slawka, use_container_width=True, hide_index=True)
    else:
        st.info("Brak terminów w kalendarzu Sławka.")

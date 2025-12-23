import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

def pobierz_polaczenie():
    try:
        if "gcp_service_account" in st.secrets:
            # Pobieramy dane z Secrets jako słownik
            info = dict(st.secrets["gcp_service_account"])
            
            # PANCERNA POPRAWKA: Naprawiamy klucz prywatny, jeśli Streamlit źle go odczytuje
            if "private_key" in info:
                info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                info, 
                ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Błąd konfiguracji klucza: {e}")
    return None

def pobierz_dane_po_indeksie(numer_arkusza):
    client = pobierz_polaczenie()
    if not client: return pd.DataFrame(), 0, "Błąd połączenia"
    try:
        doc = client.open(NAZWA_ARKUSZA)
        arkusze = doc.worksheets()
        
        if len(arkusze) > numer_arkusza:
            sheet = arkusze[numer_arkusza]
            dane = sheet.get_all_values()
            
            if len(dane) < 2: return pd.DataFrame(), 0, sheet.title
            
            df = pd.DataFrame(dane[1:], columns=dane[0])
            liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
            return df, liczba, sheet.title
        return pd.DataFrame(), 0, "Brak arkusza"
    except Exception as e:
        return pd.DataFrame(), 0, f"Błąd: {e}"

# --- 2. START (Pobieranie danych) ---
df_biezace, liczba_b, nazwa_b = pobierz_dane_po_indeksie(0)
df_zrealizowane, liczba_z, nazwa_z = pobierz_dane_po_indeksie(1)
df_slawka, _, nazwa_s = pobierz_dane_po_indeksie(4)

# --- 3. WYGLĄD APLIKACJI ---
st.markdown("<h3 style='text-align:center;'>Centrum Zarządzania Administracją</h3>", unsafe_allow_html=True)
st.write(f"Ostatnia aktualizacja danych: {datetime.now().strftime('%H:%M:%S')}")

c1, c2 = st.columns(2)
with c1: st.metric(f"📋 {nazwa_b.upper()}", liczba_b)
with c2: st.metric(f"✅ {nazwa_z.upper()}", liczba_z)

tabs = st.tabs([f"📋 {nazwa_b}", f"✅ {nazwa_z}", f"📅 {nazwa_s}"])
with tabs[0]: st.dataframe(df_biezace, use_container_width=True) if not df_biezace.empty else st.info("Brak danych")
with tabs[1]: st.dataframe(df_zrealizowane, use_container_width=True) if not df_zrealizowane.empty else st.write("Brak danych")
with tabs[2]: st.dataframe(df_slawka, use_container_width=True) if not df_slawka.empty else st.write("Brak danych")

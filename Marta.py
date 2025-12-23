import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA ---
# Nazwa musi być identyczna z Twoim plikiem w Google Sheets
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")
# Automatyczne odświeżanie co 5 minut
st_autorefresh(interval=300000, key="datarefresh")

def pobierz_polaczenie():
    try:
        if "gcp_service_account" in st.secrets:
            # Pobieramy dane z sekcji Secrets
            info = dict(st.secrets["gcp_service_account"])
            
            # POPRAWKA BŁĘDU BASE64: Naprawiamy formatowanie klucza prywatnego
            if "private_key" in info:
                info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                info, 
                ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Błąd konfiguracji połączenia: {e}")
    return None

def pobierz_dane_po_indeksie(numer_arkusza):
    client = pobierz_polaczenie()
    if not client: 
        return pd.DataFrame(), 0, "Błąd połączenia"
    try:
        doc = client.open(NAZWA_ARKUSZA)
        arkusze = doc.worksheets()
        
        # Pobieramy arkusz na podstawie jego kolejności (0 = pierwszy, 1 = drugi itd.)
        if len(arkusze) > numer_arkusza:
            sheet = arkusze[numer_arkusza]
            tytul = sheet.title
            dane = sheet.get_all_values()
            
            if len(dane) < 2: 
                return pd.DataFrame(), 0, tytul
            
            # Tworzymy tabelę (pierwszy rząd to nagłówki)
            df = pd.DataFrame(dane[1:], columns=dane[0])
            
            # Liczymy rzędy, które nie są puste w pierwszej kolumnie
            liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
            return df, liczba, tytul
        
        return pd.DataFrame(), 0, "Nie znaleziono"
    except Exception as e:
        return pd.DataFrame(), 0, f"Błąd: {str(e)}"

# --- 2. POBIERANIE DANYCH (Zgodnie z kolejnością w Twoim arkuszu) ---
# 0 to Zadania bieżące, 1 to Zadania zrealizowane, 4 to Terminy Sławka (piąta zakładka)
df_biezace, liczba_b, nazwa_b = pobierz_dane_po_indeksie(0)
df_zrealizowane, liczba_z, nazwa_z = pobierz_dane_po_indeksie(1)
df_slawka, _, nazwa_s = pobierz_dane_po_indeksie(4)

# --- 3. WYGLĄD I WYŚWIETLANIE ---
st.markdown("<h2 style='text-align:center;'>Centrum Zarządzania Administracją</h2>", unsafe_allow_html=True)
st.write(f"Stan na dzień: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

# Górne liczniki (Kafelki)
c1, c2 = st.columns(2)
with c1:
    st.metric(f"📋 {nazwa_b.upper()}", liczba_b)
with c2:
    st.metric(f"✅ {nazwa_z.upper()}", liczba_z)

# Przełącznik zakładek w aplikacji
tabs = st.tabs([f"📋 {nazwa_b}", f"✅ {nazwa_z}", f"📅 {nazwa_s}"])

with tabs[0]:
    if not df_biezace.empty:
        st.dataframe(df_biezace, use_container_width=True)
    else:
        st.info("Pierwsza zakładka jest pusta lub nie została wczytana.")

with tabs[1]:
    if not df_zrealizowane.empty:
        st.dataframe(df_zrealizowane, use_container_width=True)
    else:
        st.info("Druga zakładka jest pusta lub nie została wczytana.")

with tabs[2]:
    if not df_slawka.empty:
        st.dataframe(df_slawka, use_container_width=True)
    else:
        st.info("Zakładka Terminy Sławka (piąta od lewej) jest pusta.")

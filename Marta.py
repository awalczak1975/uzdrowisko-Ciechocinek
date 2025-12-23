import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. KONFIGURACJA GŁÓWNA ---
# Nazwa arkusza w Google Sheets - musi być identyczna
NAZWA_ARKUSZA = "Marta-Dział Techniczny"

st.set_page_config(page_title="System Uzdrowisko", layout="wide")
# Automatyczne odświeżanie aplikacji co 5 minut (300000 ms)
st_autorefresh(interval=300000, key="datarefresh")

# --- 2. FUNKCJE POŁĄCZENIA ---
def pobierz_polaczenie():
    """Łączy się z Google Sheets, naprawiając ewentualne błędy w kluczu."""
    try:
        if "gcp_service_account" in st.secrets:
            # Pobranie danych z sekcji Tajniki (Secrets)
            info = dict(st.secrets["gcp_service_account"])
            
            # PANCERNA POPRAWKA: Naprawiamy formatowanie klucza prywatnego, 
            # zamieniając tekstowe \n na prawdziwe znaki nowej linii.
            if "private_key" in info:
                info["private_key"] = info["private_key"].replace("\\n", "\n")
            
            # Autoryzacja w Google
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Błąd konfiguracji połączenia: {e}")
    return None

def pobierz_dane_po_indeksie(numer_arkusza):
    """Pobiera dane z arkusza na podstawie jego pozycji (indeksu)."""
    client = pobierz_polaczenie()
    if not client: 
        return pd.DataFrame(), 0, "Błąd połączenia"
    try:
        doc = client.open(NAZWA_ARKUSZA)
        arkusze = doc.worksheets()
        
        # Sprawdzamy, czy żądany arkusz istnieje
        if len(arkusze) > numer_arkusza:
            sheet = arkusze[numer_arkusza]
            tytul_zakladki = sheet.title
            dane_surowe = sheet.get_all_values()
            
            # Jeśli arkusz jest pusty lub ma tylko nagłówki
            if len(dane_surowe) < 2: 
                return pd.DataFrame(), 0, tytul_zakladki
            
            # Konwersja na tabelę (pierwszy wiersz to nagłówki)
            df = pd.DataFrame(dane_surowe[1:], columns=dane_surowe[0])
            
            # Liczymy rzędy z danymi (niepuste w pierwszej kolumnie)
            liczba_zadan = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
            return df, liczba_zadan, tytul_zakladki
        
        return pd.DataFrame(), 0, "Nie znaleziono arkusza"
    except Exception as e:
        return pd.DataFrame(), 0, f"Błąd wczytywania: {str(e)}"

# --- 3. POBIERANIE DANYCH ---
# 0 = pierwsza zakładka od lewej
df_biezace, liczba_b, nazwa_b = pobierz_dane_po_indeksie(0)
# 1 = druga zakładka od lewej
df_zrealizowane, liczba_z, nazwa_z = pobierz_dane_po_indeksie(1)
# 4 = piąta zakładka od lewej (Terminy Sławka)
df_slawka, _, nazwa_s = pobierz_dane_po_indeksie(4)

# --- 4. WYGLĄD APLIKACJI (INTERFEJS) ---
st.markdown("<h2 style='text-align:center; color: #1E3A8A;'>Centrum Zarządzania Administracją</h2>", unsafe_allow_html=True)
st.write(f"Aktualizacja danych: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

# Wyświetlanie kafelków z sumami
kol1, kol2 = st.columns(2)
with kol1:
    st.metric(label=f"📋 {nazwa_b.upper()}", value=liczba_b)
with kol2:
    st.metric(label=f"✅ {nazwa_z.upper()}", value=liczba_z)

st.divider()

# Tworzenie zakładek w aplikacji Streamlit
zakladki_ui = st.tabs([f"📋 {nazwa_b}", f"✅ {nazwa_z}", f"📅 {nazwa_s}"])

# Wyświetlanie tabel w odpowiednich zakładkach
with zakladki_ui[0]:
    if not df_biezace.empty:
        st.dataframe(df_biezace, use_container_width=True, hide_index=True)
    else:
        st.info("Brak aktywnych zadań w arkuszu.")

with zakladki_ui[1]:
    if not df_zrealizowane.empty:
        st.dataframe(df_zrealizowane, use_container_width=True, hide_index=True)
    else:
        st.info("Lista zrealizowanych zadań jest pusta.")

with zakladki_ui[2]:
    if not df_slawka.empty:
        st.dataframe(df_slawka, use_container_width=True, hide_index=True)
    else:
        st.info("Brak danych w terminach Sławka.")

import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from google.oauth2.service_account import Credentials

# ==========================================================
# 1. KONFIGURACJA GŁÓWNA
# ==========================================================

SPREADSHEET_ID = "1RQXQZf1uO7o0flu7EuXJu9IA7NKq37ZY0KiXer8gXOs"

st.set_page_config(
    page_title="System Uzdrowisko",
    layout="wide"
)

# Automatyczne odświeżanie co 5 minut
st_autorefresh(interval=300000, key="datarefresh")

# ==========================================================
# 2. POŁĄCZENIE Z GOOGLE SHEETS
# ==========================================================

def pobierz_polaczenie():
    try:
        info = dict(st.secrets["gcp_service_account"])

        creds = Credentials.from_service_account_info(
            info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        return gspread.authorize(creds)

    except Exception as e:
        st.error(f"❌ Błąd autoryzacji Google: {e}")
        return None

# ==========================================================
# 3. POBIERANIE DANYCH Z ARKUSZA
# ==========================================================

def pobierz_dane_po_indeksie(numer_arkusza):
    client = pobierz_polaczenie()
    if not client:
        return pd.DataFrame(), 0, "BŁĄD POŁĄCZENIA"

    try:
        doc = client.open_by_key(SPREADSHEET_ID)
        arkusze = doc.worksheets()

        if numer_arkusza >= len(arkusze):
            return pd.DataFrame(), 0, "BRAK ZAKŁADKI"

        sheet = arkusze[numer_arkusza]
        tytul = sheet.title
        dane = sheet.get_all_values()

        if len(dane) < 2:
            return pd.DataFrame(), 0, tytul

        df = pd.DataFrame(dane[1:], columns=dane[0])

        liczba_zadan = (
            df.iloc[:, 0]
            .astype(str)
            .str.strip()
            .ne("")
            .sum()
        )

        return df, liczba_zadan, tytul

    except Exception as e:
        return pd.DataFrame(), 0, f"BŁĄD: {e}"

# ==========================================================
# 4. POBRANIE DANYCH
# ==========================================================

# 0 = Zadania bieżące
# 1 = Zadania zrealizowane
# 4 = Terminy Sławka

df_biezace, liczba_b, nazwa_b = pobierz_dane_po_indeksie(0)
df_zrealizowane, liczba_z, nazwa_z = pobierz_dane_po_indeksie(1)
df_slawka, _, nazwa_s = pobierz_dane_po_indeksie(4)

# ==========================================================
# 5. INTERFEJS UŻYTKOWNIKA
# ==========================================================

st.markdown(
    "<h2 style='text-align:center;'>Centrum Zarządzania Administracją</h2>",
    unsafe_allow_html=True
)

st.write(
    f"Aktualizacja danych: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
)

# ---- Kafelki ----
kol1, kol2 = st.columns(2)
kol1.metric(label=f"📋 {nazwa_b.upper()}", value=liczba_b)
kol2.metric(label=f"✅ {nazwa_z.upper()}", value=liczba_z)

st.divider()

# ---- Zakładki ----
zakladki = st.tabs([
    f"📋 {nazwa_b}",
    f"✅ {nazwa_z}",
    f"📅 {nazwa_s}"
])

with zakladki[0]:
    if not df_biezace.empty:
        st.dataframe(df_biezace, use_container_width=True, hide_index=True)
    else:
        st.info("Brak aktywnych zadań.")

with zakladki[1]:
    if not df_zrealizowane.empty:
        st.dataframe(df_zrealizowane, use_container_width=True, hide_index=True)
    else:
        st.info("Brak zrealizowanych zadań.")

with zakladki[2]:
    if not df_slawka.empty:
        st.dataframe(df_slawka, use_container_width=True, hide_index=True)
    else:
        st.info("Brak danych w tej zakładce.")

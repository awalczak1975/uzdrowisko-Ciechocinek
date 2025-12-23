import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- KONFIGURACJA ---
NAZWA_ARKUSZA = "Marta-Dział Techniczny"
st.set_page_config(page_title="System Uzdrowisko", layout="wide")
st_autorefresh(interval=300000, key="datarefresh")

def pobierz_polaczenie():
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            # Ta linia naprawia błędy formatowania klucza
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Błąd klucza: {e}")
    return None

def pobierz_dane(nr_arkusza):
    client = pobierz_polaczenie()
    if not client: return pd.DataFrame(), 0, "Błąd"
    try:
        doc = client.open(NAZWA_ARKUSZA)
        sheet = doc.worksheets()[nr_arkusza]
        dane = sheet.get_all_values()
        if len(dane) < 2: return pd.DataFrame(), 0, sheet.title
        df = pd.DataFrame(dane[1:], columns=dane[0])
        liczba = len([x for x in df.iloc[:, 0] if str(x).strip() != ""])
        return df, liczba, sheet.title
    except Exception as e:
        return pd.DataFrame(), 0, f"Błąd: {e}"

# --- POBIERANIE ---
df1, l1, n1 = pobierz_dane(0)
df2, l2, n2 = pobierz_dane(1)
df3, l3, n3 = pobierz_dane(4)

# --- INTERFEJS ---
st.markdown("<h3 style='text-align:center;'>Centrum Zarządzania Administracją</h3>", unsafe_allow_html=True)
st.write(f"Ostatnia aktualizacja: {datetime.now().strftime('%H:%M:%S')}")

c1, c2 = st.columns(2)
with c1: st.metric(f"📋 {n1}", l1)
with c2: st.metric(f"✅ {n2}", l2)

tabs = st.tabs([n1, n2, n3])
with tabs[0]:
    if not df1.empty: st.dataframe(df1, use_container_width=True, hide_index=True)
with tabs[1]:
    if not df2.empty: st.dataframe(df2, use_container_width=True, hide_index=True)
with tabs[2]:
    if not df3.empty: st.dataframe(df3, use_container_width=True, hide_index=True)

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA
# ==========================================================
st.set_page_config(
    page_title="System Uzdrowisko",
    layout="wide",
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=30000, key="refresh")

# ==========================================================
# 2. CSS – POKOLOROWANY 1 WIERSZ ARKUSZA (NAGŁÓWEK)
# ==========================================================
st.markdown("""
<style>

/* =====================================================
   1. WIERSZ ARKUSZA = NAGŁÓWEK st.data_editor
   (BaseWeb – JEDYNE SKUTECZNE SELECTORY)
   ===================================================== */

/* tło całego nagłówka */
div[data-testid="stDataFrame"] [role="columnheader"] {
    background-color: #1e293b !important;      /* granat */
    border-bottom: 4px solid #eab308 !important;
}

/* tekst nagłówka */
div[data-testid="stDataFrame"] [role="columnheader"] span,
div[data-testid="stDataFrame"] [role="columnheader"] button {
    color: #facc15 !important;                  /* złoty */
    font-weight: 900 !important;
    text-transform: uppercase;
    font-size: 0.8rem !important;
}

/* separator kolumn */
div[data-testid="stDataFrame"] [role="columnheader"]:not(:last-child) {
    border-right: 1px solid #334155 !important;
}

/* =====================================================
   WIERSZE DANYCH – delikatny hover
   ===================================================== */
div[data-testid="stDataFrame"] tbody tr:hover {
    background-color: #e0f2fe !important;
    transition: background-color 0.15s ease-in-out;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# 3. LOGOWANIE (JAK U CIEBIE)
# ==========================================================
USERS = {
    "Andrzej": "8800",
    "Marta": "1111",
    "Sławek": "2222",
    "Agata": "3333",
    "Rafał": "4444",
    "Dagmara": "5555",
    "Ewelina": "6666",
    "Ireneusz": "7777"
}

u_p = st.query_params.get("u", "")
k_p = st.query_params.get("k", "")

if u_p in USERS and USERS[u_p] == k_p:
    zalogowany = u_p
else:
    st.error("BŁĄD LOGOWANIA")
    st.stop()

# ==========================================================
# 4. POŁĄCZENIE Z GOOGLE SHEETS
# ==========================================================
def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds)

@st.cache_data(ttl=10)
def pobierz_arkusz(nazwa):
    sh = polacz().open("Marta-Dział Techniczny")
    ws = sh.worksheet(nazwa)
    dane = ws.get_all_values()
    if len(dane) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(dane[1:], columns=dane[0])
    df = df[df.iloc[:, 0].astype(str).str.strip() != ""]
    return df

# ==========================================================
# 5. WIDOK GŁÓWNY
# ==========================================================
df = pobierz_arkusz("Zadania bieżące")
now = datetime.now(pytz.timezone("Europe/Warsaw"))

c1, c2, c3, c4 = st.columns(4)
c1.metric("RAZEM", len(df))
c2.metric("PILNE 🔥", len(df))
c3.metric("ZREALIZOWANE", 0)
c4.metric("AKTUALIZACJA", now.strftime("%H:%M"))

st.markdown("---")

st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    height=700
)

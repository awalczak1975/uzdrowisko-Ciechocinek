import streamlit as st
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
# 2. CSS – KOLOR 1. WIERSZA ARKUSZA (NAGŁÓWKA)
# ==========================================================
st.markdown("""
<style>

/* ===== CAŁY KOMPONENT TABELI ===== */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* =================================================
   1. WIERSZ ARKUSZA = NAGŁÓWEK KOLUMN
   ================================================= */

/* tło nagłówka */
div[data-testid="stDataFrame"] thead tr th {
    background-color: #1e293b !important;   /* granat */
    color: #facc15 !important;              /* złoty tekst */
    font-weight: 900 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    border-bottom: 4px solid #f59e0b !important;
    padding: 10px 8px !important;
}

/* wyrównanie i ikony sortowania */
div[data-testid="stDataFrame"] thead tr th span {
    color: #facc15 !important;
}

/* =================================================
   RESZTA WIERSZY (DANE)
   ================================================= */
div[data-testid="stDataFrame"] tbody tr td {
    font-size: 0.85rem;
}

/* hover dla czytelności */
div[data-testid="stDataFrame"] tbody tr:hover {
    background-color: #e0f2fe !important;
    transition: background-color 0.15s ease-in-out;
}

/* =================================================
   SCROLLBAR (PREMIUM)
   ================================================= */
div[data-testid="stDataFrame"] ::-webkit-scrollbar {
    height: 10px;
    width: 10px;
}
div[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {
    background: #facc15;
    border-radius: 10px;
}
div[data-testid="stDataFrame"] ::-webkit-scrollbar-track {
    background: #020617;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# 3. PRZYKŁADOWE DANE (JAK Z ARKUSZA)
# ==========================================================
data = {
    "Treść zadania": [
        "🔥 Nadzór inwestorski – Dom Zdrojowy",
        "⏳ Termomodernizacja Grażyna",
        "🟢 Projekt windy – Markiewicza"
    ],
    "Uwagi": [
        "Czekamy na podpisanie umowy",
        "Spotkanie z konserwatorem",
        "Wstępna koncepcja OK"
    ],
    "Deadline": [
        "2025-12-31",
        "2025-12-29",
        "2026-01-15"
    ],
    "Dni": [
        "7",
        "5",
        "-21"
    ],
    "Osoba": [
        "Rafał",
        "Agata",
        "Andrzej"
    ]
}

df = pd.DataFrame(data)

# ==========================================================
# 4. WIDOK
# ==========================================================
now = datetime.now(pytz.timezone("Europe/Warsaw"))

m1, m2, m3, m4 = st.columns(4)
m1.metric("RAZEM", len(df))
m2.metric("PILNE 🔥", 1)
m3.metric("ZREALIZOWANE", 0)
m4.metric("AKTUALIZACJA", now.strftime("%H:%M"))

st.markdown("---")

st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    height=500
)

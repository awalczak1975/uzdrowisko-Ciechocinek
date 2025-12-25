import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (PEŁNY KALENDARZ)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="globalrefresh")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    
    /* LEWY PANEL BOCZNY */
    [data-testid="stSidebar"] { 
        background-color: #1e293b !important; 
        border-right: 5px solid #eab308 !important; 
    }
    
    /* WYMUSZENIE WIDOCZNOŚCI PEŁNEGO KALENDARZA MIESIĘCZNEGO */
    div[data-testid="stSidebar"] div[data-baseweb="calendar"] {
        width: 100% !important;
        background-color: white !important;
        border-radius: 10px !important;
        padding: 5px !important;
        display: block !important;
    }
    
    /* STYLIZACJA KAFELKÓW PODSUMOWANIA */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; border-top: 4px solid #eab308 !important; 
        border-radius: 10px !important; text-align: center !important; 
    }
    [data-testid="stMetricValue"] > div { color: #eab308 !important; font-weight: 900; font-size: 2.8rem !important; justify-content: center !important; display: flex !important;}
    [data-testid="stMetricLabel"] > div { color: white !important; font-weight: 600; justify-content: center !important; display: flex !important;}

    /* ZAKŁADKI */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important; font-weight: 700 !important;
        color: #475569 !important; background-color: #f1f5f9 !important;
        border-radius: 8px 8px 0 0 !important; margin-right: 5px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important; background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 2. FUNKCJE TECHNICZNE
# ==========================================================
def polacz():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], 
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def pobierz_df(zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        dane = ws.get_all_values()
        if not dane: return pd.DataFrame()
        df = pd.DataFrame(dane[1:], columns=dane[0]).iloc[:, :5]
        return df[df.iloc[:, 0].str.strip() != ""]
    except: return pd.DataFrame()

def zapisz_df(df, zakladka):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet(zakladka)
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())
        return True
    except: return False

# ==========================================================
# 3. WERYFIKACJA UŻYTKOWNIKA (Andrzej Walczak)
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
uzytkownicy = {"Andrzej": "8800", "Marta": "1234", "Rafał": "5566", "Sławek": "4422"}

if u in uzytkownicy and uzytkownicy[u] == k:
    zalogowany = u
    czy_admin = u in ["Andrzej", "Marta"]
else:
    st.error("❌ BŁĄD DOSTĘPU"); st.stop()

# ==========================================================
# 4. LEWY PANEL (SIDEBAR) - PEŁNY KALENDARZ MIESIĘCZNY
# ==========================================================
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center; color:white;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h3>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("📅 **HARMONOGRAM MIESIĘCZNY**")
    # Wyświetla kalendarz - w sidebarze Streamlit domyślnie stara się go rozwinąć
    wybrana_data = st.date_input("Wybierz datę:", datetime.now(), label_visibility="collapsed")
    
    # Pobranie danych do analizy terminów
    df_biezace = pobierz_df("Zadania bieżące")
    df_slawek = pobierz_df("Terminy Sławka") if zalogowany == "Andrzej" else pd.DataFrame()
    df_all = pd.concat([df_biezace, df_slawek])

    if not df_all.empty:
        df_all['DT'] = pd.to_datetime(df_all['DEADLINE'], dayfirst=True, errors='coerce')
        terminy_dzis = df_all[df_all['DT'].dt.date == wybrana_data]
        
        if not terminy_dzis.empty:
            st.markdown("---")
            st.markdown(f"🔔 **Terminy na {wybrana_data.strftime('%d.%m')}:**")
            for _, r in terminy_dzis.iterrows():
                # Logika: -2 dni to zadanie pilne/termin realizacji
                dni_val = pd.to_numeric(r.get('DNI', 0), errors='coerce', default=0)
                alert = "🚨" if dni_val >= -2 else "📅"
                st.markdown(f"""<div style='background-color:#334155; padding:8px; border-radius:5px; margin-bottom:5px; border-left:3px solid #eab308;'>
                    <small style='color:white;'>{alert} {r['TREŚĆ ZADANIA']}</small></div>""", unsafe_allow_html=True)
        else:
            st.caption("Brak zaplanowanych zadań na ten dzień.")

    st.divider()
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): 
        st.cache_data.clear(); st.rerun()

# ==========================================================
# 5. WIDOK GŁÓWNY (TABELE ZADANIA)
# ==========================================================
kat_list = ["Zadania bieżące", "Zadania zrealizowane"]
if zalogowany == "Andrzej": kat_list.append("Terminy Sławka")
kat_list.append("🔴 CZAT")

tabs = st.tabs(kat_list)

for i, kat in enumerate(kat_list[:-1]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            # Obliczenia DNI_N dla metryk
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            
            # KAFELKI PODSUMOWANIA
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Razem", len(df))
            m2.metric("🔥 Pilne/Spóźnione", len(df[df['DNI_N'] >= -2])) # Logika użytkownika
            m3.metric("🕒 Czas lokalny", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))
            
            # Ikona alarmu w tabeli
            df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))
            
            edytowane = st.data_editor(
                df, use_container_width=True, hide_index=True, height=700,
                disabled=not czy_admin, key=f"ed_{kat}",
                column_config={"DNI_N": None, "S": st.column_config.TextColumn(" ", width="small")}
            )
            
            if czy_admin:
                if st.button(f"💾 ZAPISZ ARKUSZ: {kat.upper()}", key=f"btn_{kat}"):
                    if zapisz_df(edytowane.drop(columns=["S", "DNI_N"]), kat):
                        st.success("Zmiany zapisane w Google Sheets!"); st.cache_data.clear(); st.rerun()

# CZAT (Skrót)
with tabs[-1]:
    st.subheader("🔴 Komunikacja Uzdrowisko Ciechocinek")
    st.write("Wiadomości pracowników...")

# ==========================================================
# 6. DOLNA BELKA WWW
# ==========================================================
st.markdown("""
    <div style="display: flex; justify-content: center; background-color: white; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-top: 40px;">
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/oferta/">Oferta</a>
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/kontakt/">Kontakt</a>
    </div>
    """, unsafe_allow_html=True)

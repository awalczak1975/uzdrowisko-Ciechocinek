import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (WYMUSZENIE BIAŁEGO TŁA)
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="globalrefresh")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
    
    /* LEWY PANEL BOCZNY */
    [data-testid="stSidebar"] { 
        background-color: #1e293b !important; 
        border-right: 5px solid #eab308 !important; 
    }
    
    /* KAFELKI PODSUMOWANIA */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; border-top: 4px solid #eab308 !important; 
        border-radius: 10px !important; text-align: center !important; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricValue"] > div { display: flex !important; justify-content: center !important; color: #eab308 !important; font-weight: 900 !important; font-size: 2.5rem !important; }
    [data-testid="stMetricLabel"] > div { display: flex !important; justify-content: center !important; color: white !important; font-weight: 600 !important; }

    /* ZAKŁADKI */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important; font-weight: 700 !important;
        color: #475569 !important; background-color: #f1f5f9 !important;
        border-radius: 8px 8px 0 0 !important; margin: 0 5px 0 0 !important;
        padding: 10px 20px !important; border: 1px solid #e2e8f0 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important; background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }
    
    /* OBNIŻENIE INFO O UŻYTKOWNIKU */
    .sidebar-user { text-align: center; color: #94a3b8; font-size: 0.85rem; margin-top: 50px; }
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
        df = pd.DataFrame(dane[1:], columns=dane[0])
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
# 3. GENERATOR KALENDARZA (ZASZYTE STYLE WEWNĄTRZ HTML)
# ==========================================================
def generuj_kalendarz_html(df_zadania):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    rok, miesiac = now.year, now.month
    cal = calendar.monthcalendar(rok, miesiac)
    
    pilne_daty = []
    if not df_zadania.empty:
        df_zadania['DT'] = pd.to_datetime(df_zadania['DEADLINE'], dayfirst=True, errors='coerce')
        df_zadania['DNI_N'] = pd.to_numeric(df_zadania['DNI'], errors='coerce').fillna(-999)
        mask = (df_zadania['DT'].dt.month == miesiac) & (df_zadania['DT'].dt.year == rok) & (df_zadania['DNI_N'] >= -2)
        pilne_daty = df_zadania[mask]['DT'].dt.day.unique().tolist()

    # WYMUSZENIE STYLÓW W KAŻDYM ELEMENTER
    html = f"""
    <div style="background-color: white; padding: 15px; border-radius: 12px; border: 2px solid #eab308; font-family: Arial, sans-serif;">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr><th colspan="7" style="color: #1e293b; text-align: center; font-weight: 800; padding-bottom: 10px; font-size: 16px; border-bottom: 1px solid #eee;">{calendar.month_name[miesiac].upper()} {rok}</th></tr>
                <tr style="color: #64748b; font-size: 11px; text-align: center; font-weight: bold;">
                    <th style="padding: 5px 0;">PN</th><th style="padding: 5px 0;">WT</th><th style="padding: 5px 0;">ŚR</th><th style="padding: 5px 0;">CZ</th><th style="padding: 5px 0;">PT</th><th style="padding: 5px 0;">SO</th><th style="padding: 5px 0;">ND</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for week in cal:
        html += "<tr>"
        for i, day in enumerate(week):
            if day == 0:
                html += "<td></td>"
            else:
                # Kolorowanie
                bg = "transparent"
                color = "#1e293b"
                weight = "600"
                border = "none"
                
                if day == now.day:
                    bg = "#eab308"
                    weight = "900"
                
                # Czerwone kółko dla terminów
                if day in pilne_daty:
                    color = "#ef4444"
                    weight = "900"
                    border = "1px solid #ef4444"

                html += f'<td style="text-align: center; padding: 8px 2px; font-size: 13px; color: {color}; font-weight: {weight}; background-color: {bg}; border-radius: 4px; border: {border};">{day}</td>'
        html += "</tr>"
    
    html += "</tbody></table></div>"
    return html

# ==========================================================
# 4. LOGIKA SYSTEMU
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800":
    zalogowany = u
else:
    st.error("❌ BŁĄD DOSTĘPU"); st.stop()

# Dane
df_biezace = pobierz_df("Zadania bieżące")
df_slawek = pobierz_df("Terminy Sławka")
df_total = pd.concat([df_biezace, df_slawek])

with st.sidebar:
    st.markdown(f"<h3 style='text-align:center; color:white; margin-bottom:0;'>UZDROWISKO</h3><h5 style='text-align:center; color:#eab308; margin-top:0;'>CIECHOCINEK</h5>", unsafe_allow_html=True)
    st.divider()
    
    # WIDOCZNY KALENDARZ
    st.components.v1.html(generuj_kalendarz_html(df_total), height=280)
    st.markdown("<p style='color:#ef4444; font-size:0.7rem; font-weight:bold; text-align:center;'>🔴 KOLOR CZERWONY - TERMINY</p>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): 
        st.cache_data.clear()
        st.rerun()
    
    st.markdown(f'<div class="sidebar-user">Zalogowany: <b>{zalogowany}</b></div>', unsafe_allow_html=True)

# ==========================================================
# 5. WIDOK GŁÓWNY
# ==========================================================
kat_list = ["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "🔴 CZAT"]
tabs = st.tabs(kat_list)

for i, kat in enumerate(kat_list[:-1]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Razem", len(df))
            m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
            m3.metric("🕒 Godzina", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))
            
            df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))
            
            edytowane = st.data_editor(
                df, use_container_width=True, hide_index=True, height=750, key=f"ed_{kat}",
                column_config={"DNI_N": None, "S": st.column_config.TextColumn(" ", width="small")}
            )
            
            if st.button(f"💾 ZAPISZ ZMIANY: {kat}", key=f"btn_{kat}"):
                if zapisz_df(edytowane.drop(columns=["S", "DNI_N"]), kat):
                    st.success("Zapisano!"); st.cache_data.clear(); st.rerun()

# CZAT (skrócony)
with tabs[-1]:
    st.subheader("🔴 Komunikacja")
    st.write("Wpisz wiadomość w arkuszu Czat.")

# BELKA DOLNA
st.markdown("""
    <div style="display: flex; justify-content: center; background-color: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; margin-top: 40px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        <a style="margin: 0 15px; text-decoration: none; color: #1e293b; font-weight: 700;" href="https://uzdrowiskociechocinek.pl/oferta/">OFERTA</a>
        <a style="margin: 0 15px; text-decoration: none; color: #1e293b; font-weight: 700;" href="https://uzdrowiskociechocinek.pl/sanatoria/">SANATORIA</a>
        <a style="margin: 0 15px; text-decoration: none; color: #1e293b; font-weight: 700;" href="https://uzdrowiskociechocinek.pl/kontakt/">KONTAKT</a>
    </div>
    """, unsafe_allow_html=True)

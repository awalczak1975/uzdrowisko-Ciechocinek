import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA
# ==========================================================
st.set_page_config(page_title="System Uzdrowisko", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="globalrefresh")

# Poprawiony link do logo na GitHub (Raw)
LOGO_URL = "https://raw.githubusercontent.com/awalczak1975/uzdrowisko-Ciechocinek/main/logo_uzdrowisko_ciechocinek%20%281%29.png"
# Link powrotny (URL Twojej aplikacji)
APP_URL = "https://uzdrowisko-ciechocinek-nex3rfaat9fpxlpug35urd.streamlit.app/?u=Andrzej&k=8800"

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 5px solid #eab308 !important; }
    
    /* STYLIZACJA LOGO - BEZPOŚREDNI LINK HTML */
    .logo-container {
        text-align: center;
        margin-top: -30px !important;
        margin-bottom: 20px !important;
        cursor: pointer;
    }
    .logo-container img {
        width: 200px;
        transition: 0.3s;
    }
    .logo-container img:hover {
        transform: scale(1.02);
    }

    /* PRZYCISKI W PANELU */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-weight: 600 !important;
        height: 46px !important; margin-bottom: 5px !important;
    }

    /* ZAKŁADKI (TABS) */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important; font-weight: 700 !important;
        color: #1e293b !important; background-color: #e2e8f0 !important;
        border-radius: 8px 8px 0 0 !important; margin-right: 5px !important;
        padding: 10px 25px !important; border: 1px solid #cbd5e1 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important; background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }

    /* STOPKA */
    .sidebar-footer { position: fixed; bottom: 10px; width: 240px; text-align: center; color: #94a3b8; font-size: 0.75rem; }
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

def generuj_kalendarz_html(df_zadania):
    now = datetime.now(pytz.timezone('Europe/Warsaw'))
    rok, miesiac = now.year, now.month
    cal = calendar.monthcalendar(rok, miesiac)
    pilne_daty = []
    if not df_zadania.empty:
        df_zadania['DT'] = pd.to_datetime(df_zadania['DEADLINE'], dayfirst=True, errors='coerce')
        df_zadania['DNI_N'] = pd.to_numeric(df_zadania['DNI'], errors='coerce').fillna(-999)
        pilne_daty = df_zadania[(df_zadania['DT'].dt.month == miesiac) & (df_zadania['DNI_N'] >= -2)]['DT'].dt.day.unique().tolist()

    html = f'<div style="background:white; padding:10px; border-radius:10px; border:2px solid #eab308; font-family:sans-serif;"><table style="width:100%; border-collapse:collapse; line-height:1.1;"><thead><tr><th colspan="7" style="color:#1e293b; text-align:center; font-weight:800; font-size:13px; border-bottom:1px solid #eee;">{calendar.month_name[miesiac].upper()} {rok}</th></tr><tr style="color:#64748b; font-size:9px; text-align:center; font-weight:bold;"><th style="padding:2px 0;">PN</th><th style="padding:2px 0;">WT</th><th style="padding:2px 0;">ŚR</th><th style="padding:2px 0;">CZ</th><th style="padding:2px 0;">PT</th><th style="padding:2px 0;">SO</th><th style="padding:2px 0;">ND</th></tr></thead><tbody style="color:#1e293b;">'
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                bg = "#eab308" if day == now.day else "transparent"
                color = "#ef4444" if day in pilne_daty else "#1e293b"
                border = "1px solid #ef4444" if day in pilne_daty else "none"
                html += f'<td style="text-align:center; padding:4px 1px; font-size:11px; font-weight:700; color:{color}; background-color:{bg}; border-radius:4px; border:{border};">{day}</td>'
        html += "</tr>"
    return html + "</tbody></table></div>"

# ==========================================================
# 3. LOGIKA SIDEBARU
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
if u == "Andrzej" and k == "8800": zalogowany = u
else: st.error("BŁĄD LOGOWANIA"); st.stop()

df_biezace = pobierz_df("Zadania bieżące")
df_slawek = pobierz_df("Terminy Sławka")
df_total = pd.concat([df_biezace, df_slawek])

with st.sidebar:
    # --- NAPRAWIONE LOGO JAKO LINK ---
    st.markdown(f"""
        <div class="logo-container">
            <a href="{APP_URL}" target="_self">
                <img src="{LOGO_URL}">
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="border-bottom:1px solid #334155; margin:5px 0 10px 0;"></div>', unsafe_allow_html=True)
    
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True): st.info("Dodaj zadanie w Arkuszu.")
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): st.cache_data.clear(); st.rerun()
    
    st.components.v1.html(generuj_kalendarz_html(df_total), height=195)
    
    st.markdown("<p style='color:white; font-weight:bold; margin-bottom:5px; font-size:0.9rem;'>📅 Nadchodzące terminy:</p>", unsafe_allow_html=True)
    df_total['DNI_N'] = pd.to_numeric(df_total['DNI'], errors='coerce').fillna(-999)
    nadchodzace = df_total[df_total['DNI_N'] >= -2].sort_values(by='DEADLINE').head(3)
    for _, r in nadchodzace.iterrows():
        st.markdown(f"<div style='background-color:#334155; padding:8px; border-radius:8px; border-left:4px solid #ef4444; margin-bottom:6px;'><p style='color:white; font-size:0.8rem; margin:0;'><b>{r['DEADLINE']}</b>: {r['TREŚĆ ZADANIA']}</p></div>", unsafe_allow_html=True)

    st.markdown(f'<div class="sidebar-footer">Zalogowany: <b>{zalogowany}</b></div>', unsafe_allow_html=True)

# ==========================================================
# 4. WIDOK GŁÓWNY
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
            
            edytowane = st.data_editor(df, use_container_width=True, hide_index=True, height=750, key=f"ed_{kat}")
            
            if st.button(f"💾 ZAPISZ ZMIANY: {kat.upper()}", key=f"btn_{kat}"):
                if zapisz_df(edytowane.drop(columns=["S", "DNI_N"]), kat):
                    st.success("Zapisano!"); st.cache_data.clear(); st.rerun()

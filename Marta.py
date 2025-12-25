import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import calendar
from streamlit_autorefresh import st_autorefresh
import pytz

# ==========================================================
# 1. KONFIGURACJA I STYLIZACJA (CZYTELNOŚĆ I KOLORY)
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
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* PRZYCISKI W PANELU */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #334155 !important; color: white !important;
        border: 1px solid #94a3b8 !important; font-weight: 600 !important;
        height: 45px !important; margin-bottom: 10px !important;
    }

    /* STYLIZACJA KALENDARZA - BIAŁA KARTA DLA KONTRASTU */
    .cal-container {
        background-color: white;
        padding: 12px;
        border-radius: 12px;
        border: 2px solid #eab308;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }
    .cal-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
    .cal-header { color: #1e293b; text-align: center; font-weight: 800; padding-bottom: 8px; font-size: 0.9rem; text-transform: uppercase; }
    .cal-day-name { color: #64748b; font-size: 0.65rem; text-align: center; font-weight: bold; padding-bottom: 5px; }
    .cal-day { text-align: center; padding: 6px 2px; font-size: 0.8rem; color: #1e293b; font-weight: 600; }
    .cal-today { background-color: #eab308 !important; color: #1e293b !important; border-radius: 6px; font-weight: 900 !important; }
    .cal-task-urgent { color: #ef4444 !important; font-weight: 900 !important; text-decoration: underline; }

    /* KAFELKI PODSUMOWANIA - PEŁNA CENTRACJA */
    [data-testid="stMetric"] { 
        background-color: #1e293b !important; border-top: 4px solid #eab308 !important; 
        border-radius: 10px !important; text-align: center !important; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricValue"] > div { 
        display: flex !important; justify-content: center !important; 
        color: #eab308 !important; font-weight: 900 !important; font-size: 2.5rem !important; 
    }
    [data-testid="stMetricLabel"] > div { 
        display: flex !important; justify-content: center !important; 
        color: white !important; font-weight: 600 !important; font-size: 1.1rem !important; 
    }

    /* ZAKŁADKI (TABS) - CZYTELNOŚĆ */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important; font-weight: 700 !important;
        color: #475569 !important; background-color: #f1f5f9 !important;
        border-radius: 8px 8px 0 0 !important; margin-right: 5px !important;
        padding: 10px 20px !important; border: 1px solid #e2e8f0 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: white !important; background-color: #1e293b !important; 
        border-bottom: 4px solid #eab308 !important; 
    }

    /* OBNIŻENIE INFO O UŻYTKOWNIKU */
    .sidebar-user { position: fixed; bottom: 20px; width: 260px; text-align: center; color: #94a3b8; font-size: 0.85rem; }
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

def wyslij_chat(autor, adresat, tekst):
    try:
        ws = polacz().open("Marta-Dział Techniczny").worksheet("Czat")
        now = datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M (%d.%m)")
        ws.append_row([now, autor, adresat, tekst])
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
        mask = (df_zadania['DT'].dt.month == miesiac) & (df_zadania['DT'].dt.year == rok) & (df_zadania['DNI_N'] >= -2)
        pilne_daty = df_zadania[mask]['DT'].dt.day.unique().tolist()

    html = f"<div class='cal-container'><table class='cal-table'>"
    html += f"<tr class='cal-header'><td colspan='7'>{calendar.month_name[miesiac].upper()} {rok}</td></tr>"
    html += "<tr class='cal-day-name'><td>PN</td><td>WT</td><td>ŚR</td><td>CZ</td><td>PT</td><td>SO</td><td>ND</td></tr>"
    
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0: html += "<td></td>"
            else:
                classes = ["cal-day"]
                if day == now.day: classes.append("cal-today")
                if day in pilne_daty: classes.append("cal-task-urgent")
                html += f"<td class='{' '.join(classes)}'>{day}</td>"
        html += "</tr>"
    html += "</table></div>"
    return html

# ==========================================================
# 3. WERYFIKACJA UŻYTKOWNIKA
# ==========================================================
u, k = st.query_params.get("u", ""), st.query_params.get("k", "")
uzytkownicy = {"Andrzej": "8800", "Marta": "1234", "Rafał": "5566", "Agata": "9911", "Sławek": "4422"}

if u == "Andrzej" and k == "8800":
    zalogowany = u
    czy_admin = True
else:
    st.error("❌ BŁĄD DOSTĘPU"); st.stop()

# ==========================================================
# 4. PANEL BOCZNY (KALENDARZ I PRZYCISKI)
# ==========================================================
df_biezace = pobierz_df("Zadania bieżące")
df_slawek = pobierz_df("Terminy Sławka")
df_total = pd.concat([df_biezace, df_slawek])

with st.sidebar:
    st.markdown(f"<h3 style='text-align:center;'>UZDROWISKO<br><span style='color:#eab308'>CIECHOCINEK</span></h3>", unsafe_allow_html=True)
    st.divider()
    
    # WIDOCZNY KALENDARZ
    st.components.v1.html(generuj_kalendarz_html(df_total), height=270)
    st.markdown("<p style='color:#ef4444; font-size:0.75rem; font-weight:bold; text-align:center;'>Oznaczone - terminy kończące się</p>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("➕ DODAJ NOWE ZADANIE", use_container_width=True):
        st.info("Otwórz arkusz Google, aby dodać nowy wiersz.")
    
    if st.button("🔄 ODŚWIEŻ SYSTEM", use_container_width=True): 
        st.cache_data.clear()
        st.rerun()
    
    st.markdown(f'<div class="sidebar-user">Zalogowany: <b>{zalogowany}</b></div>', unsafe_allow_html=True)

# ==========================================================
# 5. WIDOK GŁÓWNY
# ==========================================================
kat_list = ["Zadania bieżące", "Zadania zrealizowane", "Terminy Sławka", "🔴 CZAT"]
tabs = st.tabs(kat_list)

# Zakładki zadań
for i, kat in enumerate(kat_list[:-1]):
    with tabs[i]:
        df = pobierz_df(kat)
        if not df.empty:
            df['DNI_N'] = pd.to_numeric(df['DNI'], errors='coerce').fillna(-999)
            
            # WYŚRODKOWANE KAFELKI
            m1, m2, m3 = st.columns(3)
            m1.metric("📋 Razem zadań", len(df))
            m2.metric("🔥 Pilne (-2+)", len(df[df['DNI_N'] >= -2]))
            m3.metric("🕒 Czas lokalny", datetime.now(pytz.timezone('Europe/Warsaw')).strftime("%H:%M"))
            
            df.insert(0, "S", df['DNI_N'].apply(lambda x: "🚨" if x >= -2 else ("⚪" if x == -999 else "✅")))
            
            edytowane = st.data_editor(
                df, use_container_width=True, hide_index=True, height=750,
                key=f"ed_{kat}",
                column_config={"DNI_N": None, "S": st.column_config.TextColumn(" ", width="small")}
            )
            
            if st.button(f"💾 ZAPISZ ZMIANY: {kat.upper()}", key=f"btn_{kat}"):
                if zapisz_df(edytowane.drop(columns=["S", "DNI_N"]), kat):
                    st.success("Zapisano!"); st.cache_data.clear(); st.rerun()

# CZAT
with tabs[-1]:
    st.subheader("🔴 Komunikacja")
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        do_kogo = st.selectbox("Do kogo:", ["Wszyscy", "Marta", "Sławek", "Rafał"])
    with c2:
        msg = st.text_input("Wiadomość...", key="chat_msg")
    with c3:
        st.write(" ")
        if st.button("WYŚLIJ 📩", use_container_width=True):
            if msg and wyslij_chat(zalogowany, do_kogo, msg): st.rerun()
    
    st.divider()
    df_c = pobierz_df("Czat")
    if not df_c.empty:
        for _, r in df_c.iloc[::-1].iterrows():
            st.markdown(f'<div style="padding:10px; border-radius:10px; border-left:5px solid #0ea5e9; background-color:#f8fafc; margin-bottom:8px;"><b>{r["Autor"]}</b> do <b>{r["Adresat"]}</b> ({r["Data"]}):<br>{r["Wiadomość"]}</div>', unsafe_allow_html=True)

# ==========================================================
# 6. DOLNA BELKA WWW
# ==========================================================
st.markdown("""
    <div style="display: flex; justify-content: center; background-color: white; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-top: 40px;">
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/oferta/">Oferta</a>
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; border-right: 1px solid #f1f5f9; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/sanatoria/">Sanatoria</a>
        <a style="flex: 1; text-align: center; padding: 18px 10px; text-decoration: none; color: #1e293b; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;" href="https://uzdrowiskociechocinek.pl/kontakt/">Kontakt</a>
    </div>
    """, unsafe_allow_html=True)

import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

# --- POŁĄCZENIE ---
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Pakamera", layout="centered")

# --- PROSTE LOGOWANIE ---
if 'ok' not in st.session_state:
    st.session_state.ok = False

if not st.session_state.ok:
    st.title("🔐 Podaj hasło")
    haslo = st.text_input("Hasło:", type="password")
    if st.button("WEJDŹ"):
        if haslo == "Sosna100%":
            st.session_state.ok = True
            st.rerun()
else:
    # --- WYBÓR OSOBY (TO JEST TERAZ NAJWAŻNIEJSZE) ---
    st.title("📦 Wydania Sprzętu")
    
    # Pobranie listy osób z bazy
    osoby_db = supabase.table("pracownicy").select("login").execute()
    lista_ludzi = sorted([o['login'] for o in osoby_db.data]) if osoby_db.data else []
    
    wybrany = st.selectbox("1. WYBIERZ OSOBĘ:", ["-- Wybierz z listy --"] + lista_ludzi)

    # --- LOGIKA: CO WIDZIMY? ---
    if wybrany == "-- Wybierz z listy --":
        # JEŚLI NIKT NIE JEST WYBRANY - POKAZUJEMY TYLKO OSTATNIE 5 WPISÓW OGÓLNIE
        st.info("Wybierz pracownika powyżej, aby zobaczyć jego historię.")
        st.subheader("🕒 Ostatnie 5 wydania w firmie:")
        res_ogolne = supabase.table("wydania").select("*").order("id", desc=True).limit(5).execute()
        if res_ogolne.data:
            df_ogolne = pd.DataFrame(res_ogolne.data)
            st.table(df_ogolne[['kto_pobiera', 'narzedzie', 'data_wydania']])

    else:
        # JEŚLI KTOŚ JEST WYBRANY (NP. BARTEK) - CAŁA RESZTA ZNIKA, ZOSTAJE TYLKO TO:
        st.header(f"👤 Historia: {wybrany}")
        
        # Pobieramy wpisy TYLKO dla tego konkretnego gościa
        res_filtra = supabase.table("wydania").select("*").eq("kto_pobiera", wybrany).order("id", desc=True).execute()
        
        if res_filtra.data:
            for r in res_filtra.data:
                with st.container(border=True):
                    st.write(f"🛠️ **{r['narzedzie']}**")
                    st.caption(f"Data: {r['data_wydania']} | Cel: {r['powod']}")
        else:
            st.warning(f"Brak wpisów dla {wybrany} w bazie.")

        st.divider()
        
        # FORMULARZ DODAWANIA POJAWIA SIĘ TYLKO, GDY KTOŚ JEST WYBRANY
        st.subheader(f"➕ Nowe wydanie dla: {wybrany}")
        n_narzedzie = st.text_input("Nazwa narzędzia:")
        n_powod = st.text_input("Cel/Projekt:")
        
        if st.button("ZAPISZ DLA " + wybrany.upper()):
            if n_narzedzie and n_powod:
                supabase.table("wydania").insert({
                    "kto_pobiera": wybrany,
                    "narzedzie": n_narzedzie,
                    "powod": n_powod,
                    "data_wydania": datetime.now().strftime("%Y-%m-%d")
                }).execute()
                st.success("Zapisano!")
                st.balloons()
                # Krótka pauza i odświeżenie, żeby wpis wskoczył na listę powyżej
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Wpisz nazwę i cel!")

    # Przycisk wylogowania na samym dole
    if st.sidebar.button("Wyloguj"):
        st.session_state.ok = False
        st.rerun()

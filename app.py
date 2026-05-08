import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time

# --- KONFIGURACJA ---
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"

# Inicjalizacja klienta
@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)

supabase = get_supabase()

st.set_page_config(page_title="Pakamera Emila", page_icon="📦", layout="wide")

# --- STAN SESJI ---
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.uzytkownik = ""
    st.session_state.rola = "użytkownik"

# --- LOGOWANIE ---
if not st.session_state.zalogowany:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📦 Logowanie")
        l = st.text_input("Login")
        p = st.text_input("Hasło", type="password")
        if st.button("ZALOGUJ", use_container_width=True, type="primary"):
            if l == "Emil" and p == "Sosna100%":
                st.session_state.zalogowany, st.session_state.uzytkownik, st.session_state.rola = True, "Emil", "admin"
                st.rerun()
            else:
                res = supabase.table("pracownicy").select("*").eq("login", l).eq("haslo", p).execute()
                if res.data:
                    st.session_state.zalogowany = True
                    st.session_state.uzytkownik = l
                    st.session_state.rola = res.data[0].get('rola') or "użytkownik"
                    st.rerun()
                else:
                    st.error("Błędny login lub hasło!")
else:
    # --- MENU BOCZNE ---
    with st.sidebar:
        st.success(f"Zalogowano: **{st.session_state.uzytkownik}**")
        st.info("Wersja: 2.1 - Historia") # <--- SPRAWDŹ CZY TO WIDZISZ NA STRONIE
        st.divider()
        opcje = ["📦 Wydania", "🔎 Wyszukiwarka", "📈 Statystyki", "👥 Pracownicy", "📊 Eksport Excel", "🔐 Konta Web"]
        menu = st.radio("Opcje", opcje)
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.zalogowany = False
            st.rerun()

    # =========================================================================
    # ZAKŁADKA: WYDANIA
    # =========================================================================
    if menu == "📦 Wydania":
        st.title("Nowe wydanie sprzętu")
        
        # Pobieranie danych
        res_prac = supabase.table("pracownicy").select("login").execute()
        lista_pracownikow = sorted([p['login'] for p in res_prac.data]) if res_prac.data else []
        
        res_h = supabase.table("wydania").select("narzedzie, powod").execute()
        lista_n = sorted(list(set([x['narzedzie'] for x in res_h.data if x.get('narzedzie')])))
        lista_p = sorted(list(set([x['powod'] for x in res_h.data if x.get('powod')])))

        # 1. Wybór osoby (Zmieniona ikona dla testu)
        kto = st.selectbox("👷 Wybierz osobę pobierającą:", ["-- Wybierz --"] + lista_pracownikow)
        
        # --- BLOK HISTORII (MUSI SIĘ POJAWIĆ PO WYBORZE) ---
        if kto != "-- Wybierz --":
            st.write(f"🔍 Sprawdzam historię dla: **{kto}**") # Debugger
            res_user = supabase.table("wydania").select("*").eq("kto_pobiera", kto).order("id", desc=True).execute()
            
            with st.expander(f"📋 Historia sprzętu u: {kto}", expanded=True):
                if res_user.data:
                    df_u = pd.DataFrame(res_user.data)
                    st.dataframe(df_u[['narzedzie', 'powod', 'data_wydania']], use_container_width=True, hide_index=True)
                else:
                    st.info("Ten pracownik nie brał jeszcze niczego.")
        
        st.divider()

        # 2. Reszta formularza
        n_wyb = st.selectbox("🔧 Narzędzie", ["+ DODAJ NOWE..."] + lista_n)
        n_final = st.text_input("Wpisz nazwę narzędzia...") if n_wyb == "+ DODAJ NOWE..." else n_wyb
            
        p_wyb = st.selectbox("🏗️ Powód", ["+ DODAJ NOWE..."] + lista_p)
        p_final = st.text_input("Wpisz powód...") if p_wyb == "+ DODAJ NOWE..." else p_wyb
            
        uwagi = st.text_input("📝 Uwagi")
        
        if st.button("ZAPISZ WYDANIE", type="primary", use_container_width=True):
            if kto != "-- Wybierz --" and n_final and p_final:
                supabase.table("wydania").insert({
                    "kto_pobiera": kto, "narzedzie": n_final, "powod": p_final,
                    "uwagi": uwagi, "data_wydania": str(datetime.today().date())
                }).execute()
                st.success("Zapisano!")
                time.sleep(1); st.rerun()
            else:
                st.error("Uzupełnij dane!")

        st.subheader("🕒 Ostatnie 5 wpisów")
        res_last = supabase.table("wydania").select("*").order("id", desc=True).limit(5).execute()
        if res_last.data:
            st.table(pd.DataFrame(res_last.data)[['kto_pobiera', 'narzedzie', 'data_wydania']])

    # --- Pozostałe zakładki (uproszczone dla jasności) ---
    elif menu == "🔎 Wyszukiwarka":
        st.title("Wyszukiwarka")
        f = st.text_input("Szukaj...")
        if f:
            res = supabase.table("wydania").select("*").execute()
            df = pd.DataFrame(res.data)
            st.write(df[df.apply(lambda row: f.lower() in row.astype(str).str.lower().values, axis=1)])

    elif menu == "📈 Statystyki":
        st.title("Statystyki")
        res = supabase.table("wydania").select("*").execute()
        if res.data:
            st.bar_chart(pd.DataFrame(res.data)['kto_pobiera'].value_counts())

    elif menu == "👥 Pracownicy":
        st.title("Pracownicy")
        with st.form("add_p"):
            new_p = st.text_input("Nowy pracownik")
            if st.form_submit_button("Dodaj"):
                supabase.table("pracownicy").insert({"login": new_p}).execute()
                st.rerun()

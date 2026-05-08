import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time

# --- KONFIGURACJA ---
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"

supabase: Client = create_client(URL, KEY)

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
        st.title("📦 Logowanie do systemu")
        with st.container(border=True):
            l = st.text_input("Login")
            p = st.text_input("Hasło", type="password")
            if st.button("ZALOGUJ", use_container_width=True, type="primary"):
                if l == "Emil" and p == "Sosna100%":
                    st.session_state.zalogowany = True
                    st.session_state.uzytkownik = "Emil"
                    st.session_state.rola = "admin"
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
    # --- MENU BOCZNE (Jak na Twoim zrzucie ekranu) ---
    with st.sidebar:
        st.success(f"Zalogowano: **{st.session_state.uzytkownik}**")
        st.divider()
        
        st.caption("MENU")
        opcje = ["📦 Wydania", "🔎 Wyszukiwarka", "📈 Statystyki", "👥 Pracownicy", "📊 Eksport Excel", "🔐 Konta Web"]
        menu = st.radio("Opcje", opcje, label_visibility="collapsed")
            
        st.divider()
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.zalogowany = False
            st.rerun()

    # =========================================================================
    # ZAKŁADKA: WYDANIA (DOKŁADNIE JAK NA SCREENIE + NOWA FUNKCJA)
    # =========================================================================
    if menu == "📦 Wydania":
        st.title("Nowe wydanie sprzętu")
        
        # 1. Pobieranie list z bazy do pól wyboru
        res_prac = supabase.table("pracownicy").select("login").execute()
        lista_pracownikow = [p['login'] for p in res_prac.data] if res_prac.data else []
        
        # Pobieranie unikalnych narzędzi i powodów z historii (żeby podpowiadało w Selectbox)
        res_hist = supabase.table("wydania").select("narzedzie, powod").execute()
        lista_narzedzi = sorted(list(set([x['narzedzie'] for x in res_hist.data if x.get('narzedzie')])))
        lista_powodow = sorted(list(set([x['powod'] for x in res_hist.data if x.get('powod')])))

        # 2. Formularz wydania
        kto_pobiera = st.selectbox("🧑 Kto pobiera?", ["-- Wybierz osobę --"] + lista_pracownikow)
        
        # --- NOWA FUNKCJA: POKAZYWANIE HISTORII WYBRANEJ OSOBY ---
        if kto_pobiera and kto_pobiera != "-- Wybierz osobę --":
            with st.expander(f"📋 Zobacz co {kto_pobiera} ma już na stanie:", expanded=True):
                res_user = supabase.table("wydania").select("*").eq("kto_pobiera", kto_pobiera).order("id", desc=True).execute()
                if res_user.data:
                    df_u = pd.DataFrame(res_user.data)
                    st.dataframe(df_u[['narzedzie', 'powod', 'data_wydania']], use_container_width=True, hide_index=True)
                else:
                    st.info(f"{kto_pobiera} nie ma jeszcze żadnych wydań na koncie.")
        st.write("") # Odstęp
        
        # Wybór narzędzia z opcją dodania nowego
        wybrane_narzedzie = st.selectbox("🔧 Narzędzie", ["+ DODAJ NOWE..."] + lista_narzedzi)
        if wybrane_narzedzie == "+ DODAJ NOWE...":
            docelowe_narzedzie = st.text_input("Wpisz nazwę narzędzia...")
        else:
            docelowe_narzedzie = wybrane_narzedzie
            
        # Wybór powodu z opcją dodania nowego
        wybrany_powod = st.selectbox("🏗️ Powód", ["+ DODAJ NOWE..."] + lista_powodow)
        if wybrany_powod == "+ DODAJ NOWE...":
            docelowy_powod = st.text_input("Wpisz powód...")
        else:
            docelowy_powod = wybrany_powod
            
        uwagi = st.text_input("📝 Uwagi")
        
        st.write("")
        if st.button("ZAPISZ WYDANIE", type="primary", use_container_width=True):
            if kto_pobiera == "-- Wybierz osobę --" or not docelowe_narzedzie or not docelowy_powod:
                st.error("Wypełnij wszystkie wymagane pola (Osoba, Narzędzie, Powód)!")
            else:
                # Zapis do bazy
                supabase.table("wydania").insert({
                    "kto_pobiera": kto_pobiera,
                    "narzedzie": docelowe_narzedzie,
                    "powod": docelowy_powod,
                    "uwagi": uwagi,
                    "data_wydania": str(datetime.today().date())
                }).execute()
                st.success("Wydanie zapisane pomyślnie!")
                time.sleep(1.5)
                st.rerun()

        st.divider()
        
        # 3. Sekcja: Ostatnie wydania na dole
        st.subheader("🕒 Ostatnie wydania")
        res_ostatnie = supabase.table("wydania").select("*").order("id", desc=True).limit(10).execute()
        if res_ostatnie.data:
            df_ost = pd.DataFrame(res_ostatnie.data)
            st.dataframe(df_ost[['kto_pobiera', 'narzedzie', 'powod', 'data_wydania']], use_container_width=True, hide_index=True)
        else:
            st.info("Brak wpisów w bazie.")

    # =========================================================================
    # ZAKŁADKA: WYSZUKIWARKA
    # =========================================================================
    elif menu == "🔎 Wyszukiwarka":
        st.title("🔎 Wyszukiwarka sprzętu")
        fraza = st.text_input("Wpisz nazwę narzędzia, pracownika lub powód...")
        if fraza:
            res_szukaj = supabase.table("wydania").select("*").execute()
            if res_szukaj.data:
                wyniki = [w for w in res_szukaj.data if fraza.lower() in str(w).lower()]
                if wyniki:
                    st.dataframe(pd.DataFrame(wyniki), use_container_width=True, hide_index=True)
                else:
                    st.warning("Nic nie znaleziono.")

    # =========================================================================
    # ZAKŁADKA: STATYSTYKI
    # =========================================================================
    elif menu == "📈 Statystyki":
        st.title("📈 Statystyki")
        res_stat = supabase.table("wydania").select("*").execute()
        if res_stat.data:
            df_stat = pd.DataFrame(res_stat.data)
            col1, col2 = st.columns(2)
            col1.subheader("Wydania na pracownika")
            col1.bar_chart(df_stat['kto_pobiera'].value_counts())
            col2.subheader("Najczęściej wydawane narzędzia")
            col2.bar_chart(df_stat['narzedzie'].value_counts())

    # =========================================================================
    # ZAKŁADKA: PRACOWNICY
    # =========================================================================
    elif menu == "👥 Pracownicy":
        st.title("👥 Zarządzanie pracownikami")
        with st.expander("➕ Dodaj pracownika"):
            n_log = st.text_input("Imię i Nazwisko (Login)")
            n_has = st.text_input("Hasło (opcjonalnie)")
            if st.button("Dodaj"):
                supabase.table("pracownicy").insert({"login": n_log, "haslo": n_has}).execute()
                st.success("Dodano"); time.sleep(1); st.rerun()
                
        res_p = supabase.table("pracownicy").select("*").execute()
        if res_p.data:
            st.dataframe(pd.DataFrame(res_p.data)[['login']], use_container_width=True, hide_index=True)

    # =========================================================================
    # ZAKŁADKA: EKSPORT EXCEL
    # =========================================================================
    elif menu == "📊 Eksport Excel":
        st.title("📊 Pobierz dane")
        res_ex = supabase.table("wydania").select("*").order("id", desc=True).execute()
        if res_ex.data:
            df_ex = pd.DataFrame(res_ex.data)
            csv = '\ufeff'.encode('utf8') + df_ex.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button("📥 Pobierz pełną historię (.csv)", csv, "historia_wydań.csv", "text/csv", use_container_width=True)

    # =========================================================================
    # ZAKŁADKA: KONTA WEB
    # =========================================================================
    elif menu == "🔐 Konta Web":
        st.title("🔐 Ustawienia kont dostępowych")
        st.info("Tutaj możesz zarządzać uprawnieniami administracyjnymi.")
        # Logika zarządzania uprawnieniami (odpowiednik z Twojego starego kodu)

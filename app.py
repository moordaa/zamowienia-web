import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time

# --- KONFIGURACJA ---
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"

@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)

supabase = get_supabase()

st.set_page_config(page_title="Pakamera Emila - DEBUG", page_icon="📦", layout="wide")

# --- STAN SESJI ---
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.uzytkownik = ""

# --- LOGOWANIE ---
if not st.session_state.zalogowany:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📦 Logowanie")
        l = st.text_input("Login")
        p = st.text_input("Hasło", type="password")
        if st.button("ZALOGUJ", use_container_width=True, type="primary"):
            if l == "Emil" and p == "Sosna100%":
                st.session_state.zalogowany, st.session_state.uzytkownik = True, "Emil"
                st.rerun()
            else:
                res = supabase.table("pracownicy").select("*").eq("login", l).eq("haslo", p).execute()
                if res.data:
                    st.session_state.zalogowany, st.session_state.uzytkownik = True, l
                    st.rerun()
                else:
                    st.error("Błędny login lub hasło!")
else:
    # --- MENU BOCZNE ---
    with st.sidebar:
        st.header("WERSJA DIAGNOSTYCZNA 🛠️")
        st.write(f"Zalogowano: **{st.session_state.uzytkownik}**")
        st.divider()
        opcje = ["📦 Wydania", "🔎 Wyszukiwarka", "📈 Statystyki", "👥 Pracownicy", "📊 Eksport Excel"]
        menu = st.radio("MENU", opcje)
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.zalogowany = False
            st.rerun()

    # =========================================================================
    # ZAKŁADKA: WYDANIA (WERSJA DIAGNOSTYCZNA)
    # =========================================================================
    if menu == "📦 Wydania":
        st.title("Nowe wydanie sprzętu")

        # 1. Pobieranie listy osób
        res_p = supabase.table("pracownicy").select("login").execute()
        lista_pracownikow = sorted([p['login'] for p in res_p.data]) if res_p.data else []

        # 2. WYBÓR OSOBY
        wybrany = st.selectbox(
            "🧑‍🔧 Kto pobiera?", 
            ["-- Wybierz osobę --"] + lista_pracownikow,
            key="v_debug_osoba"
        )

        st.divider()

        # 3. POBIERANIE I FILTROWANIE DANYCH (Z PODGLĄDEM)
        st.subheader("📋 Historia / Podgląd wpisów")
        
        # Pobieramy ostatnie 100 wpisów
        res_h = supabase.table("wydania").select("*").order("id", desc=True).limit(100).execute()
        
        if res_h.data:
            df_all = pd.DataFrame(res_h.data)
            
            # --- DEBUG INFO (Pokaże Ci co się dzieje) ---
            if wybrany != "-- Wybierz osobę --":
                # Filtrujemy dane, usuwając spacje (strip) i ignorując wielkość liter
                df_filtered = df_all[df_all['kto_pobiera'].str.strip() == wybrany.strip()]
                
                st.code(f"DEBUG: Wybrałeś '{wybrany}'. W bazie znaleziono {len(df_filtered)} wpisów dla tej osoby.")
                
                if len(df_filtered) == 0:
                    st.warning(f"⚠️ Uwaga: Wybrałeś '{wybrany}', ale w bazie dane mogą być zapisane inaczej (np. ze spacją).")
                    st.write("Dostępne osoby w bazie danych (pierwsze 5):", df_all['kto_pobiera'].unique()[:5])
                
                # Wyświetlamy TYLKO przefiltrowane dane
                st.dataframe(df_filtered[['kto_pobiera', 'narzedzie', 'powod', 'data_wydania']], use_container_width=True, hide_index=True)
            else:
                # Jeśli nikt nie wybrany, pokazujemy 5 ostatnich
                st.info("Wybierz osobę powyżej. Poniżej 5 ostatnich wpisów ogólnych:")
                st.dataframe(df_all.head(5)[['kto_pobiera', 'narzedzie', 'powod', 'data_wydania']], use_container_width=True, hide_index=True)
        else:
            st.info("Brak danych w tabeli 'wydania'.")

        st.divider()

        # 4. FORMULARZ (POD TABELĄ)
        st.subheader("➕ Dodaj nowe wydanie")
        
        # Pobieranie podpowiedzi
        res_hints = supabase.table("wydania").select("narzedzie, powod").execute()
        un_n = sorted(list(set([x['narzedzie'] for x in res_hints.data if x.get('narzedzie')])))
        un_p = sorted(list(set([x['powod'] for x in res_hints.data if x.get('powod')])))

        c1, c2 = st.columns(2)
        with c1:
            n_w = st.selectbox("🔧 Narzędzie", ["+ DODAJ NOWE..."] + un_n)
            n_f = st.text_input("Nazwa narzędzia") if n_w == "+ DODAJ NOWE..." else n_w
        with c2:
            p_w = st.selectbox("🏗️ Powód", ["+ DODAJ NOWE..."] + un_p)
            p_f = st.text_input("Cel wydania") if p_w == "+ DODAJ NOWE..." else p_w

        uwagi = st.text_area("📝 Uwagi")
        
        if st.button("ZAPISZ WYDANIE", type="primary", use_container_width=True):
            if wybrany != "-- Wybierz osobę --" and n_f and p_f:
                supabase.table("wydania").insert({
                    "kto_pobiera": wybrany, # Zapisujemy dokładnie to co wybraliśmy
                    "narzedzie": n_f,
                    "powod": p_f,
                    "uwagi": uwagi,
                    "data_wydania": datetime.now().strftime("%d.%m.%Y %H:%M")
                }).execute()
                st.success("Zapisano!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Wybierz osobę i podaj nazwę narzędzia!")

    # --- Pozostałe zakładki ---
    elif menu == "🔎 Wyszukiwarka":
        st.title("🔎 Wyszukiwarka")
        f = st.text_input("Szukaj...")
        if f:
            res = supabase.table("wydania").select("*").execute()
            df = pd.DataFrame(res.data)
            m = df.apply(lambda r: f.lower() in r.astype(str).str.lower().values, axis=1)
            st.dataframe(df[m], use_container_width=True, hide_index=True)

    elif menu == "📈 Statystyki":
        st.title("📈 Statystyki")
        res = supabase.table("wydania").select("*").execute()
        if res.data:
            st.bar_chart(pd.DataFrame(res.data)['kto_pobiera'].value_counts())

    elif menu == "👥 Pracownicy":
        st.title("👥 Pracownicy")
        np = st.text_input("Imię i Nazwisko")
        if st.button("Dodaj"):
            supabase.table("pracownicy").insert({"login": np}).execute()
            st.rerun()

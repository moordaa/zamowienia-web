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

st.set_page_config(page_title="Pakamera Emila", page_icon="📦", layout="wide")

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
        st.success(f"Zalogowano: **{st.session_state.uzytkownik}**")
        st.divider()
        opcje = ["📦 Wydania", "🔎 Wyszukiwarka", "📈 Statystyki", "👥 Pracownicy", "📊 Eksport Excel"]
        menu = st.radio("MENU", opcje)
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.zalogowany = False
            st.rerun()

    # =========================================================================
    # ZAKŁADKA: WYDANIA (POPRAWIONE FILTROWANIE)
    # =========================================================================
    if menu == "📦 Wydania":
        st.title("Nowe wydanie sprzętu")

        # 1. Pobranie listy pracowników
        res_p = supabase.table("pracownicy").select("login").execute()
        lista_pracownikow = sorted([p['login'] for p in res_p.data]) if res_p.data else []

        # 2. Wybór osoby
        wybrany_pracownik = st.selectbox(
            "🧑‍🔧 Kto pobiera?", 
            ["-- Wybierz osobę --"] + lista_pracownikow,
            key="wybor_osoby_klucz"
        )

        # --- SEKCJA HISTORII (DYNAMICZNA) ---
        st.subheader(f"📋 Historia sprzętu")
        
        if wybrany_pracownik != "-- Wybierz osobę --":
            # JEŚLI WYBRANO OSOBĘ: Pobierz tylko jej wpisy
            st.write(f"Wyświetlam wpisy dla: **{wybrany_pracownik}**")
            res_h = supabase.table("wydania").select("*").eq("kto_pobiera", wybrany_pracownik).order("id", desc=True).execute()
        else:
            # JEŚLI NIE WYBRANO: Pokaż ostatnie 5 wpisów ogólnie
            st.write("Wybierz osobę, aby przefiltrować wyniki. Poniżej ostatnie ogólne wpisy:")
            res_h = supabase.table("wydania").select("*").order("id", desc=True).limit(5).execute()
            
        if res_h.data:
            df_h = pd.DataFrame(res_h.data)
            st.dataframe(
                df_h[['kto_pobiera', 'narzedzie', 'powod', 'data_wydania']], 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("Brak danych do wyświetlenia.")

        st.divider()

        # 3. Formularz dodawania nowego wydania
        st.subheader("➕ Dodaj nowe wydanie")
        
        # Pobranie unikalnych narzędzi/powodów do podpowiedzi
        res_all = supabase.table("wydania").select("narzedzie, powod").execute()
        unikalne_n = sorted(list(set([x['narzedzie'] for x in res_all.data if x.get('narzedzie')])))
        unikalne_p = sorted(list(set([x['powod'] for x in res_all.data if x.get('powod')])))

        col_n, col_p = st.columns(2)
        with col_n:
            n_wyb = st.selectbox("🔧 Narzędzie", ["+ DODAJ NOWE..."] + unikalne_n)
            n_final = st.text_input("Wpisz nazwę sprzętu") if n_wyb == "+ DODAJ NOWE..." else n_wyb
        with col_p:
            p_wyb = st.selectbox("🏗️ Powód", ["+ DODAJ NOWE..."] + unikalne_p)
            p_final = st.text_input("Wpisz powód") if p_wyb == "+ DODAJ NOWE..." else p_wyb

        uwagi = st.text_area("📝 Dodatkowe uwagi")
        
        if st.button("ZAPISZ WYDANIE", type="primary", use_container_width=True):
            if wybrany_pracownik != "-- Wybierz osobę --" and n_final and p_final:
                nowe_wydanie = {
                    "kto_pobiera": wybrany_pracownik,
                    "narzedzie": n_final,
                    "powod": p_final,
                    "uwagi": uwagi,
                    "data_wydania": datetime.now().strftime("%d.%m.%Y %H:%M")
                }
                supabase.table("wydania").insert(nowe_wydanie).execute()
                st.success(f"Zapisano!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Upewnij się, że wybrałeś osobę oraz wpisałeś narzędzie i powód!")

    # --- Pozostałe zakładki ---
    elif menu == "🔎 Wyszukiwarka":
        st.title("🔎 Wyszukiwarka")
        szukaj = st.text_input("Szukaj...")
        if szukaj:
            res = supabase.table("wydania").select("*").execute()
            df = pd.DataFrame(res.data)
            mask = df.apply(lambda row: szukaj.lower() in row.astype(str).str.lower().values, axis=1)
            st.dataframe(df[mask], use_container_width=True, hide_index=True)

    elif menu == "📈 Statystyki":
        st.title("📈 Statystyki")
        res = supabase.table("wydania").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.bar_chart(df['kto_pobiera'].value_counts())

    elif menu == "👥 Pracownicy":
        st.title("👥 Pracownicy")
        new_p = st.text_input("Imię i Nazwisko")
        if st.button("Dodaj"):
            supabase.table("pracownicy").insert({"login": new_p}).execute()
            st.rerun()
        res = supabase.table("pracownicy").select("login").execute()
        if res.data:
            st.table(pd.DataFrame(res.data))

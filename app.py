import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time

# --- KONFIGURACJA ---
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"

# Połączenie z bazą
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Pakamera Emila", page_icon="📦", layout="wide")

# --- STAN SESJI (Logowanie) ---
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.uzytkownik = ""

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
        st.success(f"Użytkownik: **{st.session_state.uzytkownik}**")
        st.divider()
        opcje = ["📦 Wydania", "👥 Pracownicy", "🔎 Wyszukiwarka", "📈 Statystyki", "📊 Eksport CSV"]
        menu = st.radio("MENU", opcje)
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.zalogowany = False
            st.rerun()

    # =========================================================================
    # ZAKŁADKA: WYDANIA
    # =========================================================================
    if menu == "📦 Wydania":
        st.title("📦 Nowe wydanie sprzętu")

        # Pobieramy AKTUALNĄ listę pracowników z bazy
        res_p = supabase.table("pracownicy").select("login").execute()
        lista_osob = sorted([p['login'] for p in res_p.data]) if res_p.data else []

        # 1. Wybór osoby
        if not lista_osob:
            st.warning("⚠️ Brak pracowników w bazie! Idź do zakładki 'Pracownicy' i dodaj Bartka.")
            wybrany = "-- Brak osób --"
        else:
            wybrany = st.selectbox("🧑‍🔧 Kto pobiera sprzęt?", ["-- Wybierz osobę --"] + lista_osob)

        # 2. Wyświetlanie historii (TYLKO DLA WYBRANEJ OSOBY)
        st.subheader("📋 Historia sprzętu")
        if wybrany != "-- Wybierz osobę --" and wybrany != "-- Brak osób --":
            # Pobieramy wpisy TYLKO dla tej osoby
            res_h = supabase.table("wydania").select("*").eq("kto_pobiera", wybrany).order("id", desc=True).execute()
            if res_h.data:
                df_h = pd.DataFrame(res_h.data)
                st.info(f"To są wszystkie narzędzia, które pobrał: **{wybrany}**")
                st.dataframe(df_h[['narzedzie', 'powod', 'data_wydania', 'uwagi']], use_container_width=True, hide_index=True)
            else:
                st.info(f"Użytkownik **{wybrany}** nie pobierał jeszcze żadnego sprzętu.")
        else:
            # Jeśli nikt nie jest wybrany, pokaż 5 ostatnich wydań ogólnie
            st.write("Wybierz osobę powyżej, aby zobaczyć jej historię. Poniżej 5 ostatnich wpisów ogólnych:")
            res_last = supabase.table("wydania").select("*").order("id", desc=True).limit(5).execute()
            if res_last.data:
                st.dataframe(pd.DataFrame(res_last.data)[['kto_pobiera', 'narzedzie', 'data_wydania']], use_container_width=True, hide_index=True)

        st.divider()

        # 3. Formularz wydawania
        st.subheader("➕ Zapisz nowe wydanie")
        
        # Podpowiedzi narzędzi i powodów
        res_all = supabase.table("wydania").select("narzedzie, powod").execute()
        un_n = sorted(list(set([x['narzedzie'] for x in res_all.data if x.get('narzedzie')])))
        un_p = sorted(list(set([x['powod'] for x in res_all.data if x.get('powod')])))

        c1, c2 = st.columns(2)
        with c1:
            n_w = st.selectbox("🔧 Narzędzie", ["+ DOPISZ NOWE..."] + un_n)
            n_final = st.text_input("Podaj nazwę narzędzia") if n_w == "+ DOPISZ NOWE..." else n_w
        with c2:
            p_w = st.selectbox("🏗️ Powód / Projekt", ["+ DOPISZ NOWY..."] + un_p)
            p_final = st.text_input("Podaj cel/projekt") if p_w == "+ DOPISZ NOWY..." else p_w

        uwagi = st.text_area("📝 Dodatkowe uwagi (opcjonalnie)")
        
        if st.button("✅ ZATWIERDŹ I ZAPISZ", type="primary", use_container_width=True):
            if wybrany == "-- Wybierz osobę --" or not n_final or not p_final:
                st.error("BŁĄD: Musisz wybrać OSOBĘ oraz podać NARZĘDZIE i POWÓD!")
            else:
                supabase.table("wydania").insert({
                    "kto_pobiera": wybrany,
                    "narzedzie": n_final,
                    "powod": p_final,
                    "uwagi": uwagi,
                    "data_wydania": datetime.now().strftime("%d.%m.%Y %H:%M")
                }).execute()
                st.success("Zapisano pomyślnie!")
                time.sleep(1)
                st.rerun()

    # =========================================================================
    # ZAKŁADKA: PRACOWNICY (TUTAJ DODAJESZ BARTKA)
    # =========================================================================
    elif menu == "👥 Pracownicy":
        st.title("👥 Zarządzanie pracownikami")
        
        with st.container(border=True):
            st.subheader("➕ Dodaj nową osobę do bazy")
            nowy_p = st.text_input("Imię i Nazwisko pracownika (np. Bartek)")
            if st.button("DODAJ PRACOWNIKA", type="primary"):
                if nowy_p:
                    supabase.table("pracownicy").insert({"login": nowy_p}).execute()
                    st.success(f"Dodano użytkownika **{nowy_p}**! Teraz znajdziesz go na liście w zakładce Wydania.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Wpisz imię!")

        st.divider()
        st.subheader("Lista osób obecnie w bazie:")
        res_list = supabase.table("pracownicy").select("login").execute()
        if res_list.data:
            st.table(pd.DataFrame(res_list.data))
        else:
            st.info("Baza pracowników jest pusta.")

    # Pozostałe zakładki (uproszczone)
    elif menu == "🔎 Wyszukiwarka":
        st.title("🔎 Wyszukiwarka")
        f = st.text_input("Szukaj frazy...")
        if f:
            res = supabase.table("wydania").select("*").execute()
            df = pd.DataFrame(res.data)
            m = df.apply(lambda r: f.lower() in r.astype(str).str.lower().values, axis=1)
            st.dataframe(df[m], use_container_width=True)

    elif menu == "📈 Statystyki":
        st.title("📈 Statystyki")
        res = supabase.table("wydania").select("*").execute()
        if res.data:
            st.bar_chart(pd.DataFrame(res.data)['kto_pobiera'].value_counts())

    elif menu == "📊 Eksport CSV":
        st.title("📊 Pobieranie danych")
        res = supabase.table("wydania").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.download_button("Pobierz plik CSV", df.to_csv(index=False), "wydania.csv", "text/csv")

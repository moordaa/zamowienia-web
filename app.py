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

# --- LOGOWANIE ---
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False

if not st.session_state.zalogowany:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📦 Logowanie")
        l = st.text_input("Login")
        p = st.text_input("Hasło", type="password")
        if st.button("ZALOGUJ", use_container_width=True, type="primary"):
            if l == "Emil" and p == "Sosna100%":
                st.session_state.zalogowany = True
                st.rerun()
            else:
                res = supabase.table("pracownicy").select("*").eq("login", l).eq("haslo", p).execute()
                if res.data:
                    st.session_state.zalogowany = True
                    st.rerun()
                else:
                    st.error("Błędny login!")
else:
    # --- MENU BOCZNE ---
    with st.sidebar:
        st.success("Zalogowano")
        menu = st.radio("MENU", ["📦 Wydania", "👥 Pracownicy", "🔎 Historia"])
        if st.button("🚪 Wyloguj"):
            st.session_state.zalogowany = False
            st.rerun()

    # =========================================================================
    # ZAKŁADKA: WYDANIA
    # =========================================================================
    if menu == "📦 Wydania":
        st.title("📦 Nowe wydanie sprzętu")

        # 1. POBIERANIE LISTY (POZA FORMULARZEM)
        res_p = supabase.table("pracownicy").select("login").execute()
        lista_osob = sorted([p['login'] for p in res_p.data]) if res_p.data else []

        # 2. WYBÓR OSOBY (POZA FORMULARZEM - to gwarantuje odświeżanie!)
        wybrany = st.selectbox("🧑‍🔧 Kto pobiera sprzęt?", ["-- Wybierz osobę --"] + lista_osob, key="glowne_wybranie")

        # 3. WYŚWIETLANIE HISTORII (NATYCHMIASTOWE)
        if wybrany != "-- Wybierz osobę --":
            st.write(f"🔍 Sprawdzam bazę dla: **{wybrany}**")
            res_h = supabase.table("wydania").select("*").eq("kto_pobiera", wybrany).order("id", desc=True).execute()
            
            if res_h.data:
                st.subheader(f"📋 Sprzęt u pracownika: {wybrany}")
                df_h = pd.DataFrame(res_h.data)
                st.dataframe(df_h[['narzedzie', 'powod', 'data_wydania']], use_container_width=True, hide_index=True)
            else:
                st.info(f"Brak wpisów dla {wybrany}. Możesz dodać pierwsze wydanie poniżej.")
        else:
            st.info("Wybierz osobę, aby zobaczyć co już pobrała.")

        st.divider()

        # 4. FORMULARZ DODAWANIA (TYLKO DLA SAMEGO ZAPISU)
        st.subheader("➕ Nowy wpis")
        
        # Pobieramy podpowiedzi narzędzi
        res_all = supabase.table("wydania").select("narzedzie, powod").execute()
        un_n = sorted(list(set([x['narzedzie'] for x in res_all.data if x.get('narzedzie')])))
        un_p = sorted(list(set([x['powod'] for x in res_all.data if x.get('powod')])))

        # Używamy st.form, aby przyciski dodawania narzędzi nie przeładowywały strony co sekundę
        with st.form("form_wydania", clear_on_submit=True):
            c1, c2 = st.columns(2)
            narzedzie_input = c1.text_input("Wpisz narzędzie (lub wybierz z listy obok)")
            narzedzie_list = c1.selectbox("Podpowiedzi narzędzi", ["-- Wybierz --"] + un_n)
            
            powod_input = c2.text_input("Wpisz cel/projekt")
            powod_list = c2.selectbox("Podpowiedzi powodów", ["-- Wybierz --"] + un_p)
            
            uwagi = st.text_input("Uwagi")
            
            submit = st.form_submit_button("✅ ZAPISZ WYDANIE", use_container_width=True, type="primary")
            
            if submit:
                # Logika wyboru: weź z inputa, a jak pusty to z listy
                n_final = narzedzie_input if narzedzie_input else (narzedzie_list if narzedzie_list != "-- Wybierz --" else None)
                p_final = powod_input if powod_input else (powod_list if powod_list != "-- Wybierz --" else None)

                if wybrany != "-- Wybierz osobę --" and n_final and p_final:
                    supabase.table("wydania").insert({
                        "kto_pobiera": wybrany,
                        "narzedzie": n_final,
                        "powod": p_final,
                        "uwagi": uwagi,
                        "data_wydania": datetime.now().strftime("%d.%m.%Y %H:%M")
                    }).execute()
                    st.success("Zapisano!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Uzupełnij dane! Wybierz osobę i podaj narzędzie.")

    # =========================================================================
    # ZAKŁADKA: PRACOWNICY
    # =========================================================================
    elif menu == "👥 Pracownicy":
        st.title("👥 Lista pracowników")
        with st.form("add_p"):
            imie = st.text_input("Imię i Nazwisko (Login)")
            if st.form_submit_button("DODAJ BARTKA"):
                if imie:
                    supabase.table("pracownicy").insert({"login": imie}).execute()
                    st.success(f"Dodano {imie}!")
                    time.sleep(1)
                    st.rerun()

        res = supabase.table("pracownicy").select("login").execute()
        if res.data:
            st.table(pd.DataFrame(res.data))

    # =========================================================================
    # ZAKŁADKA: HISTORIA (OGÓLNA)
    # =========================================================================
    elif menu == "🔎 Historia":
        st.title("🔎 Pełna historia wydań")
        res = supabase.table("wydania").select("*").order("id", desc=True).execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True, hide_index=True)

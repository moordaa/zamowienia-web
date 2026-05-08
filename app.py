import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time

# 1. POŁĄCZENIE (Zawsze na górze)
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Pakamera Emila", layout="wide")

# 2. PROSTE LOGOWANIE
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False

if not st.session_state.zalogowany:
    l = st.text_input("Login")
    p = st.text_input("Hasło", type="password")
    if st.button("ZALOGUJ"):
        if (l == "Emil" and p == "Sosna100%") or l == "admin":
            st.session_state.zalogowany = True
            st.rerun()
else:
    # 3. MENU
    menu = st.sidebar.radio("MENU", ["Wydania", "Pracownicy"])
    if st.sidebar.button("Wyloguj"):
        st.session_state.zalogowany = False
        st.rerun()

    # --- ZAKŁADKA PRACOWNICY ---
    if menu == "Pracownicy":
        st.title("👥 Dodaj Bartka tutaj")
        nowy = st.text_input("Imię i nazwisko")
        if st.button("ZAPISZ PRACOWNIKA"):
            supabase.table("pracownicy").insert({"login": nowy}).execute()
            st.success(f"Dodano: {nowy}")
            st.rerun()
        
        res = supabase.table("pracownicy").select("login").execute()
        st.write("Ludzie w bazie:", [p['login'] for p in res.data])

    # --- ZAKŁADKA WYDANIA ---
    elif menu == "Wydania":
        st.title("📦 Wydanie sprzętu")

        # Pobieranie listy osób
        res_p = supabase.table("pracownicy").select("login").execute()
        lista_osob = sorted([p['login'] for p in res_p.data]) if res_p.data else []

        # WYBÓR OSOBY (KLUCZOWY ELEMENT)
        wybrany = st.selectbox("Wybierz osobę z listy:", ["-- Wybierz --"] + lista_osob)

        st.divider()

        # TUTAJ DZIEJE SIĘ FILTROWANIE
        if wybrany != "-- Wybierz --":
            st.subheader(f"To co ma u siebie: {wybrany}")
            # POBIERAMY TYLKO DLA TEJ OSOBY
            res_h = supabase.table("wydania").select("*").eq("kto_pobiera", wybrany).order("id", desc=True).execute()
            
            if res_h.data:
                for r in res_h.data:
                    with st.container(border=True):
                        st.write(f"🔧 **{r['narzedzie']}** | 📅 {r['data_wydania']}")
                        st.caption(f"Powód: {r['powod']}")
            else:
                st.info("Ten gość jeszcze nic nie brał.")
        else:
            st.warning("Wybierz kogoś z listy powyżej, aby zobaczyć jego sprzęt.")

        st.divider()

        # FORMULARZ DODAWANIA (TYLKO DLA TEGO WYBRANEGO)
        if wybrany != "-- Wybierz --":
            st.subheader(f"Wydaj coś dla: {wybrany}")
            n = st.text_input("Co wydajesz?")
            p = st.text_input("Na co (powód)?")
            if st.button("ZATWIERDŹ WYDANIE"):
                if n and p:
                    supabase.table("wydania").insert({
                        "kto_pobiera": wybrany,
                        "narzedzie": n,
                        "powod": p,
                        "data_wydania": datetime.now().strftime("%Y-%m-%d")
                    }).execute()
                    st.success("Zapisano!")
                    time.sleep(1)
                    st.rerun()

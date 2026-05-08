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

# --- LOGOWANIE ---
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
                    st.error("Błąd logowania!")
else:
    # --- MENU BOCZNE ---
    with st.sidebar:
        st.success("Zalogowano: Emil")
        menu = st.radio("MENU", ["📦 Wydania", "👥 Pracownicy", "🔎 Wyszukiwarka"])
        if st.button("Wyloguj"):
            st.session_state.zalogowany = False
            st.rerun()

    # =========================================================================
    # ZAKŁADKA: WYDANIA
    # =========================================================================
    if menu == "📦 Wydania":
        st.title("Nowe wydanie sprzętu")

        # 1. Pobranie listy pracowników
        res_p = supabase.table("pracownicy").select("login").execute()
        lista_osob = sorted([p['login'] for p in res_p.data]) if res_p.data else []

        # 2. WYBÓR OSOBY (Musi być POZA st.form, żeby strona od razu reagowała!)
        wybrany_pracownik = st.selectbox(
            "🧑‍🔧 Kto pobiera?", 
            ["-- Wybierz osobę --"] + lista_osob,
            key="glowne_wybranie_osoby"
        )

        # 3. FORMULARZ DODAWANIA (TYLKO DLA SAMEGO ZAPISU)
        with st.container(border=True):
            res_all = supabase.table("wydania").select("narzedzie, powod").execute()
            un_n = sorted(list(set([x['narzedzie'] for x in res_all.data if x.get('narzedzie')])))
            un_p = sorted(list(set([x['powod'] for x in res_all.data if x.get('powod')])))

            col_n, col_p = st.columns(2)
            with col_n:
                n_wyb = st.selectbox("🔧 Narzędzie", ["+ DODAJ NOWE..."] + un_n)
                n_final = st.text_input("Wpisz nazwę sprzętu") if n_wyb == "+ DODAJ NOWE..." else n_wyb
            with col_p:
                p_wyb = st.selectbox("🏗️ Powód", ["+ DODAJ NOWE..."] + un_p)
                p_final = st.text_input("Wpisz powód") if p_wyb == "+ DODAJ NOWE..." else p_wyb

            uwagi = st.text_input("📝 Uwagi")
            
            if st.button("ZAPISZ WYDANIE", type="primary", use_container_width=True):
                if wybrany_pracownik != "-- Wybierz osobę --" and n_final and p_final:
                    supabase.table("wydania").insert({
                        "kto_pobiera": wybrany_pracownik,
                        "narzedzie": n_final,
                        "powod": p_final,
                        "uwagi": uwagi,
                        "data_wydania": datetime.now().strftime("%Y-%m-%d")
                    }).execute()
                    st.success("Zapisano!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Wybierz osobę i podaj narzędzie!")

        st.divider()

        # =========================================================================
        # 4. DYNAMICZNA SEKCJA: OSTATNIE WYDANIA / HISTORIA
        # =========================================================================
        # Ta sekcja zmienia się w zależności od tego, czy wybrałeś kogoś na górze!
        
        if wybrany_pracownik != "-- Wybierz osobę --":
            st.subheader(f"🕒 Historia wydań dla: {wybrany_pracownik}")
            # Pobieramy tylko wpisy dla tej osoby
            res_h = supabase.table("wydania").select("*").eq("kto_pobiera", wybrany_pracownik).order("id", desc=True).execute()
        else:
            st.subheader("🕒 Ostatnie ogólne wydania")
            # Jeśli nikt nie jest wybrany, pokazujemy 5 ostatnich wpisów ogólnie
            res_h = supabase.table("wydania").select("*").order("id", desc=True).limit(5).execute()

        if res_h.data:
            for r in res_h.data:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{r['narzedzie']}**")
                        st.caption(f"👤 {r['kto_pobiera']} | 🏗️ {r['powod']} | 📅 {r['data_wydania']}")
                    with c2:
                        # Przycisk usuwania (opcjonalnie)
                        if st.button("🗑️", key=f"del_{r['id']}"):
                            supabase.table("wydania").delete().eq("id", r['id']).execute()
                            st.rerun()
        else:
            st.info("Brak wpisów do wyświetlenia.")

    # --- POZOSTAŁE ZAKŁADKI ---
    elif menu == "👥 Pracownicy":
        st.title("👥 Pracownicy")
        nowy = st.text_input("Imię i Nazwisko")
        if st.button("Dodaj"):
            supabase.table("pracownicy").insert({"login": nowy}).execute()
            st.success(f"Dodano {nowy}")
            time.sleep(1); st.rerun()
        
        res = supabase.table("pracownicy").select("login").execute()
        if res.data:
            st.table(pd.DataFrame(res.data))

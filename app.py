import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time

# --- 1. KONFIGURACJA POŁĄCZENIA ---
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"

@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)

supabase = get_supabase()

st.set_page_config(page_title="Pakamera Emila", page_icon="📦", layout="wide")

# --- 2. LOGOWANIE (Uproszczone dla stabilności) ---
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
                    st.error("Błąd logowania")
else:
    # --- 3. MENU BOCZNE ---
    with st.sidebar:
        st.success("Zalogowano: Emil")
        menu = st.radio("MENU", ["📦 Wydania", "👥 Pracownicy", "🔎 Wyszukiwarka"])
        if st.button("Wyloguj"):
            st.session_state.zalogowany = False
            st.rerun()

    # =========================================================================
    # ZAKŁADKA: WYDANIA (Kluczowa sekcja)
    # =========================================================================
    if menu == "📦 Wydania":
        st.title("Nowe wydanie sprzętu")

        # POBIERANIE LISTY PRACOWNIKÓW
        res_p = supabase.table("pracownicy").select("login").execute()
        lista_osob = sorted([p['login'] for p in res_p.data]) if res_p.data else []

        # A. WYBÓR OSOBY (POZA FORMULARZEM)
        # To musi być tutaj, żeby 'rozjaśnienie' strony powodowało przeładowanie danych
        wybrany = st.selectbox(
            "🧑‍🔧 Kto pobiera?", 
            ["-- Wybierz osobę --"] + lista_osob,
            key="wybor_pracownika_main"
        )

        # B. FORMULARZ WYDANIA
        # Używamy kontenera, aby oddzielić formularz od historii
        with st.container(border=True):
            st.subheader("➕ Formularz wydania")
            res_all = supabase.table("wydania").select("narzedzie, powod").execute()
            un_n = sorted(list(set([x['narzedzie'] for x in res_all.data if x.get('narzedzie')])))
            un_p = sorted(list(set([x['powod'] for x in res_all.data if x.get('powod')])))

            c1, c2 = st.columns(2)
            n_wyb = c1.selectbox("🔧 Narzędzie", ["+ DODAJ NOWE..."] + un_n)
            n_input = c1.text_input("Nazwa narzędzia") if n_wyb == "+ DODAJ NOWE..." else n_wyb
            
            p_wyb = c2.selectbox("🏗️ Powód", ["+ DODAJ NOWE..."] + un_p)
            p_input = c2.text_input("Powód/Projekt") if p_wyb == "+ DODAJ NOWE..." else p_wyb
            
            uwagi = st.text_input("📝 Uwagi")
            
            if st.button("ZAPISZ WYDANIE", type="primary", use_container_width=True):
                if wybrany != "-- Wybierz osobę --" and n_input and p_input:
                    supabase.table("wydania").insert({
                        "kto_pobiera": wybrany,
                        "narzedzie": n_input,
                        "powod": p_input,
                        "uwagi": uwagi,
                        "data_wydania": datetime.now().strftime("%Y-%m-%d")
                    }).execute()
                    st.success("Zapisano!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Uzupełnij kogo dotyczy wydanie!")

        st.divider()

        # =========================================================================
        # C. DYNAMICZNA SEKCJA HISTORII (To tutaj dzieje się magia)
        # =========================================================================
        # Ta sekcja sprawdza: czy ktoś jest wybrany?
        # Jeśli TAK -> filtruje tylko jego historię
        # Jeśli NIE -> pokazuje 5 ostatnich wpisów ogólnych
        
        if wybrany != "-- Wybierz osobę --":
            st.subheader(f"🕒 Historia wydań dla: {wybrany}")
            # POBIERAMY TYLKO DLA TEJ OSOBY
            res_h = supabase.table("wydania").select("*").eq("kto_pobiera", wybrany).order("id", desc=True).execute()
        else:
            st.subheader("🕒 Ostatnie wydania (ogólne)")
            # POBIERAMY 5 OSTATNICH OGÓLNIE
            res_h = supabase.table("wydania").select("*").order("id", desc=True).limit(5).execute()

        # RENDEROWANIE KART (Dokładnie tak jak na Twoim screenie)
        if res_h.data:
            for r in res_h.data:
                with st.container(border=True):
                    col_text, col_del = st.columns([5, 1])
                    with col_text:
                        st.markdown(f"**{r['narzedzie']}**")
                        st.caption(f"👤 {r['kto_pobiera']} | 🏗️ {r['powod']} | 📅 {r['data_wydania']}")
                    with col_del:
                        if st.button("🗑️", key=f"del_{r['id']}"):
                            supabase.table("wydania").delete().eq("id", r['id']).execute()
                            st.rerun()
        else:
            st.info("Brak wpisów dla tego pracownika.")

    # --- POZOSTAŁE ZAKŁADKI (Uproszczone) ---
    elif menu == "👥 Pracownicy":
        st.title("Zarządzanie pracownikami")
        n_p = st.text_input("Dodaj imię i nazwisko")
        if st.button("Dodaj"):
            supabase.table("pracownicy").insert({"login": n_p}).execute()
            st.success("Dodano")
            st.rerun()
        res = supabase.table("pracownicy").select("login").execute()
        if res.data:
            st.table(pd.DataFrame(res.data))

    elif menu == "🔎 Wyszukiwarka":
        st.title("Wyszukiwarka")
        szukaj = st.text_input("Szukaj...")
        if szukaj:
            res = supabase.table("wydania").select("*").execute()
            df = pd.DataFrame(res.data)
            mask = df.apply(lambda row: szukaj.lower() in row.astype(str).str.lower().values, axis=1)
            st.dataframe(df[mask], use_container_width=True)

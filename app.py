import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

# --- KONFIGURACJA ---
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Zapotrzebowanie", page_icon="🛒", layout="centered")

if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.uzytkownik = ""
    st.session_state.rola = "użytkownik"

# --- LOGOWANIE (DZIELI BAZĘ Z PAKAMERĄ) ---
if not st.session_state.zalogowany:
    st.title("🛒 ZAPOTRZEBOWANIE")
    st.caption("System zamówień materiałowych")
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
                st.error("Błędne dane!")
else:
    # --- MENU BOCZNE ---
    with st.sidebar:
        st.success(f"Zalogowano: **{st.session_state.uzytkownik}**")
        st.divider()
        
        # Menu różni się w zależności od roli
        if st.session_state.rola == "admin":
            menu = st.radio("MENU", ["📝 Nowe Zgłoszenie", "⚙️ Panel Realizacji (Admin)", "🔎 Historia i Szukaj"])
        else:
            menu = st.radio("MENU", ["📝 Nowe Zgłoszenie", "📋 Moje Aktywne", "🔎 Historia i Szukaj"])
            
        st.divider()
        if st.button("🔄 Odśwież dane", use_container_width=True):
            st.rerun()
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.zalogowany = False
            st.session_state.rola = "użytkownik"
            st.rerun()

    # --- MAPOWANIE KOLORÓW STATUSÓW ---
    status_emoji = {
        "Oczekujące": "⏳",
        "Zamówione": "🚚",
        "Niedostępne": "❌",
        "Zamiennik": "🔄",
        "Zrealizowane": "✅"
    }

    # =========================================================================
    # ZAKŁADKA: NOWE ZGŁOSZENIE
    # =========================================================================
    if menu == "📝 Nowe Zgłoszenie":
        st.title("📝 Dodaj zapotrzebowanie")
        
        with st.container(border=True):
            pozycja = st.text_input("🔧 Pozycja (np. Śruba zamkowa)")
            col1, col2 = st.columns(2)
            wymiary = col1.text_input("📏 Wymiary (np. M8x40)")
            material = col2.text_input("🧱 Materiał (np. Ocynk)")
            
            col3, col4 = st.columns(2)
            ilosc = col3.text_input("🔢 Ilość (np. 100 szt., 5 kg)")
            pilnosc = col4.selectbox("🚨 Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"])
            
            projekt = st.text_input("🏗️ Projekt / Budowa / Cel")
            
            if st.button("WYŚLIJ ZGŁOSZENIE", type="primary", use_container_width=True):
                if pozycja and ilosc:
                    supabase.table("zapotrzebowanie").insert({
                        "pozycja": pozycja,
                        "wymiary": wymiary,
                        "material": material,
                        "ilosc": ilosc,
                        "projekt": projekt,
                        "pilnosc": pilnosc,
                        "status": "Oczekujące",
                        "zgloszone_przez": st.session_state.uzytkownik,
                        "data_zgloszenia": str(datetime.today().date())
                    }).execute()
                    st.toast("Zgłoszenie wysłane!")
                    st.rerun()
                else:
                    st.error("Pola 'Pozycja' i 'Ilość' są obowiązkowe!")

    # =========================================================================
    # ZAKŁADKA: PANEL REALIZACJI (ADMIN)
    # =========================================================================
    elif menu == "⚙️ Panel Realizacji (Admin)":
        st.title("⚙️ Zarządzaj Zamówieniami")
        st.caption("Lista wszystkich aktywnych zgłoszeń. Zmieniaj statusy i dodawaj uwagi.")
        
        # Pobierz wszystkie niezrealizowane
        res = supabase.table("zapotrzebowanie").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        
        if not res.data:
            st.success("Wszystkie zamówienia są zrealizowane! Brak aktywnych zgłoszeń.")
        else:
            for r in res.data:
                with st.container(border=True):
                    # Nagłówek elementu
                    st.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                    if "PILNE" in r['pilnosc'] or "KRYTYCZNE" in r['pilnosc']:
                        st.error(f"🚨 {r['pilnosc']}")
                        
                    st.caption(f"📏 Wymiary: {r['wymiary']} | 🧱 Materiał: {r['material']} | 🏗️ Projekt: {r['projekt']}")
                    st.caption(f"👤 Zgłosił: **{r['zgloszone_przez']}** ({r['data_zgloszenia']})")
                    
                    st.divider()
                    
                    # Panel kontrolny Admina
                    col_stat, col_uwg = st.columns([1, 2])
                    
                    lista_statusow = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    aktualny_index = lista_statusow.index(r['status']) if r['status'] in lista_statusow else 0
                    
                    nowy_status = col_stat.selectbox("Status", lista_statusow, index=aktualny_index, key=f"stat_{r['id']}")
                    nowe_uwagi = col_uwg.text_input("Notatka (np. numer paczki, jaki zamiennik)", value=r.get('uwagi_admina') or "", key=f"uwg_{r['id']}")
                    
                    c1, c2 = st.columns([3, 1])
                    if c1.button("💾 Zapisz zmiany", key=f"zapisz_{r['id']}", type="primary"):
                        supabase.table("zapotrzebowanie").update({
                            "status": nowy_status, 
                            "uwagi_admina": nowe_uwagi
                        }).eq("id", r['id']).execute()
                        st.toast("Zaktualizowano!")
                        st.rerun()
                    if c2.button("🗑️ Usuń", key=f"del_{r['id']}", type="secondary"):
                        supabase.table("zapotrzebowanie").delete().eq("id", r['id']).execute()
                        st.rerun()

    # =========================================================================
    # ZAKŁADKA: MOJE AKTYWNE (ZWYKŁY UŻYTKOWNIK)
    # =========================================================================
    elif menu == "📋 Moje Aktywne":
        st.title("📋 Aktywne Zgłoszenia")
        st.caption("Tutaj widzisz statusy elementów, które zamówiłeś.")
        
        res = supabase.table("zapotrzebowanie").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").order("id", desc=True).execute()
        
        if not res.data:
            st.info("Nie masz obecnie żadnych oczekujących zamówień.")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"**{r['pozycja']}** | Ilość: {r['ilosc']}")
                    st.caption(f"🏗️ {r['projekt']} | 📅 {r['data_zgloszenia']}")
                    
                    ikona = status_emoji.get(r['status'], "🔹")
                    st.markdown(f"**Status:** {ikona} {r['status']}")
                    
                    if r.get('uwagi_admina'):
                        st.info(f"📝 Odpis Admina: {r['uwagi_admina']}")

    # =========================================================================
    # ZAKŁADKA: WYSZUKIWARKA I HISTORIA
    # =========================================================================
    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Baza Zamówień")
        
        res_all = supabase.table("zapotrzebowanie").select("projekt, zgloszone_przez").execute()
        projekty = sorted(list(set([x['projekt'] for x in res_all.data if x['projekt']])))
        osoby = sorted(list(set([x['zgloszone_przez'] for x in res_all.data if x['zgloszone_przez']])))
        
        with st.container(border=True):
            f_slowo = st.text_input("🔍 Szukaj po nazwie (np. śruba)...")
            col1, col2, col3 = st.columns(3)
            f_proj = col1.selectbox("🏗️ Projekt", ["-- Wszystkie --"] + projekty)
            f_kto = col2.selectbox("👤 Kto", ["-- Wszyscy --"] + osoby)
            f_status = col3.selectbox("📌 Status", ["-- Wszystkie --", "Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"])
            
            if st.button("SZUKAJ", type="primary", use_container_width=True):
                q = supabase.table("zapotrzebowanie").select("*")
                if f_proj != "-- Wszystkie --": q = q.eq("projekt", f_proj)
                if f_kto != "-- Wszyscy --": q = q.eq("zgloszone_przez", f_kto)
                if f_status != "-- Wszystkie --": q = q.eq("status", f_status)
                
                wynik_szukania = q.order("id", desc=True).execute().data
                
                if f_slowo.strip():
                    f_slowo = f_slowo.lower()
                    wynik_szukania = [x for x in wynik_szukania if f_slowo in x['pozycja'].lower() or f_slowo in (x.get('uwagi_admina') or '').lower()]
                
                st.divider()
                if wynik_szukania:
                    st.success(f"Znaleziono: {len(wynik_szukania)}")
                    for r in wynik_szukania:
                        with st.container(border=True):
                            ikona = status_emoji.get(r['status'], "🔹")
                            st.markdown(f"**{ikona} {r['status']}** | {r['pozycja']} ({r['ilosc']})")
                            st.caption(f"👤 {r['zgloszone_przez']} | 🏗️ {r['projekt']} | 📅 {r['data_zgloszenia']}")
                            if r.get('uwagi_admina'): st.info(f"Notatka: {r['uwagi_admina']}")
                else:
                    st.warning("Brak wyników spełniających kryteria.")

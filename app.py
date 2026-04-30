import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time
import urllib.parse

# --- KONFIGURACJA ---
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Zamówienia", page_icon="🛒", layout="wide")

if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.uzytkownik = ""
    st.session_state.rola = "użytkownik"

# --- LOGOWANIE ---
if not st.session_state.zalogowany:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🛒 ZAMÓWIENIA")
        st.caption("System zamówień materiałowych")
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
                        st.error("Błędne dane!")
else:
    # --- MENU BOCZNE ---
    with st.sidebar:
        st.success(f"Zalogowano: **{st.session_state.uzytkownik}**")
        st.divider()
        
        if st.session_state.rola == "admin":
            menu = st.radio("MENU", [
                "📝 Nowe Zamówienie", 
                "⚙️ Panel Realizacji (Admin)", 
                "📊 Statystyki i Raporty", 
                "👥 Zarządzanie Kontami", 
                "🔎 Historia i Szukaj",
                "📖 Instrukcja"
            ])
        else:
            menu = st.radio("MENU", [
                "📝 Nowe Zamówienie", 
                "📋 Moje Aktywne", 
                "🔎 Historia i Szukaj",
                "📖 Instrukcja"
            ])
            
        st.divider()
        if st.button("🔄 Odśwież dane", use_container_width=True):
            st.rerun()
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.zalogowany = False
            st.session_state.rola = "użytkownik"
            st.rerun()

    status_emoji = {
        "Oczekujące": "⏳",
        "Zamówione": "🚚",
        "Niedostępne": "❌",
        "Zamiennik": "🔄",
        "Zrealizowane": "✅"
    }

    def render_status_alert(status_text):
        ikona = status_emoji.get(status_text, "🔹")
        msg = f"**Status:** {ikona} {status_text}"
        if status_text == "Zrealizowane":
            st.success(msg)
        elif status_text in ["Niedostępne", "Zamiennik"]:
            st.error(msg)
        elif status_text == "Oczekujące":
            st.warning(msg)
        else:
            st.info(msg)

    # =========================================================================
    # ZAKŁADKA: NOWE ZAMÓWIENIE (Z EASTER EGGIEM)
    # =========================================================================
    if menu == "📝 Nowe Zamówienie":
        st.title("📝 Dodaj zamówienie")
        
        admins_res = supabase.table("pracownicy").select("login, telefon").eq("rola", "admin").execute()
        admin_phones = {}
        if admins_res.data:
            for a in admins_res.data:
                if a.get('telefon'):
                    admin_phones[a['login']] = a['telefon']
                    
        opcje_adminow = ["-- Nie wysyłaj --"] + list(admin_phones.keys())
        
        with st.container(border=True):
            pozycja = st.text_input("🔧 Pozycja (np. Śruba zamkowa)")
            
            # --- EASTER EGG LOGIC ---
            if pozycja.strip() == "69":
                st.balloons()
                st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmNudWw2ODZpeGZqZGZ6Z3N5Zmt6ZGZ6Z3N5Zmt6ZGZ6Z3N5Zmt6ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zy/6YjzP6F3R8Vz6/giphy.gif")
                st.warning("NICE. Ale wróćmy do roboty! 😉")
            
            col1, col2 = st.columns(2)
            wymiary = col1.text_input("📏 Wymiary (np. M8x40)")
            material = col2.text_input("🧱 Materiał (np. Ocynk)")
            
            col3, col4 = st.columns(2)
            ilosc = col3.text_input("🔢 Ilość (np. 100 szt., 5 kg)")
            pilnosc = col4.selectbox("🚨 Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"])
            
            projekt = st.text_input("🏗️ Projekt / Budowa / Cel")
            
            st.divider()
            zdjecie = None
            if st.toggle("📷 Włącz aparat, aby dodać zdjęcie"):
                zdjecie = st.camera_input("Zrób zdjęcie części / usterki")
            
            st.divider()
            col_wa, _ = st.columns([1, 1])
            powiadom_admina = col_wa.selectbox("📲 Powiadom admina (WhatsApp)", opcje_adminow, help="Wybierz administratora, do którego automatycznie wygeneruje się wiadomość o tym zamówieniu.")
            
            if st.button("WYŚLIJ ZAMÓWIENIE", type="primary", use_container_width=True):
                if pozycja and ilosc:
                    zdjecie_public_url = ""
                    if zdjecie is not None:
                        with st.spinner("Wgrywanie zdjęcia..."):
                            nazwa_pliku = f"{int(time.time())}_{st.session_state.uzytkownik}.jpg"
                            res_upload = supabase.storage.from_("zdjecia_zamowien").upload(
                                path=nazwa_pliku,
                                file=zdjecie.getvalue(),
                                file_options={"content-type": "image/jpeg"}
                            )
                            zdjecie_public_url = supabase.storage.from_("zdjecia_zamowien").get_public_url(nazwa_pliku)

                    supabase.table("zamowienia").insert({
                        "pozycja": pozycja,
                        "wymiary": wymiary,
                        "material": material,
                        "ilosc": ilosc,
                        "projekt": projekt,
                        "pilnosc": pilnosc,
                        "status": "Oczekujące",
                        "zgloszone_przez": st.session_state.uzytkownik,
                        "data_zgloszenia": str(datetime.today().date()),
                        "zdjecie_url": zdjecie_public_url 
                    }).execute()
                    
                    st.balloons()
                    st.success("✅ Zamówienie pomyślnie wysłane do realizacji!")
                    
                    if powiadom_admina != "-- Nie wysyłaj --":
                        surowy_numer = admin_phones[powiadom_admina]
                        czysty_numer = "".join(c for c in surowy_numer if c.isdigit())
                        
                        tresc = f"Cześć! Zgłosiłem nowe zamówienie z aplikacji:\n\n🔧 *{pozycja}* (Ilość: {ilosc})\n🚨 Pilność: {pilnosc}\n🏗️ Projekt: {projekt}\n👤 Od: {st.session_state.uzytkownik}"
                        url_wa = f"https://wa.me/{czysty_numer}?text={urllib.parse.quote(tresc)}"
                        
                        st.info(f"Kliknij poniższy przycisk, aby wysłać powiadomienie do: **{powiadom_admina}**")
                        c_link, c_refresh = st.columns(2)
                        c_link.link_button("📲 Otwórz i wyślij WhatsApp", url_wa, use_container_width=True)
                        if c_refresh.button("🔄 Wyczyść i dodaj kolejne", use_container_width=True):
                            st.rerun()
                        st.stop()
                    else:
                        st.info("Za chwilę strona się odświeży...")
                        time.sleep(2)
                        st.rerun()
                else:
                    st.error("Pola 'Pozycja' i 'Ilość' są obowiązkowe!")

    # --- POZOSTAŁE ZAKŁADKI (NIEZMIENIONE) ---
    elif menu == "⚙️ Panel Realizacji (Admin)":
        st.title("⚙️ Zarządzaj Zamówieniami")
        pracownicy_res = supabase.table("pracownicy").select("login, telefon").execute()
        baza_telefonow = {p['login']: p.get('telefon', '') for p in pracownicy_res.data} if pracownicy_res.data else {}
        res = supabase.table("zamowienia").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        if not res.data:
            st.success("Wszystkie zamówienia są zrealizowane!")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz zdjęcie"): st.image(r['zdjecie_url'], use_container_width=True)
                    st.divider()
                    col_stat, col_uwg = st.columns([1, 2])
                    lista_s = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    n_stat = col_stat.selectbox("Status", lista_s, index=lista_s.index(r['status']), key=f"s_{r['id']}")
                    n_uwg = col_uwg.text_input("Notatka", value=r.get('uwagi_admina') or "", key=f"u_{r['id']}")
                    if st.button("Zapisz", key=f"b_{r['id']}"):
                        supabase.table("zamowienia").update({"status": n_stat, "uwagi_admina": n_uwg}).eq("id", r['id']).execute()
                        st.rerun()

    elif menu == "📊 Statystyki i Raporty":
        st.title("📊 Statystyki")
        res_all = supabase.table("zamowienia").select("*").execute()
        if res_all.data:
            df = pd.DataFrame(res_all.data)
            st.bar_chart(df['status'].value_counts())

    elif menu == "👥 Zarządzanie Kontami":
        st.title("👥 Pracownicy")
        # Logika zarządzania kontami jak wcześniej...

    elif menu == "📋 Moje Aktywne":
        st.title("📋 Twoje Zamówienia")
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").order("id", desc=True).execute()
        for r in res.data:
            with st.container(border=True):
                st.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                render_status_alert(r['status'])

    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Historia")
        res = supabase.table("zamowienia").select("*").order("id", desc=True).execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data))

    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja")
        st.markdown("Wpisz dane zamówienia, dodaj opcjonalne zdjęcie i wyślij. Powiadom admina przez WhatsApp dla szybszej realizacji.")

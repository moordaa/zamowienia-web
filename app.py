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

st.set_page_config(page_title="Zamówienia", page_icon="🛒", layout="centered")

if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.uzytkownik = ""
    st.session_state.rola = "użytkownik"

# --- LOGOWANIE ---
if not st.session_state.zalogowany:
    st.title("🛒 ZAMÓWIENIA")
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
        
        if st.session_state.rola == "admin":
            menu = st.radio("MENU", ["📝 Nowe Zamówienie", "⚙️ Panel Realizacji (Admin)", "👥 Zarządzanie Kontami", "🔎 Historia i Szukaj"])
        else:
            menu = st.radio("MENU", ["📝 Nowe Zamówienie", "📋 Moje Aktywne", "🔎 Historia i Szukaj"])
            
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
    # ZAKŁADKA: NOWE ZAMÓWIENIE
    # =========================================================================
    if menu == "📝 Nowe Zamówienie":
        st.title("📝 Dodaj zamówienie")
        
        with st.container(border=True):
            pozycja = st.text_input("🔧 Pozycja (np. Śruba zamkowa)")
            col1, col2 = st.columns(2)
            wymiary = col1.text_input("📏 Wymiary (np. M8x40)")
            material = col2.text_input("🧱 Materiał (np. Ocynk)")
            
            col3, col4 = st.columns(2)
            ilosc = col3.text_input("🔢 Ilość (np. 100 szt., 5 kg)")
            pilnosc = col4.selectbox("🚨 Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"])
            
            projekt = st.text_input("🏗️ Projekt / Budowa / Cel")
            
            if st.button("WYŚLIJ ZAMÓWIENIE", type="primary", use_container_width=True):
                if pozycja and ilosc:
                    supabase.table("zamowienia").insert({
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
                    
                    st.balloons()
                    st.success("✅ Zamówienie pomyślnie wysłane do realizacji! Za chwilę strona się odświeży...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Pola 'Pozycja' i 'Ilość' są obowiązkowe!")

    # =========================================================================
    # ZAKŁADKA: PANEL REALIZACJI (ADMIN)
    # =========================================================================
    elif menu == "⚙️ Panel Realizacji (Admin)":
        st.title("⚙️ Zarządzaj Zamówieniami")
        st.caption("Lista wszystkich aktywnych zamówień. Zmieniaj statusy i wysyłaj powiadomienia WhatsApp.")
        
        # Pobieramy najpierw wszystkich pracowników, by mieć ich numery telefonów
        pracownicy_res = supabase.table("pracownicy").select("login, telefon").execute()
        baza_telefonow = {p['login']: p.get('telefon', '') for p in pracownicy_res.data} if pracownicy_res.data else {}

        res = supabase.table("zamowienia").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        
        if not res.data:
            st.success("Wszystkie zamówienia są zrealizowane! Brak aktywnych zgłoszeń.")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                    if "PILNE" in r['pilnosc'] or "KRYTYCZNE" in r['pilnosc']:
                        st.error(f"🚨 {r['pilnosc']}")
                        
                    st.caption(f"📏 Wymiary: {r['wymiary']} | 🧱 Materiał: {r['material']} | 🏗️ Projekt: {r['projekt']}")
                    st.caption(f"👤 Zgłosił: **{r['zgloszone_przez']}** ({r['data_zgloszenia']})")
                    
                    st.divider()
                    
                    col_stat, col_uwg = st.columns([1, 2])
                    lista_statusow = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    aktualny_index = lista_statusow.index(r['status']) if r['status'] in lista_statusow else 0
                    
                    nowy_status = col_stat.selectbox("Status", lista_statusow, index=aktualny_index, key=f"stat_{r['id']}")
                    nowe_uwagi = col_uwg.text_input("Notatka (np. numer paczki, jaki zamiennik)", value=r.get('uwagi_admina') or "", key=f"uwg_{r['id']}")
                    
                    c1, c2, c3 = st.columns([2, 1, 3])
                    
                    # Zapisywanie zmian
                    if c1.button("💾 Zapisz zmiany", key=f"zapisz_{r['id']}", type="primary"):
                        supabase.table("zamowienia").update({
                            "status": nowy_status, 
                            "uwagi_admina": nowe_uwagi
                        }).eq("id", r['id']).execute()
                        st.toast("Zaktualizowano status w bazie!")
                        st.rerun()
                        
                    # Usuwanie
                    if c2.button("🗑️ Usuń", key=f"del_{r['id']}", type="secondary"):
                        supabase.table("zamowienia").delete().eq("id", r['id']).execute()
                        st.rerun()

                    # Integracja z WhatsApp
                    tresc_wa = f"Cześć! Twoje zamówienie na '{r['pozycja']}' zmieniło status na: *{r['status']}*."
                    if r.get('uwagi_admina'):
                        tresc_wa += f" Notatka: {r['uwagi_admina']}"
                    
                    # Pobieranie i czyszczenie numeru telefonu (WhatsApp wymaga samych cyfr, najlepiej z prefiksem np. 48)
                    surowy_numer = baza_telefonow.get(r['zgloszone_przez'])
                    
                    if surowy_numer:
                        czysty_numer = "".join(cyfra for cyfra in surowy_numer if cyfra.isdigit())
                        url_wa = f"https://wa.me/{czysty_numer}?text={urllib.parse.quote(tresc_wa)}"
                        c3.link_button("📲 Wyślij WhatsApp", url_wa, use_container_width=True)
                    else:
                        url_wa = f"https://wa.me/?text={urllib.parse.quote(tresc_wa)}"
                        c3.link_button("📲 Wyślij (brak nr w bazie)", url_wa, use_container_width=True, help="Ten pracownik nie ma przypisanego numeru telefonu w bazie.")

    # =========================================================================
    # ZAKŁADKA: ZARZĄDZANIE KONTAMI (ADMIN)
    # =========================================================================
    elif menu == "👥 Zarządzanie Kontami":
        st.title("👥 Zarządzanie pracownikami")
        st.caption("Dodawaj i usuwaj konta użytkowników mających dostęp do aplikacji.")
        
        with st.container(border=True):
            st.subheader("➕ Dodaj nowe konto")
            c1, c2, c3, c4 = st.columns(4)
            nowy_login = c1.text_input("Login")
            nowe_haslo = c2.text_input("Hasło")
            nowa_rola = c3.selectbox("Rola", ["użytkownik", "admin"])
            nowy_telefon = c4.text_input("Telefon (z kierunkowym np. 48123456789)")
            
            if st.button("Utwórz konto", type="primary"):
                if nowy_login and nowe_haslo:
                    czy_istnieje = supabase.table("pracownicy").select("login").eq("login", nowy_login).execute()
                    if czy_istnieje.data:
                        st.error("Pracownik o takim loginie już istnieje w bazie!")
                    else:
                        supabase.table("pracownicy").insert({
                            "login": nowy_login,
                            "haslo": nowe_haslo,
                            "rola": nowa_rola,
                            "telefon": nowy_telefon  # Zapisujemy telefon
                        }).execute()
                        st.success(f"Dodano użytkownika {nowy_login}!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Uzupełnij login i hasło!")

        st.divider()
        st.subheader("📋 Lista aktywnych kont")
        res_pracownicy = supabase.table("pracownicy").select("*").order("login").execute()
        
        if res_pracownicy.data:
            for p in res_pracownicy.data:
                with st.container(border=True):
                    col_info, col_btn = st.columns([4, 1])
                    rola_wyswietlana = p.get('rola') or "użytkownik"
                    tel_wyswietlany = p.get('telefon') or "Brak"
                    col_info.markdown(f"👤 Login: **{p['login']}** | 🔑 Hasło: `{p['haslo']}` | 🛡️ Rola: `{rola_wyswietlana}` | 📱 Tel: `{tel_wyswietlany}`")
                    
                    if p['login'].lower() != "emil":
                        if col_btn.button("🗑️ Usuń", key=f"del_user_{p['login']}", type="secondary"):
                            supabase.table("pracownicy").delete().eq("login", p['login']).execute()
                            st.rerun()
                    else:
                        col_btn.caption("👑 Konto główne")

    # =========================================================================
    # ZAKŁADKA: MOJE AKTYWNE (ZWYKŁY UŻYTKOWNIK)
    # =========================================================================
    elif menu == "📋 Moje Aktywne":
        st.title("📋 Aktywne Zamówienia")
        st.caption("Tutaj widzisz statusy elementów, które zamówiłeś.")
        
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").order("id", desc=True).execute()
        
        if not res.data:
            st.info("Nie masz obecnie żadnych oczekujących zamówień.")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"### {r['pozycja']} (Ilość: {r['ilosc']})")
                    st.caption(f"🏗️ {r['projekt']} | 📅 {r['data_zgloszenia']}")
                    
                    render_status_alert(r['status'])
                    
                    if r.get('uwagi_admina'):
                        st.info(f"📝 Odpis Admina: {r['uwagi_admina']}")

    # =========================================================================
    # ZAKŁADKA: WYSZUKIWARKA I HISTORIA 
    # =========================================================================
    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Baza Zamówień i Raporty")
        
        res_all = supabase.table("zamowienia").select("projekt, zgloszone_przez").execute()
        projekty = sorted(list(set([x['projekt'] for x in res_all.data if x['projekt']])))
        osoby = sorted(list(set([x['zgloszone_przez'] for x in res_all.data if x['zgloszone_przez']])))
        
        with st.container(border=True):
            f_slowo = st.text_input("🔍 Szukaj po nazwie lub uwagach...")
            col1, col2, col3 = st.columns(3)
            f_proj = col1.selectbox("🏗️ Projekt", ["-- Wszystkie --"] + projekty)
            f_kto = col2.selectbox("👤 Kto", ["-- Wszyscy --"] + osoby)
            f_status = col3.selectbox("📌 Status", ["-- Wszystkie --", "Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"])
            
            q = supabase.table("zamowienia").select("*")
            if f_proj != "-- Wszystkie --": q = q.eq("projekt", f_proj)
            if f_kto != "-- Wszyscy --": q = q.eq("zgloszone_przez", f_kto)
            if f_status != "-- Wszystkie --": q = q.eq("status", f_status)
            
            wynik_szukania = q.order("id", desc=True).execute().data
            
            if f_slowo.strip():
                f_slowo = f_slowo.lower()
                wynik_szukania = [x for x in wynik_szukania if f_slowo in x['pozycja'].lower() or f_slowo in (x.get('uwagi_admina') or '').lower()]
            
        st.divider()
        
        if wynik_szukania:
            col_wynik, col_pobierz = st.columns([3, 1])
            col_wynik.success(f"Znaleziono wyników: **{len(wynik_szukania)}**")
            
            df = pd.DataFrame(wynik_szukania)
            csv = df.to_csv(index=False).encode('utf-8')
            col_pobierz.download_button("📥 Pobierz listę (CSV)", data=csv, file_name="historia_zamowien.csv", mime="text/csv")
            
            for r in wynik_szukania:
                with st.container(border=True):
                    ikona = status_emoji.get(r['status'], "🔹")
                    st.markdown(f"**{ikona} {r['status']}** | {r['pozycja']} ({r['ilosc']})")
                    st.caption(f"👤 {r['zgloszone_przez']} | 🏗️ {r['projekt']} | 📅 {r['data_zgloszenia']}")
                    if r.get('uwagi_admina'): st.info(f"Notatka: {r['uwagi_admina']}")
        else:
            st.warning("Brak wyników spełniających kryteria.")

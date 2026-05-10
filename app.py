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

st.set_page_config(page_title="Zamówienia Pakamera", page_icon="🛒", layout="wide")

# --- STAN SESJI ---
if 'zalogowany' not in st.session_state:
    st.session_state.zalogowany = False
    st.session_state.uzytkownik = ""
    st.session_state.rola = "użytkownik"

# --- LOGOWANIE ---
if not st.session_state.zalogowany:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🛒 ZAMÓWIENIA")
        st.caption("System zarządzania materiałami")
        with st.container(border=True):
            l = st.text_input("Login")
            p = st.text_input("Hasło", type="password")
            if st.button("ZALOGUJ", use_container_width=True, type="primary"):
                # Wyjście awaryjne dla admina głównego
                if l == "Emil" and p == "Sosna100%":
                    st.session_state.zalogowany = True
                    st.session_state.uzytkownik = "Emil"
                    st.session_state.rola = "admin"
                    st.rerun()
                else:
                    # Sprawdzanie w bazie (używamy 'hasło' lub 'haslo' w zależności co masz w DB)
                    res = supabase.table("pracownicy").select("*").eq("login", l).execute()
                    if res.data:
                        user_data = res.data[0]
                        # Sprawdzamy hasło (obsługujemy obie wersje nazwy kolumny dla pewności)
                        db_password = user_data.get('hasło') or user_data.get('haslo')
                        if db_password == p:
                            st.session_state.zalogowany = True
                            st.session_state.uzytkownik = l
                            st.session_state.rola = user_data.get('rola') or "użytkownik"
                            st.rerun()
                        else:
                            st.error("Błędne hasło!")
                    else:
                        st.error("Użytkownik nie istnieje!")
else:
    # --- MENU BOCZNE ---
    with st.sidebar:
        st.success(f"Zalogowano: **{st.session_state.uzytkownik}**")
        st.divider()
        
        opcje = ["📝 Nowe Zamówienie", "📋 Moje Aktywne", "🔎 Historia i Szukaj", "📖 Instrukcja"]
        if st.session_state.rola == "admin":
            opcje.insert(1, "⚙️ Panel Realizacji (Admin)")
            opcje.insert(2, "📊 Statystyki i Raporty")
            opcje.insert(3, "👥 Zarządzanie Kontami")
        
        menu = st.radio("MENU", opcje)
            
        st.divider()
        if st.button("🔄 Odśwież dane", use_container_width=True):
            st.rerun()
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.zalogowany = False
            st.rerun()

    status_emoji = {"Oczekujące": "⏳", "Zamówione": "🚚", "Niedostępne": "❌", "Zamiennik": "🔄", "Zrealizowane": "✅"}

    def render_status_alert(status_text):
        ikona = status_emoji.get(status_text, "🔹")
        msg = f"**Status:** {ikona} {status_text}"
        if status_text == "Zrealizowane": st.success(msg)
        elif status_text in ["Niedostępne", "Zamiennik"]: st.error(msg)
        elif status_text == "Oczekujące": st.warning(msg)
        else: st.info(msg)

    # =========================================================================
    # ZAKŁADKA: NOWE ZAMÓWIENIE
    # =========================================================================
    if menu == "📝 Nowe Zamówienie":
        st.title("📝 Dodaj zamówienie")
        
        admins_res = supabase.table("pracownicy").select("login, telefon").eq("rola", "admin").execute()
        admin_phones = {a['login']: a['telefon'] for a in admins_res.data if a.get('telefon')}
        
        with st.container(border=True):
            pozycja = st.text_input("🔧 Pozycja (np. Śruba zamkowa)")
            col1, col2 = st.columns(2)
            wymiary = col1.text_input("📏 Wymiary (np. M8x40)")
            material = col2.text_input("🧱 Materiał (np. Ocynk)")
            col3, col4 = st.columns(2)
            ilosc = st.text_input("🔢 Ilość (np. 100 szt.)")
            pilnosc = col4.selectbox("🚨 Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"])
            projekt = st.text_input("🏗️ Projekt / Cel")

            st.divider()
            st.subheader("📸 Załącznik (Zdjęcie lub PDF)")
            zal_col1, zal_col2 = st.columns(2)
            zdjecie_cam = None
            if zal_col1.toggle("📷 Użyj aparatu"):
                zdjecie_cam = st.camera_input("Zrób zdjęcie")
            plik_upload = zal_col2.file_uploader("📁 Wybierz plik", type=["jpg", "jpeg", "png", "pdf"])

            st.divider()
            opcje_wa = ["-- Nie wysyłaj --"] + list(admin_phones.keys())
            powiadom = st.selectbox("📲 Powiadom admina (WhatsApp):", opcje_wa)
            
            if st.button("WYŚLIJ ZAMÓWIENIE", type="primary", use_container_width=True):
                if pozycja and ilosc:
                    url_zdj = ""
                    final_file = None
                    ext = "jpg"
                    if zdjecie_cam:
                        final_file = zdjecie_cam.getvalue()
                    elif plik_upload:
                        final_file = plik_upload.getvalue()
                        ext = plik_upload.name.split('.')[-1]

                    if final_file:
                        nazwa = f"{int(time.time())}_{st.session_state.uzytkownik}.{ext}"
                        c_type = "application/pdf" if ext.lower() == "pdf" else "image/jpeg"
                        supabase.storage.from_("zdjecia_zamowien").upload(nazwa, final_file, {"content-type": c_type})
                        url_zdj = supabase.storage.from_("zdjecia_zamowien").get_public_url(nazwa)

                    supabase.table("zamowienia").insert({
                        "pozycja": pozycja, "wymiary": wymiary, "material": material, "ilosc": ilosc, 
                        "projekt": projekt, "pilnosc": pilnosc, "status": "Oczekujące", 
                        "zgloszone_przez": st.session_state.uzytkownik, "data_zgloszenia": str(datetime.today().date()),
                        "zdjecie_url": url_zdj
                    }).execute()
                    
                    st.success("Wysłano pomyślnie!")
                    if powiadom != "-- Nie wysyłaj --":
                        nr = "".join(c for c in admin_phones[powiadom] if c.isdigit())
                        t = f"Nowe zamówienie: {pozycja}. Od: {st.session_state.uzytkownik}"
                        st.link_button("📲 Wyślij WhatsApp", f"https://wa.me/{nr}?text={urllib.parse.quote(t)}", use_container_width=True)
                    else:
                        time.sleep(1.5); st.rerun()
                else:
                    st.error("Wypełnij wymagane pola!")

    # =========================================================================
    # ZAKŁADKA: PANEL REALIZACJI (ADMIN)
    # =========================================================================
    elif menu == "⚙️ Panel Realizacji (Admin)":
        st.title("⚙️ Zarządzanie realizacją")
        prac_res = supabase.table("pracownicy").select("login, telefon").execute()
        tels = {p['login']: p.get('telefon', '') for p in prac_res.data}
        
        res = supabase.table("zamowienia").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        if not res.data: st.success("Wszystko zrealizowane!")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.subheader(f"{r['pozycja']} ({r['ilosc']})")
                    if r.get('zdjecie_url'):
                        if r['zdjecie_url'].lower().endswith(".pdf"):
                            st.link_button("📄 Otwórz PDF", r['zdjecie_url'])
                        else:
                            with st.expander("🖼️ Zobacz zdjęcie"): st.image(r['zdjecie_url'], use_container_width=True)
                    
                    col1, col2 = st.columns([1, 2])
                    st_list = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    n_st = col1.selectbox("Status", st_list, index=st_list.index(r['status']), key=f"st_{r['id']}")
                    n_uw = col2.text_input("Notatka", value=r.get('uwagi_admina') or "", key=f"uw_{r['id']}")
                    
                    c_s, c_d, c_w = st.columns([1, 1, 2])
                    if c_s.button("💾 Zapisz", key=f"s_{r['id']}", type="primary"):
                        supabase.table("zamowienia").update({"status": n_st, "uwagi_admina": n_uw}).eq("id", r['id']).execute()
                        st.rerun()
                    if c_d.button("🗑️ Usuń", key=f"d_{r['id']}"):
                        supabase.table("zamowienia").delete().eq("id", r['id']).execute(); st.rerun()
                    
                    tel = tels.get(r['zgloszone_przez'])
                    if tel:
                        nr_c = "".join(c for c in tel if c.isdigit())
                        msg = f"Status {r['pozycja']}: {n_st}. {n_uw}"
                        c_w.link_button("📲 Wyślij WA", f"https://wa.me/{nr_c}?text={urllib.parse.quote(msg)}", use_container_width=True)

    # =========================================================================
    # ZAKŁADKA: ZARZĄDZANIE KONTAMI (Z WYŚWIETLANIEM HASŁA)
    # =========================================================================
    elif menu == "👥 Zarządzanie Kontami":
        st.title("👥 Zarządzanie pracownikami")
        
        with st.container(border=True):
            st.subheader("➕ Dodaj nowe konto")
            c1, c2, c3, c4 = st.columns(4)
            n_log = c1.text_input("Login")
            n_has = c2.text_input("Hasło") # Tu wpisujemy hasło dla nowego pracownika
            n_rol = c3.selectbox("Rola", ["użytkownik", "admin"])
            n_tel = c4.text_input("Telefon (np. 48123456789)")
            if st.button("Utwórz konto", type="primary"):
                if n_log and n_has:
                    # Zapisujemy do bazy pod Twoją nazwą kolumny 'hasło'
                    supabase.table("pracownicy").insert({"login": n_log, "hasło": n_has, "rola": n_rol, "telefon": n_tel}).execute()
                    st.success(f"Dodano: {n_log}"); time.sleep(1); st.rerun()
                else:
                    st.error("Login i Hasło są obowiązkowe!")

        st.divider()
        st.subheader("📋 Lista pracowników")
        res_p = supabase.table("pracownicy").select("*").order("login").execute()
        
        if not res_p.data:
            st.info("Baza pracowników jest pusta.")
        else:
            for p in res_p.data:
                if not p.get('login'): continue
                
                with st.container(border=True):
                    col_i, col_b = st.columns([5, 1])
                    
                    # POBIERANIE HASŁA (próbuje 'hasło' lub 'haslo')
                    haslo_widoczne = p.get('hasło') or p.get('haslo') or "???"
                    rola_p = p.get('rola') or "użytkownik"
                    
                    # WYŚWIETLANIE (Teraz z hasłem!)
                    col_i.markdown(f"👤 **{p['login']}** | 🔑 Hasło: `{haslo_widoczne}` | 🛠️ Rola: `{rola_p}` | 📞 Tel: `{p.get('telefon','')}`")
                    
                    if p['login'].lower() != "emil":
                        if col_b.button("🗑️ Usuń", key=f"dp_{p['login']}"):
                            supabase.table("pracownicy").delete().eq("login", p['login']).execute(); st.rerun()

    # =========================================================================
    # RESZTA FUNKCJI (STATYSTYKI, HISTORIA)
    # =========================================================================
    elif menu == "📊 Statystyki i Raporty":
        st.title("📊 Statystyki")
        res = supabase.table("zamowienia").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.bar_chart(df['projekt'].value_counts())
        else:
            st.info("Brak danych.")

    elif menu == "📋 Moje Aktywne":
        st.title("📋 Twoje zamówienia")
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").execute()
        if not res.data: st.info("Brak aktywnych zamówień.")
        for r in res.data:
            with st.container(border=True):
                st.subheader(f"{r['pozycja']}")
                render_status_alert(r['status'])

    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Historia")
        res = supabase.table("zamowienia").select("*").order("id", desc=True).execute()
        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)

    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja")
        st.write("W zakładce Zarządzanie Kontami widzisz hasła wszystkich pracowników.")

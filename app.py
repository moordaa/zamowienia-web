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
                if l == "Emil" and p == "Sosna100%":
                    st.session_state.zalogowany = True
                    st.session_state.uzytkownik = "Emil"
                    st.session_state.rola = "admin"
                    st.rerun()
                else:
                    res = supabase.table("pracownicy").select("*").eq("login", l).execute()
                    if res.data:
                        user_data = res.data[0]
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
        pracownicy_dict = {p['login']: p.get('telefon', '') for p in prac_res.data}
        
        res = supabase.table("zamowienia").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        
        if not res.data:
            st.success("Wszystkie zamówienia zrealizowane! 👏")
        else:
            for r in res.data:
                # DODANO: Wyraźne obramowanie i wyróżniający się niebieski nagłówek dla każdego zamówienia
                with st.container(border=True):
                    st.info(f"### 📦 {r['pozycja'].upper()}\n**Zgłosił(a):** {r['zgloszone_przez']} | **Data:** {r['data_zgloszenia']}")
                    
                    c_info1, c_info2, c_info3 = st.columns(3)
                    c_info1.write(f"**Ilość:** {r['ilosc']}")
                    c_info1.write(f"**Wymiary:** {r.get('wymiary') or '---'}")
                    c_info2.write(f"**Materiał:** {r.get('material') or '---'}")
                    c_info2.write(f"**Projekt:** {r.get('projekt') or '---'}")
                    c_info3.write(f"**Pilność:** {r.get('pilnosc') or 'Normalna'}")
                    c_info3.write(f"**Status:** {r['status']}")

                    if r.get('zdjecie_url'):
                        if r['zdjecie_url'].lower().endswith(".pdf"):
                            st.link_button("📄 Otwórz Załącznik PDF", r['zdjecie_url'])
                        else:
                            with st.expander("🖼️ Zobacz zdjęcie"):
                                st.image(r['zdjecie_url'], use_container_width=True)

                    st.divider()

                    # EDYCJA
                    with st.expander("✏️ Edytuj dane zamówienia"):
                        e_col1, e_col2 = st.columns(2)
                        up_poz = e_col1.text_input("Nazwa pozycji", value=r['pozycja'], key=f"edit_poz_{r['id']}")
                        up_ilo = e_col2.text_input("Ilość", value=r['ilosc'], key=f"edit_ilo_{r['id']}")
                        up_wym = e_col1.text_input("Wymiary", value=r.get('wymiary',''), key=f"edit_wym_{r['id']}")
                        up_mat = e_col2.text_input("Materiał", value=r.get('material',''), key=f"edit_mat_{r['id']}")
                        up_pro = e_col1.text_input("Projekt", value=r.get('projekt',''), key=f"edit_pro_{r['id']}")
                        up_pil = e_col2.selectbox("Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"], 
                                                 index=["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"].index(r.get('pilnosc','Normalna')), 
                                                 key=f"edit_pil_{r['id']}")
                        
                        if st.button("💾 Zapisz poprawki danych", key=f"btn_edit_{r['id']}", use_container_width=True):
                            supabase.table("zamowienia").update({
                                "pozycja": up_poz, "ilosc": up_ilo, "wymiary": up_wym, 
                                "material": up_mat, "projekt": up_pro, "pilnosc": up_pil
                            }).eq("id", r['id']).execute()
                            st.success("Dane zaktualizowane!")
                            time.sleep(1); st.rerun()

                    # STATUS 
                    st.divider()
                    col_st1, col_st2 = st.columns([1, 2])
                    st_list = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    n_st = col_st1.selectbox("Zmień status", st_list, index=st_list.index(r['status']), key=f"st_sel_{r['id']}")
                    n_uw = col_st2.text_input("Notatka dla pracowników", value=r.get('uwagi_admina') or "", key=f"uw_inp_{r['id']}")
                    
                    c_act1, c_act2 = st.columns([1, 1])
                    if c_act1.button("✅ Zapisz status", key=f"save_st_{r['id']}", type="primary", use_container_width=True):
                        supabase.table("zamowienia").update({"status": n_st, "uwagi_admina": n_uw}).eq("id", r['id']).execute()
                        st.toast("Status zapisany pomyślnie!")
                        time.sleep(0.5); st.rerun()

                    if c_act2.button("🗑️ Usuń zamówienie", key=f"del_{r['id']}", use_container_width=True):
                        supabase.table("zamowienia").delete().eq("id", r['id']).execute()
                        st.rerun()

                    # POWIADOMIENIA WHATSAPP (Teraz bezpieczne w expanderze - zawsze dostępne!)
                    with st.expander("📲 Powiadomienia WhatsApp (Wyślij po zapisaniu statusu)"):
                        st.write("Wybierz dodatkowe osoby, które chcesz powiadomić:")
                        wszyscy_pracownicy = list(pracownicy_dict.keys())
                        zainteresowani = st.multiselect("Dodatkowi pracownicy:", wszyscy_pracownicy, key=f"multi_{r['id']}")
                        
                        # Wiadomość generuje się na podstawie tego, co jest aktualnie wybrane w oknach
                        msg = f"Aktualizacja zamów

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
    # ZAKŁADKA: PANEL REALIZACJI (ADMIN) -> ZWARTSZA WERSJA
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
                with st.container(border=True):
                    # 1. Zwarty Nagłówek i Informacje
                    st.markdown(f"### 📦 {r['pozycja'].upper()} `x {r['ilosc']}`")
                    st.markdown(f"👤 **Zgłosił(a):** `{r['zgloszone_przez']}` ({r['data_zgloszenia']}) | 🏗️ **Projekt:** `{r.get('projekt') or '-'}` | 🚨 **Pilność:** `{r.get('pilnosc') or 'Normalna'}`")
                    st.caption(f"📏 Wymiary: {r.get('wymiary') or '-'} | 🧱 Materiał: {r.get('material') or '-'} | 📌 Aktualny status: **{r['status']}**")
                    
                    # 2. Narzędzia Statusu (w jednej linii)
                    c_st, c_uw, c_zap = st.columns([2, 4, 1])
                    st_list = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    n_st = c_st.selectbox("Status", st_list, index=st_list.index(r['status']), key=f"st_sel_{r['id']}", label_visibility="collapsed")
                    n_uw = c_uw.text_input("Notatka", value=r.get('uwagi_admina') or "", key=f"uw_inp_{r['id']}", placeholder="Dodaj krótką notatkę...", label_visibility="collapsed")
                    
                    if c_zap.button("💾 Zapisz", key=f"save_{r['id']}", type="primary", use_container_width=True):
                        supabase.table("zamowienia").update({"status": n_st, "uwagi_admina": n_uw}).eq("id", r['id']).execute()
                        st.toast("Status zaktualizowany!")
                        time.sleep(0.5); st.rerun()

                    # 3. Przyciski Akcji (WhatsApp, Edycja, Zdjęcie) - na dole, w małych bloczkach
                    b1, b2, b3, b4 = st.columns([2, 2, 1, 1])
                    
                    msg = f"Aktualizacja: {r['pozycja']} | Status: {n_st} | Uwagi: {n_uw}"
                    tel_zgl = pracownicy_dict.get(r['zgloszone_przez'], '')
                    
                    # -> Główny guzik dla Zgłaszającego
                    if tel_zgl:
                        nr_zgl = "".join(filter(str.isdigit, tel_zgl))
                        b1.link_button(f"📲 WA Zgłaszający ({r['zgloszone_przez']})", f"https://wa.me/{nr_zgl}?text={urllib.parse.quote(msg)}", use_container_width=True)
                    else:
                        b1.button(f"❌ Brak Tel ({r['zgloszone_przez']})", disabled=True, key=f"b_tel_{r['id']}", use_container_width=True)
                    
                    # -> Opcjonalne dodatkowe powiadomienia (Wyskakujące)
                    with b2.popover("➕ WA Dodatkowo"):
                        zaint = st.multiselect("Wybierz kogo powiadomić:", [k for k in pracownicy_dict.keys() if k != r['zgloszone_przez']], key=f"multi_{r['id']}")
                        for os in zaint:
                            tel_os = pracownicy_dict.get(os, '')
                            if tel_os:
                                nr_os = "".join(filter(str.isdigit, tel_os))
                                st.link_button(f"Wyślij do: {os}", f"https://wa.me/{nr_os}?text={urllib.parse.quote(msg)}", use_container_width=True)

                    # -> Edycja (Wyskakujące okienko)
                    with b3.popover("⚙️ Edycja"):
                        up_poz = st.text_input("Pozycja", value=r['pozycja'], key=f"ep_{r['id']}")
                        up_ilo = st.text_input("Ilość", value=r['ilosc'], key=f"ei_{r['id']}")
                        up_wym = st.text_input("Wymiary", value=r.get('wymiary',''), key=f"ew_{r['id']}")
                        up_mat = st.text_input("Materiał", value=r.get('material',''), key=f"em_{r['id']}")
                        up_pro = st.text_input("Projekt", value=r.get('projekt',''), key=f"ej_{r['id']}")
                        up_pil = st.selectbox("Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"], index=["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"].index(r.get('pilnosc','Normalna')), key=f"epi_{r['id']}")
                        if st.button("Zapisz", key=f"btn_edit_{r['id']}", type="primary", use_container_width=True):
                            supabase.table("zamowienia").update({"pozycja": up_poz, "ilosc": up_ilo, "wymiary": up_wym, "material": up_mat, "projekt": up_pro, "pilnosc": up_pil}).eq("id", r['id']).execute()
                            st.rerun()
                        st.divider()
                        if st.button("🗑️ Usuń", key=f"del_{r['id']}", use_container_width=True):
                            supabase.table("zamowienia").delete().eq("id", r['id']).execute()
                            st.rerun()

                    # -> Podgląd Załącznika
                    if r.get('zdjecie_url'):
                        if r['zdjecie_url'].lower().endswith(".pdf"):
                            b4.link_button("📄 PDF", r['zdjecie_url'], use_container_width=True)
                        else:
                            with b4.popover("🖼️ Foto"):
                                st.image(r['zdjecie_url'], use_container_width=True)
                    else:
                        b4.button("Brak 🖼️", disabled=True, key=f"no_pic_{r['id']}", use_container_width=True)

    # =========================================================================
    # ZAKŁADKA: ZARZĄDZANIE KONTAMI
    # =========================================================================
    elif menu == "👥 Zarządzanie Kontami":
        st.title("👥 Zarządzanie pracownikami")
        with st.container(border=True):
            st.subheader("➕ Dodaj nowe konto")
            c1, c2, c3, c4 = st.columns(4)
            n_log = c1.text_input("Login")
            n_has = c2.text_input("Hasło") 
            n_rol = c3.selectbox("Rola", ["użytkownik", "admin"])
            n_tel = c4.text_input("Telefon (np. 48123456789)")
            if st.button("Utwórz konto", type="primary"):
                if n_log and n_has:
                    supabase.table("pracownicy").insert({"login": n_log, "haslo": n_has, "rola": n_rol, "telefon": n_tel}).execute()
                    st.success(f"Dodano: {n_log}"); time.sleep(1); st.rerun()
                else:
                    st.error("Login i Hasło są obowiązkowe!")

        st.divider()
        res_p = supabase.table("pracownicy").select("*").order("login").execute()
        for p in res_p.data:
            if not p.get('login'): continue
            with st.container(border=True):
                col_i, col_b = st.columns([5, 1])
                haslo_widoczne = p.get('hasło') or p.get('haslo') or "???"
                col_i.markdown(f"👤 **{p['login']}** | 🔑 Hasło: `{haslo_widoczne}` | 🛠️ Rola: `{p.get('rola')}` | 📞 Tel: `{p.get('telefon','')}`")
                if p['login'].lower() != "emil":
                    if col_b.button("🗑️ Usuń", key=f"dp_{p['login']}"):
                        supabase.table("pracownicy").delete().eq("login", p['login']).execute(); st.rerun()

    # =========================================================================
    # RESZTA FUNKCJI
    # =========================================================================
    elif menu == "📊 Statystyki i Raporty":
        st.title("📊 Statystyki")
        res = supabase.table("zamowienia").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.bar_chart(df['projekt'].value_counts())
        else: st.info("Brak danych.")

    elif menu == "📋 Moje Aktywne":
        st.title("📋 Twoje zamówienia")
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").execute()
        if not res.data: st.info("Brak aktywnych zamówień.")
        for r in res.data:
            with st.container(border=True):
                st.markdown(f"### 📦 {r['pozycja'].upper()} `x {r['ilosc']}`")
                render_status_alert(r['status'])
                if r.get('uwagi_admina'): st.info(f"Odpis Admina: {r['uwagi_admina']}")

    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Historia")
        res = supabase.table("zamowienia").select("*").order("id", desc=True).execute()
        if res.data: st.dataframe(pd.DataFrame(res.data), use_container_width=True)

    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja")
        st.write("Panel admina pozwala na edycję wszystkich danych zamówienia i wysyłkę powiadomień do wielu osób.")

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
                with st.container(border=True):
                    st.markdown(f"### 📦 {r['pozycja'].upper()} `x {r['ilosc']}`")
                    st.markdown(f"👤 `{r['zgloszone_przez']}` | 🏗️ `{r.get('projekt') or '-'}` | 🚨 `{r.get('pilnosc') or 'Normalna'}` | 📏 `{r.get('wymiary') or '-'}`")
                    
                    c_st, c_uw, c_zap = st.columns([2, 4, 1])
                    st_list = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    n_st = c_st.selectbox("Status", st_list, index=st_list.index(r['status']), key=f"st_sel_{r['id']}", label_visibility="collapsed")
                    n_uw = c_uw.text_input("Notatka", value=r.get('uwagi_admina') or "", key=f"uw_inp_{r['id']}", placeholder="Dodaj notatkę...", label_visibility="collapsed")
                    
                    if c_zap.button("💾 Zapisz", key=f"save_{r['id']}", type="primary", use_container_width=True):
                        u_data = {"status": n_st, "uwagi_admina": n_uw}
                        if n_st == "Zrealizowane":
                            u_data["data_realizacji"] = str(datetime.today().date())
                        else:
                            u_data["data_realizacji"] = None
                        
                        supabase.table("zamowienia").update(u_data).eq("id", r['id']).execute()
                        st.toast("Zapisano!")
                        time.sleep(0.5); st.rerun()

                    b1, b2, b3, b4 = st.columns([2, 2, 1, 1])
                    msg = f"Aktualizacja: {r['pozycja']} | Status: {n_st} | Uwagi: {n_uw}"
                    tel_zgl = pracownicy_dict.get(r['zgloszone_przez'], '')
                    
                    if tel_zgl:
                        nr_zgl = "".join(filter(str.isdigit, tel_zgl))
                        b1.link_button(f"📲 WA: {r['zgloszone_przez']}", f"https://wa.me/{nr_zgl}?text={urllib.parse.quote(msg)}", use_container_width=True)
                    else:
                        b1.button(f"⚠️ {r['zgloszone_przez']} (Brak Tel)", disabled=True, use_container_width=True)
                    
                    with b2.popover("➕ WA Inni"):
                        st.write("Wybierz osoby do powiadomienia:")
                        lista_opcji = [k for k in pracownicy_dict.keys() if k != r['zgloszone_przez']]
                        zaint = st.multiselect("Dodaj osoby:", lista_opcji, key=f"multi_{r['id']}")
                        for os in zaint:
                            t_os = pracownicy_dict.get(os, '')
                            if t_os:
                                n_os = "".join(filter(str.isdigit, t_os))
                                st.link_button(f"Wyślij do: {os}", f"https://wa.me/{n_os}?text={urllib.parse.quote(msg)}", use_container_width=True)

                    with b3.popover("⚙️ Akcje"):
                        up_poz = st.text_input("Pozycja", value=r['pozycja'], key=f"ep_{r['id']}")
                        up_ilo = st.text_input("Ilość", value=r['ilosc'], key=f"ei_{r['id']}")
                        up_wym = st.text_input("Wymiary", value=r.get('wymiary',''), key=f"ew_{r['id']}")
                        up_mat = st.text_input("Materiał", value=r.get('material',''), key=f"em_{r['id']}")
                        up_pro = st.text_input("Projekt", value=r.get('projekt',''), key=f"ej_{r['id']}")
                        up_pil = st.selectbox("Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"], index=["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"].index(r.get('pilnosc','Normalna')), key=f"epi_{r['id']}")
                        if st.button("Zapisz zmiany", key=f"btn_edit_{r['id']}", type="primary", use_container_width=True):
                            supabase.table("zamowienia").update({"pozycja": up_poz, "ilosc": up_ilo, "wymiary": up_wym, "material": up_mat, "projekt": up_pro, "pilnosc": up_pil}).eq("id", r['id']).execute()
                            st.rerun()
                        st.divider()
                        if st.button("🗑️ Usuń trwale", key=f"del_{r['id']}", use_container_width=True):
                            supabase.table("zamowienia").delete().eq("id", r['id']).execute()
                            st.rerun()

                    if r.get('zdjecie_url'):
                        if r['zdjecie_url'].lower().endswith(".pdf"):
                            b4.link_button("📄 PDF", r['zdjecie_url'], use_container_width=True)
                        else:
                            with b4.popover("🖼️ FOTO"):
                                st.image(r['zdjecie_url'], use_container_width=True)
                    else:
                        b4.button("❌ 🖼️", disabled=True, use_container_width=True)

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
                col_info, col_edit, col_del = st.columns([4, 1, 1])
                aktualne_haslo = p.get('hasło') or p.get('haslo') or ""
                haslo_widoczne = aktualne_haslo if aktualne_haslo else "???"
                if p['login'].lower() == "emil" and st.session_state.uzytkownik.lower() != "emil":
                    haslo_widoczne = "••••••••"
                col_info.markdown(f"👤 **{p['login']}** | 🔑 Hasło: `{haslo_widoczne}` | 🛠️ Rola: `{p.get('rola')}` | 📞 Tel: `{p.get('telefon','')}`")
                
                with col_edit.popover("✏️ Edytuj"):
                    e_has = st.text_input("Nowe hasło", value=aktualne_haslo, key=f"eh_{p['login']}")
                    e_tel = st.text_input("Nowy telefon", value=p.get('telefon') or "", key=f"et_{p['login']}")
                    e_rol = st.selectbox("Rola", ["użytkownik", "admin"], index=0 if p.get('rola') == 'użytkownik' else 1, key=f"er_{p['login']}")
                    if st.button("💾 Zapisz", key=f"es_{p['login']}", type="primary", use_container_width=True):
                        supabase.table("pracownicy").update({"haslo": e_has, "telefon": e_tel, "rola": e_rol}).eq("login", p['login']).execute()
                        st.toast(f"Zapisano zmiany dla {p['login']}")
                        time.sleep(0.5); st.rerun()

                if p['login'].lower() != "emil":
                    if col_del.button("🗑️ Usuń", key=f"dp_{p['login']}", use_container_width=True):
                        supabase.table("pracownicy").delete().eq("login", p['login']).execute(); st.rerun()

    # =========================================================================
    # ZAKŁADKA: HISTORIA I SZUKAJ (PRZYWRÓCONA PEŁNA WERSJA)
    # =========================================================================
    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Pełna baza zamówień")
        
        # Pobieranie danych do filtrów
        res_all = supabase.table("zamowienia").select("projekt, zgloszone_przez").execute()
        projekty = sorted(list(set([x['projekt'] for x in res_all.data if x.get('projekt')])))
        osoby = sorted(list(set([x['zgloszone_przez'] for x in res_all.data if x.get('zgloszone_przez')])))
        
        with st.container(border=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            f_slowo = f_col1.text_input("🔍 Szukaj nazwy...")
            f_proj = f_col2.selectbox("🏗️ Projekt", ["-- Wszystkie --"] + projekty)
            f_kto = f_col3.selectbox("👤 Kto zgłosił", ["-- Wszyscy --"] + osoby)
            f_status = f_col4.selectbox("📌 Status", ["-- Wszystkie --", "Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"])
            
            q = supabase.table("zamowienia").select("*")
            if f_proj != "-- Wszystkie --": q = q.eq("projekt", f_proj)
            if f_kto != "-- Wszyscy --": q = q.eq("zgloszone_przez", f_kto)
            if f_status != "-- Wszystkie --": q = q.eq("status", f_status)
            
            wynik = q.order("id", desc=True).execute().data
            if f_slowo:
                wynik = [x for x in wynik if f_slowo.lower() in x['pozycja'].lower()]

        if wynik:
            st.caption(f"Znaleziono: {len(wynik)} zamówień")
            # Przycisk pobierania Excela
            df_export = pd.DataFrame(wynik)
            st.download_button("📥 Pobierz historię (CSV)", df_export.to_csv(index=False).encode('utf-8-sig'), "historia.csv", "text/csv")
            
            for r in wynik:
                with st.container(border=True):
                    # Nagłówek karty historii
                    h_col1, h_col2 = st.columns([4, 1])
                    h_col1.markdown(f"### 📦 {r['pozycja'].upper()} `x {r['ilosc']}`")
                    
                    ikona = status_emoji.get(r['status'], "🔹")
                    h_col2.markdown(f"**{ikona} {r['status']}**")
                    
                    # Dane szczegółowe w historii
                    d_col1, d_col2, d_col3 = st.columns(3)
                    d_col1.markdown(f"**📅 Zgłoszono:** `{r['data_zgloszenia']}`")
                    d_col1.markdown(f"**📅 Realizacja:** `{r.get('data_realizacji') or '---'}`")
                    
                    d_col2.markdown(f"**🏗️ Projekt:** {r.get('projekt') or '---'}")
                    d_col2.markdown(f"**👤 Zgłosił:** {r['zgloszone_przez']}")
                    
                    d_col3.markdown(f"**📏 Wymiary:** {r.get('wymiary') or '---'}")
                    d_col3.markdown(f"**🧱 Materiał:** {r.get('material') or '---'}")
                    
                    if r.get('uwagi_admina'):
                        st.info(f"**💬 Notatka admina:** {r['uwagi_admina']}")
                    
                    # Załącznik w historii
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz załącznik"):
                            if r['zdjecie_url'].lower().endswith(".pdf"):
                                st.link_button("📄 Otwórz PDF", r['zdjecie_url'])
                            else:
                                st.image(r['zdjecie_url'], use_container_width=True)
        else:
            st.info("Nie znaleziono zamówień spełniających kryteria.")

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

    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja")
        st.write("Historia została przywrócona do pełnej, czytelnej formy z filtrami i pełnymi danymi.")

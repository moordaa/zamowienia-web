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
                "📖 Instrukcja" # Dodano do menu Admina
            ])
        else:
            menu = st.radio("MENU", [
                "📝 Nowe Zamówienie", 
                "📋 Moje Aktywne", 
                "🔎 Historia i Szukaj",
                "📖 Instrukcja" # Dodano do menu Użytkownika
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
    # ZAKŁADKA: NOWE ZAMÓWIENIE
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
                        if zdjecie_public_url:
                            tresc += f"\n📷 Zdjęcie: {zdjecie_public_url}"
                            
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

    # =========================================================================
    # ZAKŁADKA: PANEL REALIZACJI (ADMIN)
    # =========================================================================
    elif menu == "⚙️ Panel Realizacji (Admin)":
        st.title("⚙️ Zarządzaj Zamówieniami")
        st.caption("Lista aktywnych zamówień. Możesz edytować statusy, dane zamówienia i wysyłać WhatsApp.")
        
        pracownicy_res = supabase.table("pracownicy").select("login, telefon").execute()
        baza_telefonow = {p['login']: p.get('telefon', '') for p in pracownicy_res.data} if pracownicy_res.data else {}

        res = supabase.table("zamowienia").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        
        if not res.data:
            st.success("Wszystkie zamówienia są zrealizowane!")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                    if "PILNE" in r['pilnosc'] or "KRYTYCZNE" in r['pilnosc']:
                        st.error(f"🚨 {r['pilnosc']}")
                    st.caption(f"📏 Wymiary: {r['wymiary']} | 🧱 Materiał: {r['material']} | 🏗️ Projekt: {r['projekt']}")
                    st.caption(f"👤 Zgłosił: **{r['zgloszone_przez']}** ({r['data_zgloszenia']})")
                    
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz załączone zdjęcie"):
                            st.image(r['zdjecie_url'], use_container_width=True)
                            
                    with st.expander("✏️ Edytuj szczegóły zamówienia"):
                        e_col1, e_col2 = st.columns(2)
                        edit_pozycja = e_col1.text_input("Pozycja", value=r['pozycja'], key=f"epoz_{r['id']}")
                        edit_ilosc = e_col2.text_input("Ilość", value=r['ilosc'], key=f"eilo_{r['id']}")
                        e_col3, e_col4 = st.columns(2)
                        edit_wymiary = e_col3.text_input("Wymiary", value=r['wymiary'] or "", key=f"ewym_{r['id']}")
                        edit_material = e_col4.text_input("Materiał", value=r['material'] or "", key=f"emat_{r['id']}")
                        e_col5, e_col6 = st.columns(2)
                        edit_projekt = e_col5.text_input("Projekt", value=r['projekt'] or "", key=f"eproj_{r['id']}")
                        pilnosci_lista = ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"]
                        akt_pilnosc = r['pilnosc'] if r['pilnosc'] in pilnosci_lista else "Normalna"
                        idx_pilnosc = pilnosci_lista.index(akt_pilnosc)
                        edit_pilnosc = e_col6.selectbox("Pilność", pilnosci_lista, index=idx_pilnosc, key=f"epil_{r['id']}")
                        if st.button("💾 Zapisz poprawki", key=f"esave_{r['id']}", type="primary"):
                            supabase.table("zamowienia").update({
                                "pozycja": edit_pozycja, "ilosc": edit_ilosc, "wymiary": edit_wymiary, 
                                "material": edit_material, "projekt": edit_projekt, "pilnosc": edit_pilnosc
                            }).eq("id", r['id']).execute()
                            st.success("Zapisano zmiany!")
                            time.sleep(1)
                            st.rerun()
                    
                    st.divider()
                    col_stat, col_uwg = st.columns([1, 2])
                    lista_statusow = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    aktualny_index = lista_statusow.index(r['status']) if r['status'] in lista_statusow else 0
                    nowy_status = col_stat.selectbox("Status", lista_statusow, index=aktualny_index, key=f"stat_{r['id']}")
                    nowe_uwagi = col_uwg.text_input("Notatka", value=r.get('uwagi_admina') or "", key=f"uwg_{r['id']}")
                    
                    c1, c2, c3 = st.columns([2, 1, 3])
                    if c1.button("💾 Zapisz status", key=f"zapisz_{r['id']}", type="primary"):
                        supabase.table("zamowienia").update({"status": nowy_status, "uwagi_admina": nowe_uwagi}).eq("id", r['id']).execute()
                        st.toast("Zaktualizowano status!")
                        st.rerun()
                    if c2.button("🗑️ Usuń", key=f"del_{r['id']}", type="secondary"):
                        supabase.table("zamowienia").delete().eq("id", r['id']).execute()
                        st.rerun()
                    surowy_numer = baza_telefonow.get(r['zgloszone_przez'])
                    if surowy_numer:
                        czysty_numer = "".join(cyfra for cyfra in surowy_numer if cyfra.isdigit())
                        tresc_wa = f"Cześć! Twoje zamówienie na '{r['pozycja']}' zmieniło status na: *{r['status']}*."
                        url_wa = f"https://wa.me/{czysty_numer}?text={urllib.parse.quote(tresc_wa)}"
                        c3.link_button("📲 Wyślij WhatsApp", url_wa, use_container_width=True)

    # =========================================================================
    # ZAKŁADKA: STATYSTYKI I RAPORTY
    # =========================================================================
    elif menu == "📊 Statystyki i Raporty":
        st.title("📊 Przegląd i Statystyki")
        res_all = supabase.table("zamowienia").select("*").execute()
        if res_all.data:
            df = pd.DataFrame(res_all.data)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Wszystkie pozycje", len(df))
            c2.metric("Zrealizowane", len(df[df['status'] == 'Zrealizowane']))
            c3.metric("Oczekujące", len(df[df['status'] == 'Oczekujące']))
            pilne_count = len(df[df['pilnosc'].str.contains("PILNE|KRYTYCZNE", na=False)])
            c4.metric("Pilne / Krytyczne", pilne_count)
            st.divider()
            col_wykres1, col_wykres2 = st.columns(2)
            with col_wykres1:
                st.subheader("🏗️ Zamówienia wg Projektu")
                st.bar_chart(df[df['projekt'] != '']['projekt'].value_counts())
            with col_wykres2:
                st.subheader("📌 Rozkład Statusów")
                st.bar_chart(df['status'].value_counts(), color="#ffaa00")
            st.divider()
            col_wykres3, col_wykres4 = st.columns(2)
            with col_wykres3:
                st.subheader("🏆 TOP 10 Materiałów")
                df['pozycja_czysta'] = df['pozycja'].str.capitalize().str.strip()
                st.bar_chart(df['pozycja_czysta'].value_counts().head(10), color="#00ff88")
            with col_wykres4:
                st.subheader("👤 Aktywność Pracowników")
                st.bar_chart(df['zgloszone_przez'].value_counts(), color="#0088ff")

    # =========================================================================
    # ZAKŁADKA: ZARZĄDZANIE KONTAMI (ADMIN)
    # =========================================================================
    elif menu == "👥 Zarządzanie Kontami":
        st.title("👥 Zarządzanie pracownikami")
        with st.container(border=True):
            st.subheader("➕ Dodaj nowe konto")
            c1, c2, c3, c4 = st.columns(4)
            nowy_login = c1.text_input("Login")
            nowe_haslo = c2.text_input("Hasło")
            nowa_rola = c3.selectbox("Rola", ["użytkownik", "admin"])
            nowy_telefon = c4.text_input("Telefon (np. 48123456789)")
            if st.button("Utwórz konto", type="primary"):
                if nowy_login and nowe_haslo:
                    supabase.table("pracownicy").insert({"login": nowy_login, "haslo": nowe_haslo, "rola": nowa_rola, "telefon": nowy_telefon}).execute()
                    st.success("Dodano użytkownika!")
                    time.sleep(1); st.rerun()

        st.divider()
        res_pracownicy = supabase.table("pracownicy").select("*").order("login").execute()
        for p in res_pracownicy.data:
            with st.container(border=True):
                col_info, col_btn = st.columns([5, 1])
                rola_w = p.get('rola') or "użytkownik"
                col_info.markdown(f"👤 Login: **{p['login']}** | 🔑 Hasło: `{p['haslo']}` | 🛡️ Rola: `{rola_w}` | 📱 Tel: `{p.get('telefon','')}`")
                if p['login'].lower() != "emil":
                    if col_btn.button("🗑️ Usuń", key=f"del_user_{p['login']}", type="secondary"):
                        supabase.table("pracownicy").delete().eq("login", p['login']).execute()
                        st.rerun()
                with st.expander(f"✏️ Edytuj: {p['login']}"):
                    e_c1, e_c2, e_c3, e_c4 = st.columns([2, 2, 2, 1])
                    n_haslo = e_c1.text_input("Hasło", value=p['haslo'], key=f"h_{p['login']}")
                    n_tel = e_c2.text_input("Telefon", value=p.get('telefon', ''), key=f"t_{p['login']}")
                    n_rola = e_c3.selectbox("Rola", ["użytkownik", "admin"], index=(1 if rola_w == "admin" else 0), disabled=(p['login'].lower() == "emil"), key=f"r_{p['login']}")
                    if e_c4.button("💾 Zapisz", key=f"s_{p['login']}", type="primary"):
                        upd = {"haslo": n_haslo, "telefon": n_tel}
                        if p['login'].lower() != "emil": upd["rola"] = n_rola
                        supabase.table("pracownicy").update(upd).eq("login", p['login']).execute()
                        st.rerun()

    # =========================================================================
    # ZAKŁADKA: MOJE AKTYWNE (UŻYTKOWNIK)
    # =========================================================================
    elif menu == "📋 Moje Aktywne":
        st.title("📋 Twoje Aktywne Zamówienia")
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").order("id", desc=True).execute()
        if not res.data:
            st.info("Brak oczekujących zamówień.")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz zdjęcie"): st.image(r['zdjecie_url'], use_container_width=True)
                    with st.expander("✏️ Edytuj zamówienie"):
                        e_c1, e_c2 = st.columns(2)
                        u_poz = e_c1.text_input("Pozycja", value=r['pozycja'], key=f"up_{r['id']}")
                        u_ilo = e_c2.text_input("Ilość", value=r['ilosc'], key=f"ui_{r['id']}")
                        if st.button("💾 Zapisz poprawki", key=f"us_{r['id']}", type="primary"):
                            supabase.table("zamowienia").update({"pozycja": u_poz, "ilosc": u_ilo}).eq("id", r['id']).execute()
                            st.rerun()
                    render_status_alert(r['status'])

    # =========================================================================
    # ZAKŁADKA: WYSZUKIWARKA I HISTORIA
    # =========================================================================
    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Baza Zamówień")
        res_all = supabase.table("zamowienia").select("projekt, zgloszone_przez").execute()
        projekty = sorted(list(set([x['projekt'] for x in res_all.data if x['projekt']])))
        osoby = sorted(list(set([x['zgloszone_przez'] for x in res_all.data if x['zgloszone_przez']])))
        with st.container(border=True):
            f_slowo = st.text_input("🔍 Szukaj...")
            c1, c2, c3 = st.columns(3)
            f_proj = c1.selectbox("🏗️ Projekt", ["-- Wszystkie --"] + projekty)
            f_kto = c2.selectbox("👤 Kto", ["-- Wszyscy --"] + osoby)
            f_status = c3.selectbox("📌 Status", ["-- Wszystkie --", "Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"])
            q = supabase.table("zamowienia").select("*")
            if f_proj != "-- Wszystkie --": q = q.eq("projekt", f_proj)
            if f_kto != "-- Wszyscy --": q = q.eq("zgloszone_przez", f_kto)
            if f_status != "-- Wszystkie --": q = q.eq("status", f_status)
            wynik = q.order("id", desc=True).execute().data
            if f_slowo.strip():
                wynik = [x for x in wynik if f_slowo.lower() in x['pozycja'].lower()]
        
        if wynik:
            df_res = pd.DataFrame(wynik)
            csv = '\ufeff'.encode('utf8') + df_res.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button("📥 Pobierz dla Excela", data=csv, file_name="historia.csv", mime="text/csv")
            for r in wynik:
                with st.container(border=True):
                    st.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz zdjęcie"): st.image(r['zdjecie_url'], use_container_width=True)
                    render_status_alert(r['status'])
                    if st.session_state.rola == "admin":
                        c_s1, c_s2 = st.columns([4, 1])
                        if r['status'] == "Zrealizowane" and c_s1.button("🔄 Przywróć", key=f"rev_{r['id']}"):
                            supabase.table("zamowienia").update({"status": "Oczekujące"}).eq("id", r['id']).execute(); st.rerun()
                        with c_s2.popover("🗑️ Usuń"):
                            if st.button("Tak, usuń", key=f"cdel_{r['id']}", type="primary"):
                                supabase.table("zamowienia").delete().eq("id", r['id']).execute(); st.rerun()

    # =========================================================================
    # ZAKŁADKA: INSTRUKCJA (NOWOŚĆ W MENU)
    # =========================================================================
    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja Obsługi Systemu")
        
        st.info("Witaj w systemie zamówień materiałowych! Poniżej znajdziesz krótką ściągę, jak sprawnie korzystać z aplikacji.")
        
        col_inst, _ = st.columns([2, 1])
        with col_inst:
            st.markdown("""
            ### 1️⃣ Logowanie
            *   Używaj swojego indywidualnego loginu i hasła.
            *   Pamiętaj o wylogowaniu się, jeśli korzystasz z ogólnodostępnego komputera.

            ### 2️⃣ Jak dodać zamówienie?
            *   Wejdź w **📝 Nowe Zamówienie**.
            *   Podaj nazwę przedmiotu, ilość, wymiary i materiał.
            *   **Wybierz Projekt** – to ułatwia adminowi przypisanie kosztów.
            *   **📷 Zdjęcie:** Jeśli element jest nietypowy, włącz aparat i zrób zdjęcie.
            *   **📲 WhatsApp:** Możesz od razu wysłać wiadomość do administratora o nowym zgłoszeniu.

            ### 3️⃣ Twoje zamówienia i edycja
            *   W zakładce **📋 Moje Aktywne** sprawdzisz status swoich zgłoszeń.
            *   **Edycja:** Dopóki zamówienie nie jest zrealizowane, możesz poprawić dane (przycisk **✏️ Edytuj**).

            ### 4️⃣ Statusy (co oznaczają ikony?)
            *   ⏳ **Oczekujące**: Admin widzi zgłoszenie, jeszcze nie zamówił.
            *   🚚 **Zamówione**: Towar jest kupiony i w drodze do firmy.
            *   ❌ **Niedostępne**: Brak towaru w hurtowni (sprawdź notatkę admina!).
            *   🔄 **Zamiennik**: Kupiono coś podobnego (sprawdź notatkę!).
            *   ✅ **Zrealizowane**: Towar jest do odbioru w pakamerze.

            ### 5️⃣ Historia i Szukaj
            *   Możesz przeglądać stare zamówienia i pobierać je do pliku Excel.

            ---
            💡 **Wskazówka:** Na telefonie dodaj stronę do **ekranu głównego**, aby mieć do niej szybki dostęp jak do zwykłej aplikacji!
            """)
            st.success("W razie pytań lub problemów technicznych kontaktuj się z Emilem.")

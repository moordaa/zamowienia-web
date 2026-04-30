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
                "🔎 Historia i Szukaj"
            ])
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
            
            # APARAT NA ŻĄDANIE
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
        st.caption("Lista wszystkich aktywnych zamówień. Zmieniaj statusy i wysyłaj powiadomienia WhatsApp.")
        
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
                                "pozycja": edit_pozycja,
                                "ilosc": edit_ilosc,
                                "wymiary": edit_wymiary,
                                "material": edit_material,
                                "projekt": edit_projekt,
                                "pilnosc": edit_pilnosc
                            }).eq("id", r['id']).execute()
                            st.success("Zapisano zmiany!")
                            time.sleep(1)
                            st.rerun()
                    
                    st.divider()
                    
                    col_stat, col_uwg = st.columns([1, 2])
                    lista_statusow = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    aktualny_index = lista_statusow.index(r['status']) if r['status'] in lista_statusow else 0
                    
                    nowy_status = col_stat.selectbox("Status", lista_statusow, index=aktualny_index, key=f"stat_{r['id']}")
                    nowe_uwagi = col_uwg.text_input("Notatka (np. numer paczki, jaki zamiennik)", value=r.get('uwagi_admina') or "", key=f"uwg_{r['id']}")
                    
                    c1, c2, c3 = st.columns([2, 1, 3])
                    
                    if c1.button("💾 Zapisz status", key=f"zapisz_{r['id']}", type="primary"):
                        supabase.table("zamowienia").update({
                            "status": nowy_status, 
                            "uwagi_admina": nowe_uwagi
                        }).eq("id", r['id']).execute()
                        st.toast("Zaktualizowano status w bazie!")
                        st.rerun()
                        
                    if c2.button("🗑️ Usuń", key=f"del_{r['id']}", type="secondary"):
                        supabase.table("zamowienia").delete().eq("id", r['id']).execute()
                        st.rerun()

                    tresc_wa = f"Cześć! Twoje zamówienie na '{r['pozycja']}' zmieniło status na: *{r['status']}*."
                    if r.get('uwagi_admina'):
                        tresc_wa += f" Notatka: {r['uwagi_admina']}"
                    
                    surowy_numer = baza_telefonow.get(r['zgloszone_przez'])
                    
                    if surowy_numer:
                        czysty_numer = "".join(cyfra for cyfra in surowy_numer if cyfra.isdigit())
                        url_wa = f"https://wa.me/{czysty_numer}?text={urllib.parse.quote(tresc_wa)}"
                        c3.link_button("📲 Wyślij WhatsApp", url_wa, use_container_width=True)
                    else:
                        url_wa = f"https://wa.me/?text={urllib.parse.quote(tresc_wa)}"
                        c3.link_button("📲 Wyślij (brak nr w bazie)", url_wa, use_container_width=True, help="Ten pracownik nie ma przypisanego numeru telefonu w bazie.")

    # =========================================================================
    # ZAKŁADKA: STATYSTYKI I RAPORTY
    # =========================================================================
    elif menu == "📊 Statystyki i Raporty":
        st.title("📊 Przegląd i Statystyki")
        st.caption("Analiza danych ze wszystkich zgłoszeń. Wciśnij CTRL+P, aby wydrukować tę stronę jako Raport PDF.")
        
        res_all = supabase.table("zamowienia").select("*").execute()
        
        if not res_all.data:
            st.info("Brak danych do wygenerowania statystyk.")
        else:
            df = pd.DataFrame(res_all.data)
            
            st.subheader("Wskaźniki ogólne")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Wszystkie pozycje", len(df))
            c2.metric("Zrealizowane", len(df[df['status'] == 'Zrealizowane']))
            c3.metric("Oczekujące", len(df[df['status'] == 'Oczekujące']))
            
            pilne_count = len(df[df['pilnosc'].str.contains("PILNE|KRYTYCZNE", na=False)])
            c4.metric("Pilne / Krytyczne", pilne_count)
            
            st.divider()
            
            col_wykres1, col_wykres2 = st.columns(2)
            
            with col_wykres1:
                st.subheader("🏗️ Ilość zamówień wg Projektu")
                projekty_counts = df[df['projekt'] != '']['projekt'].value_counts()
                st.bar_chart(projekty_counts)
                
            with col_wykres2:
                st.subheader("📌 Rozkład Statusów")
                statusy_counts = df['status'].value_counts()
                st.bar_chart(statusy_counts, color="#ffaa00")
                
            st.divider()
            
            col_wykres3, col_wykres4 = st.columns(2)
            
            with col_wykres3:
                st.subheader("🏆 TOP 10 Najczęściej Zamawianych Materiałów")
                df['pozycja_czysta'] = df['pozycja'].str.capitalize().str.strip()
                top_materialy = df['pozycja_czysta'].value_counts().head(10)
                st.bar_chart(top_materialy, color="#00ff88")
                
            with col_wykres4:
                st.subheader("👤 Aktywność Pracowników (Kto najwięcej zgłasza)")
                top_pracownicy = df['zgloszone_przez'].value_counts()
                st.bar_chart(top_pracownicy, color="#0088ff")

    # =========================================================================
    # ZAKŁADKA: ZARZĄDZANIE KONTAMI (ADMIN)
    # =========================================================================
    elif menu == "👥 Zarządzanie Kontami":
        st.title("👥 Zarządzanie pracownikami")
        st.caption("Dodawaj, edytuj i usuwaj konta użytkowników mających dostęp do aplikacji.")
        
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
                            "telefon": nowy_telefon
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
                    col_info, col_btn = st.columns([5, 1])
                    rola_wyswietlana = p.get('rola') or "użytkownik"
                    tel_wyswietlany = p.get('telefon') or "Brak"
                    col_info.markdown(f"👤 Login: **{p['login']}** | 🔑 Hasło: `{p['haslo']}` | 🛡️ Rola: `{rola_wyswietlana}` | 📱 Tel: `{tel_wyswietlany}`")
                    
                    if p['login'].lower() != "emil":
                        if col_btn.button("🗑️ Usuń", key=f"del_user_{p['login']}", type="secondary"):
                            supabase.table("pracownicy").delete().eq("login", p['login']).execute()
                            st.rerun()
                    else:
                        col_btn.caption("👑 Konto główne")
                        
                    with st.expander(f"✏️ Edytuj dane dla: {p['login']}"):
                        czy_konto_glowne = (p['login'].lower() == "emil")
                        
                        e_col1, e_col2, e_col3, e_col4 = st.columns([2, 2, 2, 1])
                        
                        nowe_haslo_edit = e_col1.text_input("Nowe hasło", value=p['haslo'], key=f"edit_haslo_{p['login']}")
                        nowy_telefon_edit = e_col2.text_input("Nowy telefon", value=p.get('telefon', ''), key=f"edit_tel_{p['login']}")
                        
                        index_roli = 1 if rola_wyswietlana == "admin" else 0
                        nowa_rola_edit = e_col3.selectbox("Rola", ["użytkownik", "admin"], index=index_roli, disabled=czy_konto_glowne, key=f"edit_rola_{p['login']}")
                        
                        e_col4.write("")
                        e_col4.write("")
                        if e_col4.button("💾 Zapisz", key=f"save_edit_{p['login']}", type="primary", use_container_width=True):
                            update_dane = {
                                "haslo": nowe_haslo_edit,
                                "telefon": nowy_telefon_edit
                            }
                            if not czy_konto_glowne:
                                update_dane["rola"] = nowa_rola_edit
                                
                            supabase.table("pracownicy").update(update_dane).eq("login", p['login']).execute()
                            
                            st.success("Zaktualizowano profil!")
                            time.sleep(1)
                            st.rerun()

    # =========================================================================
    # ZAKŁADKA: MOJE AKTYWNE (ZWYKŁY UŻYTKOWNIK) - Z EDYCJĄ WŁASNYCH ZAMÓWIEŃ
    # =========================================================================
    elif menu == "📋 Moje Aktywne":
        st.title("📋 Aktywne Zamówienia")
        st.caption("Tutaj widzisz statusy elementów, które zamówiłeś. Możesz edytować ich szczegóły do czasu realizacji.")
        
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").order("id", desc=True).execute()
        
        if not res.data:
            st.info("Nie masz obecnie żadnych oczekujących zamówień.")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"### {r['pozycja']} (Ilość: {r['ilosc']})")
                    st.caption(f"🏗️ {r['projekt']} | 📅 {r['data_zgloszenia']}")
                    
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz załączone zdjęcie"):
                            st.image(r['zdjecie_url'], use_container_width=True)
                            
                    # --- EDYCJA DLA UŻYTKOWNIKA ---
                    with st.expander("✏️ Edytuj swoje zamówienie"):
                        e_col1, e_col2 = st.columns(2)
                        edit_pozycja = e_col1.text_input("Pozycja", value=r['pozycja'], key=f"user_epoz_{r['id']}")
                        edit_ilosc = e_col2.text_input("Ilość", value=r['ilosc'], key=f"user_eilo_{r['id']}")
                        
                        e_col3, e_col4 = st.columns(2)
                        edit_wymiary = e_col3.text_input("Wymiary", value=r['wymiary'] or "", key=f"user_ewym_{r['id']}")
                        edit_material = e_col4.text_input("Materiał", value=r['material'] or "", key=f"user_emat_{r['id']}")
                        
                        e_col5, e_col6 = st.columns(2)
                        edit_projekt = e_col5.text_input("Projekt", value=r['projekt'] or "", key=f"user_eproj_{r['id']}")
                        
                        pilnosci_lista = ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"]
                        akt_pilnosc = r['pilnosc'] if r['pilnosc'] in pilnosci_lista else "Normalna"
                        idx_pilnosc = pilnosci_lista.index(akt_pilnosc)
                        edit_pilnosc = e_col6.selectbox("Pilność", pilnosci_lista, index=idx_pilnosc, key=f"user_epil_{r['id']}")
                        
                        if st.button("💾 Zapisz poprawki", key=f"user_esave_{r['id']}", type="primary"):
                            supabase.table("zamowienia").update({
                                "pozycja": edit_pozycja,
                                "ilosc": edit_ilosc,
                                "wymiary": edit_wymiary,
                                "material": edit_material,
                                "projekt": edit_projekt,
                                "pilnosc": edit_pilnosc
                            }).eq("id", r['id']).execute()
                            st.success("Zapisano zmiany!")
                            time.sleep(1)
                            st.rerun()
                    # ---------------------------------
                            
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
            csv_data = '\ufeff'.encode('utf8') + df.to_csv(index=False, sep=';').encode('utf-8')
            col_pobierz.download_button("📥 Pobierz dla Excela", data=csv_data, file_name="historia_zamowien.csv", mime="text/csv")
            
            for r in wynik_szukania:
                with st.container(border=True):
                    st.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                    
                    c_info1, c_info2 = st.columns(2)
                    c_info1.markdown(f"**Wymiary:** {r['wymiary'] if r['wymiary'] else '---'}")
                    c_info1.markdown(f"**Materiał:** {r['material'] if r['material'] else '---'}")
                    
                    pilnosc_display = f"🚨 {r['pilnosc']}" if "PILNE" in r['pilnosc'] or "KRYTYCZNE" in r['pilnosc'] else r['pilnosc']
                    c_info2.markdown(f"**Pilność:** {pilnosc_display}")
                    c_info2.markdown(f"**Projekt:** 🏗️ {r['projekt']}")
                    
                    st.caption(f"👤 Zgłosił(a): {r['zgloszone_przez']} | 📅 {r['data_zgloszenia']}")
                    
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz załączone zdjęcie"):
                            st.image(r['zdjecie_url'], use_container_width=True)
                            
                    if r.get('uwagi_admina'):
                        st.info(f"📝 Notatka Admina: {r['uwagi_admina']}")
                        
                    st.divider()
                    
                    col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
                    
                    ikona = status_emoji.get(r['status'], "🔹")
                    if r['status'] == 'Zrealizowane':
                        col_s1.success(f"Status: **{ikona} {r['status']}**")
                    else:
                        col_s1.markdown(f"Status: **{ikona} {r['status']}**")
                    
                    if st.session_state.rola == "admin":
                        if r['status'] == "Zrealizowane":
                            if col_s2.button("🔄 Przywróć", key=f"revert_{r['id']}", help="Przywróci status tego zamówienia na 'Oczekujące'", use_container_width=True):
                                supabase.table("zamowienia").update({
                                    "status": "Oczekujące",
                                    "uwagi_admina": r.get('uwagi_admina', '') + " [Przywrócono awaryjnie]"
                                }).eq("id", r['id']).execute()
                                st.rerun()
                                
                        with col_s3.popover("🗑️ Usuń", use_container_width=True):
                            st.markdown("⚠️ **Czy na pewno?**")
                            st.caption("Tej operacji nie można cofnąć.")
                            if st.button("Tak, usuń", key=f"confirm_del_hist_{r['id']}", type="primary", use_container_width=True):
                                supabase.table("zamowienia").delete().eq("id", r['id']).execute()
                                st.rerun()

        else:
            st.warning("Brak wyników spełniających kryteria.")

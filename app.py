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
                    res = supabase.table("pracownicy").select("*").eq("login", l).eq("haslo", p).execute()
                    if res.data:
                        st.session_state.zalogowany = True
                        st.session_state.uzytkownik = l
                        st.session_state.rola = res.data[0].get('rola') or "użytkownik"
                        st.rerun()
                    else:
                        st.error("Błędny login lub hasło!")
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
            
            # --- EASTER EGGS ---
            cp = pozycja.strip().lower()
            if cp == "69":
                st.balloons(); st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmNudWw2ODZpeGZqZGZ6Z3N5Zmt6ZGZ6Z3N5Zmt6ZGZ6Z3N5Zmt6ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zy/6YjzP6F3R8Vz6/giphy.gif")
                st.warning("Klasyk. Ale wróćmy do roboty! 😉")
            if cp == "666":
                st.snow(); st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM2I1NjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/gui67fZ3xIneM/giphy.gif")
                st.error("PIEKIELNIE DOBRE ZAMÓWIENIE! 🤘🔥")

            col1, col2 = st.columns(2)
            wymiary = col1.text_input("📏 Wymiary (np. M8x40)")
            material = col2.text_input("🧱 Materiał (np. Ocynk)")
            
            col3, col4 = st.columns(2)
            ilosc = st.text_input("🔢 Ilość (np. 100 szt.)")
            
            # --- EASTER EGGS DLA ILOŚCI ---
            ci = ilosc.strip()
            if ci == "69": st.balloons()
            if ci == "666": st.snow()

            pilnosc = col4.selectbox("🚨 Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"])
            projekt = st.text_input("🏗️ Projekt / Cel")
            
            # --- EASTER EGGS DLA PROJEKTU ---
            cproj = projekt.strip().lower()
            if cproj == "dla szefa":
                st.balloons(); st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHpwaXlyMTBmaG0wYjFqcTJwaXlyMTBmaG0wYjFqcTJwaXlyMTBmaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zy/MUeQeEQaLFOda/giphy.gif")
            if cproj in ["fucha", "prywatne"]:
                st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHRibmJ1aGRuZWhtcmV6Zmt1OHRibmJ1aGRuZWhtcmV6Zmt1OHRibmJ1JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/uO0G8t5w1wPmw/giphy.gif")

            st.divider()
            zdjecie = None
            if st.toggle("📷 Dodaj zdjęcie z aparatu"):
                zdjecie = st.camera_input("Zrób zdjęcie")
            
            st.divider()
            opcje_wa = ["-- Nie wysyłaj --"] + list(admin_phones.keys())
            powiadom = st.selectbox("📲 Powiadom admina (WhatsApp):", opcje_wa)
            
            if st.button("WYŚLIJ ZAMÓWIENIE", type="primary", use_container_width=True):
                if pozycja and ilosc:
                    url_zdj = ""
                    if zdjecie:
                        nazwa = f"{int(time.time())}_{st.session_state.uzytkownik}.jpg"
                        supabase.storage.from_("zdjecia_zamowien").upload(nazwa, zdjecie.getvalue(), {"content-type": "image/jpeg"})
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
                        t = f"Nowe zamówienie: {pozycja} ({ilosc}). Projekt: {projekt}. Od: {st.session_state.uzytkownik}"
                        st.link_button("📲 Wyślij WhatsApp do Admina", f"https://wa.me/{nr}?text={urllib.parse.quote(t)}", use_container_width=True)
                        st.stop()
                    else:
                        time.sleep(2); st.rerun()
                else:
                    st.error("Pozycja i Ilość są wymagane!")

    # =========================================================================
    # ZAKŁADKA: PANEL REALIZACJI (ADMIN)
    # =========================================================================
    elif menu == "⚙️ Panel Realizacji (Admin)":
        st.title("⚙️ Zarządzanie realizacją")
        prac_res = supabase.table("pracownicy").select("login, telefon").execute()
        tels = {p['login']: p.get('telefon', '') for p in prac_res.data}
        
        res = supabase.table("zamowienia").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        if not res.data: st.success("Brak aktywnych zamówień!")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.subheader(f"{r['pozycja']} ({r['ilosc']})")
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz zdjęcie"): st.image(r['zdjecie_url'], use_container_width=True)
                    
                    with st.expander("✏️ Edytuj szczegóły (wymiary, projekt itp.)"):
                        e_col1, e_col2 = st.columns(2)
                        up_poz = e_col1.text_input("Pozycja", value=r['pozycja'], key=f"ep_{r['id']}")
                        up_ilo = e_col2.text_input("Ilość", value=r['ilosc'], key=f"ei_{r['id']}")
                        up_wym = e_col1.text_input("Wymiary", value=r.get('wymiary',''), key=f"ew_{r['id']}")
                        up_pro = e_col2.text_input("Projekt", value=r.get('projekt',''), key=f"ej_{r['id']}")
                        if st.button("Zapisz zmiany w danych", key=f"eb_{r['id']}"):
                            supabase.table("zamowienia").update({"pozycja": up_poz, "ilosc": up_ilo, "wymiary": up_wym, "projekt": up_pro}).eq("id", r['id']).execute()
                            st.rerun()

                    st.divider()
                    col1, col2 = st.columns([1, 2])
                    st_list = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    n_st = col1.selectbox("Zmień status", st_list, index=st_list.index(r['status']), key=f"st_{r['id']}")
                    n_uw = col2.text_input("Notatka dla pracownika", value=r.get('uwagi_admina') or "", key=f"uw_{r['id']}")
                    
                    c_s, c_d, c_w = st.columns([1, 1, 2])
                    if c_s.button("💾 Zapisz status", key=f"s_{r['id']}", type="primary"):
                        supabase.table("zamowienia").update({"status": n_st, "uwagi_admina": n_uw}).eq("id", r['id']).execute()
                        st.rerun()
                    if c_d.button("🗑️ Usuń", key=f"d_{r['id']}"):
                        supabase.table("zamowienia").delete().eq("id", r['id']).execute(); st.rerun()
                    
                    tel = tels.get(r['zgloszone_przez'])
                    if tel:
                        nr_c = "".join(c for c in tel if c.isdigit())
                        msg = f"Status zamówienia {r['pozycja']}: {n_st}. {n_uw}"
                        c_w.link_button("📲 Wyślij WhatsApp do pracownika", f"https://wa.me/{nr_c}?text={urllib.parse.quote(msg)}", use_container_width=True)

    # =========================================================================
    # ZAKŁADKA: STATYSTYKI
    # =========================================================================
    elif menu == "📊 Statystyki i Raporty":
        st.title("📊 Statystyki")
        res = supabase.table("zamowienia").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            col_a, col_b = st.columns(2)
            col_a.subheader("Zamówienia wg projektu")
            col_a.bar_chart(df['projekt'].value_counts())
            col_b.subheader("Aktywność pracowników")
            col_b.bar_chart(df['zgloszone_przez'].value_counts())
            st.subheader("Najczęściej zamawiane materiały")
            df['p_c'] = df['pozycja'].str.capitalize()
            st.bar_chart(df['p_c'].value_counts().head(10))

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
                supabase.table("pracownicy").insert({"login": n_log, "haslo": n_has, "rola": n_rol, "telefon": n_tel}).execute()
                st.success("Dodano!"); time.sleep(1); st.rerun()

        st.divider()
        res_p = supabase.table("pracownicy").select("*").order("login").execute()
        for p in res_p.data:
            with st.container(border=True):
                col_i, col_b = st.columns([5, 1])
                rola_p = p.get('rola') or "użytkownik"
                col_i.markdown(f"👤 **{p['login']}** | Rola: `{rola_p}` | Tel: `{p.get('telefon','')}`")
                if p['login'].lower() != "emil":
                    if col_b.button("🗑️ Usuń", key=f"dp_{p['login']}"):
                        supabase.table("pracownicy").delete().eq("login", p['login']).execute(); st.rerun()
                
                with st.expander(f"✏️ Edytuj dane: {p['login']}"):
                    ce1, ce2, ce3 = st.columns(3)
                    e_has = ce1.text_input("Hasło", value=p['haslo'], key=f"eh_{p['login']}")
                    e_tel = ce2.text_input("Telefon", value=p.get('telefon',''), key=f"et_{p['login']}")
                    e_rol = ce3.selectbox("Rola", ["użytkownik", "admin"], index=(1 if rola_p=="admin" else 0), key=f"er_{p['login']}")
                    if st.button("💾 Zapisz zmiany", key=f"es_{p['login']}"):
                        supabase.table("pracownicy").update({"haslo": e_has, "telefon": e_tel, "rola": e_rol}).eq("login", p['login']).execute()
                        st.rerun()

    # =========================================================================
    # ZAKŁADKA: MOJE AKTYWNE (UŻYTKOWNIK)
    # =========================================================================
    elif menu == "📋 Moje Aktywne":
        st.title("📋 Twoje zamówienia w realizacji")
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").order("id", desc=True).execute()
        if not res.data: st.info("Brak aktywnych zamówień.")
        for r in res.data:
            with st.container(border=True):
                st.subheader(f"{r['pozycja']} ({r['ilosc']})")
                render_status_alert(r['status'])
                if r.get('uwagi_admina'): st.info(f"Odpis Admina: {r['uwagi_admina']}")
                with st.expander("✏️ Popraw dane (zanim zrealizują)"):
                    up_p = st.text_input("Pozycja", value=r['pozycja'], key=f"up_{r['id']}")
                    up_i = st.text_input("Ilość", value=r['ilosc'], key=f"ui_{r['id']}")
                    if st.button("Zapisz poprawki", key=f"ubs_{r['id']}"):
                        supabase.table("zamowienia").update({"pozycja": up_p, "ilosc": up_i}).eq("id", r['id']).execute(); st.rerun()

    # =========================================================================
    # ZAKŁADKA: HISTORIA I SZUKAJ
    # =========================================================================
    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Baza wszystkich zamówień")
        res_f = supabase.table("zamowienia").select("projekt, zgloszone_przez").execute()
        projekty = sorted(list(set([x['projekt'] for x in res_f.data if x['projekt']])))
        osoby = sorted(list(set([x['zgloszone_przez'] for x in res_f.data if x['zgloszone_przez']])))
        
        with st.container(border=True):
            f_slowo = st.text_input("🔍 Szukaj po nazwie...")
            c1, c2, c3 = st.columns(3)
            f_proj = c1.selectbox("🏗️ Projekt", ["-- Wszystkie --"] + projekty)
            f_kto = c2.selectbox("👤 Kto", ["-- Wszyscy --"] + osoby)
            f_status = c3.selectbox("📌 Status", ["-- Wszystkie --", "Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"])
            
            q = supabase.table("zamowienia").select("*")
            if f_proj != "-- Wszystkie --": q = q.eq("projekt", f_proj)
            if f_kto != "-- Wszyscy --": q = q.eq("zgloszone_przez", f_kto)
            if f_status != "-- Wszystkie --": q = q.eq("status", f_status)
            wynik = q.order("id", desc=True).execute().data
            if f_slowo: wynik = [x for x in wynik if f_slowo.lower() in x['pozycja'].lower()]

        if wynik:
            df_h = pd.DataFrame(wynik)
            csv = '\ufeff'.encode('utf8') + df_h.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button("📥 Pobierz historię do Excela", csv, "historia.csv", "text/csv")
            
            for r in wynik:
                with st.container(border=True):
                    col_h1, col_h2 = st.columns([4,1])
                    col_h1.markdown(f"### {r['pozycja']} ({r['ilosc']})")
                    col_h1.caption(f"Projekt: {r['projekt']} | Zgłosił: {r['zgloszone_przez']} | Data: {r['data_zgloszenia']}")
                    
                    ikona = status_emoji.get(r['status'], "🔹")
                    col_h2.write(f"**{ikona} {r['status']}**")
                    
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz zdjęcie"): st.image(r['zdjecie_url'], use_container_width=True)
                    
                    if st.session_state.rola == "admin":
                        ca, cb = st.columns([1,1])
                        if r['status'] == "Zrealizowane" and ca.button("🔄 Przywróć", key=f"rev_{r['id']}"):
                            supabase.table("zamowienia").update({"status": "Oczekujące"}).eq("id", r['id']).execute(); st.rerun()
                        with cb.popover("🗑️ Usuń"):
                            st.write("Na pewno?")
                            if st.button("Tak, usuń trwale", key=f"fdel_{r['id']}", type="primary"):
                                supabase.table("zamowienia").delete().eq("id", r['id']).execute(); st.rerun()

    # =========================================================================
    # ZAKŁADKA: INSTRUKCJA
    # =========================================================================
    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja Obsługi")
        st.info("Krótka ściąga dla pracowników:")
        st.markdown("""
        1.  **Zgłaszanie**: Wypełnij formularz w 'Nowe zamówienie'. Pamiętaj o podaniu projektu.
        2.  **Zdjęcia**: Jeśli element jest nietypowy, włącz aparat i zrób fotkę.
        3.  **Statusy**: ⏳ - czeka, 🚚 - zamówione, ✅ - gotowe do odbioru w pakamerze.
        4.  **Edycja**: Możesz poprawić swoje zamówienie w zakładce 'Moje Aktywne', dopóki nie zostanie zrealizowane.
        5.  **WhatsApp**: Używaj przycisków WhatsApp, aby szybko powiadomić Admina o nowym zgłoszeniu.
        """)

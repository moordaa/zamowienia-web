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
    # ZAKŁADKA: NOWE ZAMÓWIENIE (Z POLSKIMI ŻARTAMI)
    # =========================================================================
    if menu == "📝 Nowe Zamówienie":
        st.title("📝 Dodaj zamówienie")
        
        admins_res = supabase.table("pracownicy").select("login, telefon").eq("rola", "admin").execute()
        admin_phones = {a['login']: a['telefon'] for a in admins_res.data if a.get('telefon')}
        
        with st.container(border=True):
            pozycja = st.text_input("🔧 Pozycja (np. Śruba zamkowa)")
            
            # --- EASTER EGGS ---
            if pozycja.strip() == "69":
                st.balloons(); st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmNudWw2ODZpeGZqZGZ6Z3N5Zmt6ZGZ6Z3N5Zmt6ZGZ6Z3N5Zmt6ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zy/6YjzP6F3R8Vz6/giphy.gif")
                st.warning("Klasyk. Ale wróćmy do roboty! 😉")
            if pozycja.strip() == "666":
                st.snow(); st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM2I1NjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/gui67fZ3xIneM/giphy.gif")
                st.error("PIEKIELNIE DOBRE ZAMÓWIENIE! 🤘🔥")

            col1, col2 = st.columns(2)
            wymiary = col1.text_input("📏 Wymiary (np. M8x40)")
            material = col2.text_input("🧱 Materiał (np. Ocynk)")
            
            col3, col4 = st.columns(2)
            ilosc = col3.text_input("🔢 Ilość (np. 100 szt.)")
            
            # --- EASTER EGGS DLA ILOŚCI ---
            if ilosc.strip() == "69":
                st.balloons(); st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmNudWw2ODZpeGZqZGZ6Z3N5Zmt6ZGZ6Z3N5Zmt6ZGZ6Z3N5Zmt6ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zy/6YjzP6F3R8Vz6/giphy.gif")
            if ilosc.strip() == "666":
                st.snow(); st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM2I1NjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5YjY0M2Y5JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/gui67fZ3xIneM/giphy.gif")

            pilnosc = col4.selectbox("🚨 Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"])
            projekt = st.text_input("🏗️ Projekt / Cel")
            
            # --- EASTER EGGS DLA PROJEKTU ---
            if projekt.strip().lower() == "dla szefa":
                st.balloons(); st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHpwaXlyMTBmaG0wYjFqcTJwaXlyMTBmaG0wYjFqcTJwaXlyMTBmaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zy/MUeQeEQaLFOda/giphy.gif")
                st.info("Szykujcie się na premię! 👑")
            if projekt.strip().lower() in ["fucha", "prywatne"]:
                st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHRibmJ1aGRuZWhtcmV6Zmt1OHRibmJ1aGRuZWhtcmV6Zmt1OHRibmJ1JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/uO0G8t5w1wPmw/giphy.gif")
                st.warning("Admin wszystko widzi... 👀")

            st.divider()
            zdjecie = None
            if st.toggle("📷 Dodaj zdjęcie z aparatu"):
                zdjecie = st.camera_input("Zrób zdjęcie")
            
            st.divider()
            opcje_wa = ["-- Nie wysyłaj --"] + list(admin_phones.keys())
            powiadom = st.selectbox("📲 Wyślij powiadomienie WhatsApp do:", opcje_wa)
            
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
                    
                    st.success("Wysłano!")
                    if powiadom != "-- Nie wysyłaj --":
                        nr = "".join(c for c in admin_phones[powiadom] if c.isdigit())
                        t = f"Nowe zamówienie: {pozycja} ({ilosc}). Projekt: {projekt}. Od: {st.session_state.uzytkownik}"
                        st.link_button("📲 Otwórz WhatsApp i wyślij", f"https://wa.me/{nr}?text={urllib.parse.quote(t)}", use_container_width=True)
                        st.stop()
                    else:
                        time.sleep(2); st.rerun()
                else:
                    st.error("Wypełnij wymagane pola (Pozycja i Ilość)!")

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
                    st.caption(f"Zgłosił: {r['zgloszone_przez']} | Projekt: {r['projekt']}")
                    if r.get('zdjecie_url'):
                        with st.expander("🖼️ Zobacz zdjęcie"): st.image(r['zdjecie_url'], use_container_width=True)
                    
                    with st.expander("✏️ Edytuj dane zamówienia"):
                        e_poz = st.text_input("Pozycja", value=r['pozycja'], key=f"e_{r['id']}")
                        e_ilo = st.text_input("Ilość", value=r['ilosc'], key=f"i_{r['id']}")
                        if st.button("Zapisz zmiany w danych", key=f"b_e_{r['id']}"):
                            supabase.table("zamowienia").update({"pozycja": e_poz, "ilosc": e_ilo}).eq("id", r['id']).execute()
                            st.rerun()

                    st.divider()
                    col1, col2 = st.columns([1, 2])
                    st_list = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    n_st = col1.selectbox("Status", st_list, index=st_list.index(r['status']), key=f"st_{r['id']}")
                    n_uw = col2.text_input("Notatka admina", value=r.get('uwagi_admina') or "", key=f"uw_{r['id']}")
                    
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
                        c_w.link_button("📲 Powiadom przez WhatsApp", f"https://wa.me/{nr_c}?text={urllib.parse.quote(msg)}", use_container_width=True)

    # =========================================================================
    # ZAKŁADKA: STATYSTYKI
    # =========================================================================
    elif menu == "📊 Statystyki i Raporty":
        st.title("📊 Statystyki")
        res = supabase.table("zamowienia").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.subheader("Ilość zamówień wg projektu")
            st.bar_chart(df['projekt'].value_counts())
            st.subheader("Kto najwięcej zgłasza?")
            st.bar_chart(df['zgloszone_przez'].value_counts())
        else:
            st.info("Brak danych.")

    # =========================================================================
    # ZAKŁADKA: MOJE AKTYWNE (UŻYTKOWNIK)
    # =========================================================================
    elif menu == "📋 Moje Aktywne":
        st.title("📋 Twoje aktywne zamówienia")
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").execute()
        if not res.data: st.info("Brak oczekujących zamówień.")
        for r in res.data:
            with st.container(border=True):
                st.write(f"**{r['pozycja']}** ({r['ilosc']})")
                render_status_alert(r['status'])
                with st.expander("✏️ Edytuj"):
                    n_p = st.text_input("Pozycja", value=r['pozycja'], key=f"up_{r['id']}")
                    n_i = st.text_input("Ilość", value=r['ilosc'], key=f"ui_{r['id']}")
                    if st.button("Zapisz", key=f"ub_{r['id']}"):
                        supabase.table("zamowienia").update({"pozycja": n_p, "ilosc": n_i}).eq("id", r['id']).execute(); st.rerun()

    # =========================================================================
    # ZAKŁADKA: HISTORIA I INSTRUKCJA
    # =========================================================================
    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Historia zamówień")
        res = supabase.table("zamowienia").select("*").order("id", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df, use_container_width=True)
            csv = '\ufeff'.encode('utf8') + df.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button("📥 Pobierz do Excela (CSV)", csv, "historia.csv", "text/csv")

    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja")
        st.info("Krótka pomoc jak korzystać z aplikacji:")
        st.markdown("""
        1.  **Dodawanie**: Wybierz 'Nowe zamówienie', wpisz co potrzebujesz i projekt.
        2.  **Zdjęcie**: Jeśli to coś nietypowego, zrób zdjęcie telefonem.
        3.  **WhatsApp**: Po wysłaniu możesz kliknąć przycisk, aby od razu powiadomić admina.
        4.  **Status**: Sprawdzaj 'Moje Aktywne', żeby wiedzieć na czym stoisz. ✅ oznacza, że towar czeka w pakamerze!
        """)

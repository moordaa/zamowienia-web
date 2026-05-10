import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time
import urllib.parse
import io
import os
import tempfile
import urllib.request
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# Używamy fpdf do prawdziwych plików PDF
try:
    from fpdf import FPDF
except ImportError:
    st.error("Błąd: Brak biblioteki fpdf. Wpisz w terminalu: pip install fpdf2")

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
        if st.button("🔄 Odśwież dane", use_container_width=True): st.rerun()
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

    # --- FUNKCJA GENEROWANIA PDF (PIONOWA A4) ---
    def make_real_pdf(df, title_text):
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        def cln(text):
            if pd.isna(text) or text is None: return "-"
            text = str(text)
            mapping = {'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z','Ą':'A','Ć':'C','Ę':'E','Ł':'L','Ń':'N','Ó':'O','Ś':'S','Ź':'Z','Ż':'Z'}
            for k, v in mapping.items(): text = text.replace(k, v)
            return text.encode('ascii', 'ignore').decode('ascii')
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, cln(title_text), ln=1, align="C")
        pdf.ln(3)
        pdf.set_font("Arial", "", 5.5)
        cols = ["Zglosz.", "Realiz.", "Pozycja", "Wymiary", "Material", "Ilosc", "Projekt", "Pilnosc", "Zglosil", "Status", "Uwagi"]
        widths = [14, 14, 26, 14, 14, 8, 16, 12, 16, 16, 38]
        pdf.set_fill_color(47, 117, 181)
        pdf.set_text_color(255, 255, 255)
        for i, col in enumerate(cols): pdf.cell(widths[i], 6, cln(col), border=1, align="C", fill=True)
        pdf.ln()
        pdf.set_text_color(0, 0, 0)
        for _, row in df.iterrows():
            pdf.cell(widths[0], 5, cln(row['Zgłoszono'])[:10], border=1)
            pdf.cell(widths[1], 5, cln(row['Zrealizowano'])[:10], border=1)
            pdf.cell(widths[2], 5, cln(row['Pozycja'])[:20], border=1)
            pdf.cell(widths[3], 5, cln(row['Wymiary'])[:10], border=1)
            pdf.cell(widths[4], 5, cln(row['Materiał'])[:10], border=1)
            pdf.cell(widths[5], 5, cln(row['Ilość'])[:6], border=1)
            pdf.cell(widths[6], 5, cln(row['Projekt'])[:12], border=1)
            pdf.cell(widths[7], 5, cln(row['Pilność'])[:8], border=1)
            pdf.cell(widths[8], 5, cln(row['Zgłaszający'])[:12], border=1)
            pdf.cell(widths[9], 5, cln(row['Status'])[:12], border=1)
            pdf.cell(widths[10], 5, cln(row['Uwagi'])[:32], border=1)
            pdf.ln()
        try:
            out = pdf.output(dest='S')
            if isinstance(out, str): return out.encode('latin1')
            return bytes(out)
        except TypeError: return bytes(pdf.output())

    # =========================================================================
    # LOGIKA ZAKŁADEK
    # =========================================================================
    if menu == "📝 Nowe Zamówienie":
        st.title("📝 Nowe zamówienie")
        admins_res = supabase.table("pracownicy").select("login, telefon").eq("rola", "admin").execute()
        admin_phones = {a['login']: a['telefon'] for a in admins_res.data if a.get('telefon')}
        with st.container(border=True):
            pozycja = st.text_input("🔧 Pozycja (np. Śruba zamkowa)")
            col1, col2 = st.columns(2)
            wymiary = col1.text_input("📏 Wymiary")
            material = col2.text_input("🧱 Materiał")
            col3, col4 = st.columns(2)
            ilosc = col3.text_input("🔢 Ilość")
            pilnosc = col4.selectbox("🚨 Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"])
            projekt = st.text_input("🏗️ Projekt / Cel")
            st.divider()
            zal_col1, zal_col2 = st.columns(2)
            zdjecie_cam = None
            if zal_col1.toggle("📷 Użyj aparatu"): zdjecie_cam = st.camera_input("Zrób zdjęcie")
            plik_upload = zal_col2.file_uploader("📁 Wybierz plik", type=["jpg", "jpeg", "png", "pdf"])
            st.divider()
            opcje_wa = ["-- Nie wysyłaj --"] + list(admin_phones.keys())
            powiadom = st.selectbox("📲 Powiadom admina (WhatsApp):", opcje_wa)
            if st.button("WYŚLIJ ZAMÓWIENIE", type="primary", use_container_width=True):
                if pozycja and ilosc:
                    url_zdj = ""
                    final_file = None
                    if zdjecie_cam: final_file = zdjecie_cam.getvalue()
                    elif plik_upload: final_file = plik_upload.getvalue()
                    if final_file:
                        nazwa = f"{int(time.time())}_{st.session_state.uzytkownik}.jpg"
                        supabase.storage.from_("zdjecia_zamowien").upload(nazwa, final_file, {"content-type": "image/jpeg"})
                        url_zdj = supabase.storage.from_("zdjecia_zamowien").get_public_url(nazwa)
                    supabase.table("zamowienia").insert({"pozycja": pozycja, "wymiary": wymiary, "material": material, "ilosc": ilosc, "projekt": projekt, "pilnosc": pilnosc, "status": "Oczekujące", "zgloszone_przez": st.session_state.uzytkownik, "data_zgloszenia": str(datetime.today().date()), "zdjecie_url": url_zdj}).execute()
                    st.success("Wysłano!"); time.sleep(1); st.rerun()

    elif menu == "⚙️ Panel Realizacji (Admin)":
        st.title("⚙️ Panel Realizacji")
        prac_res = supabase.table("pracownicy").select("login, telefon").execute()
        pracownicy_dict = {p['login']: p.get('telefon', '') for p in prac_res.data}
        res = supabase.table("zamowienia").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        if not res.data: st.success("Brak zamówień do realizacji!")
        else:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"### 📦 {r['pozycja'].upper()} `x {r['ilosc']}`")
                    st.markdown(f"👤 `{r['zgloszone_przez']}` | 🏗️ `{r.get('projekt') or '-'}` | 🚨 `{r.get('pilnosc') or 'Normalna'}`")
                    c_st, c_uw, c_zap = st.columns([2, 4, 1])
                    st_list = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                    n_st = c_st.selectbox("Status", st_list, index=st_list.index(r['status']), key=f"st_{r['id']}", label_visibility="collapsed")
                    n_uw = c_uw.text_input("Notatka", value=r.get('uwagi_admina') or "", key=f"uw_{r['id']}", label_visibility="collapsed")
                    if c_zap.button("💾", key=f"sv_{r['id']}", use_container_width=True):
                        u_data = {"status": n_st, "uwagi_admina": n_uw}
                        if n_st == "Zrealizowane": u_data["data_realizacji"] = str(datetime.today().date())
                        supabase.table("zamowienia").update(u_data).eq("id", r['id']).execute()
                        st.rerun()
                    b1, b2, b3, b4 = st.columns([2, 2, 1, 1])
                    msg = f"Aktualizacja: {r['pozycja']} | Status: {n_st} | Uwagi: {n_uw}"
                    tel_zgl = pracownicy_dict.get(r['zgloszone_przez'], '')
                    if tel_zgl:
                        nr_zgl = "".join(filter(str.isdigit, tel_zgl))
                        b1.link_button(f"📲 WA: {r['zgloszone_przez']}", f"https://wa.me/{nr_zgl}?text={urllib.parse.quote(msg)}", use_container_width=True)
                    else: b1.button("Brak Tel", disabled=True, use_container_width=True)
                    with b2.popover("➕ Inni"):
                        lista_opcji = [k for k in pracownicy_dict.keys() if k != r['zgloszone_przez']]
                        zaint = st.multiselect("Powiadom:", lista_opcji, key=f"m_{r['id']}")
                        for os in zaint:
                            t_os = pracownicy_dict.get(os, '')
                            if t_os:
                                n_os = "".join(filter(str.isdigit, t_os))
                                st.link_button(f"Wyślij do: {os}", f"https://wa.me/{n_os}?text={urllib.parse.quote(msg)}", use_container_width=True)
                    with b3.popover("⚙️"):
                        up_poz = st.text_input("Pozycja", value=r['pozycja'], key=f"e1_{r['id']}")
                        if st.button("Zapisz zmiany", key=f"eb_{r['id']}"):
                            supabase.table("zamowienia").update({"pozycja": up_poz}).eq("id", r['id']).execute(); st.rerun()
                        if st.button("🗑️ Usuń", key=f"db_{r['id']}"):
                            supabase.table("zamowienia").delete().eq("id", r['id']).execute(); st.rerun()
                    if r.get('zdjecie_url'):
                        with b4.popover("🖼️"): st.image(r['zdjecie_url'])
                    else: b4.button("❌", disabled=True)

    elif menu == "👥 Zarządzanie Kontami":
        st.title("👥 Zarządzanie pracownikami")
        with st.container(border=True):
            st.subheader("➕ Nowe konto")
            c1, c2, c3, c4 = st.columns(4)
            n_log = c1.text_input("Login")
            n_has = c2.text_input("Hasło") 
            n_rol = c3.selectbox("Rola", ["użytkownik", "admin"])
            n_tel = c4.text_input("Telefon")
            if st.button("Utwórz"):
                supabase.table("pracownicy").insert({"login": n_log, "haslo": n_has, "rola": n_rol, "telefon": n_tel}).execute(); st.rerun()
        res_p = supabase.table("pracownicy").select("*").order("login").execute()
        for p in res_p.data:
            with st.container(border=True):
                col_i, col_e, col_d = st.columns([4, 1, 1])
                h_wid = p.get('haslo','') if st.session_state.uzytkownik.lower() == "emil" or p['login'].lower() != "emil" else "••••"
                col_i.markdown(f"👤 **{p['login']}** | 🔑 `{h_wid}` | 📞 `{p.get('telefon','')}`")
                with col_e.popover("✏️"):
                    e_has = st.text_input("Nowe hasło", value=p.get('haslo',''), key=f"h_{p['login']}")
                    e_tel = st.text_input("Nowy telefon", value=p.get('telefon',''), key=f"t_{p['login']}")
                    if st.button("Zapisz", key=f"s_{p['login']}"):
                        supabase.table("pracownicy").update({"haslo": e_has, "telefon": e_tel}).eq("login", p['login']).execute(); st.rerun()
                if p['login'].lower() != "emil":
                    if col_d.button("🗑️", key=f"d_{p['login']}"):
                        supabase.table("pracownicy").delete().eq("login", p['login']).execute(); st.rerun()

    elif menu == "🔎 Historia i Szukaj":
        st.title("🔎 Historia")
        res = supabase.table("zamowienia").select("*").order("id", desc=True).execute()
        if res.data:
            df_h = pd.DataFrame(res.data)
            st.dataframe(df_h, use_container_width=True, hide_index=True)
            df_export = df_h[["data_zgloszenia", "data_realizacji", "pozycja", "wymiary", "material", "ilosc", "projekt", "pilnosc", "zgloszone_przez", "status", "uwagi_admina"]].copy()
            df_export.columns = ["Zgłoszono", "Zrealizowano", "Pozycja", "Wymiary", "Materiał", "Ilość", "Projekt", "Pilność", "Zgłaszający", "Status", "Uwagi"]
            c1, c2 = st.columns(2)
            # Excel
            out_xls = io.BytesIO()
            with pd.ExcelWriter(out_xls, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Historia', startrow=2)
                ws = writer.sheets['Historia']
                ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
                ws.page_setup.fitToPage = True
            c1.download_button("📊 Pobierz Excel (A4 Pion)", out_xls.getvalue(), "historia.xlsx", use_container_width=True)
            # PDF
            pdf_bytes = make_real_pdf(df_export, f"HISTORIA ZAMOWIEN")
            c2.download_button("📄 Pobierz PDF (A4 Pion)", pdf_bytes, "historia.pdf", use_container_width=True)

    elif menu == "📊 Statystyki i Raporty":
        st.title("📊 Statystyki")
        res = supabase.table("zamowienia").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.bar_chart(df['projekt'].value_counts())

    elif menu == "📋 Moje Aktywne":
        st.title("📋 Twoje zamówienia")
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").execute()
        for r in res.data:
            with st.container(border=True):
                st.markdown(f"### 📦 {r['pozycja'].upper()} `x {r['ilosc']}`")
                render_status_alert(r['status'])

    # =========================================================================
    # ZAKŁADKA: INSTRUKCJA (ZWARTE I CZYTELNE WYJAŚNIENIE)
    # =========================================================================
    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja Obsługi Systemu")
        
        with st.container(border=True):
            st.markdown("### 📝 Składanie Zamówień")
            st.write("1. Wejdź w zakładkę **Nowe Zamówienie**.")
            st.write("2. Wypełnij nazwę pozycji, ilość oraz dane techniczne (wymiary, materiał).")
            st.write("3. Możesz zrobić zdjęcie telefonem (📷) lub wgrać plik PDF/Zdjęcie z dysku.")
            st.write("4. Wybierz Admina, którego chcesz powiadomić i kliknij **Wyślij**.")
            st.info("💡 Po wysłaniu pojawi się przycisk WhatsApp – kliknij go, aby od razu przesłać treść zamówienia do admina.")

        with st.container(border=True):
            st.markdown("### ⚙️ Zarządzanie Realizacją (Admin)")
            st.write("Wszystkie aktywne zamówienia są widoczne w **Panelu Realizacji**.")
            st.markdown("- **Zmiana statusu:** Wybierz nowy status z listy i wpisz notatkę, a następnie kliknij dyskietkę (**💾**).")
            st.markdown("- **Powiadomienia:** Przycisk **📲 WA** wysyła aktualizację statusu bezpośrednio do osoby, która zamówiła towar.")
            st.markdown("- **Dodatkowi Odbiorcy:** Użyj **➕ Inni**, aby wysłać tę samą wiadomość do kilku osób naraz (np. na budowę).")
            st.markdown("- **Narzędzia:** Ikona zębatki (**⚙️**) pozwala na edycję szczegółów lub usunięcie zamówienia.")

        with st.container(border=True):
            st.markdown("### 🔎 Historia i Raporty")
            st.write("W sekcji **Historia i Szukaj** możesz przeglądać wszystkie archiwalne zamówienia.")
            st.markdown("- **Eksport danych:** Dostępne są dwa profesjonalne przyciski eksportu.")
            st.markdown("- **Excel:** Pełna tabela z kolorami, gotowa do dalszej obróbki.")
            st.markdown("- **PDF:** Przejrzysty dokument sformatowany pod wydruk **A4 w pionie**.")

        with st.container(border=True):
            st.markdown("### 👥 Bezpieczeństwo i Konta")
            st.write("- Hasło Szefa (Emila) jest widoczne **tylko dla niego**.")
            st.write("- Inni administratorzy widzą hasła użytkowników, aby móc im pomóc w logowaniu, ale nie widzą haseł innych adminów.")
            st.warning("⚠️ Pamiętaj, aby przy dodawaniu konta podać numer telefonu z kodem kraju (np. 48123456789), aby WhatsApp działał poprawnie.")

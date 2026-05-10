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
                        else: st.error("Błędne hasło!")
                    else: st.error("Użytkownik nie istnieje!")
else:
    # --- MENU BOCZNE (ZAKTUALIZOWANE NAZWY) ---
    with st.sidebar:
        st.success(f"Zalogowano: **{st.session_state.uzytkownik}**")
        st.divider()
        opcje = ["📝 Nowe Zamówienie", "📋 Moje Aktywne", "🔎 Historia i Raporty", "📊 Statystyki", "📖 Instrukcja"]
        if st.session_state.rola == "admin":
            opcje.insert(1, "⚙️ Panel Realizacji (Admin)")
            opcje.insert(4, "👥 Zarządzanie Kontami")
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

    # --- FUNKCJA PDF ---
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
        with st.container(border=True):
            pozycja = st.text_input("🔧 Pozycja (np. Śruba zamkowa)")
            c1, c2 = st.columns(2)
            wymiary = c1.text_input("📏 Wymiary")
            material = c2.text_input("🧱 Materiał")
            c3, c4 = st.columns(2)
            ilosc = c3.text_input("🔢 Ilość")
            pilnosc = c4.selectbox("🚨 Pilność", ["Normalna", "PILNE ⚡", "KRYTYCZNE 🛑"])
            projekt = st.text_input("🏗️ Projekt / Cel")
            st.divider()
            plik_upload = st.file_uploader("📁 Wybierz plik", type=["jpg", "jpeg", "png", "pdf"])
            if st.button("WYŚLIJ ZAMÓWIENIE", type="primary", use_container_width=True):
                if pozycja and ilosc:
                    url_zdj = ""
                    if plik_upload:
                        nazwa = f"{int(time.time())}.jpg"
                        supabase.storage.from_("zdjecia_zamowien").upload(nazwa, plik_upload.getvalue())
                        url_zdj = supabase.storage.from_("zdjecia_zamowien").get_public_url(nazwa)
                    supabase.table("zamowienia").insert({"pozycja": pozycja, "wymiary": wymiary, "material": material, "ilosc": ilosc, "projekt": projekt, "pilnosc": pilnosc, "status": "Oczekujące", "zgloszone_przez": st.session_state.uzytkownik, "data_zgloszenia": str(datetime.today().date()), "zdjecie_url": url_zdj}).execute()
                    st.success("Wysłano!"); time.sleep(1); st.rerun()

    elif menu == "⚙️ Panel Realizacji (Admin)":
        st.title("⚙️ Panel Realizacji")
        res = supabase.table("zamowienia").select("*").neq("status", "Zrealizowane").order("id", desc=True).execute()
        for r in res.data:
            with st.container(border=True):
                st.markdown(f"### 📦 {r['pozycja'].upper()} x {r['ilosc']}")
                c_st, c_uw, c_zap = st.columns([2, 4, 1])
                st_list = ["Oczekujące", "Zamówione", "Niedostępne", "Zamiennik", "Zrealizowane"]
                n_st = c_st.selectbox("Status", st_list, index=st_list.index(r['status']), key=f"s_{r['id']}")
                n_uw = c_uw.text_input("Notatka", value=r.get('uwagi_admina') or "", key=f"u_{r['id']}")
                if c_zap.button("💾", key=f"b_{r['id']}"):
                    u_data = {"status": n_st, "uwagi_admina": n_uw}
                    if n_st == "Zrealizowane": u_data["data_realizacji"] = str(datetime.today().date())
                    supabase.table("zamowienia").update(u_data).eq("id", r['id']).execute(); st.rerun()

    elif menu == "🔎 Historia i Raporty":
        st.title("🔎 Historia i Raporty")
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

    # =========================================================================
    # ZAKŁADKA: STATYSTYKI (ROZBUDOWANA)
    # =========================================================================
    elif menu == "📊 Statystyki":
        st.title("📊 Statystyki i Analityka")
        res = supabase.table("zamowienia").select("*").execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            
            # WSKAŹNIKI OGÓLNE (METRYKI)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Wszystkich zamówień", len(df))
            m2.metric("Oczekujące", len(df[df['status'] == 'Oczekujące']))
            m3.metric("Zrealizowane", len(df[df['status'] == 'Zrealizowane']))
            
            # Obliczanie średniego czasu realizacji
            df['data_zgloszenia'] = pd.to_datetime(df['data_zgloszenia'])
            df['data_realizacji'] = pd.to_datetime(df['data_realizacji'])
            df_zrealizowane = df[df['data_realizacji'].notna()]
            if not df_zrealizowane.empty:
                sredni_czas = (df_zrealizowane['data_realizacji'] - df_zrealizowane['data_zgloszenia']).dt.days.mean()
                m4.metric("Średni czas realizacji", f"{sredni_czas:.1f} dni")
            else:
                m4.metric("Średni czas realizacji", "---")

            st.divider()

            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("👤 Zamówienia wg Osób")
                st.bar_chart(df['zgloszone_przez'].value_counts())
                
                st.subheader("🚨 Rozkład Pilności")
                st.bar_chart(df['pilnosc'].value_counts())

            with col_b:
                st.subheader("🏗️ Zamówienia wg Projektu")
                st.bar_chart(df['projekt'].value_counts())
                
                st.subheader("🔝 Top 5 Produktów")
                top_produkty = df['pozycja'].value_counts().head(5)
                st.table(top_produkty)

            st.divider()
            with st.expander("💡 Podpowiedź: Co jeszcze może się przydać?"):
                st.markdown("""
                * **Koszty:** Jeśli dodamy kolumnę 'Cena', będziemy mogli generować wykresy wydatków na konkretne budowy.
                * **Dostawcy:** Jeśli będziesz wpisywać, gdzie kupiłeś towar, statystyki pokażą, u którego dostawcy zostawiasz najwięcej pieniędzy.
                * **Czas pracy admina:** Możemy mierzyć, jak szybko admin reaguje na zamówienie (zmienia status z Oczekujące na Zamówione).
                """)
        else:
            st.info("Brak danych do wygenerowania statystyk.")

    elif menu == "📋 Moje Aktywne":
        st.title("📋 Twoje zamówienia")
        res = supabase.table("zamowienia").select("*").eq("zgloszone_przez", st.session_state.uzytkownik).neq("status", "Zrealizowane").execute()
        for r in res.data:
            with st.container(border=True):
                st.markdown(f"### 📦 {r['pozycja'].upper()} x {r['ilosc']}")
                render_status_alert(r['status'])

    elif menu == "📖 Instrukcja":
        st.title("📖 Instrukcja")
        st.write("W zakładce Statystyki sprawdzisz efektywność i najczęstsze wybory.")

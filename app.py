import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. POŁĄCZENIE
URL = "https://hdmptdcuqxqutfgrgmrj.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkbXB0ZGN1cXhxdXRmZ3JnbXJqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3NzQ2NTksImV4cCI6MjA5MjM1MDY1OX0.ZI18vTCpYloVOdzpZuVHYVH2OwKJMsrQINgaJNl-vho"
supabase = create_client(URL, KEY)

st.set_page_config(layout="wide")

# WIELKI TESTOWY NAPIS - Jeśli go nie widzisz, Twój kod się nie zaktualizował!
st.error("# 🚨 WERSJA TESTOWA: FILTROWANIE BARTKA 🚨")

# 2. PROSTA LISTA OSÓB
res_p = supabase.table("pracownicy").select("login").execute()
lista_osob = sorted([p['login'] for p in res_p.data]) if res_p.data else []

st.write("### KROK 1: Wybierz osobę")
wybrany = st.selectbox("Wybierz z listy:", ["-- NIKT --"] + lista_osob)

st.divider()

# 3. LOGIKA FILTROWANIA
if wybrany != "-- NIKT --":
    st.write(f"### KROK 2: Historia dla: {wybrany}")
    
    # Pobieramy wpisy TYLKO dla tej osoby
    res = supabase.table("wydania").select("*").eq("kto_pobiera", wybrany).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        st.success(f"Znaleziono {len(df)} wpisów dla {wybrany}")
        st.dataframe(df[['narzedzie', 'powod', 'data_wydania']], use_container_width=True)
    else:
        st.warning(f"Brak wpisów w bazie dla: {wybrany}")
else:
    st.info("Wybierz kogoś powyżej, aby zobaczyć historię.")
    st.write("### Ostatnie 3 wpisy w całej bazie (ogólnie):")
    res_last = supabase.table("wydania").select("*").order("id", desc=True).limit(3).execute()
    if res_last.data:
        st.table(pd.DataFrame(res_last.data)[['kto_pobiera', 'narzedzie']])

# 4. DODAWANIE (Bardzo proste)
st.divider()
st.write("### KROK 3: Dodaj nowy wpis")
with st.container(border=True):
    n = st.text_input("Co wydajesz?")
    p = st.text_input("Cel?")
    if st.button("ZAPISZ"):
        if wybrany != "-- NIKT --" and n:
            supabase.table("wydania").insert({"kto_pobiera": wybrany, "narzedzie": n, "powod": p}).execute()
            st.rerun()
        else:
            st.error("Wybierz osobę i wpisz narzędzie!")

import requests
import streamlit as st
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.title("Znajdź lekarza po jedo danych")

try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        st.success("Połączenie z backendem działa poprawnie!")
    else:
        st.error("Błąd połączenia z backendem")
except Exception as e:
    st.error(f"Błąd połączenia z backendem: {e}")

try:
    response = requests.get(f"{BACKEND_URL}/doctors", timeout=5)
    if response.status_code == 200:
        doctors_data = response.json()
        if  not doctors_data:
            st.warning("Brak aktywnych lekarzy w bazie.")
    else:
        st.warning("Błąd pobrania danych lekarzy")
        st.warning(f"{response.status_code}, {response.text}")
        doctors_data = []
except Exception as e:
    st.error(f"Błąd połączenia z backendem: {e}")
    doctors_data = []

with st.subheader("Wyszukaj lekarza"):
    with st.expander("Wyszukaj lekarza"):
        wybrany_lekarz_szukaj = st.selectbox(
            "Wybierz lekarza",
            options=doctors_data,
            format_func=lambda x: f"{x['imie']} {x['nazwisko']} ({x['specjalizacja']})",
            key="search_doc_select"
        )
        if st.button("Pokaż szczegóły lekarza", disabled=not doctors_data):
            try:
                res = requests.get(f"{BACKEND_URL}/doctors/{wybrany_lekarz_szukaj['id']}", timeout=5)
                if res.status_code == 200:
                    d = res.json()
                    status_txt = "Aktywny" if d["aktywny"] else "Nieaktywny"
                    st.success(f"Lekarz #{d['id']}: {d['imie']} {d['nazwisko']} ({d['specjalizacja']})")
                    st.write(f"Godziny: **{d['godzina_od']}–{d['godzina_do']}** | Gabinet: **{d['gabinet']}** | Status: **{status_txt}**")
                elif res.status_code == 404:
                    st.warning(res.json().get("detail", "Nie znaleziono lekarza."))
                else:
                    st.error(f"Błąd serwera: {res.status_code}")
            except Exception as e:
                st.error(f"Błąd połączenia z backendem: {e}")


if st.button("Powrót do panelu umawiania wizyt"):
    st.switch_page("app.py")
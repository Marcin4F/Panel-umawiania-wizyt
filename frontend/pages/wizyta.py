import requests
import streamlit as st
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.title("Znajdź wizytę po ID")

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



with st.subheader("Wyszukaj wizytę po ID"):
    with st.expander("Wyszukaj wizytę po ID"):
        wizyta_id = st.number_input("ID wizyty", min_value=1, step=1, key="search_app_id")
        if st.button("Szukaj wizyty"):
            try:
                res = requests.get(f"{BACKEND_URL}/appointments/{wizyta_id}", timeout=5)
                if res.status_code == 200:
                    w = res.json()
                    st.success(f"Wizyta #{w['id']}: {w['lekarz']} ({w['specjalizacja']})")
                    st.write(f"Godzina: **{w['godzina']}** | Dostępna: **{w['dostepna']}**")
                elif res.status_code == 404:
                    st.warning(res.json().get("detail", "Nie znaleziono wizyty."))
                else:
                    st.error(f"Błąd serwera: {res.status_code}")
            except Exception as e:
                st.error(f"Błąd połączenia z backendem: {e}")


if st.button("Powrót do panelu umawiania wizyt"):
    st.switch_page("app.py")
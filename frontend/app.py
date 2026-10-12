import requests
import streamlit as st

st.title("Panel umawiania wizyt")

# komunikacja po http z backendem
try:
    response = requests.get("http://backend:8000/appointments", timeout=5)
    if response.status_code == 200:
        data = response.json()
        st.table(data)  # wyświetlenie danych w formie tabeli
    else:
        st.error("Błąd pobrania danych")
except Exception as e:
    # TODO: obsługa błędów, bez komunikatów (niski priorytet)
    st.error(f"Błąd połączenia z backendem {e}")

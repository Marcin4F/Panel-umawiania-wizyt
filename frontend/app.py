import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.title("Panel umawiania wizyt")

with st.expander("Dodaj nową wizytę"):
    with st.form("new_appointment"):
        lekarz = st.text_input("Lekarz (imię i nazwisko)")
        godzina = st.text_input("Godzina (format HH:MM, np. 14:30)")
        dostepna = st.checkbox("Dostępna", value=True)
        submitted = st.form_submit_button("Dodaj")

        if submitted:
            res = requests.post(
                f"{BACKEND_URL}/appointments",
                json={"lekarz": lekarz, "godzina": godzina, "dostepna": dostepna},
            )
            if res.status_code == 201:
                st.success("Wizyta dodana pomyślnie!")
                st.rerun()
            else:
                st.error(f"Błąd walidacji: Niepoprawne dane wejściowe lub format godziny.")

try:
    response = requests.get(f"{BACKEND_URL}/appointments", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if data:
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
            col1.write("ID")
            col2.write("Lekarz")
            col3.write("Godzina")
            col4.write("Dostępna")
            col5.write("Akcja")

            for item in data:
                c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
                c1.write(str(item.get("id")))
                c2.write(str(item.get("lekarz")))
                c3.write(str(item.get("godzina")))
                c4.write(str(item.get("dostepna")))

                if c5.button("Usuń", key=f"delete_{item.get('id')}"):
                    del_res = requests.delete(
                        f"{BACKEND_URL}/appointments/{item.get('id')}"
                    )
                    if del_res.status_code == 200:
                        st.success(f"Usunięto wizytę {item.get('id')}")
                        st.rerun()
                    else:
                        st.error(f"Błąd usuwania: {del_res.text}")
        else:
            st.info("Brak zaplanowanych wizyt.")
    else:
        st.error("Błąd pobrania danych")
except Exception as e:
    st.error(f"Błąd połączenia z backendem: {e}")

#Wspomoganie AI podczas ustalania wyglądu np 'st.columns([1, 3, 2, 2, 2])' oraz powtarzajacth sie sekwencji kodu np kolumn.
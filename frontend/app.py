import requests
import streamlit as st
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.title("Panel umawiania wizyt")

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

    
with st.expander("Dodaj nową wizytę"):
    with st.form("new_appointment"):
        wybor_lekarza = st.selectbox("Lekarz (imię i nazwisko)", options=doctors_data, format_func=lambda x: f"{x['imie']} {x['nazwisko']} ({x['specjalizacja']}) godziny pracy: {x['godzina_od']} - {x['godzina_do']}")
        godzina = st.text_input("Godzina (format HH:MM, np. 14:30)")
        dostepna = st.checkbox("Dostępna", value=True)
        submitted = st.form_submit_button("Dodaj", disabled = not doctors_data)

        if submitted:
            res = requests.post(
                f"{BACKEND_URL}/appointments",
                json={"lekarz_id": wybor_lekarza['id'], "godzina": godzina, "dostepna": dostepna},
            )
            if res.status_code == 201:
                st.success("Wizyta dodana pomyślnie!")
                st.rerun()
            else:
                st.error(f"Błąd walidacji: Niepoprawne dane wejściowe lub format godziny.")

try:
    tylko_dostepne = st.checkbox("Pokaż tylko dostępne wizyty")
    response = requests.get(f"{BACKEND_URL}/appointments",params={"tylko_dostepne": tylko_dostepne}, timeout=5)
    if response.status_code == 200:
        data = response.json()
        if data:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 2, 2, 2, 2, 2])
            col1.write("ID")
            col2.write("Lekarz")
            col3.write("Godzina")
            col4.write("Specjalizacja")
            col5.write("Gabinet")
            col6.write("Dostępna")
            col7.write("Akcja")

            for item in data:
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 3, 2, 2, 2, 2, 2])
                c1.write(str(item.get("id")))
                c2.write(str(item.get("lekarz")))
                c3.write(str(item.get("godzina")))
                c4.write(str(item.get("specjalizacja")))
                c5.write(str(item.get("gabinet")))
                c6.write(str(item.get("dostepna")))

                if c7.button("Usuń", key=f"delete_{item.get('id')}"):
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

col_search1, col_search2 = st.columns(2)

with col_search1:
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

with col_search2:
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

#Wspomaganie AI podczas ustalania wyglądu np 'st.columns([1, 3, 2, 2, 2])' oraz powtarzajacth sie sekwencji kodu np kolumn.
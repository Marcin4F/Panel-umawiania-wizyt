import os
from typing import Optional
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
import psycopg
from psycopg.rows import dict_row
from datetime import time
from psycopg import errors

# Pomoc AI przy przejściu na postgreSQL
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "wizyty")
DB_USER = os.getenv("DB_USER", "wizyty")
DB_PASSWORD = os.getenv("DB_PASSWORD", "wizyty")

app = FastAPI(title="Panel umawiania wizyt API")


def polacz():
    # Nowe polaczenie przy kazdym zapytaniu (mala skala, wiec wystaarcza)
    # dict_row sprawia ze wiersze wracaja jako slowniki, wiec fastAPI od razu zamienia je na json
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        row_factory=dict_row,
        connect_timeout=3,
    )


class AppointmentCreate(BaseModel):
    lekarz_id: int = Field(..., gt=0, description="ID lekarza z tabeli lekarze")
    godzina: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$", description="Format HH:MM")
    dostepna: bool = True


class AppointmentUpdate(BaseModel):
    lekarz_id: Optional[int] = Field(None, gt=0)
    godzina: Optional[str] = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    dostepna: Optional[bool] = None


# Pomoc AI przy dodaniu tabeli lekarze i JOIN-a
# Wizyta razem z danymi lekarza; pole "lekarz" zostaje, żeby frontend dalej je wyświetlał
WIZYTA_SELECT = """
    SELECT w.id,
           w.lekarz_id,
           l.imie || ' ' || l.nazwisko AS lekarz,
           l.specjalizacja,
           w.godzina,
           w.dostepna
    FROM wizyty w
    JOIN lekarze l ON l.id = w.lekarz_id
"""


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    try:
        with polacz() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Baza danych niedostępna: {e}",
        )


@app.get("/appointments")
def get_all_appointments(tylko_dostepne: bool = Query(False)):
    sql = WIZYTA_SELECT
    if tylko_dostepne:
        sql += " WHERE w.dostepna = TRUE"
    sql += " ORDER BY w.id"

    with polacz() as conn:
        return conn.execute(sql).fetchall()


@app.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int):
    with polacz() as conn:
        wizyta = conn.execute(WIZYTA_SELECT + " WHERE w.id = %s", (appointment_id,)).fetchone()

    if wizyta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wizyta o ID {appointment_id} nie istnieje.",
        )
    return wizyta


# Pomoc AI w przerobieniu POSTa po zmianie działania bazy
# TODO: tymczasowo przestaje działać dokoki nie zostaną wprowadzone zmiany na frontendzie
@app.post("/appointments", status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate):
    with polacz() as conn:
        lekarz = conn.execute(
            "SELECT godzina_od, godzina_do, aktywny FROM lekarze WHERE id = %s",
            (payload.lekarz_id,),
        ).fetchone()

        if lekarz is None or not lekarz["aktywny"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lekarz o ID {payload.lekarz_id} nie istnieje.",
            )

        # wizyta musi zaczynać się w godzinach pracy lekarza (od <= godzina < do)
        if not (lekarz["godzina_od"] <= time.fromisoformat(payload.godzina) < lekarz["godzina_do"]):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Lekarz przyjmuje w godzinach "
                       f"{lekarz['godzina_od']:%H:%M}-{lekarz['godzina_do']:%H:%M}.",
            )

        try:
            nowa = conn.execute(
                "INSERT INTO wizyty (lekarz_id, godzina, dostepna) VALUES (%s, %s, %s) RETURNING id",
                (payload.lekarz_id, payload.godzina, payload.dostepna),
            ).fetchone()
        except errors.UniqueViolation:
            # naruszenie UNIQUE (lekarz_id, godzina) z init.sql
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lekarz ma już wizytę o godzinie {payload.godzina}.",
            )
    return conn.execute(WIZYTA_SELECT + " WHERE w.id = %s", (nowa["id"],)).fetchone()


@app.delete("/appointments/{appointment_id}", status_code=status.HTTP_200_OK)
def delete_appointment(appointment_id: int):
    with polacz() as conn:
        kursor = conn.execute("DELETE FROM wizyty WHERE id = %s", (appointment_id,))

    # rowcount mówi, ile wierszy usunięto - 0 oznacza, że takiej wizyty nie było
    if kursor.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wizyta o ID {appointment_id} nie istnieje.",
        )
    return {"message": f"Wizyta o ID {appointment_id} została usunięta."}


@app.get("/doctors")
def get_all_doctors(tylko_aktywni: bool = Query(True)):
    # to_char, żeby godziny w JSON-ie miały format "08:00", a nie "08:00:00"
    sql = """
        SELECT id, imie, nazwisko, specjalizacja,
               to_char(godzina_od, 'HH24:MI') AS godzina_od,
               to_char(godzina_do, 'HH24:MI') AS godzina_do,
               gabinet, aktywny
        FROM lekarze
    """
    if tylko_aktywni:
        sql += " WHERE aktywny = TRUE"
    sql += " ORDER BY nazwisko, imie"

    with polacz() as conn:
        return conn.execute(sql).fetchall()


@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int):
    with polacz() as conn:
        lekarz = conn.execute(
            """
            SELECT id, imie, nazwisko, specjalizacja,
                   to_char(godzina_od, 'HH24:MI') AS godzina_od,
                   to_char(godzina_do, 'HH24:MI') AS godzina_do,
                   gabinet, aktywny
            FROM lekarze WHERE id = %s
            """,
            (doctor_id,),
        ).fetchone()

    if lekarz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lekarz o ID {doctor_id} nie istnieje.",
        )
    return lekarz

#Pomoc AI przy napisaniu walidacji danych.
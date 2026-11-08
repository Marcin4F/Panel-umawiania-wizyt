import os
from typing import Optional
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
import psycopg
from psycopg.rows import dict_row

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
    lekarz: str = Field(
        ..., min_length=3, description="Imię i nazwisko lekarza"
    )
    godzina: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$", description="Format HH:MM")
    dostepna: bool = True


class AppointmentUpdate(BaseModel):
    lekarz: Optional[str] = Field(None, min_length=3)
    godzina: Optional[str] = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    dostepna: Optional[bool] = None


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
    sql = "SELECT id, lekarz, godzina, dostepna FROM wizyty"
    if tylko_dostepne:
        sql += " WHERE dostepna = TRUE"
    sql += " ORDER BY id"

    with polacz() as conn:
        return conn.execute(sql).fetchall()


@app.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int):
    with polacz() as conn:
        wizyta = conn.execute(
            "SELECT id, lekarz, godzina, dostepna FROM wizyty WHERE id = %s",
            (appointment_id,),
        ).fetchone()

    if wizyta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wizyta o ID {appointment_id} nie istnieje.",
        )
    return wizyta


@app.post("/appointments", status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate):
    # RETURNING zwraca od razu cały zapisany wiersz razem z id nadanym przez bazę
    with polacz() as conn:
        wizyta = conn.execute(
            """
            INSERT INTO wizyty (lekarz, godzina, dostepna)
            VALUES (%s, %s, %s)
            RETURNING id, lekarz, godzina, dostepna
            """,
            (payload.lekarz, payload.godzina, payload.dostepna),
        ).fetchone()
    return wizyta


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


#Pomoc AI przy napisaniu walidacji danych.
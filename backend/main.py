import json
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "db")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

app = FastAPI(title="Panel umawiania wizyt API")
client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


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
        client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis unavailable: {str(e)}",
        )


@app.get("/appointments")
def get_all_appointments(tylko_dostepne: bool = Query(False)):
    keys = client.keys("appointment:*")
    appointments = []
    for key in keys:
        raw_data = client.get(key)
        if raw_data:
            appointments.append(json.loads(raw_data))

    appointments.sort(key=lambda item: item.get("id", 0))

    if tylko_dostepne:
        appointments = [a for a in appointments if a.get("dostepna") is True]

    return appointments


@app.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int):
    raw_data = client.get(f"appointment:{appointment_id}")
    if not raw_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wizyta o ID {appointment_id} nie istnieje.",
        )
    return json.loads(raw_data)


@app.post("/appointments", status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate):
    # Generowanie auto-inkrementowanego ID w Redis
    new_id = client.incr("appointment_id_seq")
    appointment_data = {"id": new_id, **payload.model_dump()}

    client.set(f"appointment:{new_id}", json.dumps(appointment_data))
    return appointment_data


@app.delete("/appointments/{appointment_id}", status_code=status.HTTP_200_OK)
def delete_appointment(appointment_id: int):
    key = f"appointment:{appointment_id}"
    if not client.exists(key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wizyta o ID {appointment_id} nie istnieje.",
        )
    client.delete(key)
    return {"message": f"Wizyta o ID {appointment_id} została usunięta."}


#Pomoc AI przy napisaniu walidacji danych.
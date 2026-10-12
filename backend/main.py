import redis
from fastapi import FastAPI

# próba połączenia z bazą
client = redis.Redis(host="db", port=6379)
app = FastAPI()


@app.get("/appointments")
def get_appointments():
    # lista przykładowych danych w formacie JSON - WYGENEROWANIE PRZEZ AI
    return [
        {"id": 1, "lekarz": "Dr Kowalski", "godzina": "10:00", "dostepna": True},
        {"id": 2, "lekarz": "Dr Nowak", "godzina": "11:30", "dostepna": False},
    ]

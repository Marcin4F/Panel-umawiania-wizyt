# Projekt numer 31 - System umawiania wizyt u lekarza

Aplikacja opiera się na architekturze trójwarstwowej, w której każdy z elementów działa w wyizolowanym kontenerze Docker.

## Architektura i użyte technologie

```
frontend (Streamlit)  --HTTP/JSON-->  backend (FastAPI)  --SQL-->  db (PostgreSQL)
```

Frontend nigdy nie łączy się bezpośrednio z bazą danych - cała komunikacja przechodzi przez API backendu.

1. **Warstwa prezentacji (Frontend)**
   * Technologia: `Python` + `Streamlit`
   * Działanie: Pobiera z backendu listę wizyt w formacie JSON i wyświetla ją w tabeli. Pozwala dodać nową wizytę (formularz) oraz usunąć istniejącą (przycisk „Usuń” przy każdej wizycie).
   * Dostępny lokalnie pod adresem: `http://localhost:8501`

2. **Warstwa logiki biznesowej (Backend)**
   * Technologia: `Python` + `FastAPI` + `Uvicorn` + `psycopg`
   * Działanie: Wystawia REST API (opisane niżej), waliduje dane wejściowe i wykonuje zapytania SQL do bazy.
   * Dostępny lokalnie pod adresem: `http://localhost:8000` (interaktywna dokumentacja API: `http://localhost:8000/docs`)

3. **Warstwa danych (Baza danych)**
   * Technologia: `PostgreSQL 17` (obraz `postgres:17-alpine` z Docker Hub)
   * Działanie: Relacyjna baza danych przechowująca wizyty w tabeli `wizyty`. Tabela jest tworzona automatycznie przy pierwszym uruchomieniu przez skrypt [db/init.sql](db/init.sql).
   * Dane są zapisywane w wolumenie `pgdata`, więc przetrwają restart kontenerów.
   * Baza nie jest wystawiona na zewnątrz - backend łączy się z nią przez wewnętrzną sieć Docker Compose.

### Kolejność uruchamiania i healthchecki

Kolejność startu kontenerów jest wymuszona w [docker-compose.yml](docker-compose.yml) przez `depends_on` z `condition: service_healthy`:

1. `db` - healthcheck: `pg_isready` (baza przyjmuje połączenia),
2. `backend` - startuje dopiero, gdy `db` jest zdrowa; healthcheck: zapytanie `GET /health`,
3. `frontend` - startuje dopiero, gdy `backend` jest zdrowy.

## Jak uruchomić projekt?

Upewnij się, że masz zainstalowane środowisko **Docker Desktop**. Następnie otwórz terminal w głównym folderze projektu i wpisz polecenie:

```bash
docker compose up --build
```

Po zbudowaniu obrazów i uruchomieniu kontenerów, interfejs użytkownika będzie dostępny w przeglądarce pod adresem: `http://localhost:8501`

Przydatne polecenia:

```bash
docker compose logs -f backend                                  # podgląd logów backendu
docker compose exec db psql -U wizyty -d wizyty -c "SELECT * FROM wizyty;"   # podgląd danych w bazie
docker compose down                                             # zatrzymanie kontenerów (dane zostają)
docker compose down -v                                          # zatrzymanie i usunięcie danych z bazy
```

Skrypt `db/init.sql` wykonuje się tylko wtedy, gdy wolumen z danymi jest pusty. Po zmianie schematu tabeli należy zresetować bazę poleceniem `docker compose down -v`.

## Konfiguracja (zmienne środowiskowe)

Wszystkie ustawienia są przekazywane przez zmienne środowiskowe zdefiniowane w `docker-compose.yml`.

| Kontener | Zmienna | Wartość w compose | Opis |
|---|---|---|---|
| `db` | `POSTGRES_DB` | `wizyty` | nazwa tworzonej bazy |
| `db` | `POSTGRES_USER` | `wizyty` | użytkownik bazy |
| `db` | `POSTGRES_PASSWORD` | `wizyty` | hasło użytkownika |
| `backend` | `DB_HOST` | `db` | adres serwera bazy (nazwa usługi w compose) |
| `backend` | `DB_PORT` | `5432` | port bazy |
| `backend` | `DB_NAME` | `wizyty` | nazwa bazy |
| `backend` | `DB_USER` | `wizyty` | użytkownik bazy |
| `backend` | `DB_PASSWORD` | `wizyty` | hasło użytkownika |
| `frontend` | `BACKEND_URL` | `http://backend:8000` | adres API backendu |

## Model danych

Tabela `wizyty` (definicja w [db/init.sql](db/init.sql)):

| Kolumna | Typ | Opis |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | identyfikator nadawany automatycznie przez bazę |
| `lekarz` | `TEXT NOT NULL` | imię i nazwisko lekarza |
| `godzina` | `VARCHAR(5) NOT NULL` | godzina wizyty w formacie `HH:MM` |
| `dostepna` | `BOOLEAN NOT NULL DEFAULT TRUE` | czy termin jest wolny |

## API backendu

Wszystkie dane są przesyłane w formacie **JSON** (nagłówek `Content-Type: application/json`).

### Obiekt wizyty

```json
{
  "id": 1,
  "lekarz": "Jan Kowalski",
  "godzina": "09:30",
  "dostepna": true
}
```

| Pole | Typ | Wymagane przy tworzeniu | Walidacja |
|---|---|---|---|
| `id` | liczba całkowita | nie (nadaje baza) | - |
| `lekarz` | tekst | tak | minimum 3 znaki |
| `godzina` | tekst | tak | format `HH:MM`, zakres `00:00`-`23:59` |
| `dostepna` | wartość logiczna | nie (domyślnie `true`) | `true` / `false` |

### Lista endpointów

| Metoda | Ścieżka | Opis | Kody odpowiedzi |
|---|---|---|---|
| `GET` | `/health` | stan backendu i połączenia z bazą | `200`, `503` |
| `GET` | `/appointments` | lista wszystkich wizyt, posortowana po `id` | `200` |
| `GET` | `/appointments?tylko_dostepne=true` | lista tylko wolnych terminów | `200` |
| `GET` | `/appointments/{id}` | pojedyncza wizyta | `200`, `404`, `422` |
| `POST` | `/appointments` | dodanie nowej wizyty | `201`, `422` |
| `DELETE` | `/appointments/{id}` | usunięcie wizyty | `200`, `404`, `422` |

### Przykłady

**`GET /health`** → `200 OK`

```json
{ "status": "healthy", "database": "connected" }
```

Gdy baza jest niedostępna → `503 Service Unavailable`:

```json
{ "detail": "Baza danych niedostępna: ..." }
```

**`GET /appointments`** → `200 OK`

```json
[
  { "id": 1, "lekarz": "Jan Kowalski", "godzina": "09:30", "dostepna": true },
  { "id": 2, "lekarz": "Anna Nowak", "godzina": "14:00", "dostepna": false }
]
```

**`GET /appointments/1`** → `200 OK`

```json
{ "id": 1, "lekarz": "Jan Kowalski", "godzina": "09:30", "dostepna": true }
```

**`POST /appointments`**

Treść żądania:

```json
{ "lekarz": "Jan Kowalski", "godzina": "09:30", "dostepna": true }
```

Odpowiedź → `201 Created` (zapisana wizyta razem z nadanym `id`):

```json
{ "id": 1, "lekarz": "Jan Kowalski", "godzina": "09:30", "dostepna": true }
```

**`DELETE /appointments/1`** → `200 OK`

```json
{ "message": "Wizyta o ID 1 została usunięta." }
```

### Obsługa błędów

**`404 Not Found`** - wizyta o podanym `id` nie istnieje (`GET` i `DELETE /appointments/{id}`):

```json
{ "detail": "Wizyta o ID 999 nie istnieje." }
```

**`422 Unprocessable Entity`** - niepoprawne dane wejściowe: brak wymaganego pola, za krótkie nazwisko lekarza, zły format godziny, treść żądania niebędąca JSON-em albo `id` niebędące liczbą. Odpowiedź wskazuje, które pole jest błędne, np. dla `"godzina": "25:99"`:

```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["body", "godzina"],
      "msg": "String should match pattern '^(?:[01]\\d|2[0-3]):[0-5]\\d$'",
      "input": "25:99"
    }
  ]
}
```

---
*Uwaga: Ten plik został wygenerowany przez AI. W kodzie źródłowym projektu dodano odpowiednie komentarze w miejscach, gdzie wsparto się asystentem AI.*

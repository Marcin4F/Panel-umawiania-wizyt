# Projekt numer 31 - System umawiania wizyt u lekarza

Aplikacja opiera się na architekturze trójwarstwowej, w której każdy z elementów działa w wyizolowanym kontenerze Docker.

## Architektura i użyte technologie

```
frontend (Streamlit)  --HTTP/JSON-->  backend (FastAPI)  --SQL-->  db (PostgreSQL)
        └──── siec_frontend ────┘             └──── siec_bazy ────┘
```

Frontend nigdy nie łączy się bezpośrednio z bazą danych - cała komunikacja przechodzi przez API backendu. Wymusza to podział na dwie sieci Docker Compose: baza jest tylko w sieci `siec_bazy`, frontend tylko w `siec_frontend`, a backend w obu.

1. **Warstwa prezentacji (Frontend)**
   * Technologia: `Python` + `Streamlit`
   * Działanie: Pobiera z backendu listę wizyt w formacie JSON i wyświetla ją w tabeli. Pozwala dodać nową wizytę (formularz) oraz usunąć istniejącą (przycisk „Usuń” przy każdej wizycie).
   * Dostępny lokalnie pod adresem: `http://localhost:8501`
   * **Uwaga:** formularz dodawania wizyty wysyła jeszcze pole `lekarz` (tekst), a backend wymaga teraz `lekarz_id`, więc dodawanie wizyt z poziomu frontendu tymczasowo nie działa. Do zrobienia: wybór lekarza z listy pobieranej z `GET /doctors`.

2. **Warstwa logiki biznesowej (Backend)**
   * Technologia: `Python` + `FastAPI` + `Uvicorn` + `psycopg`
   * Działanie: Wystawia REST API (opisane niżej), waliduje dane wejściowe i wykonuje zapytania SQL do bazy.
   * Dostępny lokalnie pod adresem: `http://localhost:8000` (interaktywna dokumentacja API: `http://localhost:8000/docs`)

3. **Warstwa danych (Baza danych)**
   * Technologia: `PostgreSQL 17` (oficjalny obraz `postgres:17-alpine` z Docker Hub)
   * Działanie: Relacyjna baza danych z dwiema powiązanymi tabelami: `lekarze` i `wizyty` (opis w sekcji [Model danych](#model-danych)).
   * Skrypt inicjalizujący [db/init.sql](db/init.sql) przy pierwszym uruchomieniu tworzy schemat i wstawia dane startowe (5 lekarzy, 11 wizyt).
   * Dane są zapisywane w nazwanym wolumenie `pgdata`, więc przetrwają restart kontenerów.
   * Baza nie ma opublikowanego portu - nie da się z nią połączyć z komputera hosta. Backend łączy się z nią przez wewnętrzną sieć `siec_bazy` pod nazwą hosta `db`.

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
docker compose exec db psql -U wizyty -d wizyty                 # konsola SQL bazy
docker compose exec db psql -U wizyty -d wizyty -c "SELECT * FROM lekarze;"   # podgląd lekarzy
docker compose down                                             # zatrzymanie kontenerów (dane zostają)
docker compose down -v                                          # zatrzymanie i usunięcie danych z bazy
```

Skrypt `db/init.sql` wykonuje się tylko wtedy, gdy wolumen z danymi jest pusty. Po zmianie schematu lub danych startowych należy zresetować bazę poleceniem `docker compose down -v`.

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

Schemat i dane startowe są zdefiniowane w [db/init.sql](db/init.sql). Tabele są połączone relacją jeden do wielu: jeden lekarz może mieć wiele wizyt, każda wizyta należy do dokładnie jednego lekarza.

```
lekarze (1) ────< (N) wizyty
   id  ◄──────────── lekarz_id
```

### Tabela `lekarze`

| Kolumna | Typ | Opis |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | identyfikator nadawany automatycznie przez bazę |
| `imie` | `VARCHAR(50) NOT NULL` | imię lekarza |
| `nazwisko` | `VARCHAR(80) NOT NULL` | nazwisko lekarza |
| `specjalizacja` | `VARCHAR(80) NOT NULL` | np. `Dermatolog`, `Kardiolog` |
| `godzina_od` | `TIME NOT NULL` | początek godzin pracy |
| `godzina_do` | `TIME NOT NULL` | koniec godzin pracy |
| `gabinet` | `VARCHAR(10)` | numer gabinetu (może być pusty) |
| `aktywny` | `BOOLEAN NOT NULL DEFAULT TRUE` | czy lekarz przyjmuje pacjentów; pozwala „wyłączyć” lekarza bez usuwania jego wizyt |

Ograniczenie: `CHECK (godzina_od < godzina_do)`.

### Tabela `wizyty`

| Kolumna | Typ | Opis |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | identyfikator nadawany automatycznie przez bazę |
| `lekarz_id` | `INTEGER NOT NULL` | klucz obcy do `lekarze(id)` |
| `godzina` | `VARCHAR(5) NOT NULL` | godzina wizyty w formacie `HH:MM` |
| `dostepna` | `BOOLEAN NOT NULL DEFAULT TRUE` | czy termin jest wolny |

Ograniczenia:

* `REFERENCES lekarze(id) ON DELETE RESTRICT` - nie można dodać wizyty u nieistniejącego lekarza ani usunąć lekarza, który ma wizyty,
* `UNIQUE (lekarz_id, godzina)` - lekarz nie może mieć dwóch wizyt o tej samej godzinie,
* `CHECK` z wyrażeniem regularnym na kolumnie `godzina` - format `HH:MM` jest sprawdzany także po stronie bazy, nie tylko w backendzie.

### Dane startowe

| id | Lekarz | Specjalizacja | Godziny pracy | Gabinet |
|---|---|---|---|---|
| 1 | Jan Kowalski | Internista | 08:00-14:00 | 101 |
| 2 | Anna Nowak | Dermatolog | 10:00-16:00 | 204 |
| 3 | Piotr Wiśniewski | Kardiolog | 12:00-18:00 | 305 |
| 4 | Katarzyna Wójcik | Pediatra | 07:30-13:30 | 102 |
| 5 | Tomasz Kamiński | Okulista | 09:00-15:00 | 210 |

Do tego 11 wizyt (po 2-3 na lekarza), wszystkie w godzinach pracy danego lekarza, część oznaczona jako zajęta.

## API backendu

Wszystkie dane są przesyłane w formacie **JSON** (nagłówek `Content-Type: application/json`).

### Obiekt wizyty

Backend łączy tabele `wizyty` i `lekarze` (`JOIN`), więc w odpowiedzi oprócz `lekarz_id` są też imię i nazwisko oraz specjalizacja lekarza.

```json
{
  "id": 1,
  "lekarz_id": 1,
  "lekarz": "Jan Kowalski",
  "specjalizacja": "Internista",
  "godzina": "08:00",
  "dostepna": false
}
```

| Pole | Typ | Wymagane przy tworzeniu | Walidacja |
|---|---|---|---|
| `id` | liczba całkowita | nie (nadaje baza) | - |
| `lekarz_id` | liczba całkowita | tak | liczba > 0; lekarz musi istnieć i być aktywny |
| `lekarz` | tekst | nie (tylko w odpowiedzi) | - |
| `specjalizacja` | tekst | nie (tylko w odpowiedzi) | - |
| `godzina` | tekst | tak | format `HH:MM`, zakres `00:00`-`23:59`; musi mieścić się w godzinach pracy lekarza (`godzina_od` ≤ godzina < `godzina_do`) i nie może być zajęta u tego lekarza |
| `dostepna` | wartość logiczna | nie (domyślnie `true`) | `true` / `false` |

### Obiekt lekarza

```json
{
  "id": 1,
  "imie": "Jan",
  "nazwisko": "Kowalski",
  "specjalizacja": "Internista",
  "godzina_od": "08:00",
  "godzina_do": "14:00",
  "gabinet": "101",
  "aktywny": true
}
```

### Lista endpointów

| Metoda | Ścieżka | Opis | Kody odpowiedzi |
|---|---|---|---|
| `GET` | `/health` | stan backendu i połączenia z bazą | `200`, `503` |
| `GET` | `/appointments` | lista wszystkich wizyt, posortowana po `id` | `200` |
| `GET` | `/appointments?tylko_dostepne=true` | lista tylko wolnych terminów | `200` |
| `GET` | `/appointments/{id}` | pojedyncza wizyta | `200`, `404`, `422` |
| `POST` | `/appointments` | dodanie nowej wizyty | `201`, `404`, `409`, `422` |
| `DELETE` | `/appointments/{id}` | usunięcie wizyty | `200`, `404`, `422` |
| `GET` | `/doctors` | lista aktywnych lekarzy, posortowana po nazwisku i imieniu | `200` |
| `GET` | `/doctors?tylko_aktywni=false` | lista wszystkich lekarzy, także nieaktywnych | `200` |
| `GET` | `/doctors/{id}` | pojedynczy lekarz | `200`, `404`, `422` |

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
  { "id": 1, "lekarz_id": 1, "lekarz": "Jan Kowalski", "specjalizacja": "Internista", "godzina": "08:00", "dostepna": false },
  { "id": 2, "lekarz_id": 1, "lekarz": "Jan Kowalski", "specjalizacja": "Internista", "godzina": "08:30", "dostepna": true }
]
```

**`GET /appointments/1`** → `200 OK`

```json
{ "id": 1, "lekarz_id": 1, "lekarz": "Jan Kowalski", "specjalizacja": "Internista", "godzina": "08:00", "dostepna": false }
```

**`POST /appointments`**

Treść żądania:

```json
{ "lekarz_id": 2, "godzina": "12:00", "dostepna": true }
```

Odpowiedź → `201 Created` (zapisana wizyta razem z nadanym `id` i danymi lekarza):

```json
{ "id": 12, "lekarz_id": 2, "lekarz": "Anna Nowak", "specjalizacja": "Dermatolog", "godzina": "12:00", "dostepna": true }
```

**`DELETE /appointments/1`** → `200 OK`

```json
{ "message": "Wizyta o ID 1 została usunięta." }
```

**`GET /doctors`** → `200 OK`

```json
[
  { "id": 5, "imie": "Tomasz", "nazwisko": "Kamiński", "specjalizacja": "Okulista", "godzina_od": "09:00", "godzina_do": "15:00", "gabinet": "210", "aktywny": true },
  { "id": 1, "imie": "Jan", "nazwisko": "Kowalski", "specjalizacja": "Internista", "godzina_od": "08:00", "godzina_do": "14:00", "gabinet": "101", "aktywny": true }
]
```

**`GET /doctors/2`** → `200 OK`

```json
{ "id": 2, "imie": "Anna", "nazwisko": "Nowak", "specjalizacja": "Dermatolog", "godzina_od": "10:00", "godzina_do": "16:00", "gabinet": "204", "aktywny": true }
```

### Obsługa błędów

**`404 Not Found`** - wizyta lub lekarz o podanym `id` nie istnieje (`GET`/`DELETE /appointments/{id}`, `GET /doctors/{id}`), albo w `POST /appointments` podano `lekarz_id` nieistniejącego lub nieaktywnego lekarza:

```json
{ "detail": "Wizyta o ID 999 nie istnieje." }
```

```json
{ "detail": "Lekarz o ID 99 nie istnieje." }
```

**`409 Conflict`** - lekarz ma już wizytę o tej godzinie (naruszenie `UNIQUE (lekarz_id, godzina)` w bazie):

```json
{ "detail": "Lekarz ma już wizytę o godzinie 08:00." }
```

**`422 Unprocessable Entity`** - niepoprawne dane wejściowe. Są dwa rodzaje takich odpowiedzi.

1. Błąd walidacji modelu: brak wymaganego pola, `lekarz_id` niebędące dodatnią liczbą, zły format godziny, treść żądania niebędąca JSON-em albo `id` w ścieżce niebędące liczbą. Odpowiedź wskazuje, które pole jest błędne, np. dla `"godzina": "25:99"`:

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

2. Godzina poza godzinami pracy lekarza, np. `{ "lekarz_id": 2, "godzina": "09:00" }`:

```json
{ "detail": "Lekarz przyjmuje w godzinach 10:00-16:00." }
```

---
*Uwaga: Ten plik został wygenerowany przez AI. W kodzie źródłowym projektu dodano odpowiednie komentarze w miejscach, gdzie wsparto się asystentem AI.*

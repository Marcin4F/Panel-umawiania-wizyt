# Projekt numer 31 - System umawiania wizyt u lekarza

Aplikacja opiera się na architekturze trójwarstwowej, w której każdy z elementów działa w wyizolowanym kontenerze Docker.

## Architektura i użyte technologie

Obecny stan projektu to **szkielet 3 połączonych kontenerów**:

1. **Warstwa prezentacji (Frontend)**
   * Technologia: `Python` + `Streamlit`
   * Działanie: Komunikuje się z backendem po protokole HTTP, pobiera listę dostępnych wizyt w formacie JSON i wyświetla ją użytkownikowi w postaci przejrzystej tabeli.
   * Dostępny lokalnie pod portem: `8501`

2. **Warstwa logiki biznesowej (Backend)**
   * Technologia: `Python` + `FastAPI` + `Uvicorn`
   * Działanie: Wystawia API (endpoint `GET /appointments`), które zwraca dane. Stanowi most pomiędzy warstwą prezentacji a bazą danych.
   * Dostępny lokalnie pod portem: `8000`

3. **Warstwa danych (Baza danych)**
   * Technologia: `Redis` (obraz bazowy z Docker Hub)
   * Działanie: Nierelacyjna baza danych przechowująca informacje o wizytach (komunikuje się z backendem na standardowym porcie `6379`).

## Jak uruchomić projekt?

Upewnij się, że masz zainstalowane środowisko **Docker Desktop**. Następnie otwórz terminal w głównym folderze projektu i wpisz polecenie:

```bash
docker compose up --build
```

Po zbudowaniu obrazów i uruchomieniu kontenerów, interfejs użytkownika będzie dostępny w przeglądarce pod adresem: `http://localhost:8501`

---
*Uwaga: Ten plik został wygenerowany przez AI. W kodzie źródłowym projektu dodano odpowiednie komentarze w miejscach, gdzie wsparto się asystentem AI.*
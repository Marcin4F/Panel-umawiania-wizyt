-- przygotowane przy wsparciu AI
CREATE TABLE IF NOT EXISTS wizyty (
    id        SERIAL PRIMARY KEY,
    lekarz    TEXT       NOT NULL,
    godzina   VARCHAR(5) NOT NULL,
    dostepna  BOOLEAN    NOT NULL DEFAULT TRUE
);

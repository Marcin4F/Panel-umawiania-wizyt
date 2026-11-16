-- przygotowane przy wsparciu AI
-- Schemat: lekarze (1) ---< (N) wizyty, połączone kluczem obcym wizyty.lekarz_id

CREATE TABLE IF NOT EXISTS lekarze (
    id             SERIAL       PRIMARY KEY,
    imie           VARCHAR(50)  NOT NULL,
    nazwisko       VARCHAR(80)  NOT NULL,
    specjalizacja  VARCHAR(80)  NOT NULL,
    godzina_od     TIME         NOT NULL,
    godzina_do     TIME         NOT NULL,
    gabinet        VARCHAR(10),
    aktywny        BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT lekarze_godziny_pracy_chk CHECK (godzina_od < godzina_do)
);

CREATE TABLE IF NOT EXISTS wizyty (
    id        SERIAL        PRIMARY KEY,
    lekarz_id INTEGER       NOT NULL REFERENCES lekarze(id) ON DELETE RESTRICT,
    godzina   VARCHAR(5)    NOT NULL,
    dostepna  BOOLEAN       NOT NULL DEFAULT TRUE
    CONSTRAINT wizyty_godzina_format_chk CHECK (godzina ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'),
    CONSTRAINT wizyty_lekarz_godzina_uq UNIQUE (lekarz_id, godzina)
);

-- ============ DANE STARTOWE ============
INSERT INTO lekarze (imie, nazwisko, specjalizacja, godzina_od, godzina_do, gabinet) VALUES
    ('Jan',       'Kowalski',   'Internista', '08:00', '14:00', '101'),
    ('Anna',      'Nowak',      'Dermatolog', '10:00', '16:00', '204'),
    ('Piotr',     'Wiśniewski', 'Kardiolog',  '12:00', '18:00', '305'),
    ('Katarzyna', 'Wójcik',     'Pediatra',   '07:30', '13:30', '102'),
    ('Tomasz',    'Kamiński',   'Okulista',   '09:00', '15:00', '210');

INSERT INTO wizyty (lekarz_id, godzina, dostepna) VALUES
    (1, '08:00', FALSE),
    (1, '08:30', TRUE),
    (1, '09:00', TRUE),
    (2, '10:00', FALSE),
    (2, '11:30', TRUE),
    (3, '12:00', TRUE),
    (3, '15:45', FALSE),
    (4, '07:30', TRUE),
    (4, '12:00', TRUE),
    (5, '09:00', FALSE),
    (5, '14:30', TRUE);
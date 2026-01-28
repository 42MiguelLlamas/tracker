PRAGMA foreign_keys = ON;

-- 1) Jugadores (tú y rivales)
CREATE TABLE IF NOT EXISTS players (
  player_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  screen_name   TEXT NOT NULL UNIQUE,
  first_seen_at INTEGER,
  last_seen_at  INTEGER
);

-- 2) Torneos (opcional pero útil desde el inicio)
CREATE TABLE IF NOT EXISTS tournaments (
  tournament_id TEXT PRIMARY KEY,
  buy_in        INTEGER, -- en céntimos (ej: 90)
  fee           INTEGER, -- en céntimos (ej: 10)
  currency      TEXT,    -- "EUR"
  format        TEXT     -- "MTT"/"SNG"/etc (si lo sabes)
);

-- 3) Manos
CREATE TABLE IF NOT EXISTS hands (
  hand_id       TEXT PRIMARY KEY,     -- PokerStars Hand #...
  room          TEXT NOT NULL,         -- "PokerStars"
  played_at     INTEGER,              -- epoch (si lo parseas)
  tournament_id TEXT,                 -- FK tournaments (nullable)
  table_name    TEXT,
  button_seat   INTEGER,
  max_seats     INTEGER,
  hero_player_id INTEGER,             -- FK players (nullable)
  raw_text      TEXT,                 -- guardamos el bloque completo (debug/recálculo)
  FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id),
  FOREIGN KEY (hero_player_id) REFERENCES players(player_id)
);

-- 4) Participantes en la mano (asiento/posición/stack/resultados)
CREATE TABLE IF NOT EXISTS hand_players (
  hand_id      TEXT NOT NULL,
  player_id    INTEGER NOT NULL,
  seat_no      INTEGER,
  pos          TEXT,      -- BTN/SB/BB/UTG/...
  stack_start  INTEGER,   -- en fichas (o en cents si cash)
  is_hero      INTEGER DEFAULT 0, -- 0/1
  cards        TEXT,      -- "AsKd" o similar (si se conoce)
  result_net   INTEGER,   -- neto de la mano (si lo calculas)
  PRIMARY KEY (hand_id, player_id),
  FOREIGN KEY (hand_id) REFERENCES hands(hand_id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(player_id)
);

-- 5) Acciones (lo que te permite todas las stats)
CREATE TABLE IF NOT EXISTS actions (
  action_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  hand_id      TEXT NOT NULL,
  street       TEXT NOT NULL,   -- PREFLOP/FLOP/TURN/RIVER
  action_no    INTEGER NOT NULL, -- orden dentro de la calle
  player_id    INTEGER NOT NULL,
  action_type  TEXT NOT NULL,   -- FOLD/CALL/BET/RAISE/CHECK/ALLIN/POST
  amount       INTEGER,         -- cantidad puesta en esa acción (si aplica)
  to_amount    INTEGER,         -- en raises (raise-to)
  is_allin     INTEGER DEFAULT 0,
  FOREIGN KEY (hand_id) REFERENCES hands(hand_id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(player_id)
);

-- Índices (clave para queries de stats)
CREATE INDEX IF NOT EXISTS idx_players_name ON players(screen_name);
CREATE INDEX IF NOT EXISTS idx_hands_tourney ON hands(tournament_id);
CREATE INDEX IF NOT EXISTS idx_hand_players_player ON hand_players(player_id, hand_id);
CREATE INDEX IF NOT EXISTS idx_actions_hand_street_order ON actions(hand_id, street, action_no);
CREATE INDEX IF NOT EXISTS idx_actions_player ON actions(player_id);

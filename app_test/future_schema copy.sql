PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS players (
  player_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  screen_name   TEXT NOT NULL UNIQUE,
  first_seen_at INTEGER,
  last_seen_at  INTEGER
);

CREATE TABLE IF NOT EXISTS tournaments (
  tournament_id TEXT PRIMARY KEY,
  buy_in_cents  INTEGER,
  fee_cents     INTEGER,
  currency      TEXT,
  format        TEXT
);

CREATE TABLE IF NOT EXISTS hands (
  hand_id        TEXT PRIMARY KEY,
  room           TEXT NOT NULL,
  played_at      INTEGER,
  tournament_id  TEXT,
  table_name     TEXT,
  max_seats      INTEGER,
  button_seat    INTEGER,
  hero_player_id INTEGER,

  sb_amount      INTEGER,
  bb_amount      INTEGER,
  ante_amount    INTEGER,
  pot_total      INTEGER,
  rake           INTEGER,

  raw_text       TEXT,

  FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id),
  FOREIGN KEY (hero_player_id) REFERENCES players(player_id)
);

CREATE TABLE IF NOT EXISTS hand_players (
  hand_id           TEXT NOT NULL,
  player_id         INTEGER NOT NULL,
  seat_no           INTEGER,
  pos               TEXT,
  stack_start       INTEGER,
  sitting_out       INTEGER DEFAULT 0,

  dealt_cards       TEXT,
  went_to_showdown  INTEGER DEFAULT 0,
  won_at_showdown   INTEGER DEFAULT 0,

  result_net        INTEGER,

  PRIMARY KEY (hand_id, player_id),
  FOREIGN KEY (hand_id) REFERENCES hands(hand_id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE TABLE IF NOT EXISTS actions (
  action_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  hand_id      TEXT NOT NULL,
  street       TEXT NOT NULL,
  action_no    INTEGER NOT NULL,
  player_id    INTEGER NOT NULL,

  action_type  TEXT NOT NULL,
  amount       INTEGER,
  to_amount    INTEGER,
  is_allin     INTEGER DEFAULT 0,
  meta         TEXT,

  FOREIGN KEY (hand_id) REFERENCES hands(hand_id) ON DELETE CASCADE,
  FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE TABLE IF NOT EXISTS boards (
  hand_id TEXT PRIMARY KEY,
  flop1 TEXT, flop2 TEXT, flop3 TEXT,
  turn  TEXT,
  river TEXT,
  FOREIGN KEY(hand_id) REFERENCES hands(hand_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tournament_results (
  tournament_id TEXT NOT NULL,
  player_id     INTEGER NOT NULL,
  finish_place  INTEGER,
  prize_type    TEXT,
  prize_amount  INTEGER,
  prize_desc    TEXT,
  PRIMARY KEY (tournament_id, player_id),
  FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id),
  FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX IF NOT EXISTS idx_players_name ON players(screen_name);
CREATE INDEX IF NOT EXISTS idx_hands_tourney ON hands(tournament_id);
CREATE INDEX IF NOT EXISTS idx_hands_table ON hands(table_name);
CREATE INDEX IF NOT EXISTS idx_hand_players_player ON hand_players(player_id, hand_id);
CREATE INDEX IF NOT EXISTS idx_hand_players_hand ON hand_players(hand_id);
CREATE INDEX IF NOT EXISTS idx_actions_hand_street_order ON actions(hand_id, street, action_no);
CREATE INDEX IF NOT EXISTS idx_actions_player ON actions(player_id);

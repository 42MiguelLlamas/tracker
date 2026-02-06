PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS files(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL UNIQUE,
  last_offset INTEGER NOT NULL DEFAULT 0,
  last_mtime REAL NOT NULL DEFAULT 0,
  last_size INTEGER NOT NULL DEFAULT 0,
  last_seen REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS players(
  player_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS hands(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_id INTEGER NOT NULL,
  hand_no TEXT NOT NULL UNIQUE,

  kind TEXT NOT NULL CHECK(kind IN ('cash', 'tournament')),

  tournament_id INTEGER,
  stakes TEXT,
  buyin INTEGER,
  currency TEXT, 

  btn_pos INTEGER,
  table_max_seats INTEGER,

  local_dt TEXT,
  local_tz TEXT,

  inserted_at REAL NOT NULL,

  FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS seats(
  hand_id INTEGER NOT NULL,
  pos INTEGER NOT NULL,
  player_name TEXT NOT NULL,
  chips INTEGER,
  sitting_out INTEGER NOT NULL DEFAULT 0,

  PRIMARY KEY(hand_id, pos),
  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE,
  FOREIGN KEY(player_name) REFERENCES players(player_name)
);

CREATE TABLE IF NOT EXISTS posts(
  hand_id INTEGER NOT NULL,
  player_name TEXT NOT NULL,
  kind TEXT NOT NULL,             -- 'ante'/'SB'/'BB' o normalizado
  amount INTEGER,

  PRIMARY KEY(hand_id, player_name, kind),
  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE,
  FOREIGN KEY(player_name) REFERENCES players(player_name)
);

CREATE TABLE IF NOT EXISTS dealt(
  hand_id INTEGER NOT NULL,
  player_name TEXT NOT NULL,
  cards TEXT NOT NULL,

  PRIMARY KEY(hand_id, player_name),
  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE,
  FOREIGN KEY(player_name) REFERENCES players(player_name)
);

CREATE TABLE IF NOT EXISTS board(
  hand_id INTEGER PRIMARY KEY,
  flop TEXT,
  turn TEXT,
  river TEXT,
  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS actions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hand_id INTEGER NOT NULL,
  seq INTEGER NOT NULL,

  street TEXT NOT NULL CHECK(street IN ('preflop','flop','turn','river','showdown')),
  player_name TEXT NOT NULL,
  action TEXT NOT NULL CHECK(action IN ('folds','checks','bets','calls','raises')),

  amount_text INTEGER,
  raise_from_text INTEGER,
  raise_to_text INTEGER,
  is_allin INTEGER NOT NULL DEFAULT 0,

  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE,
  FOREIGN KEY(player_name) REFERENCES players(player_name),

  UNIQUE(hand_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_hands_file ON hands(file_id);
CREATE INDEX IF NOT EXISTS idx_hands_tournament ON hands(tournament_id);
CREATE INDEX IF NOT EXISTS idx_actions_hand ON actions(hand_id);
CREATE INDEX IF NOT EXISTS idx_actions_player ON actions(player_name);

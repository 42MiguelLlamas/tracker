PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS files(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL UNIQUE,
  last_offset INTEGER NOT NULL DEFAULT 0,
  last_mtime REAL NOT NULL DEFAULT 0,
  last_size INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS players(
  player_id INTEGER PRIMARY KEY AUTOINCREMENT,
  player_name TEXT NOT NULL UNIQUE
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

  btn_pos INTEGER NOT NULL,
  max_seats INTEGER NOT NULL,
  players_seated INTEGER NOT NULL,

  hand_ts INTEGER NOT NULL,
  inserted_at REAL NOT NULL,

  FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);


--  # positions:
--     # btn = 1
--     # sb = 2
--     # bb = 3
--     # utg = 4
--     # utg+1 = 5
--     # mp1 = 6
--     # mp2 = 7
--     # hj = 8
--     # co = 9

CREATE TABLE IF NOT EXISTS seats(
  hand_id INTEGER NOT NULL,
  pos INTEGER NOT NULL,
  player_id INTEGER NOT NULL,
  chips INTEGER,
  bounty INTEGER,
  sitting_out INTEGER NOT NULL DEFAULT 0,

  PRIMARY KEY(hand_id, pos),
  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE,
  FOREIGN KEY(player_id) REFERENCES players(player_id)
);

CREATE TABLE IF NOT EXISTS posts(
  hand_id INTEGER NOT NULL,
  player_id INTEGER NOT NULL,
  kind TEXT NOT NULL,             -- 'ante'/'SB'/'BB' o normalizado
  amount INTEGER,

  PRIMARY KEY(hand_id, player_id, kind),
  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE,
  FOREIGN KEY(player_id) REFERENCES players(player_id)
);

CREATE TABLE IF NOT EXISTS result(
  hand_id INTEGER NOT NULL,
  player_id INTEGER NOT NULL,
  cards TEXT NOT NULL,
  collected NOT NULL,

  PRIMARY KEY(hand_id, player_id),
  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE,
  FOREIGN KEY(player_id) REFERENCES players(player_id)
);

CREATE TABLE IF NOT EXISTS board(
  hand_id INTEGER PRIMARY KEY,
  flop TEXT,
  turn TEXT,
  river TEXT,
  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE
);

-- street:
-- 0 = preflop
-- 1 = flop
-- 2 = turn
-- 3 = river
-- 4 = showdown

-- action:
-- 0 = folds
-- 1 = checks
-- 2 = calls
-- 3 = bets
-- 4 = raises

CREATE TABLE IF NOT EXISTS actions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hand_id INTEGER NOT NULL,
  seq INTEGER NOT NULL,

  street INTEGER NOT NULL,
  player_id INTEGER NOT NULL,
  action INTEGER NOT NULL,

  amount INTEGER,
  raise_from INTEGER,
  raise_to INTEGER,
  is_allin INTEGER NOT NULL DEFAULT 0,

  FOREIGN KEY(hand_id) REFERENCES hands(id) ON DELETE CASCADE,
  FOREIGN KEY(player_id) REFERENCES players(player_id),

  UNIQUE(hand_id, seq)
);

CREATE TABLE IF NOT EXISTS hole_cards (
  hand_id INTEGER,
  player_id INTEGER,
  c1_rank INTEGER,   -- 2..14
  c1_suit INTEGER,   -- 0..3
  c2_rank INTEGER,
  c2_suit INTEGER,
  PRIMARY KEY(hand_id, player_id)
);


CREATE TABLE IF NOT EXISTS player_stats (
  player_id INTEGER,
  pos INTEGER,                  -- posición absoluta

  max_seats INTEGER,
  players_seated INTEGER,              -- 2..9
  stack_bb_bucket INTEGER,      -- 0=0-20bb,1=20-40,2=40-100,3=100+


  hands INTEGER DEFAULT 0,

  -- PREFLOP
  rfi INTEGER DEFAULT 0,
  rfi_opp INTEGER DEFAULT 0,
  vpip INTEGER DEFAULT 0,
  pfr INTEGER DEFAULT 0,

  threebet INTEGER DEFAULT 0,
  threebet_opp INTEGER DEFAULT 0,

  fold_to_3bet INTEGER DEFAULT 0,
  fold_to_3bet_opp INTEGER DEFAULT 0,

  fourbet INTEGER DEFAULT 0,
  fourbet_opp INTEGER DEFAULT 0,

  squeeze INTEGER DEFAULT 0,
  squeeze_opp INTEGER DEFAULT 0,

  steal INTEGER DEFAULT 0,
  steal_opp INTEGER DEFAULT 0,

  fold_bb_vs_steal INTEGER DEFAULT 0,
  fold_bb_vs_steal_opp INTEGER DEFAULT 0,

  -- POSTFLOP
  saw_flop INTEGER DEFAULT 0,

  cbet_flop INTEGER DEFAULT 0,
  cbet_flop_opp INTEGER DEFAULT 0,

  fold_to_cbet_flop INTEGER DEFAULT 0,
  fold_to_cbet_flop_opp INTEGER DEFAULT 0,

  check_raise_flop INTEGER DEFAULT 0,
  check_raise_flop_opp INTEGER DEFAULT 0,

  donk_flop INTEGER DEFAULT 0,
  donk_flop_opp INTEGER DEFAULT 0,

  --TURN
  saw_turn INTEGER DEFAULT 0,

  barrel_turn INTEGER DEFAULT 0,
  barrel_turn_opp INTEGER DEFAULT 0,

  fold_to_barrel_turn INTEGER DEFAULT 0,
  fold_to_barrel_turn_opp INTEGER DEFAULT 0,
  


  --RIVER
  saw_river INTEGER DEFAULT 0,

  barrel_river INTEGER DEFAULT 0,
  barrel_river_opp INTEGER DEFAULT 0,

  fold_to_barrel_river INTEGER DEFAULT 0,
  fold_to_barrel_river_opp INTEGER DEFAULT 0,

  river_bet INTEGER DEFAULT 0,
  river_bet_opp INTEGER DEFAULT 0,

  -- SHOWDOWN
  went_showdown INTEGER DEFAULT 0,
  won_showdown INTEGER DEFAULT 0,

  PRIMARY KEY(player_id, pos, players_seated, stack_bb_bucket)
);


CREATE INDEX IF NOT EXISTS idx_hands_file ON hands(file_id);
CREATE INDEX IF NOT EXISTS idx_hands_tournament ON hands(tournament_id);
CREATE INDEX IF NOT EXISTS idx_actions_hand ON actions(hand_id);
CREATE INDEX IF NOT EXISTS idx_actions_player ON actions(player_id);
CREATE INDEX IF NOT EXISTS idx_stats_player ON player_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_stats_pos ON player_stats(pos);
CREATE INDEX IF NOT EXISTS idx_stats_stack ON player_stats(stack_bb_bucket);

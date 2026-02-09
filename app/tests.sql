SELECT
  s.pos,
  SUM(s.hands) AS hands,

  SUM(s.rfi) AS rfi, SUM(s.rfi_opp) AS rfi_opp,
  ROUND(100.0 * SUM(s.rfi) / NULLIF(SUM(s.rfi_opp), 0), 1) AS rfi_pct,

  SUM(s.threebet) AS threebet, SUM(s.threebet_opp) AS threebet_opp,
  ROUND(100.0 * SUM(s.threebet) / NULLIF(SUM(s.threebet_opp), 0), 1) AS threebet_pct,

  SUM(s.fold_to_3bet) AS fold_to_3bet, SUM(s.fold_to_3bet_opp) AS fold_to_3bet_opp,
  ROUND(100.0 * SUM(s.fold_to_3bet) / NULLIF(SUM(s.fold_to_3bet_opp), 0), 1) AS fold_to_3bet_pct,

  SUM(s.fourbet) AS fourbet, SUM(s.fourbet_opp) AS fourbet_opp,
  ROUND(100.0 * SUM(s.fourbet) / NULLIF(SUM(s.fourbet_opp), 0), 1) AS fourbet_pct,

  SUM(s.squeeze) AS squeeze, SUM(s.squeeze_opp) AS squeeze_opp,
  ROUND(100.0 * SUM(s.squeeze) / NULLIF(SUM(s.squeeze_opp), 0), 1) AS squeeze_pct,

  SUM(s.steal) AS steal, SUM(s.steal_opp) AS steal_opp,
  ROUND(100.0 * SUM(s.steal) / NULLIF(SUM(s.steal_opp), 0), 1) AS steal_pct,

  SUM(s.fold_bb_vs_steal) AS fold_bb_vs_steal, SUM(s.fold_bb_vs_steal_opp) AS fold_bb_vs_steal_opp,
  ROUND(100.0 * SUM(s.fold_bb_vs_steal) / NULLIF(SUM(s.fold_bb_vs_steal_opp), 0), 1) AS fold_bb_vs_steal_pct

FROM player_stats s
JOIN players p ON p.player_id = s.player_id
WHERE p.player_name = 'sunbreathking'
GROUP BY s.pos
ORDER BY s.pos;

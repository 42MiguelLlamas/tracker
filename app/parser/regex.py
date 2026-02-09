import re

HAND_START_RE = re.compile(rb"""
                           ^(?:\xef\xbb\xbf)?PokerStars\s+Hand\s+\#(?P<hand_id>\d+):\s*
                           (?:
                                Tournament\s+\#(?P<tournament_id>\d+),.*?
                                (?P<buy_in>(?:[^\d]+)?\d+(?:\.\d+)?\+(?:[^\d]+)?\d+(?:\.\d+)?)\s+(?P<cur>[A-Z]{3}).*?
                            |
                                .*?\((?P<stakes>(?:[^\d]+)?\d+(?:\.\d+)?/(?:[^\d]+)?\d+(?:\.\d+)?)\s+(?P<cur_cash>[A-Z]{3})\).*?   
                           )
                           \s*-\s*
                           (?P<local_dt>\d{4}/\d{2}/\d{2}\s+\d{1,2}:\d{2}:\d{2})\s+(?P<local_tz>[A-Z]{2,5})
                           """, 
                           re.VERBOSE)

DEALT_RE = re.compile(rb"""
                        ^Dealt\s+to\s+sunbreathking\s+\[(?P<cards>.+?)\]\s*$
                        """,
                        re.VERBOSE)

TABLE_START_RE = re.compile(rb"""
                            ^Table\s+'.*?'\s+(?P<max_seats>\d+)-max\s+Seat\s+\#(?P<btn_pos>\d+)\s+is\s+the\s+button\s*$
                            """, 
                           re.VERBOSE)

SEAT_RE = re.compile(rb"""
                        ^Seat\s+(?P<seat_no>\d+):\s+(?P<player_name>.+?)\s+
                        \((?P<chips>(?:[^\d]+)?\d+(?:\.\d+)?)\s+in\s+chips
                        (?:,\s+[^\d]+?(?P<bounty>\d+(?:\.\d+)?)\s+bounty)?
                     \)
                        (?:\s+(?:is\s+sitting\s+out|\s+out\s+of\s+hand\s+\(.*?\)))?\s*$
                     """, 
                    re.VERBOSE)

POST_RE = re.compile(rb"""
                        ^(?P<player_name>.+?):\s+posts\s+(?P<kind>the\s+ante|small\s+blind|big\s+blind).+?(?P<amount>\d+(?:\.\d+)?)(?:\s+and\s+is\s+all-in)?\s*$
                     """, 
                    re.VERBOSE)

PREFLOP_RE = re.compile(rb"""
                        ^\*\*\*\s+HOLE\s+CARDS\s+\*\*\*\s*$
                     """, 
                    re.VERBOSE)

FLOP_RE = re.compile(rb"""
                        ^\*\*\*\s+FLOP\s+\*\*\*\s+\[(?P<cards>.+?)\]\s*$
                     """, 
                    re.VERBOSE)

TURN_RE = re.compile(rb"""
                        ^\*\*\*\s+TURN\s+\*\*\*\s+\[.+?\]\s+\[(?P<cards>.+?)\]\s*$
                     """, 
                    re.VERBOSE)

RIVER_RE = re.compile(rb"""
                        ^\*\*\*\s+RIVER\s+\*\*\*\s+\[.+?\]\s+\[(?P<cards>.+?)\]\s*$
                     """, 
                    re.VERBOSE)

SUMMARY_RE = re.compile(rb"""
                        ^\*\*\*\s+SUMMARY\s+\*\*\*\s*$
                        """, 
                        re.VERBOSE)

ACTION_RE = re.compile(rb"""
                        ^(?P<player_name>.+?):\s+
                        (?P<action>folds|checks|bets|raises|calls)
                        (?:
                            \s*$ |
                            \s+(?:[^\d]+)?(?P<bet>\d+(?:\.\d+)?)\s*$ |
                            \s+(?:[^\d]+)?(?P<raise_from>\d+(?:\.\d+)?)\s+to\s+(?:[^\d]+)?(?P<raise_to>\d+(?:\.\d+)?) |
                            \s+(?:[^\d]+)?(?P<call_amount>\d+(?:\.\d+)?) 
                        )
                        (?:\s+(?P<is_all_in>and\s+is\s+all-in))?\s*$
                        """, 
                        re.VERBOSE)


SEAT_SUMMARY_RE = re.compile(rb"""
                        ^Seat\s+\d+:\s+
                        (?P<player_name>.+?)(?:\s+\([^)]*\))?
                        \s+
                        (?:
                            showed\s+\[(?P<showed>.+?)\]
                            (?:\s+and\s+(?:won|lost)(?:\s+\((?P<won>[^)]+)\))?.*)?
                        |
                            mucked\s+\[(?P<mucked>.+?)\]
                        |
                            collected\s+\((?P<collected>[^)]+)\)
                        )
                        \s*$
                        """, re.VERBOSE)

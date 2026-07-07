import sys 
sys.path.append('src')

from database import MatchDatabase

db = MatchDatabase()

test_match = {
    'match_id': 'TEST_123',
    'game_duration': 1854,
    'game_creation': 1234567890,
    'game_version': '13.24',
    't100_kills': 35,
    't100_deaths': 28,
    't100_assists': 60,
    't100_gold': 75000,
    't100_damage': 150000,
    't100_cs': 450,
    't100_vision': 120,
    't100_towers': 8,
    't100_dragons': 3,
    't100_barons': 1,
    't200_kills': 28,
    't200_deaths': 35,
    't200_assists': 50,
    't200_gold': 68000,
    't200_damage': 130000,
    't200_cs': 420,
    't200_vision': 90,
    't200_towers': 2,
    't200_dragons': 1,
    't200_barons': 0,
    'team_100_win': 1
}

success = db.insert_match(test_match)

print(f"Inserted: {success}")

stats = db.get_stats()
print(f"Total matches: {stats['total_matches']}")

matches = db.query_matches
print("\n Matches in DB:")
print(matches)

db.close()
import sys
sys.path.append('src')  

from riot_api import RIOTAPI
import pandas as pd
import json 
from datetime import datetime
from database import MatchDatabase

api = RIOTAPI(region="na1")

def extract_match_features(match_data):
    '''
    Function for extracting useful feature from raw match data     

    '''
    if not match_data:
        return None
    
    info = match_data['info']
    participants = info['participants']

    team_100 = [p for p in participants if p['teamId'] == 100]
    team_200 = [p for p in participants if p['teamId'] == 200]

    def calc_team_stats(team):
        """ Calculate aggregate stats for a team"""

        basic = {
            'kills' : sum(p['kills'] for p in team),
            'deaths': sum(p['deaths'] for p in team),
            'assists': sum(p['assists'] for p in team),
            'gold': sum(p['goldEarned'] for p in team),
            'damage': sum(p['totalDamageDealtToChampions'] for p in team),
            'cs': sum(p['totalMinionsKilled'] + p['neutralMinionsKilled'] for p in team)
        }

        vision = {
            'vision_score': sum(p.get('visionScore', 0) for p in team),
            'wards_placed': sum(p.get('wardsPlaced', 0) for p in team),
            'wards_killed': sum(p.get('wardsKilled', 0) for p in team),
            'control_wards': sum(p.get('controlWardsPlaced', 0) for p in team),
            }
        
        damage_breakdown = {
            'physical_damage': sum(p.get('physicalDamageDealtToChampions', 0) for p in team),
            'magic_damage': sum(p.get('magicDamageDealtToChampions', 0) for p in team),
            'true_damage': sum(p.get('trueDamageDealtToChampions', 0) for p in team),
        }
        
        early_game = {
            'gold_per_minute': basic['gold'] / (info['gameDuration'] / 60) if info['gameDuration'] > 0 else 0,
        }
        
        objectives = {
            'towers': sum(p.get('turretKills', 0) for p in team),
            'inhibitors': sum(p.get('inhibitorKills', 0) for p in team),
            'dragons': sum(p.get('dragonKills', 0) for p in team),
            'barons': sum(p.get('baronKills', 0) for p in team),
            'heralds': sum(p.get('challenges', {}).get('riftHeraldTakedowns', 0) for p in team),
        }
        
        return {**basic, **vision, **damage_breakdown, **early_game, **objectives}
    
    team_100_stats = calc_team_stats(team_100)
    team_200_stats = calc_team_stats(team_200)

    team_100_win = team_100[0]['win']

    features = {
        "match_id": match_data['metadata']['matchId'],
        'game_duration': info['gameDuration'],
        'game_mode': info['gameMode'],
        
        't100_kills': team_100_stats['kills'],
        't100_deaths': team_100_stats['deaths'],
        't100_assists': team_100_stats['assists'],
        't100_gold': team_100_stats['gold'],
        't100_damage': team_100_stats['damage'],
        't100_cs': team_100_stats['cs'],
        't100_vision': team_100_stats['vision_score'],
        't100_wardsPlaced': team_100_stats['wards_placed'],
        't100_wardsKilled': team_100_stats['wards_killed'],
        't100_controlWards': team_100_stats['control_wards'],
        't100_towers': team_100_stats['towers'],
        't100_dragons': team_100_stats['dragons'],
        't100_herald': team_100_stats['heralds'],
        't100_barons': team_100_stats['barons'],
        't100_phdmg': team_100_stats['physical_damage'],
        't100_mgdmg': team_100_stats['magic_damage'],
        't100_trdmg': team_100_stats['true_damage'],
        't100_goldpermin': team_100_stats['gold_per_minute'],
        't100_towers': team_100_stats['towers'],
        't100_inhibitors': team_100_stats['inhibitors'],

        
        't200_kills': team_200_stats['kills'],
        't200_deaths': team_200_stats['deaths'],
        't200_assists': team_200_stats['assists'],
        't200_gold': team_200_stats['gold'],
        't200_damage': team_200_stats['damage'],
        't200_cs': team_200_stats['cs'],
        't200_vision': team_200_stats['vision_score'],
        't200_wardsPlaced': team_200_stats['wards_placed'],
        't200_wardsKilled': team_200_stats['wards_killed'],
        't200_controlWards': team_200_stats['control_wards'],
        't200_towers': team_200_stats['towers'],
        't200_dragons': team_200_stats['dragons'],
        't200_barons': team_200_stats['barons'],
        't200_herald': team_200_stats['heralds'],
        't200_phdmg': team_200_stats['physical_damage'],
        't200_mgdmg': team_200_stats['magic_damage'],
        't200_trdmg': team_200_stats['true_damage'],
        't200_goldpermin': team_200_stats['gold_per_minute'],
        't200_towers': team_200_stats['towers'],
        't200_inhibitors': team_200_stats['inhibitors'],

        
        #Prediction
        'team_100_win': int(team_100_win)
    }

    return features 

def collect_matches_from_summoners(api, db, summoner_name, tagLine, num_matches=20):
    """ Collecting data from summoners (matches)"""
    print(f"\nRecolectando data de: {summoner_name}#{tagLine}")

    summoner = api.get_accountData(summoner_name, tagLine)
    if not summoner: 
        print("Summoner not found")

    summoner_info = api.get_summonerInfo(summoner['puuid'])
    
    if summoner_info:
        print("Summoner found!")
        print(f"Summoner: {summoner['gameName']}#{summoner['tagLine']}")
        print(f"Level: {summoner_info['summonerLevel']}")
        print(f"PUUID: {summoner_info['puuid'][:20]}...")

        match_ids = api.get_match_history(summoner_info['puuid']) #Returning a list of match ids

        collected_features = []
        skipped_count = 0
        inserted_count = 0

        for i, match_id in enumerate(match_ids, 1):
            print(f"\n[{i}/{len(match_ids)}] Loading {match_id}...")

            match_data = api.get_match_details(match_id)
            if not match_data:
                print("Match data not found")
                skipped_count += 1
                continue

            features = extract_match_features(match_data)

            if not features: 
                print("No features found")
                skipped_count += 1
                continue

            success = db.insert_match(features)

            if success:
                inserted_count += 1
                collected_features.append(features)
                print("Inserted in DB ")
            else:
                skipped_count += 1

        print(f"Summary for {summoner_name}#{tagLine}")
        print(f"     Inserted: {inserted_count} ")
        print(f"     Skipped: {skipped_count}")
    
    print(f"\n--- Collected : {len(collected_features)} matches")
    return collected_features

def collect_player_features(match_data):
    """
    Function to extract player data from match data    
    :param match_data: match data

    returns a list of dictionaries, one for each player in the match
    """
    if not match_data:
        return []
    
    info = match_data['info']
    participants = info['participants']
    player_features = []

    for participant in participants:

        player = {
            # Match info
            'match_id': match_data['metadata']['matchId'],
            'game_duration': info['gameDuration'],
            
            # Player identity
            'puuid': participant['puuid'],
            'summoner_name': participant['summonerName'],
            'champion_id': participant['championId'],
            'champion_name': participant['championName'],
            'team_position': participant.get('teamPosition', 'UNKNOWN'),
            'individual_position': participant.get('individualPosition', 'UNKNOWN'),
            'team_id': participant['teamId'],
            
            # Core stats
            'kills': participant['kills'],
            'deaths': participant['deaths'],
            'assists': participant['assists'],
            'kda': (participant['kills'] + participant['assists']) / max(participant['deaths'], 1),
            
            # Farm
            'cs': participant['totalMinionsKilled'] + participant.get('neutralMinionsKilled', 0),
            'cs_per_min': (participant['totalMinionsKilled'] + participant.get('neutralMinionsKilled', 0)) / (info['gameDuration'] / 60),
            
            # Economy
            'gold_earned': participant['goldEarned'],
            'gold_per_min': participant['goldEarned'] / (info['gameDuration'] / 60),
            'gold_spent': participant['goldSpent'],
            
            # Combat
            'damage_dealt': participant['totalDamageDealtToChampions'],
            'damage_taken': participant['totalDamageTaken'],
            'damage_mitigated': participant.get('damageSelfMitigated', 0),
            
            # Vision
            'vision_score': participant.get('visionScore', 0),
            'wards_placed': participant.get('wardsPlaced', 0),
            'wards_killed': participant.get('wardsKilled', 0),
            'control_wards': participant.get('detectorWardsPlaced', 0),
            
            # Objectives
            'turret_kills': participant.get('turretKills', 0),
            'inhibitor_kills': participant.get('inhibitorKills', 0),
            
            # Outcome
            'win': participant['win'],
        }

        player_features.append(player)

    return player_features


if __name__ == "__main__":
    print("\nLeague match data collector")

    api = RIOTAPI(region = "na1")
    db = MatchDatabase()

    summoners = [
        ("IMPACT", "DAMU"),
        ("Kid Ink", "NA2"),
        ("Oddielan", "LYON"),
        ("T0mio", "NA1"),
        ("stupid donut", "YEAH"),
        ("CLOUD9 APA", "FIGHT"),
        ("Tomo", "0999"),
        ("TL Yeon", "7lol"),
        ("From Iron", "1123"),
        ("Cosboat", "NA1"),     
    ]

    add_summoner = input("Add your summoner: (Enter to skip)").strip()
    if add_summoner:
        summoners.append(add_summoner)

    all_matches = []

    for gameName, tagLine in summoners:
        print(f"Collecting data from {gameName}#{tagLine}")
        matches = collect_matches_from_summoners(api, db, gameName, tagLine, num_matches=10)
        all_matches.extend(matches)
        print(f"Collected matches: {len(matches)}")

    # DATABASE STATS

    print("\nStats DB")
    db_stats = db.get_stats()

    print(f"\nTotal matches in DB: {db_stats['total_matches']}")
    print(f"Unique players: {db_stats.get('unique_player', 'N/A')}")
    print(f"Total player records: {db_stats.get('total_player_records', 'N/A')}")
    print(f"Win rate Team 100: {db_stats['team_100_win_rate']:.1%}")
    print(f"Average game duration: {db_stats['avg_game_duration']/60:.1f} min")

    if db_stats['total_matches'] > 0:
        print(f"\nTOP PLAYERS")
        top_players = db.get_the_top_players(limit=5)
        print(top_players.to_string(index=False))

    # BACK UP CSV AND JSON
    df = pd.DataFrame(all_matches)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


    csv_file = f"data/matches_raw_{timestamp}.csv"
    df.to_csv(csv_file, index = False)
    print(f"   CSV:  {csv_file}")
    
    json_file = f"data/matches_raw_{timestamp}.json"
    df.to_json(json_file, orient='records', indent=2)
    print(f"   JSON: {json_file}")


    print("Backup Stats")
    print(f"Total matches: {len(df)}")
    print(f"Columns:{len(df.columns)} ")
    print(df.head())
    
    db.close()

    print("Completed")


    

    




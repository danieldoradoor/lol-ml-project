import sys 
sys.path.append('src') 

from riot_api import RIOTAPI
import pandas as pd
import json 
from datetime import datetime
from lesson_2_5_collectmatches import collect_player_features

def collect_player_data(summoners_name, num_matches):
    """
    Docstring for collect_player_data
    
    :param summoners_name: List of summoners name and tagline
    :param num_matches: number of matches
    """
    api = RIOTAPI(region = 'na1')
    all_players = []

    for summoner_name, tagLine in summoners_name:
        print(f"Collecting from {summoner_name}#{tagLine}")

        summonerInfo = api.get_accountData(summoner_name, tagLine)
        if not summonerInfo:
            continue

        match_ids = api.get_match_history(summonerInfo['puuid'], count = num_matches)
        for match_id in match_ids:
            match_data = api.get_match_details(match_id)
            if not match_data:
                continue

            players = collect_player_features(match_data)
            all_players.append(players)

    df = pd.DataFrame(all_players)

    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"data/player_data_{timestamp}.csv"
    df.to_csv(filename, index=False)

    print(f"\n✅ Collected {len(df)} player records")
    print(f"   Saved to {filename}")

    return df

if __name__ == "__main__":

    summoners = [
        ("Kid Ink", "NA2"),
        ("T0mio", "NA1"),
        ("CLOUD9 APA", "FIGHT"),
        ("TL Yeon", "7lol"),
        ("Cosboat", "NA1"),     
    ]

    df = collect_player_data(summoners, num_matches=10)

    print("\n=== Player Data Stats ===")
    print(f"Total players: {len(df)}")
    print(f"Unique summoners: {df['summoner_name'].nunique()}")
    print(f"Average KDA: {df['kda'].mean():.2f}")
    print(f"Average CS/min: {df['cs_per_min'].mean():.1f}")
        
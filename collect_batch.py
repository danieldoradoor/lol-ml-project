import sys 
sys.path.append('src')

from riot_api import RIOTAPI
import pandas as pd
from datetime import datetime

from lesson_2_5_collectmatches import extract_match_features

def collect_batch(summoner_name, tagLine, num_matches, batch_name):

    api = RIOTAPI(region = 'na1')
    all_matches = []

    for summoner, tagLine in summoner_name:
        print(f"Collecting from: {summoner}")

        summoner_data = api.get_summonerInfo(summoner)
        if not summoner_data:
            continue

        match_ids = api.get_match_history(summoner_data['puuid'], count = num_matches)

        for i, match_id in enumerate(match_ids, 1):
            print(f"[{i}/{len(match_ids)}] {match_id}")

            match_data = api.get_match_details(match_id)
            if not match_id:
                continue

            features = extract_match_features(match_data)
            if features:
                all_matches.append(features)

            
    df = pd.DataFrame(all_matches)
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"data/matches_{batch_name}_{timestamp}.csv"

    df.to_csv(filename, index = False)
    print(f"Saved {len(df)} matches to {filename}")

    return df

import sys
sys.path.append('src')

from riot_api import RIOTAPI
import json 

api = RIOTAPI(region = "la1")

try: 
    summoner_name, tagLine = input("Enter a summoner name and tag (separated by space): ").split()
except ValueError:
    print("Summoner and Tagline must be separed by space. Try again")
except Exception as e:
    print(f"API error: {e}")

summoner = api.get_accountData(summoner_name, tagLine)
summoner_info = api.get_summonerInfo(summoner["puuid"])


print(f"Successfully retrieved data for {summoner_name}#{tagLine}")

if summoner_info:
    match = api.get_match_history(summoner_info['puuid'], count = 1)

    if match: 
        match_data = api.get_match_details(match[0])
        with open('sample_match_juan.json', 'w') as f:
            json.dump(match_data, f, indent=2)
    

    print("\nEstructura de match data")
    print (f"\nTop-level keys: ")
    for key in match_data.keys():
        print(f" - {key}")

    for puuid in match_data['metadata']['participants']:
        summ = api.get_summonerName(puuid)
        print(f"\nSummoner: {summ['gameName']}#{summ['tagLine']}")
        

    print("\n📋 metadata keys:")
    for key in match_data['metadata'].keys():
        print(f"  - {key}: {match_data['metadata'][key]}")
        
    print("\n📋 info keys (principales):")
    info = match_data['info']
    for key in list(info.keys())[:10]:  # Solo primeros 10
        print(f"  - {key}")
        print("  ... (más keys)")
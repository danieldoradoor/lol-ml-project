"""
Riot API Data Collector
Handles all interactions with Riot Games API
"""

import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()

class RIOTAPI:
    """
    Class to interact with API

    This class handles:
    - Authentication
    - Rate limiting
    - Error Handling
    - Different API endpoints 
    """
    def __init__(self, api_key= None, region = "na1"):
        self.api_key = os.getenv('RIOT_API_KEY')

        if not self.api_key:
            raise ValueError("No API key provided")
        
        self.region = region
        self.base_url = f"https://{region}.api.riotgames.com"
        self.headers = {"X-Riot-Token": self.api_key}
        
        #Regional routing 
        self.regional_url = self.get_regional_url(region)

    def get_regional_url(self, region):
        if region in ['na1', 'br1', 'la1', 'la2']:
            return "https://americas.api.riotgames.com"
        elif region in ['euw','eun1','tr1','ru']:
            return "https://europe.api.riotgames.com"
        elif region in ['kr','jp1']:
            return "https://asia.api.riotgames.com"
        else:
            return "https://sea.api.riotgames.com"
                      
            
    def _make_request(self, url, max_retries=3):
            """
            This function will make an an API request 


            :param self
            :param url: URL to request
            :param max_retries: Number of times to retry 

            Returns JSON data or None if failed
            """
            time.sleep(0.5)           

            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers = self.headers, timeout=10)

                    if response.status_code == 200:
                        return response.json()
                    
                    elif response.status_code == 404:
                        print(f"Not found: {url}")
                        return None
                    
                    elif response.status_code == 429:
                        retry_after = int(response.headers.get('Retry After', 120))
                        print(f'Rate limited. Waiting {retry_after} seconds...')
                        time.sleep(retry_after)
                        continue

                    elif response.status_code == 403:
                        print('Invalid API key or expired')
                        return None
                    
                    else:
                        print(f"Error {response.status_code}: {response.text}")
                        return None
                    
                except requests.exceptions.Timeout:
                    print(f'Timeout on attempt { attempt + 1 }/{max_retries}')
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                
                except Exception as e:
                    print(f'Exception: {e}')
                    return None
                
            return None
        
    def get_summonerInfo(self, puuid):
            """
            Docstring for get_summoner_by_name
            
            :param self:
            :param puuid: Puuid from the player data

            Returns: Dictionary with summoner data or none
            """
           
            url = f"{self.base_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
            print(f"Fetching summoner")

            return self._make_request(url)
    
    def get_accountData(self, gameName, tagLine):
         """
         This function is to get account data by riot id from a player using tagline ex: #LAN + gameName
         
         :param tagLine: 
         :param gameName: 
         """
         from urllib.parse import quote
         encoded_name = quote(gameName)
         url = (f"{self.regional_url}/riot/account/v1/accounts/by-riot-id/{encoded_name}/{tagLine}")
         print(f"Fetching Account")

         return self._make_request(url)
    
        
    def get_match_history(self, puuid, count=20, start=0):
            """
            Function to get match ids for a player
            
            :param puuid: Player PUUID (from summoner data)
            :param count: Number of matches to retrieve
            :param start: Starting Index

            Returns:
                List of match IDs
            """

            url = (f"{self.regional_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
                   f"?start={start}&count={count}")
            print(f"Fetching {count} matches")

            data = self._make_request(url)
            return data if data else []


    def get_match_details(self, match_id):
            """
            Function to get match details using the match id
            
            :param match_id: Match id 

            """

            url = (f"{self.regional_url}/lol/match/v5/matches/{match_id}")
            print(f"Fetching match: {match_id}")

            return self._make_request(url)
        
    def get_champion_masteries(self, puuid, count = 10):
            """
            Function to get mastery data for a summoner

            :param puuid: The encrypted puuid
            :param count: Number of masteries to retrieve

            Returns:
                List of mastery data or empty list
            """

            url = (f"{self.base_url}/lol/champion-mastery/v4/champion-masteries/"
               f"by-puuid/{puuid}/top?count={count}")
            
            print(f"Fetching top {count} champion masteries")

            return self._make_request(url)
        

if __name__ == "__main__":
    print("Testing Riot API Class")

    api = RIOTAPI(region= "la1")

    try:
        summoner_name, tagLine = input("Enter a summoner name and tag (separated by space): ").split()
        summoner = api.get_accountData(summoner_name, tagLine)
        print(f"Successfully retrieved data for {summoner_name}#{tagLine}")
    except ValueError:
        print("Error: Please enter exactly 2 values separated by a space")
    except Exception as e:
        print(f"API Error: {e}")

    summoner_info = api.get_summonerInfo(summoner['puuid'])

    if summoner_info:
        print("Summoner found!")
        print(f"Level: {summoner_info['summonerLevel']}")
        print(f"PUUID: {summoner_info['puuid'][:20]}...")


        matches = api.get_match_history(summoner_info['puuid'], count = 5)
        print(f"\nFound {len(matches)} recent matches")
        for i, match_id in enumerate(matches, 1):
            print(f"{i}. {match_id}")

        
        masteries = api.get_champion_masteries(summoner_info['puuid'], count = 5)
        print(f"\n✅ Found {len(masteries)} champion masteries")
        for i, mastery in enumerate(masteries, 1):
            print(f"  {i}. Champion {mastery['championId']}: "
                  f"{mastery['championPoints']:,} points (Level {mastery['championLevel']})")
    else:
        print("❌ Could not fetch summoner data")
    
    print("\n✅ Testing complete!")




            
            
            
            
      




"""
Database utilities for storing match data
"""

import sqlite3
import pandas as pd 
from datetime import datetime

class MatchDatabase:

    def __init__(self, db_path = 'data/lol_matches.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        #matches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                game_duration INTEGER,
                game_creation INTEGER,
                game_version TEXT,
                team_100_win INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        #team stats table 

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_stats (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       match_id TEXT,
                       team_id INTEGER,
                       kills INTEGER,
                       deaths INTEGER,
                       assists INTEGER,
                       gold INTEGER,
                       damage INTEGER,
                       cs INTEGER,
                       vision_score INTEGER,
                       towers INTEGER,
                       dragons INTEGER,
                       barons INTEGER,
                       FOREIGN KEY (match_id) REFERENCES matches(match_id)
                       )
            ''')
        
        #player stats table

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id TEXT,
                        puuid TEXT,
                        summoner_name TEXT,
                        role TEXT,
                        kills INTEGER, 
                        deaths INTEGER,
                        assists INTEGER,
                        cs INTEGER,
                        gold INTEGER,
                        win INTEGER,
                        FOREIGN KEY (match_id) REFERENCES matches(match_id)
                        )
            ''')
        
        self.conn.commit()
        print("Database created")

    def insert_match(self, match_features):
        """
        Function to insert match data into database
    
        :param match_features: dictionary with match features

        returns True if added or False if no
        """

        try: 
            self.cursor.execute('''
                INSERT INTO matches(
                    match_id, game_duration, game_creation,
                    game_version, team_100_win
                    ) VALUES (?, ?, ?, ?, ?)
            ''', (
                match_features['match_id'],
                match_features['game_duration'],
                match_features.get('game_creation', 0),
                match_features.get('game_version', 'unknown'),
                match_features['team_100_win']
            ))

            self.cursor.execute('''
                INSERT INTO team_stats(
                    match_id, team_id, kills, deaths, assists, gold,
                    damage, cs, vision_score, towers, dragons, barons 
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_features['match_id'],
                100, 
                match_features.get('t100_kills', 0),
                match_features.get('t100_deaths', 0),
                match_features.get('t100_assists', 0),
                match_features.get('t100_gold', 0),
                match_features.get('t100_damage', 0),
                match_features.get('t100_cs', 0),
                match_features.get('t100_vision', 0),
                match_features.get('t100_towers', 0),
                match_features.get('t100_dragons', 0),
                match_features.get('t100_barons', 0)
            ))

            self.cursor.execute('''
                INSERT INTO team_stats(
                    match_id, team_id, kills, deaths, assists, gold,
                    damage, cs, vision_score, towers, dragons, barons 
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_features['match_id'],
                200, 
                match_features.get('t200_kills', 0),
                match_features.get('t200_deaths', 0),
                match_features.get('t200_assists', 0),
                match_features.get('t200_gold', 0),
                match_features.get('t200_damage', 0),
                match_features.get('t200_cs', 0),
                match_features.get('t200_vision', 0),
                match_features.get('t200_towers', 0),
                match_features.get('t200_dragons', 0),
                match_features.get('t200_barons', 0)
            ))

            self.conn.commit()

            return True
        
        except sqlite3.IntegrityError:
            #Match duplicado
            print(f"Match {match_features['match_id']} already exists in DB")
            return False
        
        except Exception as e:
            print(f"Error: {e}")
            self.conn.rollback()
            return False
        
    def insert_player_data(self, player_features_list):
        """
        Docstring for insert_player_data
        
        :param player_features_list: Lista de diccionarios con datos de los jugadores

        returns number of players inserted 
        """

        ins_count = 0

        try:
            player_data = []

            for player in player_features_list:
                player_data.append((
                    player['match_id'],
                    player.get('puuid', ''),
                    player.get('summoner_name', ''),
                    player.get('champion_id', 0),
                    player.get('champion_name', ''),
                    player.get('team_position', 'UNKNOWN'),
                    player.get('team_id', 0),
                    player.get('kills', 0),
                    player.get('deaths', 0),
                    player.get('assists', 0),
                    player.get('total_cs', 0),
                    player.get('gold_earned', 0),
                    player.get('damage_dealt', 0),
                    player.get('vision_score', 0),
                    player.get('win', 0)
                    ))
                
            self.cursor.executemany('''
                INSERT INTO player_stats (
                    match_id, puuid, summoner_name, champion_id.
                    champion_name, team_position, team_id, kills, deaths, assists, total_cs
                    gold_earned, damage_dealt, vision_score, win) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', player_data)
            
            self.conn.commit()

        except Exception as e:
            print(f"Error: {e}")
            self.conn.rollback()
            return 0

    # QUERIES

    def query_matches(self, limit):
        """
        Docstring for query_matches
        
        :param limit: max matches 

        returns: dataframe with matches ordered by date 
        """

        query = f'''
            SELECT * FROM matches
            ORDER BY created_at DESC
            LIMIT {limit}
        '''
        return pd.read_sql_query(query, self.conn)

    def query_match_by_id(self, match_id):
        query = f'''
            SELECT * FROM matches
            WHERE match_id = ? 
        '''
        return pd.read_sql_query(query, self.conn, params=(match_id,))
    
    def query_player_stats(self, summoner_name):
        query = f'''
            SELECT * FROM player_stats
            WHERE summoner_name = ? 
            ORDER BY match_id DESC
        '''
        return pd.read_sql_query(query, self.conn, params=(summoner_name,) )
    
    def query_team_stats(self, match_id):
        query = f'''
            SELECT * FROM team_stats
            WHERE match_id = ?
            ORDER BY team_id
        '''
        return pd.read_sql_query(query, self.conn, params=(match_id,))
    
    def query_wins_by_summoner(self, summoner_name):
        query = f'''
            SELECT 
                COUNT(*) as total_games,
                SUM(win) as wins,
                AVG(win) as win_rate,
                AVG(kills) as avg_kills,
                AVG(deaths) as avg_deaths,
                AVG(assists) as avg_assists,
            FROM player_stats
            WHERE summoner_name = ?
        '''

        self.cursor.execute(query, (summoner_name,))
        result = self.cursor.fetchone()

        return {
            'total_games': result[0],
            'wins': result[1],
            'win_rate': result[2],
            'kills': result[3],
            'deaths': result[4],
            'assists': result[5]
        }
    
    def query_champion_stats(self, champion_name):
        query = f'''
            SELECT 
                COUNT(*) as games_played,
                AVG(win) as win_rate,
                AVG(kills) as avg_kills, 
                AVG(deaths) as avg_deaths, 
                AVG(assists) as avg_assists, 
                AVG(cs) as avg_cs
            FROM player_stats
            WHERE champion_name = ?
        '''
        self.cursor.execute(query, (champion_name,))
        result = self.cursor.fetchone()

        return {
            'games_played': result[0],
            'win_rate': result[1],
            'avg_kills': result[2],
            'avg_deaths': result[3],
            'avg_assists': result[4],
            'avg_cs': result[5]
        }
    
    def get_stats(self):
        """
        Function for fetching stats from the database

        returns a dict with general stats
        """

        stats = {}

        # total matches
        self.cursor.execute("SELECT COUNT(*) FROM matches")
        stats['total_matches'] = self.cursor.fetchone()[0]

        # total players
        self.cursor.execute("SELECT COUNT(DISTINCT summoner_name) FROM player_stats")
        stats['unique_player'] = self.cursor.fetchone()[0]

        # total player records
        self.cursor.execute("SELECT COUNT(*) FROM player_stats")
        stats['total_player_records'] = self.cursor.fetchone()[0]

        #win rate avg team 100
        self.cursor.execute("SELECT AVG(team_100_win) FROM matches")
        stats['team_100_win_rate'] = self.cursor.fetchone()[0]

        #avg match time 
        self.cursor.execute("SELECT AVG(game_duration) FROM matches")
        stats['avg_game_duration'] = self.cursor.fetchone()[0]

        return stats
    
    def get_the_top_players(self, limit=10):
        """
        Function to fetch the players with the most registered matches
        
        :param limit: Limit of players to return

        Returns:
                Data Frame of the top players
        """

        query = f''' 
            SELECT
                summoner_name,
                COUNT(*) as games_played,
                AVG(win) as win_rate,
                AVG(kills) as avg_kills,
                AVG(deaths) as avg_deaths,
                AVG(assists) as avg_assists
            FROM player_stats
            GROUP BY summoner_name
            ORDER BY games_played DESC
            LIMIT {limit}
        '''

        return pd.read_sql_query(query, self.conn)
    
    def execute_custom_query(self, query, params = None):
        """
        Function to execute a custom query 
        
        :param query: Query SQL 
        :param params: parameters for the query
        """
        if params:
            return pd.read_sql_query(query, self.conn, params=params)
        else:
            return pd.read_sql_query(query, self.conn)
        
    def export_to_cvs(self, table_name, output_path):

        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, self.conn)
        df.to_csv(output_path, index=False)
        print(f"{table_name} exported to {output_path}")

    def clear_table(self, table_name):

        confirm = input(f"Are you sure you want to clear {table_name}? (yes/no): ")

        if confirm.lower() == "yes":
            self.cursor.execute(f"DELETE FROM {table_name}")
            self.conn.commit()
            print(f"Cleared {table_name}")
        else:
            print("Cancelled")
    
    def close(self):
        self.conn.close()
        print("Connection ended")



# testing

if __name__ == "__main__":
    print("Testing DATABASE")

    db = MatchDatabase()

    stats = db.get_stats()
    print("\n Database Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Ver matches recientes
    if stats['total_matches'] > 0:
        print("\n📋 Recent Matches:")
        matches = db.query_matches(limit=5)
        print(matches)
        
        # Ver top players
        print("\n Top Players:")
        top_players = db.get_top_players(limit=5)
        print(top_players)
        
        # Ver top champions
        print("\n Top Champions:")
        top_champs = db.get_top_champions(limit=5)
        print(top_champs)
    else:
        print("\n Theres no data in the data base")
    
    # Cerrar
    db.close()
    
    print("\n Completed test")


                    
                    




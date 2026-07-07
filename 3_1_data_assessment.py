import sys 
sys.path.append('src')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from database import MatchDatabase
import sqlite3

# DB connection

def connectDB():
    db = MatchDatabase()
    conn = sqlite3.connect('lol_matches.db')
    return db, conn

def basic_inspection(conn):
    print("Data Assessment REPORT")

    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type = 'table'",
        conn
    )

    print("\nTables in the database")
    print(tables)
    
    #Match table 
    df = pd.read_sql_query("SELECT * FROM matches", conn)

    print(f"\nTotal matches: {len(df)}")
    print(f"\nTotal columns: {len(df.columns)}")
    print(f"   Memoria usada: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    return df


# Checking missing values

def check_missing_values(df):
    print("\n Missing values")

    # null values
    null_counts = df.isnull().sum()
    null_percent = (null_counts / len(df)) * 100

    missing_df = pd.DataFrame({
        'column' : null_counts.index(),
        'missing_count': null_counts.values,
        'missing_percent': null_percent.values
    })

    missing_df = missing_df[missing_df['missing_count']] > 0

    if len(missing_df) > 0:
        print("\nColumns with NULL value: ")
        print(missing_df.to_string(index=False))
    else:
        print("\nThere is no NULL values in the dataset")

    print("\nSuspicious Values:")

    # game_creation = 0 (
    if 'game_creation' in df.columns:
        zero_creation = (df['game_creation'] == 0).sum()
        print(f"   game_creation = 0: {zero_creation} ({zero_creation/len(df)*100:.1f}%)")
    
    # game_version = "unknown"
    if 'game_version' in df.columns:
        unknown_version = (df['game_version'] == 'unknown').sum()
        print(f"   game_version = 'unknown': {unknown_version} ({unknown_version/len(df)*100:.1f}%)")
    
    return missing_df

def check_duplicates(df):

    print("\nChecking duplicated values")

    duplicated_matches = df['match_id'].duplicated().sum()
    print(f"\nMatches with the same ID: {duplicated_matches}")

    if duplicated_matches > 0:
        print("Example of duplicated values")
        duped = df[df['match_id'].duplicated(keep=False)]['match_id'].value_counts().head(5)
        print(duped)

    full_duplicates = df.duplicated().sum()
    print("\nRows completely duplicated")
    print(f"Total: {full_duplicates}")

    return duplicated_matches, full_duplicates

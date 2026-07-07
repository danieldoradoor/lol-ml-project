from datetime import datetime
import sys 
sys.path.append('src')

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
import numpy as np

#
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def load_data(db_path = 'data/lol_matches.db'):
    """
    Loads data from SQLite
    
    returns dataframe
    """
    conn = sqlite3.connect(db_path)

    query = """
    SELECT 
        m.*,
        t1.kills as t100_kills,
        t1.deaths as t100_deaths,
        t1.assists as t100_assists,
        t1.gold as t100_gold,
        t1.damage as t100_damage,
        t1.cs as t100_cs,
        t1.vision_score as t100_vision,
        t1.towers as t100_towers,
        t1.dragons as t100_dragons,
        t1.barons as t100_barons,
        t2.kills as t200_kills,
        t2.deaths as t200_deaths,
        t2.assists as t200_assists,
        t2.gold as t200_gold,
        t2.damage as t200_damage,
        t2.cs as t200_cs,
        t2.vision_score as t200_vision,
        t2.towers as t200_towers,
        t2.dragons as t200_dragons,
        t2.barons as t200_barons
    FROM matches m
    LEFT JOIN team_stats t1 ON m.match_id = t1.match_id AND t1.team_id = 100
    LEFT JOIN team_stats t2 ON m.match_id = t2.match_id AND t2.team_id = 200
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def overview(df):

    """ Show baic dataset information """

    print("\nBasic Overview")
    print(f"Rows (match): {df.shape[0]}")
    print(f"Columns (features): {df.shape[0]}")

    print("Data types")
    print(df.dtypes.value_counts())

    memory_mb = df.memory_usage(deep=True).sum() / 1024**2
    print(f"\nMemoria usada: {memory_mb:.2f} MB")

    
def check_missing_values(df):
    
    print("\nChecking for missing values...")

    missing = df.isnull().sum()
    missing_percentage = (df.isnull().sum() / len(df)) * 100

    missing_df= pd.DataFrame({
        'Missing_Count' : missing,
        'Missing_Percent': missing_percentage
    })

    missing_df = missing_df[missing_df['Missing_Count'] > 0].sort_values(
        'Missing_Count', 
        ascending=False
    )
    
    if len(missing_df) == 0:
        print("\nthere is no missing values")
    else:
        print(f"\n columns with missing values:")
        print(missing_df)
        
        # graphics
        if len(missing_df) > 0:
            plt.figure(figsize=(10, 6))
            missing_df['Missing_Percent'].plot(kind='bahr', color = 'coral')
            plt.xlabel("Percentage of Missing Values")
            plt.title("Missing Values per Column")
            plt.tight_layout()
            plt.savefig('reports/missing_values.png', dpi=300)
            print("Saved")
            
    return missing_df


# CHECKING DUPLICATES

def check_duplicates(df):
    """ Checks for duplicates in the dataset """

    #duplicated match games
    duplicated_ids = df['match_id'].duplicated().sum()
    print(f'Duplicated Match Ids: {duplicated_ids}')

    #duplicated rows
    duplicated_rows = df.duplicated().sum()
    print(f'Dupliacted rows: {duplicated_rows}')

    if duplicated_ids > 0:
        print("\nDuplicate match id found")
        dup_ids = df[df['match_id'].duplicated(keep=False)]['match_id'].unique()
        for match_id in dup_ids[:5]:  
            print(f"   - {match_id}")
    
    return duplicated_ids, duplicated_rows


def descriptive_statistics(df):
    """ Calculated descriptive statistics """

    print("\nDescriptive Statistics")
    
    #selectingg only numeric columns
    numeric_colummns = df.select_dtypes(include = [np.number]).columns

    print(f"Stats for numeric columns: {numeric_colummns}")
    print(df[numeric_colummns].describe())

    print("Key Statistics: ")

    if 'game_duration' in df.columns:
        print("\nGame duration: ")
        print(f" Min: {df['game_duration'].min()/60:.1f} min")
        print(f" Max: {df['game_duration'].max()/60:.1f} min")
        print(f" Average: {df['game_duration'].mean()/60:.1f} min")

    if 'team_100_wins' in df.columns:
        winrate = df['team_100_win'].mean()
        print(f"Winrate Team 100: {winrate:.1%}")

    # checking for outliers

    for col in ['game_duration', 't100_kills', 't100_assists', 't100_deaths', 't200_kills', 't200_assists', 't200_deaths', 't100_gold', 't200_gold']:
        if col in df.columns:
            Q1 = df[col].quantile(0.24)
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]

            if len(outliers) > 0:
                print(f"   {col}: {len(outliers)} outliers ({len(outliers)/len(df)*100:.1f}%)")

def logical_validation(df):
    """
    Validating data issues 
        """
    print("Logic Validation")

    
    issues = []
    
    if 'game_duration' in df.columns:
        too_short = df[df['game_duration'] < 600]  # < 10 min
        too_long = df[df['game_duration'] > 4500]  # > 75 min
        
        if len(too_short) > 0:
            issues.append(f"  {len(too_short)} matches < 10 min (posible remake or error )")
        if len(too_long) > 0:
            issues.append(f"  {len(too_long)} matches > 75 min (rarely long)")
    
    kill_cols = [c for c in df.columns if 'kills' in c.lower()]
    for col in kill_cols:
        negative = df[df[col] < 0]
        if len(negative) > 0:
            issues.append(f" {len(negative)} negative values in {col}")
    
    gold_cols = [c for c in df.columns if 'gold' in c.lower()]
    for col in gold_cols:
        if col in df.columns:
            negative = df[df[col] < 0]
            if len(negative) > 0:
                issues.append(f" {len(negative)} negative values in {col}")
    
    if 'team_100_win' in df.columns:
        invalid_win = df[~df['team_100_win'].isin([0, 1])]
        if len(invalid_win) > 0:
            issues.append(f" {len(invalid_win)} invalid values in team_100_win")
    
    # Resultados
    if len(issues) == 0:
        print("\nAll logic validation went through")
    else:
        print("\nFound issues:")
        for issue in issues:
            print(f"   {issue}")
    
    return issues


def generate_quality_report(df, missing_df, duplicated_ids, duplicated_rows, issues):
    """
    Genera un reporte de calidad de datos.
    """
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# DATA QUALITY REPORT
**Generated:** {timestamp}
**Dataset:** lol_matches.db

---

## DATASET OVERVIEW

- **Total Matches:** {len(df):,}
- **Total Features:** {df.shape[1]}
- **Memory Usage:** {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB

---

## MISSING VALUES

"""
    
    if len(missing_df) == 0:
        report += " No missing values found!\n\n"
    else:
        report += f"Found missing values in {len(missing_df)} columns:\n\n"
        report += missing_df.to_markdown() + "\n\n"
    
    report += f"""
---

## 🔄 DUPLICATES

- **Duplicated match_ids:** {duplicated_ids}
- **Duplicated rows:** {duplicated_rows}

"""
    
    if duplicated_ids == 0 and duplicated_rows == 0:
        report += " No duplicates found!\n\n"
    
    report += """
---

## LOGICAL VALIDATION

"""
    
    if len(issues) == 0:
        report += " All logical validations passed!\n\n"
    else:
        report += "Issues found:\n\n"
        for issue in issues:
            report += f"- {issue}\n"
        report += "\n"
    
    report += f"""
---

##  KEY STATISTICS

- **Average Game Duration:** {df['game_duration'].mean()/60:.1f} minutes
- **Win Rate Team 100:** {df['team_100_win'].mean():.1%}
- **Average Kills (Team 100):** {df['t100_kills'].mean():.1f}
- **Average Gold (Team 100):** {df['t100_gold'].mean():,.0f}

---

## 🎯 NEXT STEPS

Based on this assessment:

1. {' No missing values to handle' if len(missing_df) == 0 else '  Handle missing values'}
2. {' No duplicates to remove' if duplicated_ids == 0 else '  Remove duplicates'}
3. {' No logical issues' if len(issues) == 0 else '  Fix logical inconsistencies'}
4. Check for outliers
5. Create clean dataset

---

*Report generated by Data Cleaning Pipeline v1.0*
"""
    
    # Guardar reporte
    with open('reports/data_quality_report.md', 'w') as f:
        f.write(report)
    
    print("\n" + "="*60)
    print("📄 REPORTE DE CALIDAD GENERADO")
    print("="*60)
    print(" Guardado en: reports/data_quality_report.md")


if __name__ == "__main__":
    print("DATA QUALITY ASSESSMENT")
    
    # Crear carpeta reports si no existe
    import os
    os.makedirs('reports', exist_ok=True)
    
    # 1. Cargar datos
    df = load_data()
    
    # 2. Overview básico
    overview(df)
    
    # 3. Missing values
    missing_df = check_missing_values(df)
    
    # 4. Duplicados
    dup_ids, dup_rows = check_duplicates(df)
    
    # 5. Estadísticas
    descriptive_statistics(df)
    
    # 6. Validación lógica
    issues = logical_validation(df)
    
    # 7. Generar reporte
    generate_quality_report(df, missing_df, dup_ids, dup_rows, issues)
    
    print("\n" + "="*60)
    print("LESSON 3.1 COMPLETE")
    print("="*60)
    print("\nView report in: reports/data_quality_report.md")
    print("Check graphics in: reports/")
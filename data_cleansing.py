import csv
import pandas as pd
import numpy as np
import os
from datetime import datetime

def clean_cod_hardpoint_data(input_file="score_log.csv", output_file="cleaned_score_log.csv"):
    """
    Clean Call of Duty Hardpoint scoreboard data:
    1. Truncate data after first 250 or last 249 score
    2. Smooth data to eliminate outliers and ensure logical score progression
    """
    print(f"Reading data from {input_file}...")
    
    # Read the CSV file
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Make a backup of original data
    backup_file = f"original_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(input_file)}"
    df.to_csv(backup_file, index=False)
    print(f"Original data backed up to {backup_file}")
    
    # Print column names to debug
    print(f"CSV columns: {df.columns.tolist()}")
    
    # Identify score columns (use column indices for simplicity)
    cols = df.columns.tolist()
    
    # Assuming the first column is timestamp, second is team1, third is team2
    timestamp_col = cols[0]
    team1_col = cols[1] if len(cols) > 1 else None
    team2_col = cols[2] if len(cols) > 2 else None
    
    print(f"Using columns: Timestamp={timestamp_col}, Team1={team1_col}, Team2={team2_col}")
    
    # Convert None/NaN values to None for easier handling
    df = df.replace('None', np.nan)
    
    # Fix data types
    if team1_col:
        df[team1_col] = pd.to_numeric(df[team1_col], errors='coerce')
    if team2_col:
        df[team2_col] = pd.to_numeric(df[team2_col], errors='coerce')
    
    print("Original data statistics:")
    print(f"Total rows: {len(df)}")
    if team1_col:
        print(f"Team 1 score range: {df[team1_col].min()} - {df[team1_col].max()}")
    if team2_col:
        print(f"Team 2 score range: {df[team2_col].min()} - {df[team2_col].max()}")
    
    # Step 1: Truncate data after first 250 or last 249
    max_score_index = -1
    for i, row in df.iterrows():
        team1_score = row[team1_col] if team1_col else None
        team2_score = row[team2_col] if team2_col else None
        
        # Check if either team has reached 250
        if (pd.notna(team1_score) and team1_score == 250) or (pd.notna(team2_score) and team2_score == 250):
            max_score_index = i
            break
    
    # If no 250 found, check for last 249
    if max_score_index == -1:
        for i in range(len(df)-1, -1, -1):
            team1_score = df.iloc[i][team1_col] if team1_col else None
            team2_score = df.iloc[i][team2_col] if team2_col else None
            
            if (pd.notna(team1_score) and team1_score == 249) or (pd.notna(team2_score) and team2_score == 249):
                max_score_index = i
                break
    
    # Truncate the dataframe if needed
    if max_score_index != -1:
        df = df.iloc[:max_score_index+1]
        print(f"Data truncated at index {max_score_index} where a team reached winning score")
    
    # Step 2: Smooth out data and fix outliers
    
    # Function to smooth a single team's scores
    def smooth_team_scores(scores):
        smoothed = scores.copy()
        last_valid_score = 0
        
        # First pass: Fix missing values and ensure scores never decrease
        for i in range(len(smoothed)):
            if pd.isna(smoothed[i]):
                smoothed[i] = last_valid_score
            elif smoothed[i] < last_valid_score:
                # Score decreased, which is impossible - keep last valid score
                smoothed[i] = last_valid_score
            else:
                last_valid_score = smoothed[i]
        
        # Second pass: Fix unrealistic jumps (adjust the threshold as needed)
        MAX_REASONABLE_JUMP = 10  # Maximum reasonable score jump in a single time unit
        
        for i in range(1, len(smoothed)):
            jump = smoothed[i] - smoothed[i-1]
            if jump > MAX_REASONABLE_JUMP:
                # Large jump detected, smooth it out
                smoothed[i] = smoothed[i-1] + min(jump, MAX_REASONABLE_JUMP)
        
        return smoothed
    
    # Apply smoothing to both teams
    if team1_col:
        df[team1_col] = smooth_team_scores(df[team1_col].values)
    if team2_col:
        df[team2_col] = smooth_team_scores(df[team2_col].values)
    
    # Save cleaned data
    df.to_csv(output_file, index=False)
    
    print("\nCleaning complete!")
    print(f"Cleaned data statistics:")
    print(f"Total rows: {len(df)}")
    if team1_col:
        print(f"Team 1 score range: {df[team1_col].min()} - {df[team1_col].max()}")
    if team2_col:
        print(f"Team 2 score range: {df[team2_col].min()} - {df[team2_col].max()}")
    print(f"Cleaned data saved to {output_file}")
    print("You can run the visualization script to see the results: python visualize_scores.py")

if __name__ == "__main__":
    clean_cod_hardpoint_data()

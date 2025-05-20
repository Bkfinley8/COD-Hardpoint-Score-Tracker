
import csv
import pandas as pd
import numpy as np
import os
from datetime import datetime

def clean_cod_hardpoint_data(gui_mode=False, winning_team=None):
    """
    Clean Call of Duty Hardpoint scoreboard data:
    1. Remove all data before the last 0,0 reading (match start)
    2. Truncate data after first 250 or last 249 score
    3. Smooth data to eliminate outliers and ensure logical score progression
    4. Fix the last data entry so winning team has exactly 250 points
    
    Parameters:
    gui_mode (bool): If True, function will not prompt for user input in the console
    winning_team (int, optional): For GUI mode, specify which team won (1 or 2) when both are at 249
    
    Returns:
    dict: Status information about the processing for GUI mode
    """
    # To store status information for GUI mode
    status_info = {
        "success": True,
        "message": "",
        "needs_winner_selection": False,
        "team1_name": "",
        "team2_name": ""
    }

    # Define project root as one level above this script
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, ".."))

    # File paths in root
    input_file = os.path.join(project_root, "score_log.csv")
    output_file = os.path.join(project_root, "cleaned_score_log.csv")
    backup_dir = os.path.join(project_root, "raw_output_copies")
    os.makedirs(backup_dir, exist_ok=True)  # Create folder if it doesn't exist

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
    backup_path = os.path.join(backup_dir, backup_file)
    df.to_csv(backup_path, index=False)
    print(f"Original data backed up to {backup_path}")

    
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
    
    # Step 0: Remove all data before the first two consecutive valid Timer Readings
    timer_col = cols[3] if len(cols) > 3 else None
    if timer_col:
        df[timer_col] = pd.to_numeric(df[timer_col], errors='coerce')
        first_valid_index = None
        for i in range(len(df) - 1):
            if pd.notna(df.iloc[i][timer_col]) and pd.notna(df.iloc[i + 1][timer_col]):
                first_valid_index = i
                break
        if first_valid_index is not None:
            df = df.iloc[first_valid_index:]
            print(f"Pre-game data removed: Starting from row {first_valid_index} where first two consecutive timer readings were found")
        else:
            print("No valid consecutive timer readings found. Using all data.")
    else:
        print("Timer column not found. Skipping pre-game data removal based on timer readings.")

    
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
    
    # TODO CHECK FOR GAME GOING TO TIME

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
    
    # Step 3: Normalize to one reading per second

    # Convert timestamp column to datetime
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])

    # Sort and drop duplicate timestamps, keeping the most recent (last)
    df = df.sort_values(by=timestamp_col).drop_duplicates(subset=timestamp_col, keep='last')

    # Create a full index of every second between the min and max timestamp
    full_range = pd.date_range(start=df[timestamp_col].min(), end=df[timestamp_col].max(), freq='s')

    # Reindex the DataFrame using this full range
    df = df.set_index(timestamp_col).reindex(full_range)

    # Forward-fill the missing values to fill gaps
    df = df.ffill()

    # Reset the timestamp index back to a column
    df = df.reset_index().rename(columns={"index": timestamp_col})

    print(f"Normalized to 1 row per second. Total rows: {len(df)}")
    
    # Step 4: Fix the last data entry - ensure winning team has 250 points
    final_team1_score = df.iloc[-1][team1_col] if team1_col else None
    final_team2_score = df.iloc[-1][team2_col] if team2_col else None
    
    # Get team names for better user prompts
    team1_name = team1_col if team1_col else "Team 1"
    team2_name = team2_col if team2_col else "Team 2"
    
    # Update status info with team names
    status_info["team1_name"] = team1_name
    status_info["team2_name"] = team2_name
    
    # Check if we need to fix a 249 score
    if (pd.notna(final_team1_score) and final_team1_score == 249 and 
        pd.notna(final_team2_score) and final_team2_score == 249):
        # Edge case: both teams at 249
        status_msg = f"\nEdge case detected: Both {team1_name} and {team2_name} have scores of 249."
        
        if gui_mode:
            if winning_team in [1, 2]:
                # Use the provided winning team from GUI
                if winning_team == 1:
                    df.iloc[-1, df.columns.get_loc(team1_col)] = 250
                    status_msg += f"\nFinal score updated: {team1_name}=250, {team2_name}=249"
                elif winning_team == 2:
                    df.iloc[-1, df.columns.get_loc(team2_col)] = 250
                    status_msg += f"\nFinal score updated: {team1_name}=249, {team2_name}=250"
            else:
                # GUI mode but no winning team provided - signal that we need it
                status_info["needs_winner_selection"] = True
                status_info["message"] = f"Both {team1_name} and {team2_name} have scores of 249. Please select the winning team."
                print(status_msg)
                print("GUI mode active but no winning team specified. Returning without finishing.")
                return status_info
        else:
            # Command-line mode: prompt for user input
            print(status_msg)
            valid_input = False
            while not valid_input:
                try:
                    winner = input(f"Enter 1 if {team1_name} won or 2 if {team2_name} won: ")
                    if winner == "1":
                        df.iloc[-1, df.columns.get_loc(team1_col)] = 250
                        valid_input = True
                        status_msg += f"\nFinal score updated: {team1_name}=250, {team2_name}=249"
                        print(f"Final score updated: {team1_name}=250, {team2_name}=249")
                    elif winner == "2":
                        df.iloc[-1, df.columns.get_loc(team2_col)] = 250
                        valid_input = True
                        status_msg += f"\nFinal score updated: {team1_name}=249, {team2_name}=250"
                        print(f"Final score updated: {team1_name}=249, {team2_name}=250")
                    else:
                        print("Invalid input. Please enter 1 or 2.")
                except Exception as e:
                    print(f"Error processing input: {e}")
                    print("Please enter 1 or 2.")
        
        status_info["message"] = status_msg
    
    # Handle case where only one team is at 249 (no team at 250)
    elif pd.notna(final_team1_score) and final_team1_score == 249 and (pd.isna(final_team2_score) or final_team2_score < 249):
        df.iloc[-1, df.columns.get_loc(team1_col)] = 250
        status_msg = f"Auto-fixing score: {team1_name} score updated from 249 to 250"
        print(status_msg)
        status_info["message"] = status_msg
    elif pd.notna(final_team2_score) and final_team2_score == 249 and (pd.isna(final_team1_score) or final_team1_score < 249):
        df.iloc[-1, df.columns.get_loc(team2_col)] = 250
        status_msg = f"Auto-fixing score: {team2_name} score updated from 249 to 250"
        print(status_msg)
        status_info["message"] = status_msg
    else:
        status_msg = "No score corrections needed for the last entry"
        print(status_msg) 
        status_info["message"] = status_msg

    # Save cleaned data
    df.to_csv(output_file, index=False)
    
    # Prepare final status message
    final_status = "\nCleaning complete!\n"
    final_status += f"Cleaned data statistics:\n"
    final_status += f"Total rows: {len(df)}\n"
    if team1_col:
        final_status += f"Team 1 score range: {df[team1_col].min()} - {df[team1_col].max()}\n"
    if team2_col:
        final_status += f"Team 2 score range: {df[team2_col].min()} - {df[team2_col].max()}\n"
    final_status += f"Cleaned data saved to {output_file}\n"
    final_status += "You can run the visualization script to see the results: python visualize_scores.py"
    
    print(final_status)
    
    if gui_mode:
        # Add final statistics to status_info
        status_info["final_stats"] = {
            "total_rows": len(df),
            "team1_min": df[team1_col].min() if team1_col else None,
            "team1_max": df[team1_col].max() if team1_col else None,
            "team2_min": df[team2_col].min() if team2_col else None,
            "team2_max": df[team2_col].max() if team2_col else None
        }
        return status_info

def run_from_gui(winning_team=None):
    """
    Entry point when called from GUI
    
    Parameters:
    winning_team (int, optional): Team number that won (1 or 2) if both are at 249
    
    Returns:
    dict: Status information about the processing
    """
    return clean_cod_hardpoint_data(gui_mode=True, winning_team=winning_team)

if __name__ == "__main__":
    # When run directly (not imported), run in console mode
    clean_cod_hardpoint_data(gui_mode=False)
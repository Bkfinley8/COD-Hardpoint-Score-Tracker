import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from datetime import datetime

def apply_custom_styling(ax, fig, team1_name, team2_name, map_name, team1_color, team2_color):
    import numpy as np
    import matplotlib.pyplot as plt

    # Set dark style
    plt.style.use('dark_background')
    fig.patch.set_facecolor('#171717')
    ax.set_facecolor('#171717')

    # Add background texture
    np.random.seed(42)
    texture = np.random.normal(0.1, 0.05, size=(100, 100))
    plt.imshow(texture, cmap='gray', alpha=0.3, extent=[0, len(ax.lines[0].get_xdata()), 0, 250])

    # Grid lines
    ax.grid(axis='y', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
    ax.set_axisbelow(True)
    ax.tick_params(axis='both', which='major', labelsize=14, colors='white')
    ax.set_ylim(0, 260)
    ax.set_yticks([0, 50, 100, 150, 200, 250])

    # Title and subtitle
    fig.text(0.15, 0.94, 'GAME FLOW', color='white', fontsize=40, fontweight='bold')
    fig.text(0.75, 0.94, f'MAP 1 - HARDPOINT: {map_name.upper()}', color='white', fontsize=20)

    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=team1_color, 
                   markersize=15, label=team1_name.upper(), linewidth=0),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=team2_color, 
                   markersize=15, label=team2_name.upper(), linewidth=0)
    ]
    legend = ax.legend(handles=legend_elements, loc='upper center', ncol=2, frameon=False, fontsize=14)
    legend.get_texts()[0].set_color(team1_color)
    legend.get_texts()[1].set_color(team2_color)
    plt.setp(legend, bbox_to_anchor=(0.55, 0.95))

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)


def visualize_cod_scores(input_file="cleaned_score_log.csv", output_file="score_progression.png"):
    """
    Create visualizations of Call of Duty Hardpoint score data
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
    
    # Print column names to debug
    cols = df.columns.tolist()
    print(f"CSV columns: {cols}")
    
    # Identify score columns (use column indices for simplicity)
    timestamp_col = cols[0]
    team1_col = cols[1] if len(cols) > 1 else None
    team2_col = cols[2] if len(cols) > 2 else None
    
    print(f"Using columns: Timestamp={timestamp_col}, Team1={team1_col}, Team2={team2_col}")
    
    # Create basic line chart
    plt.figure(figsize=(12, 6))
    if team1_col:
        plt.plot(df[team1_col], label='Team 1', linewidth=2)
    if team2_col:
        plt.plot(df[team2_col], label='Team 2', linewidth=2)
    
    plt.title('Call of Duty Hardpoint Score Progression', fontsize=16)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Score', fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add gridlines at score milestones
    plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
    plt.axhline(y=100, color='gray', linestyle='--', alpha=0.3)
    plt.axhline(y=150, color='gray', linestyle='--', alpha=0.3)
    plt.axhline(y=200, color='gray', linestyle='--', alpha=0.3)
    plt.axhline(y=250, color='gray', linestyle='--', alpha=0.3)
    
    # Save basic visualization
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"Basic score progression plot saved to {output_file}")
    
    # Try to create an advanced visualization if possible
    try:
        # Create a more detailed visualization with timestamps
        plt.figure(figsize=(14, 8))
        
        # Main score plot
        ax1 = plt.subplot(211)
        if team1_col:
            ax1.plot(df[team1_col], 'b-', label='Team 1', linewidth=2)
        if team2_col:
            ax1.plot(df[team2_col], 'r-', label='Team 2', linewidth=2)
        
        ax1.set_title('Call of Duty Hardpoint Score Progression', fontsize=16)
        ax1.set_ylabel('Score', fontsize=12)
        ax1.legend(loc='upper left', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # Score difference plot
        if team1_col and team2_col:
            ax2 = plt.subplot(212, sharex=ax1)
            score_diff = df[team1_col] - df[team2_col]
            ax2.plot(score_diff, 'g-', label='Team 1 - Team 2', linewidth=2)
            ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax2.set_xlabel('Time (seconds)', fontsize=12)
            ax2.set_ylabel('Score Difference', fontsize=12)
            ax2.legend(loc='upper left', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # Fill above/below zero line
            ax2.fill_between(range(len(score_diff)), score_diff, 0, 
                            where=(score_diff > 0), color='green', alpha=0.3)
            ax2.fill_between(range(len(score_diff)), score_diff, 0, 
                            where=(score_diff < 0), color='red', alpha=0.3)
        
        plt.tight_layout()
        advanced_file = f"advanced_{output_file}"
        plt.savefig(advanced_file, dpi=300)
        print(f"Advanced visualization saved to {advanced_file}")
        
    except Exception as e:
        print(f"Could not create advanced visualization: {e}")
        
    print("\nVisualization complete!")

if __name__ == "__main__":
    # Allow command line arguments for input/output files
    input_file = sys.argv[1] if len(sys.argv) > 1 else "cleaned_score_log.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "score_progression.png"
    
    visualize_cod_scores(input_file, output_file)

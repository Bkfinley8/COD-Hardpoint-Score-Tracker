import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import json

from scipy.interpolate import make_interp_spline

def smooth_line(x, y, points=300):
    x_new = np.linspace(x.min(), x.max(), points)
    spline = make_interp_spline(x, y, k=5)
    y_new = spline(x_new)
    return x_new, y_new


def apply_custom_styling(ax, fig, team1_name, team2_name, map_name, team1_color, team2_color, map_number, hill_duration, rotation_length):
    # Set dark style with clean grey background
    plt.style.use('dark_background')
    fig.patch.set_facecolor('#262626')  # Darker grey for figure background
    ax.set_facecolor('#333333')         # Lighter grey for plot area
    
    # Grid lines
    ax.grid(axis='y', color='#555555', linestyle='-', linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(axis='both', which='major', labelsize=10, colors='white')
    ax.set_ylim(0, 260)
    ax.set_yticks([0, 50, 100, 150, 200, 250])
    start, end = ax.get_xlim()
    num_ticks = int((end - start) // hill_duration) + 1
    tick_positions = np.arange(0, num_ticks * hill_duration, hill_duration)
    tick_labels = [f'P{(i % rotation_length) + 1}' for i in range(len(tick_positions))]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=10, color='white')


    # Adjust position of the plot within the figure to use more horizontal space
    plt.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.1)
    
    # Title and subtitle
    fig.text(0.05, 0.91, 'GAME FLOW', color='white', fontsize=24, fontweight='bold')
    fig.text(0.71, 0.92, f'MAP {map_number} - HARDPOINT: {map_name.upper()}', color='white', fontsize=14)

    # Legend
    legend_elements = [
        plt.Line2D([0], [0], color=team1_color, label=team1_name.upper(), linewidth=3),
        plt.Line2D([0], [0], color=team2_color, label=team2_name.upper(), linewidth=3)
    ]
    legend = ax.legend(handles=legend_elements, loc='upper center', ncol=2, frameon=False, fontsize=12)
    legend.get_texts()[0].set_color(team1_color)
    legend.get_texts()[1].set_color(team2_color)
    plt.setp(legend, bbox_to_anchor=(0.20, 0.95))

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

def visualize_cod_scores(
    input_file="cleaned_score_log.csv", 
    output_file="score_progression.png",
    config_file="tracker_config.json",
    dpi=150  # Lower DPI since we're targeting 1920x1080 resolution
):
    print(f"Reading data from {input_file}...")

    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    print(f"Reading config from {config_file}...")

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return
    
    map_name = config.get("map_name", "Unknown Map")
    map_settings = config.get("map_settings", {})
    map_info = map_settings.get(map_name, {})
    hill_duration = map_info.get("hill_duration", 60)
    rotation_length = map_info.get("rotation_length", 4)
    map_number = config.get("map_number", 1)
    team1 = config.get("team1", {})
    team2 = config.get("team2", {})

    team1_name = team1.get("name", "Team 1")
    team2_name = team2.get("name", "Team 2")
    team1_color = team1.get("color", "#FF8C42")
    team2_color = team2.get("color", "white")

    cols = df.columns.tolist()
    print(f"CSV columns: {cols}")
    
    timestamp_col = cols[0]
    team1_col = cols[1] if len(cols) > 1 else None
    team2_col = cols[2] if len(cols) > 2 else None

    print(f"Using columns: Timestamp={timestamp_col}, Team1={team1_col}, Team2={team2_col}")

    # Create figure sized appropriately for 1920x1080 broadcast
    fig, ax = plt.subplots(figsize=(12.8, 7.2))  # 16:9 aspect ratio sized for 1920x1080 at 150 DPI
    x_data = range(len(df))
    
    # For finding points at 60 second intervals
    interval_points = np.arange(0, len(df), 60)
    
    x_array = np.array(x_data)

    if team1_col:
        y1 = df[team1_col].values
        x_smooth, y_smooth = smooth_line(x_array, y1)
        ax.plot(x_smooth, y_smooth, linewidth=3, color=team1_color, label=team1_name)
        ax.plot(interval_points, df.iloc[interval_points][team1_col], 'o', color=team1_color, 
            markersize=8, markeredgecolor='black', markeredgewidth=1)

    if team2_col:
        y2 = df[team2_col].values
        xsmooth, y_smooth = smooth_line(x_array, y2)
        ax.plot(x_smooth, y_smooth, linewidth=3, color=team2_color, label=team2_name)
        ax.plot(interval_points, df.iloc[interval_points][team2_col], 'o', color=team2_color, 
            markersize=8, markeredgecolor='black', markeredgewidth=1)

    # Set x-axis limits to avoid padding
    ax.set_xlim(left=0, right=len(df) - 1)

    apply_custom_styling(ax, fig, team1_name, team2_name, map_name, team1_color, team2_color, map_number, hill_duration, rotation_length)
    
    # No need for tight_layout since we're using subplots_adjust in apply_custom_styling
    plt.savefig(output_file, dpi=dpi)
    print(f"Styled score progression plot saved to {output_file} at {dpi} DPI (approx. {int(12.8*dpi)}x{int(7.2*dpi)} pixels)")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "cleaned_score_log.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "score_progression.png"
    config_file = sys.argv[3] if len(sys.argv) > 3 else "tracker_config.json"
    visualize_cod_scores(input_file, output_file, config_file)
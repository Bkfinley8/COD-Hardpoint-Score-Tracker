import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import subprocess
import threading
import os
import signal
import sys
import json
import shutil
from PIL import Image, ImageTk
from PIL.Image import Resampling
import importlib.util

# Import data_processing module directly
script_dir = os.path.dirname(__file__)
data_processing_path = os.path.join(script_dir, "data_processing.py")
spec = importlib.util.spec_from_file_location("data_processing", data_processing_path)
data_processing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_processing)

# Initialize global variable
tracker_process = None

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INIT_SCRIPT = "init_bbox.py"
TRACKER_SCRIPT = "tracker-gui.py"
DATA_PROCESSING_SCRIPT = "data_processing.py"
VISUALIZATION_SCRIPT = "visualize_scores.py"
CLEANED_CSV = os.path.join(BASE_DIR, "cleaned_score_log.csv")
CONFIG_FILE = os.path.join(BASE_DIR, "tracker_config.json")
OUTPUT_IMAGE = os.path.join(BASE_DIR, "score_progression.png")

# Create GUI
root = tk.Tk()
root.title("Score Tracker GUI")
root.geometry("600x700")
root.protocol("WM_DELETE_WINDOW", lambda: on_close())

# Layout containers
main_frame = tk.Frame(root)
main_frame.pack(pady=10, fill=tk.X)

left_panel = tk.Frame(main_frame)
left_panel.pack(side=tk.LEFT, padx=10, fill=tk.Y)

right_panel = tk.Frame(main_frame)
right_panel.pack(side=tk.RIGHT, padx=10)

center_panel = tk.Frame(main_frame)
center_panel.pack(side=tk.LEFT, padx=10)

# Left panel for additional buttons (replacing the bbox_config viewer)
bbox_config_button = tk.Button(left_panel, text="See BBox Config", command=lambda: show_bbox_config(), width=20)
bbox_config_button.pack(pady=10)

# Center: Buttons
frame = center_panel

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=15)
text_area.pack(padx=10, pady=10)
text_area.config(state=tk.DISABLED)

team1_text = tk.Text(root, height=1, width=120)
team1_text.pack(padx=10, pady=(5, 0))
team1_text.config(state=tk.DISABLED)

team2_text = tk.Text(root, height=1, width=120)
team2_text.pack(padx=10, pady=(0, 10))
team2_text.config(state=tk.DISABLED)

# Graph window reference
graph_window = None

# Right: Config editor
entry_fields = {}
def create_entry(parent, label):
    tk.Label(parent, text=label).pack()
    entry = tk.Entry(parent, width=25)
    entry.pack()
    return entry

entry_fields['map_name'] = create_entry(right_panel, "Map Name")
entry_fields['map_number'] = create_entry(right_panel, "Map Number")
entry_fields['team1_name'] = create_entry(right_panel, "Team 1 Name")
entry_fields['team1_color'] = create_entry(right_panel, "Team 1 Color")
entry_fields['team2_name'] = create_entry(right_panel, "Team 2 Name")
entry_fields['team2_color'] = create_entry(right_panel, "Team 2 Color")

def autofill_tracker_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            entry_fields['map_name'].delete(0, tk.END)
            entry_fields['map_name'].insert(0, config.get('map_name', ''))
            entry_fields['map_number'].delete(0, tk.END)
            entry_fields['map_number'].insert(0, str(config.get('map_number', '')))
            team1 = config.get('team1', {})
            team2 = config.get('team2', {})
            entry_fields['team1_name'].delete(0, tk.END)
            entry_fields['team1_name'].insert(0, team1.get('name', ''))
            entry_fields['team1_color'].delete(0, tk.END)
            entry_fields['team1_color'].insert(0, team1.get('color', ''))
            entry_fields['team2_name'].delete(0, tk.END)
            entry_fields['team2_name'].insert(0, team2.get('name', ''))
            entry_fields['team2_color'].delete(0, tk.END)
            entry_fields['team2_color'].insert(0, team2.get('color', ''))
    except Exception as e:
        append_text(f"Error reading tracker_config.json: {e}\n")

def append_text(text):
    text_area.config(state=tk.NORMAL)
    text_area.insert(tk.END, text)
    text_area.see(tk.END)
    text_area.config(state=tk.DISABLED)

def clear_graph():
    global graph_window
    if graph_window and graph_window.winfo_exists():
        graph_window.destroy()
    graph_window = None

def set_score_range_text(team1, team2):
    team1_text.config(state=tk.NORMAL)
    team2_text.config(state=tk.NORMAL)
    team1_text.delete("1.0", tk.END)
    team2_text.delete("1.0", tk.END)
    team1_text.insert(tk.END, f"Team 1 score range: {team1}")
    team2_text.insert(tk.END, f"Team 2 score range: {team2}")
    team1_text.config(state=tk.DISABLED)
    team2_text.config(state=tk.DISABLED)

def update_graph_button_state():
    graph_button.config(state=tk.NORMAL if os.path.exists(CLEANED_CSV) else tk.DISABLED)

def download_graph(event=None):
    if os.path.exists(OUTPUT_IMAGE):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Save Graph As"
        )
        if save_path:  # User didn't cancel the dialog
            try:
                shutil.copy2(OUTPUT_IMAGE, save_path)
                append_text(f"Graph saved to: {save_path}\n")
            except Exception as e:
                append_text(f"Error saving graph: {e}\n")
    else:
        append_text("No graph available to download.\n")

def show_graph_window():
    """Display the score graph in a separate window"""
    global graph_window
    
    # Close existing window if open
    if graph_window and graph_window.winfo_exists():
        graph_window.destroy()
    
    if not os.path.exists(OUTPUT_IMAGE):
        append_text("No graph image available to display.\n")
        return
    
    # Create new window
    graph_window = tk.Toplevel(root)
    graph_window.title("Score Progression")
    graph_window.geometry("950x600")
    
    # Create a frame to hold the image
    frame = tk.Frame(graph_window)
    frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    # Load and display the image
    img = Image.open(OUTPUT_IMAGE)
    img = img.resize((900, 500), Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    
    # Use a label to display the image
    graph_label = tk.Label(frame, image=photo)
    graph_label.image = photo  # Keep a reference
    graph_label.pack(expand=True)
    
    # Add click functionality for download
    graph_label.bind("<Button-1>", download_graph)
    graph_label.bind("<Enter>", lambda e: graph_label.config(cursor="hand2"))
    graph_label.bind("<Leave>", lambda e: graph_label.config(cursor=""))
    
    # Add instruction text
    instruction_label = tk.Label(
        graph_window, 
        text="Click on the graph to download it as a PNG file",
        font=("Arial", 10)
    )
    instruction_label.pack(pady=5)
    
    # Add download button as an alternative to clicking
    download_button = tk.Button(graph_window, text="Download Graph", command=download_graph)
    download_button.pack(pady=10)
    
    return graph_window

def get_team_names_from_config():
    """Load team names from the tracker config file"""
    team1_name = "Team 1"
    team2_name = "Team 2"
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            team1 = config.get('team1', {})
            team2 = config.get('team2', {})
            team1_name = team1.get('name', 'Team 1')
            team2_name = team2.get('name', 'Team 2')
    except Exception as e:
        append_text(f"Error reading team names from config: {e}\n")
    return team1_name, team2_name

def select_winning_team():
    """Show a dialog to select the winning team when both teams are at 249"""
    # Get team names from config file
    team1_name, team2_name = get_team_names_from_config()
    
    winner_dialog = tk.Toplevel(root)
    winner_dialog.title("Select Winner")
    winner_dialog.geometry("300x150")
    winner_dialog.transient(root)
    winner_dialog.grab_set()  # Modal dialog
    
    tk.Label(
        winner_dialog, 
        text=f"Both teams are at 249 points.\nWhich team won the match?",
        pady=10
    ).pack()
    
    selected_winner = tk.IntVar()
    
    tk.Radiobutton(
        winner_dialog, 
        text=f"Team 1: {team1_name}", 
        variable=selected_winner, 
        value=1,
        pady=5
    ).pack()
    
    tk.Radiobutton(
        winner_dialog, 
        text=f"Team 2: {team2_name}", 
        variable=selected_winner, 
        value=2,
        pady=5
    ).pack()
    
    # Default selection
    selected_winner.set(0)
    
    result = {"winner": None}
    
    def on_submit():
        if selected_winner.get() in [1, 2]:
            result["winner"] = selected_winner.get()
            winner_dialog.destroy()
        else:
            messagebox.showwarning("Selection Required", "Please select a winning team")
    
    tk.Button(winner_dialog, text="Submit", command=on_submit).pack(pady=10)
    
    # Wait for dialog to close
    root.wait_window(winner_dialog)
    return result["winner"]

def run_data_processing():
    def target():
        clear_graph()
        append_text("Starting data processing...\n")
        
        try:
            # First run to check if we need to select a winner
            result = data_processing.run_from_gui()
            
            if result["needs_winner_selection"]:
                # Get team names from config for display in the log
                team1_name, team2_name = get_team_names_from_config()
                
                append_text(f"Both {team1_name} and {team2_name} have scores of 249.\n")
                append_text("Please select which team won the match...\n")
                
                # Show dialog to select winning team
                winner = select_winning_team()
                
                if winner:
                    # Run again with the winner specified
                    append_text(f"Selected winner: {'Team 1' if winner == 1 else 'Team 2'}\n")
                    result = data_processing.run_from_gui(winning_team=winner)
                else:
                    append_text("No winner selected. Data processing incomplete.\n")
                    return
            
            # Display the message from the data processing
            if "message" in result:
                append_text(result["message"] + "\n")
            
            # Set team score ranges
            if "final_stats" in result:
                stats = result["final_stats"]
                team1_range = f"{stats['team1_min']} - {stats['team1_max']}"
                team2_range = f"{stats['team2_min']} - {stats['team2_max']}"
                set_score_range_text(team1_range, team2_range)
            
            append_text("Data processing complete!\n")
            update_graph_button_state()
            
        except Exception as e:
            append_text(f"Error during data processing: {e}\n")
    
    threading.Thread(target=target, daemon=True).start()

def run_old_data_processing():
    """Legacy method that runs the script as subprocess instead of direct import"""
    def target():
        clear_graph()
        try:
            process = subprocess.Popen(
                [sys.executable, "-u", DATA_PROCESSING_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            team1_range = ""
            team2_range = ""
            for line in iter(process.stdout.readline, b''):
                decoded = line.decode("utf-8")
                append_text(decoded)
                if "Team 1 score range:" in decoded:
                    team1_range = decoded.strip().split(":")[1].strip()
                if "Team 2 score range:" in decoded:
                    team2_range = decoded.strip().split(":")[1].strip()
            process.wait()
            set_score_range_text(team1_range, team2_range)
            update_graph_button_state()
        except Exception as e:
            append_text(f"Error running data_processing: {e}\n")
    threading.Thread(target=target, daemon=True).start()

def run_visualize_scores():
    def target():
        try:
            process = subprocess.Popen(
                [sys.executable, VISUALIZATION_SCRIPT, CLEANED_CSV, OUTPUT_IMAGE, CONFIG_FILE],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            for line in iter(process.stdout.readline, b''):
                append_text(line.decode("utf-8"))
            process.wait()
            
            if os.path.exists(OUTPUT_IMAGE):
                # Open graph in a separate window
                root.after(100, show_graph_window)
                append_text("Graph generated! Opening in a new window...\n")
            
        except Exception as e:
            append_text(f"Error running visualize_scores: {e}\n")
    threading.Thread(target=target, daemon=True).start()

def run_init_bbox():
    def target():
        try:
            process = subprocess.Popen(
                [sys.executable, "-u", INIT_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            for line in iter(process.stdout.readline, b''):
                append_text(line.decode("utf-8"))
            process.wait()
        except Exception as e:
            append_text(f"Error running init_bbox: {e}\n")
    threading.Thread(target=target, daemon=True).start()

def toggle_tracker():
    global tracker_process
    if tracker_process is None:
        if os.path.exists("stop_flag.txt"):
            os.remove("stop_flag.txt")
        clear_graph()
        def target():
            global tracker_process
            try:
                tracker_process = subprocess.Popen(
                    [sys.executable, "-u", TRACKER_SCRIPT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                )
                start_stop_button.config(text="Stop Tracker")
                for line in iter(tracker_process.stdout.readline, b''):
                    append_text(line.decode("utf-8"))
                tracker_process.wait()
            except Exception as e:
                append_text(f"Error starting tracker: {e}\n")
            finally:
                tracker_process = None
                start_stop_button.config(text="Start Tracker")
        threading.Thread(target=target, daemon=True).start()
    else:
        with open("stop_flag.txt", "w") as f:
            f.write("stop")
        def wait_for_exit():
            global tracker_process
            if tracker_process:
                tracker_process.wait()
            tracker_process = None
            start_stop_button.config(text="Start Tracker")
        threading.Thread(target=wait_for_exit, daemon=True).start()

def on_close():
    global tracker_process, graph_window
    if tracker_process:
        with open("stop_flag.txt", "w") as f:
            f.write("stop")
        tracker_process.wait()
    if graph_window and graph_window.winfo_exists():
        graph_window.destroy()
    root.destroy()

def show_bbox_config():
    """Display the bbox_config.json in a popup window"""
    config_path = os.path.join(os.path.dirname(__file__), "bbox_config.json")
    config_window = tk.Toplevel(root)
    config_window.title("Bounding Box Configuration")
    config_window.geometry("600x400")
    
    # Create a scrollable text area
    config_text = scrolledtext.ScrolledText(config_window, width=70, height=20, wrap=tk.WORD)
    config_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
            pretty = json.dumps(data, indent=4)
            config_text.insert(tk.END, pretty)
        else:
            config_text.insert(tk.END, "bbox_config.json not found.")
    except Exception as e:
        config_text.insert(tk.END, f"Error loading bbox_config.json: {e}")
    
    # Make it read-only after inserting text
    config_text.config(state=tk.DISABLED)
    
    # Add a close button
    close_button = tk.Button(config_window, text="Close", command=config_window.destroy)
    close_button.pack(pady=10)

def submit_tracker_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        else:
            config = {}

        config['map_name'] = entry_fields['map_name'].get()
        config['map_number'] = int(entry_fields['map_number'].get())
        config['team1'] = {
            'name': entry_fields['team1_name'].get(),
            'color': entry_fields['team1_color'].get()
        }
        config['team2'] = {
            'name': entry_fields['team2_name'].get(),
            'color': entry_fields['team2_color'].get()
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

        append_text("tracker_config.json updated successfully.\n")
    except Exception as e:
        append_text(f"Failed to update config: {e}\n")

# Buttons
init_button = tk.Button(frame, text="Run Bounding Box Setup", command=run_init_bbox, width=30)
init_button.pack(pady=5)

start_stop_button = tk.Button(frame, text="Start Tracker", command=toggle_tracker, width=30)
start_stop_button.pack(pady=5)

process_button = tk.Button(frame, text="Run Data Processing", command=run_data_processing, width=30)
process_button.pack(pady=5)

graph_button = tk.Button(frame, text="Generate Score Graph", command=run_visualize_scores, width=30)
graph_button.pack(pady=5)
graph_button.config(state=tk.DISABLED)

submit_button = tk.Button(right_panel, text="Submit Config", command=submit_tracker_config, width=25)
submit_button.pack(pady=10)

# Init state
update_graph_button_state()
autofill_tracker_config()

root.mainloop()
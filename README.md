# 📊 COD Hardpoint Score Visualization

This script generates a styled visual representation of a Call of Duty Hardpoint match using score log data, with customizable settings like team names, colors, map names, and hill rotations configured via a JSON file.

---

## 🔧 Requirements

- Python **3.8 or newer**  
- `pip` (Python package installer)

---

## 🐍 Step 1: Install Python

If you don’t have Python installed:

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download the latest version for your OS (Windows/macOS/Linux)
3. During installation, **make sure to check** ✅ "Add Python to PATH"

---

## 📦 Step 2: Install Required Python Packages

Open a terminal or command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

---

## 📁 Step 3: Project Structure

Your project folder should include:

```
project/
├── tracker-config.json           # Settings for map, teams, colors, hills
├── bbox_config.json              # Dimensions for tracking bounding boxes
├── init_bbox.py                  # Sets dimensions of bounding boxes
├── tracker.py                    # Script used during HP matches to track score
├── data_cleansing.py             # Script that takes raw scores from tracker.py and fills in holes and fixes outliers
├── visualize_scores_styled.py    # Takes processed data and creates graph
├── cleanse_and_visualize_data.py # Data_cleansing.py + visualize_scores_styled.py (one command)
├── cleaned_score_log.csv         # Processed data (CSV format)
└── score_progression.png         # Output image (created after running)
```

---

## ▶️ Step 4: Usage

First you need to set up your bounding boxes:

```bash
python ./init_bbox.py
```

This will prompt you to select the top-left and bottom-right corners of each teams score board by left clicking. Ensure you leave enough space for three digits numbers to fit. Tighter bounding boxes (without clipping) tend to be more accurate, so find the right balance.



Next you are ready to record the scores from a Hardpoint game. Before the game starts:

```bash
python ./tracker.py
```

Let this run for the duration of the game. When finished CTRL+C to stop recording.



Now run the data processing + visualization script:

```bash
python ./cleanse_and_visualize_data.py
```

You can run these scripts indenpentently:
```bash
python ./data_cleansing.py
```

```bash
python ./visualize_scores_styled.py /path/to/data.csv path/to/output.png path/to/config.json
```

If you omit the arguments, it defaults to:

- `cleaned_score_log.csv` (input)
- `score_progression.png` (output)
- `config.json` (config file)

---

## 📝 Configurable Options

All visual settings are stored in `config.json`. Example:

```json
{
  "map_name": "Hacienda",
  "map_number": 1,
  "team1": {
    "name": "Team 1",
    "color": "#FF8C42"
  },
  "team2": {
    "name": "Team 2",
    "color": "white"
  },
  "map_settings": {
    "Hacienda": {
      "hill_duration": 60,
      "rotation_length": 4
    }
  }
}
```

You can add other maps under `map_settings` to control how hills rotate and are labeled (P1, P2, etc.).

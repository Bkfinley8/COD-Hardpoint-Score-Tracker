import cv2
import pytesseract
import pyautogui
import time
import numpy as np
import csv
import json
from datetime import datetime

# Load bounding boxes
with open("bbox_config.json", "r") as f:
    bbox = json.load(f)

team1 = bbox["team1"]
team2 = bbox["team2"]

team1_scores = []
team2_scores = []
timestamps = []

def extract_score(image, team_name, timestamp):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(resized, 150, 255, cv2.THRESH_BINARY)

    debug_filename = f"debug_scores/{team_name}_{timestamp.replace(':', '-')}.png"
    #cv2.imwrite(debug_filename, thresh)

    config = '--oem 3 --psm 7 --dpi 300 -c tessedit_char_whitelist=0123456789'
    text = pytesseract.image_to_string(thresh, config=config)

    print(f"[DEBUG] OCR raw output for {team_name} at {timestamp}: '{text}'")
    digits = ''.join(filter(str.isdigit, text))
    print(f"[DEBUG] Extracted digits: {digits if digits else 'None'}")

    return digits



try:
    print("Starting score tracking... Press Ctrl+C to stop.")
    while True:
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Crop regions
        team1_img = frame[team1["y"]:team1["y"]+team1["height"], team1["x"]:team1["x"]+team1["width"]]
        team2_img = frame[team2["y"]:team2["y"]+team2["height"], team2["x"]:team2["x"]+team2["width"]]


        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        score1 = extract_score(team1_img, "team1", timestamp)
        score2 = extract_score(team2_img, "team2", timestamp)


        score1_val = int(score1) if score1.isdigit() else None
        score2_val = int(score2) if score2.isdigit() else None

        
        timestamps.append(timestamp)
        team1_scores.append(score1_val)
        team2_scores.append(score2_val)

        print(f"[{timestamp}] Team 1: {score1_val}, Team 2: {score2_val}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopped tracking. Saving results to 'score_log.csv'...")

    with open("score_log.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Team 1 Score", "Team 2 Score"])
        for i in range(len(timestamps)):
            writer.writerow([timestamps[i], team1_scores[i], team2_scores[i]])

    print("Saved.")

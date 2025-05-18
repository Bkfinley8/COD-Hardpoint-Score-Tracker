import cv2
import pytesseract
import pyautogui
import time
import numpy as np
import csv
import json
from datetime import datetime
import easyocr
import subprocess

# Load bounding boxes
with open("bbox_config.json", "r") as f:
    bbox = json.load(f)

team1 = bbox["team1"]
team2 = bbox["team2"]

team1_scores = []
team2_scores = []
timestamps = []

reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have a compatible GPU


def run_scripts():
    try:
        print("Running data_cleansing.py...")
        subprocess.run(["python", "data_cleansing.py"], check=True)

        print("Running visualize_scores_styled.py...")
        subprocess.run(["python", "visualize_scores_styled.py"], check=True)

        print("Both scripts executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing {e.cmd}:")
        print(e)

def extract_score_easyocr(image, team_name, timestamp):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    padded = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=0)
    resized = cv2.resize(padded, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    result = reader.readtext(resized, detail=1, paragraph=False)

    digits = ''
    for bbox, text, conf in result:
        cleaned = ''.join(filter(str.isdigit, text))
        if cleaned:
            digits += cleaned

    #print(f"[DEBUG][EasyOCR] Extracted: {digits}")
    return digits

def extract_score(image, team_name, timestamp):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    padded = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=0)
    resized = cv2.resize(padded, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(resized, 150, 255, cv2.THRESH_BINARY)

    # Save debug view
    #debug_filename = f"debug_scores/{team_name}_{timestamp.replace(':', '-')}.png"
    # cv2.imwrite(debug_filename, thresh)

    # Use image_to_data to get character-wise boxes
    config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
    data = pytesseract.image_to_data(thresh, config=config, output_type=pytesseract.Output.DICT)

    digits = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        try:
            conf = float(data['conf'][i])
        except:
            conf = -1
        if text.isdigit() and conf > 35:
            digits.append(text)

    joined = ''.join(digits)
    print(f"[DEBUG] OCR extracted pieces for {team_name}: {digits} => '{joined}'")
    return joined




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
        score1 = extract_score_easyocr(team1_img, "team1", timestamp)
        score2 = extract_score_easyocr(team2_img, "team2", timestamp)


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
    run_scripts()

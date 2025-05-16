import cv2
import pyautogui
import time
import numpy as np
import csv
import json
from datetime import datetime
from tensorflow.keras.models import load_model

# Load bounding boxes
with open("bbox_config.json", "r") as f:
    bbox = json.load(f)

team1 = bbox["team1"]
team2 = bbox["team2"]

team1_scores = []
team2_scores = []
timestamps = []

model = load_model("digit_model.h5")

def preprocess_for_contours(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Threshold to get binary image
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)  # invert so digits are white
    return thresh

def extract_digits_from_contours(score_img):
    thresh = preprocess_for_contours(score_img)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    digit_imgs = []
    bounding_boxes = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Filter out small noise contours, tweak thresholds as needed
        if w < 5 or h < 10:
            continue
        bounding_boxes.append((x, y, w, h))

    # Sort bounding boxes left to right
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])

    for (x, y, w, h) in bounding_boxes:
        digit_crop = score_img[y:y+h, x:x+w]
        digit_imgs.append(digit_crop)

    return digit_imgs

def preprocess_digit(digit_img):
    gray = cv2.cvtColor(digit_img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (28, 28))
    normalized = resized / 255.0
    input_tensor = normalized.reshape(1, 28, 28, 1)
    return input_tensor

def predict_digit(digit_img):
    input_tensor = preprocess_digit(digit_img)
    prediction = model.predict(input_tensor)
    return np.argmax(prediction)

def extract_score(score_img):
    digit_imgs = extract_digits_from_contours(score_img)
    if not digit_imgs:
        return "0"  # No digits found = 0

    digits_predicted = []
    for digit_img in digit_imgs:
        digit = predict_digit(digit_img)
        digits_predicted.append(str(digit))

    return ''.join(digits_predicted)

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

        # Assuming 3 digits max per score; adjust if your UI differs
        score1 = extract_score(team1_img)
        score2 = extract_score(team2_img)


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

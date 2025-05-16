import cv2
import json
import os
import matplotlib.pyplot as plt

# Load bounding boxes
with open("bbox_config.json", "r") as f:
    bbox = json.load(f)

team1 = bbox["team1"]
team2 = bbox["team2"]

# Path to screenshots or frames
FRAME_FOLDER = "screenshots"
OUTPUT_FOLDER = "digit_dataset"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
for i in range(10):
    os.makedirs(os.path.join(OUTPUT_FOLDER, str(i)), exist_ok=True)

def split_digits(image, num_digits=3):
    h, w = image.shape[:2]
    digit_width = w // num_digits
    digits = []
    for i in range(num_digits):
        digit = image[:, i * digit_width:(i + 1) * digit_width]
        digits.append(digit)
    return digits

def crop_scores(frame):
    team1_img = frame[team1["y"]:team1["y"] + team1["height"], team1["x"]:team1["x"] + team1["width"]]
    team2_img = frame[team2["y"]:team2["y"] + team2["height"], team2["x"]:team2["x"] + team2["width"]]
    return team1_img, team2_img


def label_digits(score_img):
    # Show the full cropped score image
    resized = cv2.resize(score_img, (score_img.shape[1]*2, score_img.shape[0]*2))
    plt.imshow(resized, cmap='gray')
    plt.title("What number is this score? (e.g., 5, 99, 142)")
    plt.axis('off')
    plt.show(block=False)

    score_str = input("Enter full score shown in image (0–250): ").strip()
    plt.close()

    if not score_str.isdigit():
        print("⚠️ Invalid input. Skipping this image.")
        return

    digits = list(score_str)
    digit_imgs = split_digits(score_img, num_digits=len(digits))

    for i, (digit_img, label) in enumerate(zip(digit_imgs, digits)):
        if digit_img is None or digit_img.size == 0:
            print(f"[WARNING] Empty digit for label {label}. Skipping.")
            continue

        resized_digit = cv2.resize(digit_img, (56, 56), interpolation=cv2.INTER_NEAREST)
        plt.imshow(resized_digit, cmap='gray')
        plt.title(f"Labeling: {label}")
        plt.axis('off')
        plt.show(block=False)

        count = len(os.listdir(os.path.join(OUTPUT_FOLDER, label)))
        filename = os.path.join(OUTPUT_FOLDER, label, f"{label}_{count}.png")
        cv2.imwrite(filename, digit_img)
        print(f"✅ Saved digit {label} to {filename}")
        plt.close()



def main():
    for fname in sorted(os.listdir(FRAME_FOLDER)):
        if not fname.lower().endswith((".png", ".jpg")):
            continue
        path = os.path.join(FRAME_FOLDER, fname)
        frame = cv2.imread(path)
        if frame is None:
            continue
        team1_img, team2_img = crop_scores(frame)

        print(f"Label digits from team1 in frame: {fname}")
        label_digits(team1_img)  # pass full crop, not digits list

        print(f"Label digits from team2 in frame: {fname}")
        label_digits(team2_img)  # pass full crop, not digits list

    try:
        cv2.destroyAllWindows()
    except cv2.error:
        pass  # OpenCV GUI functions not supported, safe to ignore



if __name__ == "__main__":
    main()

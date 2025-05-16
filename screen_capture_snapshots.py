import pyautogui
import time
import os
from datetime import datetime

# Settings
CAPTURE_INTERVAL = 2  # seconds
CAPTURE_COUNT = 100   # how many screenshots to take

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

print(f"📸 Starting screen capture every {CAPTURE_INTERVAL}s. Press Ctrl+C to stop early.")

try:
    for i in range(CAPTURE_COUNT):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot = pyautogui.screenshot()
        filepath = os.path.join(SAVE_DIR, f"frame_{timestamp}.png")
        screenshot.save(filepath)
        print(f"Saved {filepath}")
        time.sleep(CAPTURE_INTERVAL)

    print("✅ Done capturing screenshots.")

except KeyboardInterrupt:
    print("\n🛑 Capture interrupted by user.")

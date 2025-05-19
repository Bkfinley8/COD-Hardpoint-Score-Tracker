import json
import pyautogui
from pynput import mouse
import keyboard

print("Welcome to the Bounding Box Setup.",flush=True)
print("You will be asked to click on screen to define the bounding boxes for Team 1 and Team 2.",flush=True)
print("At any point, press ESC to cancel.",flush=True)

def get_click_position(label):
    print(f"\n-> Please LEFT-CLICK on the {label}. Press ESC to cancel.",flush=True)

    pos = []

    def on_click(x, y, button, pressed):
        if pressed:
            pos.append((x, y))
            return False  # Stop listener

    with mouse.Listener(on_click=on_click) as listener:
        while listener.running:
            if keyboard.is_pressed("esc"):
                print("Cancelled.",flush=True)
                listener.stop()
                return None
        listener.join()

    return pos[0] if pos else None

def main():
    team1_tl = get_click_position("TOP-LEFT of Team 1's score box")
    if not team1_tl: return
    team1_br = get_click_position("BOTTOM-RIGHT of Team 1's score box")
    if not team1_br: return

    team2_tl = get_click_position("TOP-LEFT of Team 2's score box")
    if not team2_tl: return
    team2_br = get_click_position("BOTTOM-RIGHT of Team 2's score box")
    if not team2_br: return

    timer_tl = get_click_position("TOP-LEFT of the score timer")
    if not timer_tl: return
    timer_br = get_click_position("BOTTOM-RIGHT of the score timer")
    if not timer_br: return

    config = {
        "team1": {
            "x": team1_tl[0],
            "y": team1_tl[1],
            "width": team1_br[0] - team1_tl[0],
            "height": team1_br[1] - team1_tl[1]
        },
        "team2": {
            "x": team2_tl[0],
            "y": team2_tl[1],
            "width": team2_br[0] - team2_tl[0],
            "height": team2_br[1] - team2_tl[1]
        },
        "timer": {
            "x": timer_tl[0],
            "y": timer_tl[1],
            "width": timer_br[0] - timer_tl[0],
            "height": timer_br[1] - timer_tl[1]
        }
    }

    with open("bbox_config.json", "w") as f:
        json.dump(config, f, indent=4)

    print("\n✅ Bounding boxes saved to 'bbox_config.json'.",flush=True)

if __name__ == "__main__":
    main()

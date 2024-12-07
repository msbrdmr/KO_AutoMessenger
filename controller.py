import time
import pyperclip
import pydirectinput
import autoit
import pyautogui
import pygetwindow as gw

pydirectinput.PAUSE = 0.1
pydirectinput.HOTKEYS = True

class Controller:
    def __init__(self, screen, matcher):
        self.chat_open = False
        self.screen = screen
        self.matcher = matcher

    def focus_window(self):
        """Focuses the game window."""
        try:
            windows = gw.getWindowsWithTitle(self.matcher.window_title)
            if not windows:
                print(
                    f"Error: Window titled '{self.matcher.window_title}' not found.")
                return False

            window = windows[0]
            print(f"Attempting to focus window: {window.title}")
            window.activate()
            time.sleep(0.5)

            
            x, y = window.left + 10, window.top + 10
            autoit.mouse_click("left", x, y)
            
            x, y = window.left + window.width // 2, window.top + window.height // 2 + 80
            autoit.mouse_click("left", x, y)

            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Error focusing window: {e}")
            return False

    def is_window_focused(self):
        """Checks if the game window is currently focused."""
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                active_title = active_window.title.strip()
                if active_title == self.matcher.window_title.strip():
                    return True
            return False
        except Exception as e:
            print(f"Error checking focused window: {e}")
            return False

    def send_global_chat(self, message):
        """Sends a message to the chat input."""
        if not self.is_window_focused():
            if not self.focus_window():
                print("Unable to focus the game window. Cannot send message.")
                return

        try:
            
            pyperclip.copy(message)
            

            
            pydirectinput.press('enter')
            time.sleep(0.5)

            
            
            pydirectinput.press('backspace')
            time.sleep(0.1)

            
            apply_hotkeys('ctrl', 'v')
            print(f"Pasted message: {message}")

            
            pydirectinput.press('enter')
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"Error sending message: {e}")

    def send_private_chat(self, coords, message):
        if not self.is_window_focused():
            if not self.focus_window():
                print("Unable to focus the game window. Cannot send message.")
                return

        try:
            x, y, w, h = coords

            middle_y = y + h // 2
            middle_x = x + w - 10

            autoit.mouse_click("left", middle_x, middle_y)
            time.sleep(0.5)
            print(f"Opened private chat box.")
            pyperclip.copy(message)
            pydirectinput.press('enter')
            time.sleep(0.5)
            pydirectinput.press('backspace')
            time.sleep(0.5)
            
            apply_hotkeys('ctrl', 'v')
            print(f"Pasted message: {message}")
            time.sleep(0.5)
            
            pydirectinput.press('enter')
            time.sleep(0.5)
            
            print(f"Message sent: {message}")
            # press esc to close the box.
            pydirectinput.press('esc') 

        except Exception as e:
            print(f"Error sending private message: {e}")

def apply_hotkeys(key1, key2):
    pydirectinput.keyDown(key1)
    pydirectinput.keyDown(key2)
    time.sleep(0.1)
    pydirectinput.keyUp(key1)
    pydirectinput.keyUp(key2)

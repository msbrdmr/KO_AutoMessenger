import pyautogui
import time
import pygetwindow as gw
import config


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
                print(f"Error: Window titled '{self.matcher.window_title}' not found.")
                return

            window = windows[0]
            window.activate()
            time.sleep(0.5)
            print(f"Focused on window: {self.matcher.window_title}")

        except Exception as e:
            print(f"Error focusing window: {e}")

    def is_window_focused(self):
        """Checks if the game window is currently focused."""
        try:
            active_window = gw.getActiveWindow()
            if active_window and active_window.title == self.matcher.window_title:
                return True
            return False
        except Exception as e:
            print(f"Error checking focused window: {e}")
            return False

    

    def send_global_chat(self, message):
        """Sends a message to the private chat if it's open."""
        if not self.is_window_focused():
            self.focus_window()

        try:
            pyautogui.typewrite(message + '\n', interval=0.1)
            time.sleep(0.5)
            # enter to send 
            pyautogui.press('enter')
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"Error sending message: {e}")

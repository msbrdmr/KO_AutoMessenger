import time
import pyperclip
import pydirectinput
import autoit
import pyautogui
import pygetwindow as gw
import cv2
import numpy as np

pydirectinput.PAUSE = 0.1
pydirectinput.HOTKEYS = True


class Controller:
    def __init__(self, screen, matcher):
        self.chat_open = False
        self.screen = screen
        self.matcher = matcher
        self.window = self.matcher.get_window()
        self.center_x = self.window.left + self.window.width // 2
        self.center_y = self.window.top + self.window.height // 2 + 80

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
            # time.sleep(0.5)

            # x, y = window.left + 10, window.top + 10
            # autoit.mouse_click("left", x, y)

            # x, y = window.left + window.width // 2, window.top + window.height // 2 + 80
            # autoit.mouse_click("left", x, y)

            # time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Error focusing window: {e}")
            return False


    def reset_view(self, screen):
        self.screen = screen
        autoit.mouse_click(
            "left", self.matcher.window_position['left'] +
            10, self.matcher.window_position['top'] + 10, 3
        )

        private_chats = self.matcher.detect_template('private_chat_content')
        print("Open Private Chats:", len(private_chats))

        if len(private_chats) > 0:
            for chat in private_chats:
                pydirectinput.press('esc')
                time.sleep(0.5)

        global_chat_active = self.matcher.detect_template('global_chat_active')
        if len(global_chat_active) > 0:
            pydirectinput.press('enter')
            time.sleep(0.5)
            print("Opened Global Chat")

            global_chat_active_inner = self.matcher.detect_template(
                'global_chat_active')
            if len(global_chat_active_inner) > 0:
                print("Global Chat - Inner")
                pydirectinput.press('enter')
                time.sleep(0.5)

        autoit.mouse_click("left", self.center_x, self.center_y, 10)
        print("View reset completed.")

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

    def visualize_coordinates(self, screen, x, y, w, h):
        try:
            frame = np.array(screen)
            if frame.shape[-1] == 3:
                frame_bgr = frame
            else:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            x, y, w, h = int(x), int(y), int(w), int(h)
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame_bgr, (center_x, center_y), 10, (0, 0, 255), -1)
            coordinates_text = f"X: {x}, Y: {y}, W: {w}, H: {h}"
            cv2.putText(frame_bgr, coordinates_text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.imshow("Coordinates Visualization", frame_bgr)
            print("Visualizing coordinates... Press any key to close the window.")
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        except Exception as e:
            print(f"Error visualizing coordinates: {e}")

        except Exception as e:
            print(f"Error visualizing coordinates: {e}")

    def send_global_chat(self, message):
        """Sends a message to the chat input."""
        if not self.is_window_focused():
            if not self.focus_window():
                print("Unable to focus the game window. Cannot send message.")
                return

        try:

            self.reset_view(self.screen)

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
            x, y, w, h = coords['x'], coords['y'], coords['w'], coords['h']
            x, y, w, h = int(x), int(y), int(w), int(h)

            # game picture top left coords :
            offset_y, offset_x = self.matcher.window_position[
                'left'], self.matcher.window_position['top']

            x = x + offset_x - 21
            y = y + offset_y + 25

            pyautogui.moveTo(x, y)

            middle_y = y + h // 2
            middle_x = x + w - 20
            autoit.mouse_click("left", middle_x, middle_y, 3)
            time.sleep(0.5)
            print(f"Opened private chat box.")
            pyperclip.copy(message)
            time.sleep(0.5)
            pydirectinput.press('backspace')
            time.sleep(0.5)

            apply_hotkeys('ctrl', 'v')
            print(f"Pasted message: {message}")
            time.sleep(0.5)

            pydirectinput.press('enter')
            time.sleep(0.5)

            print(f"Message sent: {message}")

            pydirectinput.press('esc')

            time.sleep(0.5)

            autoit.mouse_click("left", self.center_x, self.center_y, 3)

        except Exception as e:
            print(f"Error sending private message: {e}")

    def send_private_chat_2(self, message, coords=None):
        """Chat box is already open."""
        if not self.is_window_focused():
            if not self.focus_window():
                print("Unable to focus the game window. Cannot send message.")
                return

        try:
            x, y, w, h = coords['x'], coords['y'], coords['w'], coords['h']
            x, y, w, h = int(x), int(y), int(w), int(h)

            self.click_on_point(coords, 5)

            pyautogui.moveTo(x, y)
            time.sleep(0.1)
            pyperclip.copy(message)
            time.sleep(0.1)
            pydirectinput.press('backspace')
            time.sleep(0.1)
            apply_hotkeys('ctrl', 'v')
            print(f"Pasted message: {message}")
            time.sleep(0.1)
            pydirectinput.press('enter')
            time.sleep(0.1)
            print(f"Message sent: {message}")

            pydirectinput.press('enter')
            time.sleep(0.1)

        except Exception as e:
            print(f"Error sending private message: {e}")

    def click_on_point(self, coords, times, offset=[0, 0]):
        """This function gets the center of the point and then clicks on it after applying x and y offsets."""
        if not self.is_window_focused():
            if not self.focus_window():
                print("Unable to focus the game window. Cannot click on point.")
                return

        try:
            x, y, w, h = coords['x'], coords['y'], coords['w'], coords['h']
            x, y, w, h = int(x), int(y), int(w), int(h)

            offset_x, offset_y = self.matcher.window_position[
                'left'], self.matcher.window_position['top']

            x = x + offset_x
            y = y + offset_y

            x_centered = x + w // 2
            y_centered = y + h // 2

            x_final = x_centered + offset[0]
            y_final = y_centered + offset[1]
            autoit.mouse_click("left", x_final, y_final, times)

            # autoit.mouse_click("left", x_final, y_final, times)
            print(f"Clicked on point.")

        except Exception as e:
            print(f"Error clicking on point: {e}")

    def drag_and_drop_2(self, start_coords, end_coords):
        if not self.is_window_focused():
            if not self.focus_window():
                print("Unable to focus the game window. Cannot drag and drop.")
                return

        try:
            start_x, start_y, start_w, start_h = map(
                int, (start_coords['x'], start_coords['y'], start_coords['w'], start_coords['h']))
            end_x, end_y, end_w, end_h = map(
                int, (end_coords['x'], end_coords['y'], end_coords['w'], end_coords['h']))

            offset_x, offset_y = self.matcher.window_position[
                'left'], self.matcher.window_position['top']

            adjusted_start_x = start_x + offset_x - 21
            adjusted_start_y = start_y + offset_y + 25
            adjusted_end_x = end_x + offset_x - 21
            adjusted_end_y = end_y + offset_y + 25

            autoit.mouse_click_drag(
                "left", adjusted_start_x, adjusted_start_y, adjusted_end_x, adjusted_end_y, speed=10)
            print(
                f"Dragged from ({adjusted_start_x}, {adjusted_start_y}) to ({adjusted_end_x}, {adjusted_end_y})")
        except Exception as e:
            print(f"Error occurred while performing drag and drop: {e}")


def apply_hotkeys(key1, key2):
    pydirectinput.keyDown(key1)
    pydirectinput.keyDown(key2)
    time.sleep(0.1)
    pydirectinput.keyUp(key1)
    pydirectinput.keyUp(key2)

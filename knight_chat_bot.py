import threading
import time
import websocket
import shutil
import json
import zipfile
import base64
import cv2
import config
from template_matcher import TemplateMatcher
from controller import Controller
import requests
import subprocess
import sys
import os
import sys

if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

app_path = os.path.abspath(os.path.join(app_path, '..'))

autoit_dll_path = os.path.join(app_path, 'autoit', 'lib', 'AutoItX3_x64.dll')

if os.path.exists(autoit_dll_path):
    os.environ['AUTOIT_X64_DLL'] = autoit_dll_path
else:
    print(f"Error: {autoit_dll_path} not found.")
if os.path.exists(autoit_dll_path):
    os.environ['AUTOIT_X64_DLL'] = autoit_dll_path
else:
    print(f"Error: {autoit_dll_path} not found.")


REPO_OWNER = 'msbrdmr'
REPO_NAME = 'KO_AutoMessenger'
CURRENT_VERSION = '1.0.0'

CURRENT_DIR = os.getcwd()

GITHUB_USERNAME = "msbrdmr"
REPO_NAME = "KO_AutoMessenger"
DOWNLOAD_URL = f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}/releases/latest/download/dist.zip"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "update_temp")
EXE_NAME = "knight_chat_bot.exe"
EXTRACT_DIR = os.path.join(os.getcwd(), "dist")


config_file = os.path.join(os.getcwd(), "config.txt")
IP = config.IP
SERVER_URL = IP

ws = None
ws_thread = None
connected = False
PM_ACTIVE = False
AUTO_CHAT_ACTIVE = False
AUTO_CHAT_THREAD = None
STOP_EVENT = threading.Event()


matcher = TemplateMatcher(
    window_title=config.matcher_config["window_title"],
    global_chat_templates=config.matcher_config["global_chat_templates"],
    private_chat_templates=config.matcher_config["private_chat_templates"],
    private_chat_content_templates=config.matcher_config["private_chat_content_templates"],
    global_chat_active_templates=config.matcher_config["global_chat_active_templates"],
    offsets=config.matcher_config["offsets"],
    threshold=config.matcher_config["threshold"],
    overlap_threshold=config.matcher_config["overlap_threshold"]
)

controller = Controller(matcher.window, matcher)
matcher.controller = controller


def on_message(ws, message):
    global PM_ACTIVE, AUTO_CHAT_ACTIVE, AUTO_CHAT_THREAD, STOP_EVENT
    try:
        data = json.loads(message)
        action = data.get("action")
        username = data.get("username")
        if not action or not username:
            print("Invalid message: Missing 'action' or 'username'")
            return

        screen = matcher.capture_window_image()

        if action == "request_chat_data":
            if screen is None:
                print("Error: Failed to capture the screen.")
                return
            chat_data = matcher.detect_template('global_chat')
            private_chat_data = matcher.detect_template('private_chat')

            if chat_data or private_chat_data:
                send_requested_chat_data(
                    ws, chat_data, private_chat_data, username)
            else:
                print(f"No chat data found for user: {username}")

        elif action == "reset_view":
            controller.reset_view(screen)

        elif action == "start_private_chat":
            if screen is None:
                print("Error: Failed to capture the screen.")
                return
            start_coord = data.get("coords")
            print("Starting private chat. Coordinates:", start_coord)
            controller.click_on_point(start_coord, 6, [90, 0])
            time.sleep(0.5)
            open_private_chats = matcher.detect_template(
                'private_chat_content')

            if len(open_private_chats) > 0:
                open_private_chat = open_private_chats[0]
                controller.click_on_point(
                    open_private_chat['coordinates'], 3, [0, -170])
                PM_ACTIVE = True

            elif len(open_private_chats) == 0:
                print("No private chat found.")
                PM_ACTIVE = False

        elif action == "stop_private_chat":

            if screen is None:
                print("Error: Failed to capture the screen.")
                return
            controller.reset_view(screen)
            PM_ACTIVE = False

        elif action == "send_global_chat":
            msg = data.get("msg")
            print("Sending global chat data. Message:", msg)

            x = matcher.detect_template('global_chat')
            if x:
                controller.send_global_chat(msg)

        elif action == "send_private_chat":
            msg = data.get("msg")
            if screen is None:
                print("Error: Failed to capture the screen.")
                return
            pcc = matcher.detect_template('private_chat_content')
            if PM_ACTIVE and len(pcc) == 1 and msg:
                controller.send_private_chat_2(msg, pcc[0]['coordinates'])

        elif action == "start_auto_chat":
            messages = data.get("messages")
            duration = data.get("duration")
            interval = data.get("interval")

            print("Starting auto chat with data:",
                  messages, interval, duration)

            if not duration or duration <= 0:
                print("Invalid duration for auto chat.")
                return
            if not AUTO_CHAT_ACTIVE:
                AUTO_CHAT_ACTIVE = True
                print(
                    f"Starting auto chat for {duration} seconds at {interval}s intervals.")
                STOP_EVENT.clear()
                AUTO_CHAT_THREAD = threading.Thread(
                    target=run_auto_chat,
                    args=(ws, messages, interval, duration)
                )
                AUTO_CHAT_THREAD.start()

        elif action == "stop_auto_chat":

            if AUTO_CHAT_ACTIVE:
                print("Stopping auto chat...")
                AUTO_CHAT_ACTIVE = False
                STOP_EVENT.set()
                AUTO_CHAT_THREAD.join()
                print("Auto chat stopped.")

        else:
            print(f"Unknown action: {action}")
    except json.JSONDecodeError:
        print("Invalid message format. Expected JSON.")


def on_error(ws, error):
    print("WebSocket error:", error)


def run_auto_chat(ws, messages, interval, duration):
    global AUTO_CHAT_ACTIVE
    start_time = time.time()
    msg_index = 0

    while AUTO_CHAT_ACTIVE and not STOP_EVENT.is_set():
        current_time = time.time()
        if current_time - start_time >= duration:
            print("Auto chat duration complete.")
            break

        if msg_index < len(messages):
            message = messages[msg_index]
            print(f"Sending message: {message}")
            send_auto_global_chat(ws, message)
            msg_index = (msg_index + 1) % len(messages)

        time.sleep(interval)

    AUTO_CHAT_ACTIVE = False


def send_auto_global_chat(ws, message):
    try:
        x = matcher.detect_template('global_chat')
        if x:
            controller.send_global_chat(message)
    except Exception as e:
        print(f"Error sending auto chat message: {e}")


def on_close(ws, close_status_code, close_msg):
    global connected
    print(f"WebSocket closed: {close_status_code}, {close_msg}")
    connected = False


def on_open(ws):
    global connected
    print("WebSocket connection established.")
    connected = True


def send_heartbeat(ws, PM_ACTIVE, AUTO_CHAT_ACTIVE):
    try:
        payload = {
            'type': 'heartbeat',
            'username': config.USERNAME,
            'timestamp': int(time.time()),
            'auto_chat_active': AUTO_CHAT_ACTIVE,
            'pm_active': PM_ACTIVE
        }
        ws.send(json.dumps(payload))
    except Exception as e:
        print(f"Error sending heartbeat: {e}")


def send_requested_chat_data(ws, global_chat_crops, private_chat_crops, username):
    try:
        global_chat_data = []
        private_chat_data = []

        for crop_data in global_chat_crops:
            crop = crop_data['image']
            coords = crop_data['coordinates']

            _, img_encoded = cv2.imencode('.jpg', crop)
            img_bytes = img_encoded.tobytes()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            global_chat_data.append({
                'image': img_base64,
                'coordinates': coords
            })

        for crop_data in private_chat_crops:
            crop = crop_data['image']
            coords = crop_data['coordinates']

            _, img_encoded = cv2.imencode('.jpg', crop)
            img_bytes = img_encoded.tobytes()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            private_chat_data.append({
                'image': img_base64,
                'coordinates': coords
            })

        payload = {
            'type': 'chat_data',
            'username': username,
            'timestamp': int(time.time()),
            'data': {
                'global': global_chat_data,
                'private': private_chat_data
            }
        }
        ws.send(json.dumps(payload))
    except Exception as e:
        print(f"Error sending chat data: {e}")


def send_global_chat_crops(ws, crops):
    try:
        images_as_base64 = []
        coordinates = []

        for crop_data in crops:
            crop = crop_data['image']
            coords = crop_data['coordinates']

            _, img_encoded = cv2.imencode('.jpg', crop)
            img_bytes = img_encoded.tobytes()

            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            images_as_base64.append(img_base64)
            coordinates.append(coords)

        payload = {
            'type': 'global',
            'username': config.USERNAME,
            'data': [{
                    "image": images_as_base64,
                     "coordinates": coordinates
                     }],
            'timestamp': int(time.time())
        }
        ws.send(json.dumps(payload))
    except Exception as e:
        print(f"Error sending heartbeat: {e}")


def send_private_chat_crops(ws, crops):
    try:
        data = []

        for crop_data in crops:
            image = crop_data['image']
            coord = crop_data['coordinates']

            _, img_encoded = cv2.imencode('.jpg', image)
            img_bytes = img_encoded.tobytes()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            data.append({
                'image': img_base64,
                'coordinates': coord
            })

        payload = {
            'type': 'private',
            'username': config.USERNAME,
            'data': data,
            'timestamp': int(time.time())
        }
        ws.send(json.dumps(payload))
    except Exception as e:
        print(f"Error sending private chat crops: {e}")


def fetch_images_periodically():
    global ws_thread
    global ws
    global PM_ACTIVE
    global AUTO_CHAT_ACTIVE
    if not connected:
        print("WebSocket not connected; reconnecting...")
        reconnect_websocket()

    print("Heartbeat pm_active: ", PM_ACTIVE,
          " auto_chat_active: ", AUTO_CHAT_ACTIVE)
    if connected:
        try:
            screen = matcher.capture_window_image()

            if screen is None:
                print("Error: Failed to capture the screen.")
                return

        except Exception as e:
            print(f"Error capturing the screen: {e}")
            return

        chat_data = matcher.detect_template('global_chat')
        controller.center_x = controller.window.left + controller.window.width // 2
        controller.center_y = controller.window.top + controller.window.height // 2 + 80
        if chat_data:
            print("Sending heartbeat...")
            send_heartbeat(ws, PM_ACTIVE, AUTO_CHAT_ACTIVE)
        if PM_ACTIVE:
            private_chat_content = matcher.detect_template(
                'private_chat_content')
            if private_chat_content:
                print("Sending private chat content...")
                send_private_chat_content_crops(ws, private_chat_content)
        else:
            pass


def send_private_chat_content_crops(ws, crops):
    try:
        data = []

        for crop_data in crops:
            image = crop_data['image']
            coord = crop_data['coordinates']

            _, img_encoded = cv2.imencode('.jpg', image)
            img_bytes = img_encoded.tobytes()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            data.append({
                'image': img_base64,
                'coordinates': coord
            })

        payload = {
            'type': 'private_chat_content',
            'username': config.USERNAME,
            'data': data,
            'timestamp': int(time.time())
        }
        ws.send(json.dumps(payload))
    except Exception as e:
        print(f"Error sending private chat crops: {e}")


def reconnect_websocket():
    global ws_thread
    global ws
    global connected

    if ws is None or not ws_thread.is_alive():
        try:
            print("Attempting to reconnect to WebSocket...")

            if ws is not None:
                ws.close()

            ws = websocket.WebSocketApp(
                SERVER_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )

            if ws_thread is None or not ws_thread.is_alive():
                ws_thread = threading.Thread(
                    target=ws.run_forever, kwargs={"ping_interval": 10})
                ws_thread.start()
                print("WebSocket reconnecting...")

            connected = False

        except Exception as e:
            print(f"Error reconnecting: {e}")
            time.sleep(3)


def check_and_send_heartbeat():
    global SERVER_URL
    if connected:
        fetch_images_periodically()
    else:
        print("WebSocket is not connected. Trying to reconnect to url ", SERVER_URL)
        reconnect_websocket()


def download_update(url, save_path):
    print(f"Checking for updates from {url}...")
    with requests.get(url, stream=True) as response:
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                shutil.copyfileobj(response.raw, file)
            print("Update downloaded successfully.")
            return True
        else:
            print(f"No update available. Status code: {response.status_code}")
            return False


def create_update_script(zip_path, target_dir, exe_name):
    script_path = os.path.join(DOWNLOAD_DIR, "update_script.bat")
    extracted_dir = os.path.join(DOWNLOAD_DIR, "extracted")

    with open(script_path, "w") as script:
        script.write(f"""@echo off
        timeout /t 2 /nobreak >nul
        echo Extracting update...
        powershell -Command "Expand-Archive -Force '{zip_path}' '{extracted_dir}'"
        echo Installing update...
        xcopy "{extracted_dir}\\*" "{target_dir}" /s /e /y
        del "{zip_path}" >nul 2>&1
        rmdir /s /q "{extracted_dir}"
        echo Update installed successfully.
        echo Restarting application...
        cd /d "{target_dir}"
        start "" "{os.path.join(target_dir, exe_name)}"
        exit
        """)
    return script_path


def trigger_update(zip_path, exe_name):
    print("Preparing to update...")
    script_path = create_update_script(zip_path, CURRENT_DIR, exe_name)
    subprocess.Popen(["cmd.exe", "/c", script_path], shell=True)
    sys.exit(0)


def check_for_update():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    zip_path = os.path.join(DOWNLOAD_DIR, "dist.zip")

    if download_update(DOWNLOAD_URL, zip_path):
        trigger_update(zip_path, EXE_NAME)


if __name__ == "__main__":
    try:
        # check_for_update()
        reconnect_websocket()
        while True:
            check_and_send_heartbeat()
            time.sleep(3)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

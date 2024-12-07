import threading
import time
import websocket
import json
import base64
import cv2
import config
from template_matcher import TemplateMatcher
from controller import Controller

SERVER_URL = "ws://localhost:8000"
ws = None
ws_thread = None
connected = False

matcher = TemplateMatcher(
    window_title=config.matcher_config["window_title"],
    chat_templates=config.matcher_config["chat_templates"],
    private_chat_templates=config.matcher_config["private_chat_templates"],
    private_chat_content_templates=config.matcher_config["private_chat_content_templates"],
    offsets=config.matcher_config["offsets"],
    threshold=config.matcher_config["threshold"],
    overlap_threshold=config.matcher_config["overlap_threshold"]
)

controller = Controller(matcher.window, matcher)


def on_message(ws, message):
    try:
        data = json.loads(message)
        action = data.get("action")
        username = data.get("username")

        if not action or not username:
            print("Invalid message: Missing 'action' or 'username'")
            return

        print(f"Received action: {action} from user: {username}")
        if action == "request_chat_data":
            screen = matcher.capture_window_image()

            if screen is None:
                print("Error: Failed to capture the screen.")
                return
            chat_boxes = matcher.match_template_with_confidence(
                screen, config.chat_templates)
            chat_boxes = matcher.non_max_suppression(chat_boxes)
            chat_data = matcher.get_cropped_images(
                screen, chat_boxes, config.offsets["global_chat"])

            private_chat_boxes = matcher.match_template_with_confidence(
                screen, config.private_chat_templates)
            private_chat_boxes = matcher.non_max_suppression(
                private_chat_boxes)
            private_chat_data = matcher.get_cropped_images(
                screen, private_chat_boxes, config.offsets["private_chat"])

            if chat_data or private_chat_data:
                send_requested_chat_data(
                    ws, chat_data, private_chat_data, username)
            else:
                print(f"No chat data found for user: {username}")

        elif action == "send_global_chat":
            msg = data.get("msg")
            print("Sending global chat data. Message:", msg)
            # controller.send_global_chat(msg)

            x = detect_template(config.chat_templates)

            print(x)
            # first check if private chat is open

        else:
            print(f"Unknown action: {action}")
    except json.JSONDecodeError:
        print("Invalid message format. Expected JSON.")


def on_error(ws, error):
    print("WebSocket error:", error)


def on_close(ws, close_status_code, close_msg):
    global connected
    print(f"WebSocket closed: {close_status_code}, {close_msg}")
    connected = False


def on_open(ws):
    global connected
    print("WebSocket connection established.")
    connected = True


def send_heartbeat(ws):
    try:
        payload = {
            'type': 'heartbeat',
            'username': config.USERNAME,
            'timestamp': int(time.time())
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


def send_global_chat_crops(ws, crops, username):
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
    if not connected:
        print("WebSocket not connected; reconnecting...")
        reconnect_websocket()

    if connected:
        try:
            screen = matcher.capture_window_image()

            if screen is None:
                print("Error: Failed to capture the screen.")
                return

        except Exception as e:
            print(f"Error capturing the screen: {e}")
            return

        chat_boxes = matcher.match_template_with_confidence(
            screen, config.chat_templates)
        private_chat_boxes = matcher.match_template_with_confidence(
            screen, config.private_chat_templates)

        chat_boxes = matcher.non_max_suppression(chat_boxes)
        private_chat_boxes = matcher.non_max_suppression(private_chat_boxes)

        chat_data = matcher.get_cropped_images(
            screen, chat_boxes, config.offsets["global_chat"])
        private_chat_data = matcher.get_cropped_images(
            screen, private_chat_boxes, config.offsets["private_chat"])

        if chat_data:
            print("Sending heartbeat...")
            send_heartbeat(ws)

        if private_chat_data:
            print("Sending ", len(private_chat_data),
                  " chat crops to notify the server.")
            send_private_chat_crops(ws, private_chat_data)


def send_private_chat_data_crops(ws, crops):
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
            'type': 'private_content',
            'username': config.USERNAME,
            'data': data,
            'timestamp': int(time.time())
        }
        ws.send(json.dumps(payload))
    except Exception as e:
        print(f"Error sending private chat crops: {e}")


def detect_template(template):
    try:
        screen = matcher.capture_window_image()

        if screen is None:
            print("Error: Failed to capture the screen.")

        boxes = matcher.match_template_with_confidence(
            screen, template)

        boxes = matcher.non_max_suppression(boxes)
        boxes = matcher.get_cropped_images(
            screen, boxes, config.offsets[template])

        return boxes

    except Exception as e:
        print(f"Error capturing the screen: {e}")


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
    if connected:
        fetch_images_periodically()
    else:
        print("WebSocket is not connected. Trying to reconnect...")
        reconnect_websocket()


if __name__ == "__main__":
    reconnect_websocket()

    while True:
        check_and_send_heartbeat()
        time.sleep(3)

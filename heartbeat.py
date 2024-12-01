import requests
import numpy as np
import json
import cv2  
import base64
import time
from io import BytesIO
import config

API_URL = "http://localhost:8000"

def send_chat_crops(crops):
    """
    Send the chat crops as a numpy array to an API endpoint.
    The image is encoded in Base64 and sent with metadata.
    """
    images_as_base64 = []
    coordinates = []

    for idx, crop_data in enumerate(crops):
        crop = crop_data['image']  # Extract the image from the dictionary
        coordinates.append(crop_data['coordinates'])  # Extract the coordinates

        _, img_encoded = cv2.imencode('.jpg', crop)
        img_bytes = img_encoded.tobytes()

        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        images_as_base64.append(img_base64)

        # Optionally, display the crop
        # cv2.imshow(f"Chat Crop {idx + 1}", crop)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    payload = {
        'type': 'global',
        'username': config.USERNAME,
        'data': images_as_base64,
        'coordinates': coordinates,  # Add coordinates to the payload
        'timestamp': int(time.time())
    }

    try:
        response = requests.post(API_URL + "/heartbeat", json=payload)
        if response.status_code == 200:
            print("Chat crops successfully uploaded.")
        else:
            print(f"Failed to upload chat crops. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the request: {e}")


def send_private_chat_crops(crops):
    """
    Send the private chat crops as a numpy array to an API endpoint.
    The image is encoded in Base64 and sent with metadata.
    """
    images_as_base64 = []
    coordinates = []

    for idx, crop_data in enumerate(crops):
        crop = crop_data['image']  # Extract the image from the dictionary
        coordinates.append(crop_data['coordinates'])  # Extract the coordinates

        _, img_encoded = cv2.imencode('.jpg', crop)
        img_bytes = img_encoded.tobytes()

        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        images_as_base64.append(img_base64)

        # Optionally, display the crop
        # cv2.imshow(f"Private Chat Crop {idx + 1}", crop)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    # TODO: Also add the pm chat box coordinates so that using callback data, this app knows where to click.

    payload = {
        'type': 'private',
        'username': config.USERNAME,
        'data': images_as_base64,
        'coordinates': coordinates,  # Add coordinates to the payload
        'timestamp': int(time.time())
    }

    try:
        response = requests.post(API_URL + "/private", json=payload)
        if response.status_code == 200:
            print("Private chat crops successfully uploaded.")
        else:
            print(f"Failed to upload private chat crops. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the request: {e}")

from template_matcher import TemplateMatcher
import schedule
import pygetwindow as gw
import time
import win32gui
import win32con
import heartbeat
import config

matcher = TemplateMatcher(
    window_title=config.matcher_config["window_title"],
    chat_templates=config.matcher_config["chat_templates"],
    private_chat_templates=config.matcher_config["private_chat_templates"],
    private_chat_content_templates=config.matcher_config["private_chat_content_templates"],
    offsets=config.matcher_config["offsets"],
    threshold=config.matcher_config["threshold"],
    overlap_threshold=config.matcher_config["overlap_threshold"]
)

def focus_window():
    """Ensure the Knight Online window is focused and unminimized."""
    try:
        window = gw.getWindowsWithTitle("Knight OnLine Client")[0]
        hwnd = window._hWnd
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if style & win32con.WS_MINIMIZE:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # Restore the window
        time.sleep(0.2)
        if win32gui.GetForegroundWindow() != hwnd:
            win32gui.SetForegroundWindow(hwnd)
        return window
    except IndexError:
        print("Error: 'Knight OnLine Client' window not found.")
        return None
    except Exception as e:
        print(f"Unexpected error while focusing window: {e}")
        return None

    
def fetch_images_periodically():
    # focus_window()
    screen = matcher.capture_window_image()
    
    # Match templates
    chat_boxes = matcher.match_template_with_confidence(screen, config.chat_templates)
    private_chat_boxes = matcher.match_template_with_confidence(screen, config.private_chat_templates)
    private_chat_content_boxes = matcher.match_template_with_confidence(screen, config.private_chat_content_templates)

    # Apply non-max suppression
    chat_boxes = matcher.non_max_suppression(chat_boxes)
    private_chat_boxes = matcher.non_max_suppression(private_chat_boxes)
    private_chat_content_boxes = matcher.non_max_suppression(private_chat_content_boxes)

    # Get cropped images and coordinates
    chat_data = matcher.get_cropped_images(screen, chat_boxes, config.offsets["global_chat"])
    private_chat_data = matcher.get_cropped_images(screen, private_chat_boxes, config.offsets["private_chat"])
    private_chat_content_data = matcher.get_cropped_images(screen, private_chat_content_boxes, config.offsets["private_chat_content"])

    # Print bounding box coordinates and images
    # print("Chat Boxes Coordinates and Images:")
    # for data in chat_data:
    #     print(f"x: {data['coordinates']['x']}, y: {data['coordinates']['y']}, "
    #           f"w: {data['coordinates']['w']}, h: {data['coordinates']['h']}")
    #     # You can access the cropped image via data['image']
    #     # For example, saving or sending the image:
    #     # cv2.imwrite('chat_crop.jpg', data['image'])

    # print("Private Chat Boxes Coordinates and Images:")
    # for data in private_chat_data:
    #     print(f"x: {data['coordinates']['x']}, y: {data['coordinates']['y']}, "
    #           f"w: {data['coordinates']['w']}, h: {data['coordinates']['h']}")
    #     # Same as above, process the image as needed.

    # print("Private Chat Content Boxes Coordinates and Images:")
    # for data in private_chat_content_data:
    #     print(f"x: {data['coordinates']['x']}, y: {data['coordinates']['y']}, "
    #           f"w: {data['coordinates']['w']}, h: {data['coordinates']['h']}")
    #     # Handle the cropped image here.

    # Sending crops if any boxes are detected
    print(f"Fetched {len(chat_data)} global chat crops.")
    print(f"Fetched {len(private_chat_data)} private chat crops.")
    print(f"Fetched {len(private_chat_content_data)} private chat content crops.")

    # Send crops to the respective functions
    heartbeat.send_chat_crops(chat_data)
    if len(private_chat_data) > 0: 
        heartbeat.send_private_chat_crops(private_chat_data)


if __name__ == "__main__":
    schedule.every(config.FETCH_INTERVAL).seconds.do(fetch_images_periodically)
    while True:
        schedule.run_pending()
        time.sleep(1)

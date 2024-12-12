import os
import cv2
import numpy as np
import pygetwindow as gw
from PIL import ImageGrab
import config
from controller import Controller


class TemplateMatcher:
    def __init__(self, window_title, global_chat_templates, private_chat_templates, private_chat_content_templates, global_chat_active_templates, offsets, threshold=0.5, overlap_threshold=0.5):
        self.controller = None
        self.window_title = window_title
        self.global_chat_templates = global_chat_templates
        self.private_chat_templates = private_chat_templates
        self.private_chat_content_templates = private_chat_content_templates
        self.global_chat_active_templates = global_chat_active_templates
        self.offsets = offsets
        self.threshold = threshold
        self.overlap_threshold = overlap_threshold
        self.window_position = None
        self.top_center = None
        self.window = self.get_window()
        if not self.window:
            raise RuntimeError(f"Window '{self.window_title}' not found!")
        print(f"Window '{self.window_title}' found.")

    def get_window(self):
        """Get the game window by title."""
        windows = gw.getWindowsWithTitle(self.window_title)
        if windows:
            windows[0].activate()
            return windows[0]
        return None

    def capture_window_image(self):
        """Capture the game window."""
        left, top, right, bottom = self.window.left, self.window.top, self.window.right, self.window.bottom

        if right <= left or bottom <= top:
            print("Window is minimized or invalid. Skipping capture.")
            return None
        
        top += config.grab_screen_offset['top']
        left += config.grab_screen_offset['left']
        right += config.grab_screen_offset['right']
        bottom += config.grab_screen_offset['bottom']

        self.window_position = {"top": top, "left": left}
        self.top_center = {"top": top , "left": left + (right - left) // 2}
        # print(f"Window position: {self.window_position}")
        try:
            screenshot = ImageGrab.grab(
                bbox=(left, top, right, bottom))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except ValueError as e:
            print(f"Error capturing the screen: {e}")
            return None

    def match_template_with_confidence(self, screen, templates):
        """Match multiple templates within the screen and return bounding boxes with confidence."""
        all_boxes = []
        for template_path in templates:
            template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
            if template is None:
                raise FileNotFoundError(
                    f"Template image not found: {template_path}")

            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            result = cv2.matchTemplate(
                screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= self.threshold)
            confidences = [result[pt[1], pt[0]]
                           for pt in zip(*locations[::-1])]

            boxes = [
                (pt[0], pt[1], template.shape[1], template.shape[0], conf)
                for pt, conf in zip(zip(*locations[::-1]), confidences)
            ]
            all_boxes.extend(boxes)

        return all_boxes

    def detect_template(self, template_name, verbose=False, focus=False):
        templates = config.templates.get(template_name, None)
        if not templates:
            print(f"Error: No templates found for {template_name}.")
            return []

        if verbose:
            print(f"Detecting templates for: {template_name}")

        try:
            screen = None
            try:
                screen = self.capture_window_image()
            except Exception as e:
                print(f"Error capturing screen image: {e}")
            
            if screen is None:
                print("Error: Failed to capture the screen.")
                return []
            
            if focus:
                try:
                    self.controller.focus_window()
                except Exception as e:
                    print(f"Error focusing window: {e}")
                    return []

            try:
                boxes = self.match_template_with_confidence(screen, templates)
            except Exception as e:
                print(f"Error during template matching: {e}")
                return []
            
            if not boxes:
                return []

            try:
                boxes = self.non_max_suppression(boxes)
            except Exception as e:
                print(f"Error during non-max suppression: {e}")
                return []

            try:
                cropped_images = self.get_cropped_images(screen, boxes, config.offsets.get(template_name, {}))
            except Exception as e:
                print(f"Error cropping images: {e}")
                return []

            return cropped_images

        except Exception as e:
            print(f"Unexpected error during template detection: {e}")
            return []


    def non_max_suppression(self, boxes):
        """Filter overlapping boxes using non-maximum suppression."""
        if not boxes:
            return []

        boxes = np.array(boxes)
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = x1 + boxes[:, 2]
        y2 = y1 + boxes[:, 3]
        scores = boxes[:, 4]

        indices = cv2.dnn.NMSBoxes(
            bboxes=[[int(x), int(y), int(w), int(h)]
                    for x, y, w, h in boxes[:, :4]],
            scores=scores.tolist(),
            score_threshold=self.threshold,
            nms_threshold=self.overlap_threshold,
        )

        if len(indices) == 0:
            return []

        indices = indices.flatten()
        return [boxes[i] for i in indices]

    def draw_boxes_with_confidence_and_save_images(self, screen, boxes, label, offset, output_dir="output_images"):
        """Draw rectangles around detected areas with confidence scores and save the cropped images from these areas."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for i, (x, y, w, h, conf) in enumerate(boxes):
            if offset[0] != 0:
                y -= offset[0]
                h += offset[0]

            if offset[1] != 0:
                w += offset[1]

            if offset[2] != 0:
                h += offset[2]

            if offset[3] != 0:
                x -= offset[3]
                w += offset[3]

            # Ensure coordinates are non-negative
            x = max(x, 0)
            y = max(y, 0)

            # Draw the rectangle on the screen
            cv2.rectangle(screen, (int(x), int(y)),
                          (int(x + w), int(y + h)), (0, 255, 0), 2)

            # Display the label with the confidence score
            text = f"{label}: {conf:.2f}"
            cv2.putText(screen, text, (int(x), int(y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            cropped_image = screen[int(y):int(y + h), int(x):int(x + w)]

            # Save the cropped image with a unique filename
            output_path = os.path.join(
                output_dir, f"{label}_{i}_{int(conf * 100)}.png")
            cv2.imwrite(output_path, cropped_image)

        return screen

    def refresh_and_display(self):
        """Capture the screen, match templates, and display results."""
        screen = self.capture_window_image()
        chat_boxes = self.match_template_with_confidence(
            screen, self.global_chat_templates)
        private_chat_boxes = self.match_template_with_confidence(
            screen, self.private_chat_templates)
        private_chat_content_boxes = self.match_template_with_confidence(
            screen, self.private_chat_content_templates)

        chat_boxes = self.non_max_suppression(chat_boxes)
        private_chat_boxes = self.non_max_suppression(private_chat_boxes)
        private_chat_content_boxes = self.non_max_suppression(
            private_chat_content_boxes)

        screen_with_boxes = self.draw_boxes_with_confidence_and_save_images(
            screen, chat_boxes, "Chat Box", self.offsets["global_chat"])
        screen_with_boxes = self.draw_boxes_with_confidence_and_save_images(
            screen_with_boxes, private_chat_boxes, "Private Chat Box", self.offsets["private_chat"])
        screen_with_boxes = self.draw_boxes_with_confidence_and_save_images(
            screen_with_boxes, private_chat_content_boxes, "Private Chat Content", self.offsets["private_chat_content"])

        cv2.imshow("Detected Zones with Confidence", screen_with_boxes)

    def get_cropped_images(self, screen, boxes, offset):
        """Extract and return cropped images based on the bounding boxes, along with coordinates."""
        cropped_images = []
        for x, y, w, h, conf in boxes:
            y = max(y - offset[0], 0)
            h += offset[0]
            w += offset[1]
            h += offset[2]
            x = max(x - offset[3], 0)
            w += offset[3]

            cropped_image = screen[int(y):int(y + h), int(x):int(x + w)]

            cropped_images.append({
                'coordinates': {'x': x, 'y': y, 'w': w, 'h': h},
                'image': cropped_image
            })

        return cropped_images if len(cropped_images) > 0 else []

    def is_global_chat_active(self, screen):
        """Check if the global chat is active."""
        # firtst check if theres global chat. Then check if its active.

    def run(self):
        """Run the detection loop."""
        cv2.namedWindow("Detected Zones with Confidence", cv2.WINDOW_NORMAL)
        self.refresh_and_display()
        print("Press 'SPACE' to refresh or 'ESC' to exit.")

        while True:
            self.refresh_and_display()
            cv2.waitKey(1)
            if cv2.getWindowProperty("Detected Zones with Confidence", cv2.WND_PROP_VISIBLE) < 1:
                break

        print("Exiting...")

        cv2.destroyAllWindows()


# TODO: Make it draw entire areas. For chatbox, make it sraw about 100 pixels more above for example
# TODO: Get the user name as well and keep track of it.
# TODO: Get the incoming users name from private chat box...

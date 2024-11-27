import cv2
import numpy as np
import pygetwindow as gw
from PIL import ImageGrab


class TemplateMatcher:
    def __init__(self, window_title, chat_templates, private_chat_templates, private_chat_content_templates, threshold=0.5, overlap_threshold=0.5):
        self.window_title = window_title
        self.chat_templates = chat_templates
        self.private_chat_templates = private_chat_templates
        self.private_chat_content_templates = private_chat_content_templates

        self.threshold = threshold
        self.overlap_threshold = overlap_threshold
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
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

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

    def draw_boxes_with_confidence(self, screen, boxes, label):
        """Draw rectangles around detected areas with confidence scores."""
        for (x, y, w, h, conf) in boxes:
            cv2.rectangle(screen, (int(x), int(y)),
                          (int(x + w), int(y + h)), (0, 255, 0), 2)
            text = f"{label}: {conf:.2f}"
            cv2.putText(screen, text, (int(x), int(y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return screen

    def refresh_and_display(self):
        """Capture the screen, match templates, and display results."""
        screen = self.capture_window_image()
        chat_boxes = self.match_template_with_confidence(
            screen, self.chat_templates)
        private_chat_boxes = self.match_template_with_confidence(
            screen, self.private_chat_templates)
        private_chat_content_boxes = self.match_template_with_confidence(
            screen, self.private_chat_content_templates)

        chat_boxes = self.non_max_suppression(chat_boxes)
        private_chat_boxes = self.non_max_suppression(private_chat_boxes)
        private_chat_content_boxes = self.non_max_suppression(
            private_chat_content_boxes)

        screen_with_boxes = self.draw_boxes_with_confidence(
            screen, chat_boxes, "Chat Box")
        screen_with_boxes = self.draw_boxes_with_confidence(
            screen_with_boxes, private_chat_boxes, "Private Chat Box")
        screen_with_boxes = self.draw_boxes_with_confidence(
            screen_with_boxes, private_chat_content_boxes, "Private Chat Content")

        cv2.imshow("Detected Zones with Confidence", screen_with_boxes)

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

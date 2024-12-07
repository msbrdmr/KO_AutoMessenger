import time
USERNAME = "Veratti"


chat_templates = [
    "templates/chat_0.png",
    "templates/chat_1.png",
    "templates/chat_2.png",
    "templates/chat_3.png",
    "templates/chat_4.png",
    "templates/chat_5.png",
]

private_chat_templates = [
    "templates/private_chat.png",
]

private_chat_content_templates = [
    "templates/private_chat_content.png",
]

# top right bottom left
offsets = {
    "global_chat": (165, -10, -53, -186),
    "private_chat": (0, 0, 0, 175),
    "private_chat_content": (-30, 0, 0, 365),
}

matcher_config = {
    "window_title": "Knight OnLine Client",
    "chat_templates": chat_templates,
    "private_chat_templates": private_chat_templates,
    "private_chat_content_templates": private_chat_content_templates,
    "offsets": offsets,
    "threshold": 0.6,
    "overlap_threshold": 0.4
}

FETCH_INTERVAL = 5


log_file = open("log", "a")


def log_info(message):
    message = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    log_file.write(message + "\n")
    log_file.flush()

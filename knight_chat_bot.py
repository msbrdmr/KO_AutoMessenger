from template_matcher import TemplateMatcher

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


matcher = TemplateMatcher(
    window_title="Knight OnLine Client",  
    chat_templates=chat_templates,   
    private_chat_templates=private_chat_templates, 
    private_chat_content_templates=private_chat_content_templates, 
    threshold=0.6,  
    overlap_threshold=0.4  
)

matcher.run()

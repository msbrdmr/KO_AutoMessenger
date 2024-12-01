# this file will handlw pyautogui commands
import pyautogui
import schedule
import socket
import time
import heartbeat
import pygetwindow
import config


# also, setup socket, on socket send pm or send gm triggers, one of the below func will work. Make the sleeps corect so that, the events are queued, and processed one by one. do not trigger events in parallel.


# 1- handle receiver, honor the hb data and show on ui, show active and offline ones, show messages, parse images, get the text, and put them on ui. 
# 
# 
# 
# Then setup sending mechanisms
#   2- handle sender, send global messages, send private messages



# socket setup
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect(("127.0.0.1", 8000))



def send_global_message(message, type):
    pass

def send_private_message(message, box_coords):
    pass

import autoit
import pydirectinput
import time

time.sleep(2)

autoit.mouse_click("left")


def main():
    while True:

        pydirectinput.keyDown('w')
        time.sleep(5)
        pydirectinput.keyUp('w')


if __name__ == "__main__":
    main()

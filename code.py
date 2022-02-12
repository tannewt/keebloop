import board
import keypad
import json
import busio
import digitalio
from txuart import TXUART
import sofle

import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

from qmk import qmk_to_key_code

keyboard = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

keyboard.release_all()

FLIPPED = False

class FakeEvent:
    def __init__(self, data):
        self.key_number = data[0] & 0x7f
        self.released = (data[0] & 0x80) != 0
        self.pressed = not self.released

with open("sofle_rev1_layout_mine(12).json") as f:
    mapping = json.load(f)

print("loaded keymap {} for {}".format(mapping["keymap"], mapping["keyboard"]))

current_layer = 0

if FLIPPED:
    uart = TXUART(tx=board.RX, baudrate=115200)
else:
    uart = busio.UART(rx=board.RX, baudrate=115200)

s = sofle.Sofle(FLIPPED)
key_number_to_layout_index = bytearray(2 * len(s.columns) * len(s.rows))
for i in range(0, 42):
    key_number_to_layout_index[i] = i
for i in range(42, 53):
    key_number_to_layout_index[i] = i + 2
for i in range(55, 60):
    key_number_to_layout_index[i] = i
key_number_to_layout_index[53] = 42
key_number_to_layout_index[54] = 43

buf = bytearray(1)

mouse_over = digitalio.DigitalInOut(board.SDA)
mouse_over.switch_to_input(pull=digitalio.Pull.UP)
last_mouse = True
while True:
    
    if mouse_over.value != last_mouse:
        key_number = 53
        uart_code = key_number
        if not last_mouse:
            uart_code |= 0x80
        key_event = FakeEvent(bytes([uart_code]))
        last_mouse = not last_mouse
    else:
        key_event = s.get()
        if key_event:
            key_number, key_event = key_event
            if FLIPPED:
                out = key_number
                if key_event.released:
                    out |= 0x80
                buf[0] = out
                uart.write(buf)
        elif uart.in_waiting > 0:
            key_event = FakeEvent(uart.read(1))
            key_number = key_event.key_number

    if not key_event:
        continue
    layout_index = key_number_to_layout_index[key_number]
    qmk_code = mapping["layers"][current_layer][layout_index]

    # Transparent searches down the layers for a keycode.
    i = 1
    while qmk_code == "KC_TRNS" and i <= current_layer:
        layer_below = current_layer - i
        i += 1
        if not mapping["layers"][layer_below]:
            continue
        qmk_code = mapping["layers"][layer_below][layout_index]

    # MO switches layers when pressed down.
    if qmk_code.startswith("MO"):
        if key_event.pressed:
            _, num = qmk_code.split("(")
            current_layer = int(num[:-1])
            print("switched to", current_layer)
        else:
            current_layer = 0
            print("switched to", 0)
    elif qmk_code.startswith("KC_BTN"):
        i = int(qmk_code[-1])
        if key_event.pressed:
            mouse.press(1 << (i - 1))
        else:
            mouse.release(1 << (i - 1)) 
    elif qmk_code.startswith("KC_WH"):
        c = qmk_code[-1]
        if c == "U":
            mouse.move(wheel=10)
        elif c == "D":
            mouse.move(wheel=-10)
    else:
        key_code = qmk_to_key_code(qmk_code)
        if key_code is not None:
            if key_event.pressed:
                try:
                    keyboard.press(key_code)
                except OSError:
                    pass
            else:
                try:
                    keyboard.release(key_code)
                except OSError:
                    pass

import board
import keypad
import time
import storage
import usb_cdc
import usb_midi
import sofle

s = sofle.Sofle(False)

print("press any key to enable drive + cdc")
time.sleep(0.1)

event = s.get()
if event is None:
    storage.disable_usb_drive()
    usb_cdc.disable()
    usb_midi.disable()

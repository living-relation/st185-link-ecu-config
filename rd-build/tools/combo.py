import sys, time
import pyautogui as p
p.FAILSAFE = False
mods = sys.argv[1:-1]
key = sys.argv[-1]
for m in mods:
    p.keyDown(m); time.sleep(0.25)
p.press(key); time.sleep(0.25)
for m in reversed(mods):
    p.keyUp(m); time.sleep(0.15)
print('combo', '+'.join(mods + [key]))

"""Paste clipboard gauge N times at given positions.
Usage: python paste_batch.py "x,y,w,h" "x,y,w,h" ...
Assumes: editor open, source gauge already copied (ctrl+c done).
"""
import sys, time
import pyautogui as p
p.PAUSE = 0.15
p.FAILSAFE = False

def slow_combo(mod, key):
    p.keyDown(mod); time.sleep(0.25)
    p.press(key); time.sleep(0.25)
    p.keyUp(mod); time.sleep(0.4)

def clear_and_type(x, y, val, n=14):
    p.click(x, y); time.sleep(0.3)
    p.press('end')
    for _ in range(n):
        p.press('backspace')
    p.typewrite(str(val), interval=0.02)
    p.press('enter'); time.sleep(0.25)

for arg in sys.argv[1:]:
    x, y, w, h = arg.split(',')
    slow_combo('ctrl', 'v')
    time.sleep(0.8)
    for (fx, fy), v in zip([(681,918),(943,918),(1218,918),(1555,918)], [x, y, w, h]):
        clear_and_type(fx, fy, v)
    print('pasted at', arg)
print('done')

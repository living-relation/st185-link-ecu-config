"""Paste label copies: for each arg "x,y,w,h|TEXT": ctrl+v, position, set text.
Assumes label master already copied to clipboard, editor open.
"""
import sys, time
import pyautogui as p
p.PAUSE = 0.15
p.FAILSAFE = False

def slow_combo(mod, key):
    p.keyDown(mod); time.sleep(0.25)
    p.press(key); time.sleep(0.25)
    p.keyUp(mod); time.sleep(0.4)

def clear_and_type(x, y, val, n=20):
    p.click(x, y); time.sleep(0.3)
    p.press('end')
    for _ in range(n):
        p.press('backspace')
    if val:
        p.typewrite(str(val), interval=0.02)
    p.press('enter'); time.sleep(0.25)

for arg in sys.argv[1:]:
    pos, text = arg.split('|', 1)
    x, y, w, h = pos.split(',')
    slow_combo('ctrl', 'v'); time.sleep(0.8)
    for (fx, fy), v in zip([(681,918),(943,918),(1218,918),(1555,918)], [x, y, w, h]):
        clear_and_type(fx, fy, v, 14)
    # set text via look'n feel
    p.click(688, 100); time.sleep(1.2)
    p.click(171, 632); time.sleep(0.9)
    clear_and_type(883, 214, text)
    p.click(85, 90); time.sleep(0.7)
    p.click(85, 90); time.sleep(0.9)
    print('label', text, 'at', pos)
print('done')

"""Paste value-gauge copies and bind them.
Usage: each arg = "x,y,w,h|search term|warn|crit|dyn"
  warn/crit: '-' to skip. dyn: 'y' to enable dynamic text color (amber/red).
Special first arg 'NOPASTE' = configure currently selected gauge (master) without pasting.
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
    if val:
        p.typewrite(str(val), interval=0.02)
    p.press('enter'); time.sleep(0.25)

args = sys.argv[1:]
for arg in args:
    parts = arg.split('|')
    nopaste = parts[0] == 'NOPASTE'
    if nopaste:
        parts = parts[1:]
        pos = None
        if ',' in parts[0]:
            pos = parts[0]; parts = parts[1:]
    else:
        pos = parts[0]; parts = parts[1:]
    term, warn, crit, dyn = parts[0], parts[1], parts[2], parts[3]

    if not nopaste:
        slow_combo('ctrl', 'v'); time.sleep(0.8)
    if pos:
        x, y, w, h = pos.split(',')
        for (fx, fy), v in zip([(681,918),(943,918),(1218,918),(1555,918)], [x, y, w, h]):
            clear_and_type(fx, fy, v)

    # bind
    p.click(960, 100); time.sleep(1.5)   # INPUT & VALUES
    p.click(528, 357); time.sleep(1.6)   # SELECT DATA SOURCE
    p.click(958, 242); time.sleep(0.4)   # search box
    p.typewrite(term, interval=0.03); time.sleep(1.0)
    p.click(683, 329); time.sleep(0.8)   # first result
    p.click(135, 84); time.sleep(1.2)    # DONE picker
    if warn != '-':
        clear_and_type(1353, 842, warn)
    if crit != '-':
        clear_and_type(1353, 993, crit)
    p.click(135, 84); time.sleep(1.4)    # DONE input&values

    if dyn == 'y':
        p.click(688, 100); time.sleep(1.4)  # LOOK'N FEEL
        p.click(136, 436); time.sleep(1.0)  # COLORS
        p.click(168, 436); time.sleep(0.8)  # TEXT COLOR
        p.click(1102, 86); time.sleep(0.6)  # dynamic toggle
        p.click(709, 216); time.sleep(0.6)  # COLOR 1
        clear_and_type(1020, 985, 'ffc233ff', 12)
        p.click(709, 345); time.sleep(0.6)  # COLOR 2
        clear_and_type(1020, 985, 'ff4d57ff', 12)
        p.click(85, 90); time.sleep(0.8)
        p.click(85, 90); time.sleep(1.0)
    print('value bound:', term)
print('done')

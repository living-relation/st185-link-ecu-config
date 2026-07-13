"""Bind selected gauge to an input and set dynamic background colors.
Usage: python bind_pill.py LIST_Y "search term" COLOR1HEX COLOR2HEX
LIST_Y: y coord of gauge row in left list (click to select). Pass 0 to skip selection.
"""
import sys, time
import pyautogui as p
p.PAUSE = 0.15
p.FAILSAFE = False

LIST_Y = int(sys.argv[1])
TERM = sys.argv[2]
C1 = sys.argv[3]
C2 = sys.argv[4]

def clear_and_type(x, y, val, n=14):
    p.click(x, y); time.sleep(0.35)
    p.press('end')
    for _ in range(n):
        p.press('backspace')
    if val:
        p.typewrite(str(val), interval=0.03)
    p.press('enter'); time.sleep(0.3)

if LIST_Y:
    p.click(150, LIST_Y); time.sleep(0.8)

# bind input
p.click(960, 100); time.sleep(1.5)     # INPUT & VALUES
p.click(528, 357); time.sleep(1.6)     # SELECT DATA SOURCE
p.click(958, 242); time.sleep(0.4)     # search box
p.typewrite(TERM, interval=0.03); time.sleep(1.0)
p.click(683, 329); time.sleep(0.8)     # first result
p.click(135, 84); time.sleep(1.2)      # DONE (picker)
p.click(135, 84); time.sleep(1.4)      # DONE (input&values)

# dynamic background colors
p.click(688, 100); time.sleep(1.4)     # LOOK'N FEEL
p.click(136, 436); time.sleep(1.0)     # COLORS
p.click(237, 240); time.sleep(0.8)     # BACKGROUND COLOR
p.click(1102, 86); time.sleep(0.6)     # USE DYNAMIC COLOR RANGE toggle
p.click(709, 216); time.sleep(0.6)     # COLOR 1
clear_and_type(1020, 985, C1, 12)
p.click(709, 345); time.sleep(0.6)     # COLOR 2
clear_and_type(1020, 985, C2, 12)
p.click(85, 90); time.sleep(0.8)       # back to categories
p.click(85, 90); time.sleep(1.0)       # back to editor
print('bound', TERM, C1, C2)

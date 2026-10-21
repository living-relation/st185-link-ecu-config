"""Add a text gauge and configure position/text/colors in RealDash editor (fullscreen 1920x1080).
Usage: python add_gauge.py X Y W H "text" TEXTHEX BGHEX1 BGHEX2
Use '-' to skip a value. Empty text: use ''
Assumes: edit mode, no dialogs open.
"""
import sys, time
import pyautogui as p
p.PAUSE = 0.15
p.FAILSAFE = False

X, Y, W, H = sys.argv[1:5]
TEXT = sys.argv[5]
TEXTHEX = sys.argv[6] if len(sys.argv) > 6 else '-'
BGHEX1 = sys.argv[7] if len(sys.argv) > 7 else '-'
BGHEX2 = sys.argv[8] if len(sys.argv) > 8 else '-'

def clear_and_type(x, y, val, n=20):
    p.click(x, y); time.sleep(0.3)
    p.press('end')
    for _ in range(n):
        p.press('backspace')
    if val:
        p.typewrite(str(val), interval=0.02)
    p.press('enter'); time.sleep(0.25)

# 1. add text gauge
p.click(417, 100); time.sleep(0.9)
p.click(534, 591); time.sleep(1.6)

# 2. position
for (fx, fy), v in zip([(681,918),(943,918),(1218,918),(1555,918)], [X, Y, W, H]):
    clear_and_type(fx, fy, v, 14)

# 3. text content + static
p.click(688, 100); time.sleep(1.0)      # look'n feel
p.click(171, 632); time.sleep(0.8)      # font & text
clear_and_type(883, 214, TEXT)
p.click(1102, 344); time.sleep(0.4)     # static text ON

# 4. text color
if TEXTHEX != '-':
    p.click(85, 90); time.sleep(0.6)    # back to categories
    p.click(136, 436); time.sleep(0.8)  # colors
    p.click(168, 436); time.sleep(0.6)  # text color tab
    clear_and_type(1020, 985, TEXTHEX, 12)
    in_colors = True
else:
    in_colors = False

# 5. background color(s)
if BGHEX1 != '-':
    if not in_colors:
        p.click(85, 90); time.sleep(0.6)
        p.click(136, 436); time.sleep(0.8)
    p.click(237, 240); time.sleep(0.6)  # background color tab
    p.click(709, 216); time.sleep(0.5)  # COLOR 1
    clear_and_type(1020, 985, BGHEX1, 12)
    if BGHEX2 != '-':
        p.click(709, 345); time.sleep(0.5)  # COLOR 2
        clear_and_type(1020, 985, BGHEX2, 12)
    in_colors = True

# 6. exit look'n feel back to editor
if TEXTHEX != '-' or BGHEX1 != '-':
    p.click(85, 90); time.sleep(0.5)
p.click(85, 90); time.sleep(0.7)
print('gauge added:', X, Y, W, H, TEXT)

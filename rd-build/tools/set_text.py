"""Set text of selected gauge via Look'n Feel > Font & Text. Ends back in editor.
Usage: python set_text.py "TEXT" [TEXTHEX]
"""
import sys, time
import pyautogui as p
p.PAUSE = 0.15
p.FAILSAFE = False
TEXT = sys.argv[1]
HEX = sys.argv[2] if len(sys.argv) > 2 else '-'

def clear_and_type(x, y, val, n=20):
    p.click(x, y); time.sleep(0.35)
    p.press('end')
    for _ in range(n):
        p.press('backspace')
    if val:
        p.typewrite(str(val), interval=0.03)
    p.press('enter'); time.sleep(0.3)

p.click(688, 100); time.sleep(1.3)   # LOOK'N FEEL
p.click(171, 632); time.sleep(1.0)   # FONT & TEXT
clear_and_type(883, 214, TEXT)
if HEX != '-':
    p.click(85, 90); time.sleep(0.8)     # back to categories
    p.click(136, 436); time.sleep(0.9)   # COLORS
    p.click(168, 436); time.sleep(0.7)   # TEXT COLOR
    clear_and_type(1020, 985, HEX, 12)
p.click(85, 90); time.sleep(0.8)
p.click(85, 90); time.sleep(1.0)
print('text set:', TEXT)

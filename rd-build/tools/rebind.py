"""Rebind gauges to ST185 inputs. Args: "rowY|search term" (row 0 = keep selection).
Optionally first arg 'SCROLLTOP' scrolls gauge list to top.
"""
import sys, time
import pyautogui as p
p.PAUSE = 0.15
p.FAILSAFE = False

args = sys.argv[1:]
if args and args[0] in ('SCROLLTOP', 'SCROLLBOT'):
    amt = 600 if args[0] == 'SCROLLTOP' else -600
    args = args[1:]
    p.moveTo(200, 500)
    for _ in range(10):
        p.scroll(amt, x=200, y=500); time.sleep(0.15)
    time.sleep(0.5)

for arg in args:
    row, term = arg.split('|', 1)
    if int(row):
        p.click(150, int(row)); time.sleep(0.8)
    p.click(960, 100); time.sleep(1.5)   # INPUT & VALUES
    p.click(528, 357); time.sleep(1.6)   # SELECT DATA SOURCE
    p.click(958, 242); time.sleep(0.4)
    p.typewrite(term, interval=0.03); time.sleep(1.0)
    p.click(683, 329); time.sleep(0.8)   # first result
    p.click(135, 84); time.sleep(1.2)    # DONE picker
    p.click(135, 84); time.sleep(1.4)    # DONE input&values
    print('rebound', term)
print('done')

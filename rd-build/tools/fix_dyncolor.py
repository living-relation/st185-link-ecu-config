"""For each list-row Y given: select gauge, set TEXT COLOR COLOR1 to white f3f8ffff."""
import sys, time
import pyautogui as p
p.PAUSE = 0.15
p.FAILSAFE = False

def clear_and_type(x, y, val, n=12):
    p.click(x, y); time.sleep(0.3)
    p.press('end')
    for _ in range(n):
        p.press('backspace')
    p.typewrite(str(val), interval=0.03)
    p.press('enter'); time.sleep(0.3)

for row in sys.argv[1:]:
    p.click(150, int(row)); time.sleep(0.8)
    p.click(688, 100); time.sleep(1.3)   # LOOK'N FEEL
    p.click(136, 436); time.sleep(0.9)   # COLORS
    p.click(168, 436); time.sleep(0.7)   # TEXT COLOR
    p.click(709, 216); time.sleep(0.6)   # COLOR 1
    clear_and_type(1020, 985, 'f3f8ffff')
    p.click(85, 90); time.sleep(0.7)
    p.click(85, 90); time.sleep(1.0)
    print('fixed row', row)
print('done')

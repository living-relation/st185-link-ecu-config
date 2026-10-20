import sys, time
import pyautogui as p
p.PAUSE = 0.12
p.FAILSAFE = False
FIELDS = [(681, 918), (943, 918), (1218, 918), (1555, 918)]
vals = sys.argv[1:5]
for (x, y), v in zip(FIELDS, vals):
    if v == '-':
        continue
    p.click(x, y)
    time.sleep(0.25)
    p.press('end')
    for _ in range(14):
        p.press('backspace')
    p.typewrite(str(v), interval=0.03)
    p.press('enter')
    time.sleep(0.25)
print('set', vals)

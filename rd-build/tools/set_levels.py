"""Set warning/critical levels: args "rowY|warn|crit" """
import sys, time
import pyautogui as p
p.PAUSE = 0.15
p.FAILSAFE = False

def clear_and_type(x, y, val, n=14):
    p.click(x, y); time.sleep(0.3)
    p.press('end')
    for _ in range(n):
        p.press('backspace')
    p.typewrite(str(val), interval=0.03)
    p.press('enter'); time.sleep(0.3)

for arg in sys.argv[1:]:
    row, warn, crit = arg.split('|')
    p.click(150, int(row)); time.sleep(0.8)
    p.click(960, 100); time.sleep(1.5)   # INPUT & VALUES
    clear_and_type(1353, 842, warn)
    clear_and_type(1353, 993, crit)
    p.click(135, 84); time.sleep(1.3)    # DONE
    print('levels', row, warn, crit)
print('done')

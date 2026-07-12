#!/usr/bin/env python3
"""
automation_helper.py - tiny cross-platform desktop-automation CLI for driving the
RealDash editor from a local Cursor agent (screenshot -> decide -> click/type -> verify).

It wraps PyAutoGUI so a Cursor agent can control the GUI purely through terminal
commands + reading screenshot files. No MCP server or remote-desktop connector needed
when the agent runs on the same PC as RealDash.

Install:  pip install -r requirements.txt
          (macOS: grant Accessibility + Screen Recording to your terminal/Cursor;
           Linux: also `sudo apt install scrot python3-tk python3-dev`.)

Usage:
  python automation_helper.py size
  python automation_helper.py screenshot [path]        # default: ./rd_screen.png
  python automation_helper.py screenshot region X Y W H [path]
  python automation_helper.py move X Y
  python automation_helper.py click X Y [left|right|middle] [clicks]
  python automation_helper.py doubleclick X Y
  python automation_helper.py rightclick X Y
  python automation_helper.py dragto X Y [DURATION]
  python automation_helper.py scroll AMOUNT [X Y]       # +up / -down
  python automation_helper.py type "text" [INTERVAL]
  python automation_helper.py key NAME                  # enter, tab, esc, backspace, ...
  python automation_helper.py hotkey A B [C ...]        # e.g. ctrl s
  python automation_helper.py pixel X Y                 # prints RGB at X,Y
  python automation_helper.py moverel DX DY

Notes:
  - Coordinates are absolute screen pixels. Recompute from a fresh screenshot on each
    machine/resolution; do not reuse coordinates across machines.
  - A short pause is applied after each action so the UI can settle.
"""
import sys

try:
    import pyautogui
except Exception as e:  # pragma: no cover
    sys.stderr.write(
        "ERROR: PyAutoGUI is not installed or failed to import: %s\n"
        "Install it with:  pip install -r requirements.txt\n"
        "Linux also needs:  sudo apt install scrot python3-tk python3-dev\n" % e
    )
    sys.exit(2)

pyautogui.FAILSAFE = False   # do not abort if cursor hits a screen corner
pyautogui.PAUSE = 0.25       # settle time after each action


def _i(v):
    return int(round(float(v)))


def main(argv):
    if not argv:
        sys.stderr.write("No command. See --help / the docstring at the top of this file.\n")
        return 2
    cmd = argv[0].lower()
    a = argv[1:]

    if cmd in ("-h", "--help", "help"):
        print(__doc__)
        return 0

    if cmd == "size":
        w, h = pyautogui.size()
        print("%d %d" % (w, h))
        return 0

    if cmd == "screenshot":
        region = None
        path = "rd_screen.png"
        if a and a[0] == "region":
            region = (_i(a[1]), _i(a[2]), _i(a[3]), _i(a[4]))
            if len(a) > 5:
                path = a[5]
        elif a:
            path = a[0]
        img = pyautogui.screenshot(region=region) if region else pyautogui.screenshot()
        img.save(path)
        print("saved %s (%dx%d)" % (path, img.width, img.height))
        return 0

    if cmd == "move":
        pyautogui.moveTo(_i(a[0]), _i(a[1]))
        print("moved to %s,%s" % (a[0], a[1]))
        return 0

    if cmd == "moverel":
        pyautogui.moveRel(_i(a[0]), _i(a[1]))
        print("moved rel %s,%s" % (a[0], a[1]))
        return 0

    if cmd in ("click", "doubleclick", "rightclick"):
        x, y = _i(a[0]), _i(a[1])
        if cmd == "doubleclick":
            pyautogui.doubleClick(x, y)
        elif cmd == "rightclick":
            pyautogui.click(x, y, button="right")
        else:
            button = a[2] if len(a) > 2 else "left"
            clicks = int(a[3]) if len(a) > 3 else 1
            pyautogui.click(x, y, clicks=clicks, button=button)
        print("%s at %d,%d" % (cmd, x, y))
        return 0

    if cmd == "dragto":
        dur = float(a[2]) if len(a) > 2 else 0.4
        pyautogui.dragTo(_i(a[0]), _i(a[1]), duration=dur, button="left")
        print("dragged to %s,%s" % (a[0], a[1]))
        return 0

    if cmd == "scroll":
        amount = _i(a[0])
        if len(a) >= 3:
            pyautogui.scroll(amount, x=_i(a[1]), y=_i(a[2]))
        else:
            pyautogui.scroll(amount)
        print("scrolled %d" % amount)
        return 0

    if cmd == "type":
        text = a[0] if a else ""
        interval = float(a[1]) if len(a) > 1 else 0.02
        pyautogui.typewrite(text, interval=interval)
        print("typed %d chars" % len(text))
        return 0

    if cmd == "key":
        pyautogui.press(a[0])
        print("pressed %s" % a[0])
        return 0

    if cmd == "hotkey":
        pyautogui.hotkey(*a)
        print("hotkey %s" % "+".join(a))
        return 0

    if cmd == "pixel":
        x, y = _i(a[0]), _i(a[1])
        px = pyautogui.pixel(x, y)
        print("pixel %d,%d = rgb%s" % (x, y, tuple(px)))
        return 0

    sys.stderr.write("Unknown command: %s\n" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

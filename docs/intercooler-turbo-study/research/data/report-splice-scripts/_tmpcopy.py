import os, shutil
src = r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions\1cec9723-b110-46f1-9694-4a2692e2397f\a8dc0527-c42c-4163-8eb6-e49e1c4c8497\local_e957a84a-65a7-425d-93d0-0e485ed7f050\outputs"
dst = r"C:\projects\5sgte-intercooler-research\data"
os.makedirs(dst, exist_ok=True)
n = 0
for f in os.listdir(src):
    p = os.path.join(src, f)
    if os.path.isfile(p) and f not in ("package-lock.json",):
        shutil.copy2(p, os.path.join(dst, f))
        n += 1
print("copied", n)
print(sorted(os.listdir(dst)))

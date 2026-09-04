import glob, os, fitz

SRC = r"C:\Users\danie\.personal OneDrive\OneDrive\Desktop\Celica\Parts Invoices"
OUT = r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions\1cec9723-b110-46f1-9694-4a2692e2397f\a8dc0527-c42c-4163-8eb6-e49e1c4c8497\local_e957a84a-65a7-425d-93d0-0e485ed7f050\outputs"

files = sorted(glob.glob(os.path.join(SRC, "*.pdf")))
key = ["TurboKits","STM Tuned","ExtremePSI","MonkeyFab","TurboSmart","RaceTronix",
       "KO Racing","GT4 Racing","GT4 Play","Rat2","PrimeMR2","Revline","MA Motorsports",
       "Speeding","Lowdoller","Hux","Toyota N Miami","TwosRUS","TBD","Summit","Ballenger",
       "Chase Bays","MTEC","AeroFlow","AN Hose","Colc Hose","RockAuto"]
sel = [f for f in files if any(os.path.basename(f).startswith(k) for k in key)]

pages = []  # (file, pageindex)
for f in sel:
    d = fitz.open(f)
    n = min(d.page_count, 2)
    for i in range(n):
        pages.append((f, i))
    d.close()

print("selected files:", len(sel), "pages:", len(pages))

BATCH = 16
manifest = []
for b in range(0, len(pages), BATCH):
    chunk = pages[b:b+BATCH]
    doc = fitz.open()
    for f, i in chunk:
        s = fitz.open(f)
        doc.insert_pdf(s, from_page=i, to_page=i)
        s.close()
    p = os.path.join(OUT, f"invbatch_{b//BATCH:02d}.pdf")
    doc.save(p)
    doc.close()
    manifest.append((p, [(os.path.basename(f), i) for f, i in chunk]))

for p, c in manifest:
    print(p)
    for j, (n, i) in enumerate(c):
        print("   page", j+1, "=", n, "p", i+1)

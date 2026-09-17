import glob, os, subprocess, tempfile, fitz

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if not os.path.exists(TESS):
    for c in [r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
              os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")]:
        if os.path.exists(c):
            TESS = c
            break
print("tesseract:", TESS, os.path.exists(TESS))

SRC = r"C:\Users\danie\.personal OneDrive\OneDrive\Desktop\Celica\Parts Invoices"
OUT = r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions\1cec9723-b110-46f1-9694-4a2692e2397f\a8dc0527-c42c-4163-8eb6-e49e1c4c8497\local_e957a84a-65a7-425d-93d0-0e485ed7f050\outputs"
tmp = tempfile.mkdtemp()

files = sorted(glob.glob(os.path.join(SRC, "*.pdf")))
res = []
for f in files:
    d = fitz.open(f)
    txt = []
    for i in range(min(d.page_count, 3)):
        pg = d.load_page(i)
        pix = pg.get_pixmap(dpi=200)
        png = os.path.join(tmp, "p.png")
        pix.save(png)
        base = os.path.join(tmp, "o")
        try:
            subprocess.run([TESS, png, base, "-l", "eng", "--psm", "6"],
                           capture_output=True, timeout=120)
            with open(base + ".txt", "r", encoding="utf-8", errors="ignore") as fh:
                txt.append(fh.read())
        except Exception as e:
            txt.append("OCR_ERR " + str(e))
    d.close()
    res.append((os.path.basename(f), "\n".join(txt)))
    print("done", os.path.basename(f), len(res[-1][1]))

with open(os.path.join(OUT, "invoices_ocr.txt"), "w", encoding="utf-8") as fh:
    for n, t in res:
        fh.write("\n\n========== " + n + " ==========\n" + t)
print("WROTE", os.path.join(OUT, "invoices_ocr.txt"))

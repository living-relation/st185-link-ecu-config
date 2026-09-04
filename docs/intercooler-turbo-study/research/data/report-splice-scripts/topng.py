import glob, os, sys
os.chdir(r"C:\projects\5sgte-intercooler-research\data")
try:
    import cairosvg
except ImportError:
    print("cairosvg unavailable:", sys.exc_info()[1]); raise SystemExit(1)
n = 0
for f in sorted(glob.glob("r2_*.svg")):
    cairosvg.svg2png(url=f, write_to=f[:-4] + ".png", scale=1.5,
                     background_color="#1a2029")
    n += 1
    print("rendered", f)
print("total", n)

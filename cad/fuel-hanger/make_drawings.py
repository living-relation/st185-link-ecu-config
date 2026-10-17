"""Rev H shop drawings for the ST185 billet fuel hanger (stevecad-tools drawing engine, read-only use)."""
import os, sys
TK = "/home/daniel/projects/stevecad-tools"
for d in ("drawing", "render", "checks"): sys.path.insert(0, os.path.join(TK, d))
W = os.environ.get("FH_DWG_WORK", os.getcwd()); os.chdir(W); os.makedirs("previews", exist_ok=True); os.makedirs("out", exist_ok=True)
import part
TODAY = "2026-10-17"; J = "src/fuel-hanger/"
REVS = [("H", "LUG MADE INTEGRAL (N6)", TODAY, "SC")]
GEN = ["6061-T6 BILLET. MODEL build123d fuel_hanger.py REV H.",
       "EDGES NOT MODELLED (R138): BREAK SHARP EDGES 0.2-0.4; SEAL FACE / SPOT RIMS 0.3 MAX.",
       "SPOT TAPPED ENTRIES 90°, ⌀ = THREAD MAJOR."]
SRC = "st185-link-ecu-config\\cad\\fuel-hanger\\"
def P(f, pn, title, threads, notes, **kw):
    return dict(job="fuel-hanger", file=J + f, process="machined", title=title, pn=pn, material="6061-T6 ALUMINUM",
                source=SRC + f, hidden=True, threads=threads, rev="H", revs=REVS, notes=GEN + notes, **kw)
PARTS = {
 "flange": P("fuel-hanger-flange.step", "ST185-FH-101", "FUEL HANGER - FLANGE (INTEGRAL LUG)", {},
   ["ONE BILLET: FLANGE + LUG (REPLACES REV G FH-101 + FH-102). NO M5 SCREWS, NO DOWELS. 13 THRU-HOLES ONLY; NOTHING ELSE BREAKS THE SEALING FACE.",
    "SPOT FACES Ra 1.6 FLAT. UPRIGHT-TO-BASE R3. OPS: TANK FACE, OUTSIDE FACE, SIDE (⌀6.6)."],
   hole_text={("Z", 5.8): "2X ⌀5.79 THRU (STUD)\n⌴⌀16 ↧0.4 BOTH SIDES",
              ("Z", 14.7): "⌀14.68 THRU (-6 AN)\n⌴⌀24 ↧0.4 BOTH SIDES",
              ("Z", 19.4): "⌀19.45 THRU (-8 AN)\n⌴⌀30 ↧0.4 BOTH SIDES",
              ("Z", 5.5): "9X ⌀5.5 THRU\n⌴⌀12 ↧2.8 OUTSIDE (RIM 5.0)"}),
 "strut": P("fuel-hanger-strut.step", "ST185-FH-103", "FUEL HANGER - STRUT", {4.2: ("M5x0.8", 0.8)},
   ["STRUT POCKETS: FLOOR-TO-WALL EDGES ARE END-MILL FLOOR EDGES - SQUARE CUTTER CORNER OK.", "FIT THE BULKHEAD NUTS BEFORE THE STRUT."]),
 "foot": P("fuel-hanger-foot.step", "ST185-FH-104", "FUEL HANGER - FOOT", {3.3: ("M4x0.7", 0.7)}, []),
 "saddle": P("fuel-hanger-saddle1.step", "ST185-FH-105", "FUEL HANGER - PUMP SADDLE", {4.2: ("M5x0.8", 0.8)}, []),
}
name = sys.argv[1]; sp = PARTS[name]
s = part.make_part(sp, f"out/{sp['pn']}.pdf", f"out/{sp['pn']}.dxf", f"previews/{sp['pn']}")
print("OK", name, s)

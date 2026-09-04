"""
End tank manufacturing comparison. Numbers, not opinions.
Question on the table: should Dan machine billet end tanks at work, or buy an
off-the-shelf assembled intercooler?
"""
import math, json

# tank envelope needed for a 610 x 305 x 76 core, side inlet / side outlet
H, T, DEPTH = 305.0, 76.0, 110.0   # mm - tank height, core thickness, tank depth
WALL = 4.0                          # mm wall for billet and cast
WALL_FAB = 2.0                      # mm 5052 sheet
RHO_AL = 2.70e-3                    # g/mm3
CP_AL  = 900.0                      # J/kg/K

# --- surface area of one tapered tank, approximated as a wedge
def tank_area_mm2(h, t, d):
    return 2*(0.5*(t+t*0.4)*d) + h*d*2*0.5 + h*t + math.sqrt(d*d+h*h/4)*t*1.2

A = tank_area_mm2(H, T, DEPTH)

def mass_shell(area_mm2, wall_mm):
    return area_mm2*wall_mm*RHO_AL/1000.0   # kg

m_fab    = mass_shell(A, WALL_FAB)
m_cast   = mass_shell(A, WALL)
m_billet = mass_shell(A, WALL)*1.15         # billet tanks end up thicker at corners

# --- billet: stock block and machining
BLOCK = (H+15, DEPTH+20, T+14)              # mm blank, allowing for fixturing
block_vol_cm3 = BLOCK[0]*BLOCK[1]*BLOCK[2]/1000.0
block_kg  = block_vol_cm3*2.70/1000.0
block_lb  = block_kg*2.20462
PLATE_USD_PER_LB = 7.50                     # 6061-T651 plate, small quantity, 2026
stock_cost_each = block_lb*PLATE_USD_PER_LB

removed_cm3 = block_vol_cm3 - (m_billet/2.70*1000.0)
MRR_ROUGH   = 160.0                         # cm3/min, 16 mm 3-flute in 6061 on a rigid VMC
rough_min   = removed_cm3/MRR_ROUGH
FINISH_RATE = 0.20   # min per cm2. 12 mm cutter, 1 mm stepover, 3000 mm/min feed
                     # sweeps about 5 cm2/min in 6061. Conservative but not silly.
finish_min  = A/100.0*FINISH_RATE           # min per cm2 of finished surface
setups      = 3                             # 3 sides, re-fixture each time
setup_min   = setups*25
cam_min     = 150                           # CAM programming, one time for the pair
tool_min    = 20

mach_min_each = rough_min + finish_min + setup_min + tool_min
total_mach_h  = (2*mach_min_each + cam_min)/60.0

print("="*84)
print("BILLET END TANKS - WHAT IT ACTUALLY COSTS")
print("="*84)
print(f"  Tank envelope                 {H:.0f} x {T:.0f} x {DEPTH:.0f} mm")
print(f"  Wetted surface, one tank      {A/100:.0f} cm2")
print(f"  Blank required, one tank      {BLOCK[0]:.0f} x {BLOCK[1]:.0f} x {BLOCK[2]:.0f} mm")
print(f"  Blank mass                    {block_kg:.2f} kg  ({block_lb:.1f} lb)")
print(f"  6061-T651 plate at ${PLATE_USD_PER_LB:.2f}/lb   ${stock_cost_each:.0f} each, ${2*stock_cost_each:.0f} the pair")
print(f"  Material removed              {removed_cm3:.0f} cm3 per tank ({removed_cm3/block_vol_cm3*100:.0f}% of the blank)")
print()
print("  Machining time, one tank")
print(f"    roughing at {MRR_ROUGH:.0f} cm3/min      {rough_min:5.0f} min")
print(f"    finishing                    {finish_min:5.0f} min")
print(f"    {setups} setups / re-fixturing     {setup_min:5.0f} min")
print(f"    tool changes, probing        {tool_min:5.0f} min")
print(f"    subtotal per tank            {mach_min_each:5.0f} min  ({mach_min_each/60:.1f} h)")
print(f"  CAM programming, one time      {cam_min:5.0f} min  ({cam_min/60:.1f} h)")
print(f"  TOTAL for the pair             {total_mach_h:5.1f} machine-hours")
print(f"  Plus TIG welding ports and the core joint: 2-3 h of skilled fab time.")
print()

print("="*84)
print("WEIGHT AND THERMAL MASS, THE PAIR")
print("="*84)
print("  method                     wall mm   mass kg   heat capacity J/K   soak penalty")
base_J = 2*m_fab*CP_AL
for lab, m, w in [("fabricated 5052 sheet", m_fab, WALL_FAB),
                  ("stamped aluminium",     m_fab*1.10, 2.2),
                  ("cast aluminium",        m_cast, WALL),
                  ("CNC billet 6061",       m_billet, WALL)]:
    J = 2*m*CP_AL
    print("  %-25s  %4.1f     %5.2f      %8.0f            %+.0f%%"
          % (lab, w, 2*m, J, (J/base_J-1)*100))
print()
print("  Heat soak matters at the end tanks because they sit in the hot charge stream.")
print("  Every extra joule of aluminium there is a joule that has to be reheated on")
print("  every pull and dumped between pulls. Billet doubles the tank heat capacity.")
print()

print("="*84)
print("RANKING - flow distribution, pressure drop, cost")
print("="*84)
rank = [
 # method, flow distribution 1-5, dP 1-5, cost per pair USD, internal vanes possible, notes
 ("Stamped",          3.0, 3.5, 120,  "no",
  "One-piece, welded to core. Strong. Shape is whatever the die makes; no tuning."),
 ("Fabricated sheet", 3.5, 4.0, 180,  "bolt-in only",
  "Cut and TIG-welded 5052. Flat panels, so smooth internal shaping is hard."),
 ("Cast aluminium",   5.0, 5.0, 260,  "yes, cast in",
  "Diverters and a curved floor come free in the mould. Best flow. Needs tooling."),
 ("CNC billet 6061",  4.5, 4.5, 1150, "yes, machined in",
  "Can do everything cast can, one-off, but heavier and far more labour."),
]
print("  method             flow dist  dP score  cost/pair  internal vanes")
for m,f,d,c,v,note in rank:
    print("  %-18s   %.1f/5      %.1f/5     $%-8d %s" % (m,f,d,c,v))
    print("      %s" % note)
print()
print("  Cost of the billet pair is stock ($%.0f) + %.0f machine-hours." % (2*stock_cost_each, total_mach_h))
print("  Even at zero labour rate, that is %.0f hours of machine time Dan could spend on" % total_mach_h)
print("  the ducting, which the round-one model says is worth about 27 C.")

json.dump({"area_cm2":round(A/100),"block_kg":round(block_kg,2),
           "stock_pair_usd":round(2*stock_cost_each),
           "machine_hours":round(total_mach_h,1),
           "mass_fab_kg":round(2*m_fab,2),"mass_cast_kg":round(2*m_cast,2),
           "mass_billet_kg":round(2*m_billet,2),
           "J_fab":round(2*m_fab*CP_AL),"J_billet":round(2*m_billet*CP_AL)},
          open(r"C:\projects\5sgte-intercooler-research\data\endtank.json","w"), indent=1)
print("\nwrote data/endtank.json")

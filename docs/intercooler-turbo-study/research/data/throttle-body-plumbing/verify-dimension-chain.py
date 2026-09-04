import math
# independent re-derivation, different route, to check the spec numbers
IN=25.4
print("--- unit checks ---")
for w in (0.049,0.065,0.083):
    idin=3.0-2*w
    print(f"  wall {w}: ID {idin:.4f} in -> {idin*IN:.3f} mm ; step to 74.5 = {74.5-idin*IN:+.3f} mm")
print(f"  74.5 mm -> {74.5/IN:.4f} in ; 3.000 in -> {3.0*IN:.2f} mm")
print("--- area error OD vs ID ---")
print(f"  3.00/.065: {(76.2**2/72.898**2-1)*100:.2f}%  2.50/.065: {(63.5**2/60.198**2-1)*100:.2f}%")
print("--- velocity by continuity, cross-check ---")
mdot=45.7*0.45359237/60
rc=266000/(287.05*335.15); rh=274000/(287.05*453.15)
for d,lab in ((60.198,'2.5/.065'),(73.711,'3.0/.049'),(72.898,'3.0/.065'),(71.984,'3.0/.083')):
    A=math.pi*(d/2000)**2
    print(f"  {lab}: A={A*1e4:.3f} cm2 hot={mdot/rh/A*3.28084:.1f} cold={mdot/rc/A*3.28084:.1f} ft/s")
print("--- Borda-Carnot at the plate step, cold side ---")
for d in (73.711,72.898,71.984):
    A=math.pi*(d/2000)**2; v=mdot/rc/A
    print(f"  ID {d:.3f}: dP={0.5*rc*v*v*(1-(d/74.5)**2)**2/6894.757:.6f} psi")
print("--- dP saving 2.5 -> 3.0 ---")
print("  0.888 - 0.394 = %.3f psi" % (0.888-0.394))
print("--- extra volume, cold side 1.5 m ---")
print("  (4.174-2.846)*1.5 = %.2f L" % ((4.174-2.846)*1.5))
print("--- bend radius R/D>=1.5 ---")
print("  2.5 in: %.0f mm ; 3.0 in: %.0f mm" % (2.5*IN*1.5, 3.0*IN*1.5))

"""Factory (OEM) ends of the A-cabin wires: where the tap physically is, the EWD / locator
reference, the factory wire colour and the method (Dan 2026-10-19: OEM ends keep their notes).

Sources: interfaces.json flyingLeads (EWD page, pin, colour, method), docs/harness/ACAMP-SPUR-LABELS.md,
the 1990 ST185 EWD p.17 Instrument Panel locator (docs/electrical/ewd-snips/1990-st185-locations-dash.png),
docs/research/AUTO-AC-AMP-OPTIONS.html (Mitchell locations; "in the 1990 book the same compressor amp
is called A18"), and the old drawing's end notes (`old`, kept word for word). Nothing here is
guessed: an unknown is written TBD.
"""
A18_WHERE = ("A/C amplifier A18 (1993 book: A15), passenger side behind the glove box, on the bottom "
             "of the evaporator housing; tap point on the lead at the amplifier, distance TBD")
A18_REF = ("locator 1990 ST185 EWD p.17 Instrument Panel (ewd-snips/1990-st185-locations-dash.png); "
           "Mitchell locations (docs/research/AUTO-AC-AMP-OPTIONS.html)")

# key: the A-cabin end id. short = the plain note drawn next to that end in the .harness file.
OEM_ENDS = {
    "fl_acamp_act": dict(
        where=A18_WHERE, ref="1992 EWD132U p.93 and p.218 (A17-11 = A18-11); " + A18_REF,
        old="OEM A/C amplifier, G-Y lead, by the ECU; (EWD 1992 p.93)",
        short="A/C amp A18 pin 11 (1993: A15), behind the glove box. Solder splice onto the factory "
              "G-Y lead. EWD 1992 p.93 / p.218; locator 1990 p.17."),
    "fl_acamp_psw": dict(
        where=A18_WHERE, ref="1990 ST185 EWD p.152; 1992 EWD132U p.219 (A17-13); " + A18_REF,
        old="OEM A/C amplifier, Y-R lead, by the ECU; (EWD 1990 p.152)",
        short="A/C amp A18 pin 13 (1993: A15), behind the glove box. Solder splice onto the factory "
              "Y-R lead. EWD 1990 p.152; locator 1990 p.17."),
    "fl_acamp_mg": dict(
        where=A18_WHERE, ref="1990 ST185 EWD p.152; 1992 EWD132U p.218 (A17-5); " + A18_REF,
        old="OEM A/C amplifier, Y-B lead, by the ECU; (EWD 1990 p.152)",
        short="A/C amp A18 pin 5 (1993: A15), behind the glove box. Solder splice onto the factory "
              "Y-B lead (VC coil, not fitted). EWD 1990 p.152; locator 1990 p.17."),
    "br_ac_psw": dict(
        where="A/C pressure switch A5, engine bay; exact spot TBD (no locator figure in the repo)",
        ref="1990 ST185 EWD p.152 (A5 pin 4 Y-R)",
        old="OEM A/C pressure switch, engine bay; (EWD 1990 p.152)",
        short="Runs on in ST185-EngineRoom-C to A/C pressure switch A5 pin 4 (engine bay): new wire "
              "to the switch's own mating plug, plug part TBD. EWD 1990 p.152."),
    "br_ac_mg": dict(
        where="A/C compressor A4, engine bay; exact spot TBD (no locator figure in the repo)",
        ref="1990 ST185 EWD p.152 (A4 pin 3 Y-B)",
        old="OEM A/C compressor, engine bay; (EWD 1990 p.152)",
        short="Runs on in ST185-EngineRoom-C to A/C compressor A4 pin 3 (engine bay): new wire to "
              "the coil's own mating plug, plug part TBD. EWD 1990 p.152."),
}

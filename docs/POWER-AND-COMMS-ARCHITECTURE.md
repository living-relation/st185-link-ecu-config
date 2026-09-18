# ST185 Power and Comms Architecture

**Vehicle:** 1993 Celica GT-Four ST185 (AllTrac), full race buildout. OEM display removed.

**Status:** Sealed from Daniel 2026-09-18 (Grim Council). Feature-branch parchment - not yet merged to main.

## Power

- **Trunk battery** with **main battery kill** and **fusible link** at the battery.
- **RADLOKs** carry battery positive and negative into the engine bay for **starter** and **alternator**.
- **Jump-start lugs** near the firewall.
- **Fuse and relay box** in the passenger-side glove-box area.
- **PDU** next to the fuse box in the cabin.

## CAN 1 (only CAN in use)

Devices on **CAN 1** (CAN 2 unused):

- Custom **3-cluster** dashboard
- Auxiliary **RealDash** (Pi + 7 inch screen)
- Link **CAN-Lambda**
- **ECUMaster CSB** (overflow inputs that do not fit on the ECU)
- **PDU / PDM**

The ECU **CAN 1 comms cable** also carries **12V** and **GND out** to power the new displays and the ECUMaster CSB.

## Reverse camera / gear display

1. OEM **reverse switch** into the ECU.
2. ECU sets **Gear = 7** on CAN.
3. Cluster shows **R**.
4. RealDash switches to the **USB reverse camera** view.

## Related living SoT

- ECU IO / colours: XTREMEX-IO-TABLE.html
- Wiring audit: docs/WIRING-AUDIT-2026-09-18.md
- VSS car-side (Path B): gearbox 3-wire 12V Toyota VSS on generic oval 3-pin sockets (PN TBD); Quill faces IGN / GND / SP1 with SP1 to B29 - cavity order still open.

## Still TBD

- Fuel sender divider ohms
- VSS oval cavity order (IGN / GND / SP1 assignment)
- Main merge until Daniel verifies feature branch pass-a-bh-c-delete-locks

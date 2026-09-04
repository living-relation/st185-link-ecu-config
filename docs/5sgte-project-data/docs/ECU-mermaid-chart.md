```mermaid
graph LR
    ECU["Link G4X XtremeX ECU"]

    subgraph DI["Digital Inputs DI1-10"]
        DI1["DI1 Flex-Fuel Sensor"]
        DI2["DI2 Clutch Switch"]
        DI3["DI3 Brake Switch"]
        DI4["DI4 Reverse Switch NEW - drives Gear Pos=7"]
        DI5["DI5 Turbo Speed Sensor NEW - BorgWarner 179430"]
        DI6["DI6-DI10 spare"]
    end

    subgraph ANALOG["Analog Volt and Temp Inputs"]
        AV1["MAP Sensor"]
        AV2["TPS cable throttle"]
        AV3["Oil Pressure"]
        AV4["Fuel Pressure"]
        AV5["Coolant Pressure"]
        T1["ECT"]
        T2["IAT"]
        T3["Oil Temp"]
    end

    subgraph TRIG["Triggers and Knock"]
        TR1["Trigger1 Crank Ne - BEAMS sprocket"]
        TR2["Trigger2 Cam Home G"]
        KN1["Knock Sensor"]
    end

    subgraph OUT["Outputs"]
        IGN["Ignition 1-4 COP coils"]
        INJ["Injection 1-4 ATS 1400cc"]
        AUX1["Aux1 MAC boost solenoid to Turbosmart GenV wastegate actuator"]
        AUX2["Aux2-4 idle ISC and fuel pump"]
    end

    subgraph CANBUS["Shared 1 Mbit/s CAN Bus - 4 nodes"]
        CENTER["center-cluster-esp32-p4 gauge cluster"]
        SWB["ECUMaster CAN Switch Board V3 - cruise stalk, cabin temp, AC, fans"]
        PI["Pi5 RealDash - listen only - reverse camera page NEW"]
        LAMBDA["External Link CAN-Lambda module"]
    end

    DI --> ECU
    ANALOG --> ECU
    TRIG --> ECU
    ECU --> OUT
    ECU <--> CANBUS
    CENTER <--> SWB
    SWB <--> PI
```

> Note (added when copied into the repo, 2026-09-04): this diagram still shows the DI4/DI5
> reverse-switch and turbo-speed-sensor placement from the 2026-08-19 decision, which the
> `ECU-wiring-design` branch's `DOCS-CLEANUP-PLAN.md` has since superseded (reverse switch is
> now switchboard-routed, not DI4; DI4 itself is committed to ABS wheel speed). See
> `REVERSE-CAMERA-TRIGGER-RESOLUTION.md` in this folder for the current answer. Kept as-is for
> history — not redrawn here.

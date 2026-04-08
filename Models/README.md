# Models

This folder contains all SolidWorks part files (`.SLDPRT`), assemblies (`.SLDASM`), and exported print files (`.gcode`) for the SpiRob hardware system.

> **Note:** `~$*.SLDPRT` and `~$*.SLDASM` files are SolidWorks auto-save locks — they are excluded by `.gitignore` and should not be committed.

---

## Bill of Materials — 3D Printed Parts

| File | Description | Material | Est. Print Time |
|---|---|---|---|
| `BasePart.SLDPRT` | Original base frame | PLA | ~2 h |
| `BasePart_ArduinoHolders.SLDPRT` | Base with integrated Arduino mounting pegs | PLA | ~2.5 h |
| `05202025_BASEUPDATED.SLDPRT` | Updated base (May 20, 2025) — wider footprint for stability | PLA | ~3 h |
| `Base For SpiRob (5-22-25).SLDPRT` | Base revision (May 22, 2025) | PLA | ~3 h |
| `28byj-48-holder_longer base.SLDPRT` | Motor mount with extended base to reduce tipping | PLA | ~1.5 h |
| `28byj-48_Spool_v1.SLDPRT` | Spool v1 for 28BYJ-48 motor shaft — wraps fishing wire | PLA | ~45 min |
| `Data SpiRobs/2-cable SpiRob.SLDPRT` | Two-cable SpiRob body (logarithmic spiral) | TPU-70A | ~12 h |
| `Data SpiRobs/SpiRob Assembly.SLDASM` | Full assembly: SpiRob + base + motor mounts + spools | — | — |

### Exported G-code

| File | Description |
|---|---|
| `Data SpiRobs/SS_2-cable SpiRob.gcode` | Sliced print for the 2-cable SpiRob body |
| `Data SpiRobs/Dual_3-cable SpiRob.gcode` | Sliced print for the 3-cable SpiRob body |
| `Data SpiRobs/SS_Disk3D_Test.gcode` | Full-size disk adhesion test |
| `Data SpiRobs/SS_Disk3D_Test_Small.gcode` | Small disk adhesion test |

---

## Print Settings

| Parameter | SpiRob Body | Structural Parts (base, mounts) |
|---|---|---|
| Material | TPU-70A | PLA |
| Nozzle temp | 220–230 °C | 200–215 °C |
| Bed temp | 30–40 °C | 60 °C |
| Layer height | 0.2 mm | 0.2 mm |
| Infill | 15–20% | 30–40% |
| Print speed | 25–30 mm/s | 50 mm/s |
| Supports | No | No |

> **Tip:** The SpiRob body requires a flexible filament (TPU-70A). Print slowly and disable retraction or use minimal retraction to prevent filament jams. See [`3D Printer Troubleshooting Guide.md`](../3D%20Printer%20Troubleshooting%20Guide%20.md) for common issues.

---

## Known Design Limitations

- The 28BYJ-48 motor torque (~34.3 mN·m) is insufficient to fully curl the two-cable SpiRob against high cable tension — stronger motors are a priority upgrade.
- Fishing wire stretches at high tension, reducing precision at the ends of the range of motion. Braided line or Dyneema is recommended.
- The SpiRob body was printed at too low an infill percentage in early iterations, causing buckling under stress. Use = 20% infill.
- Without an elastic core, the SpiRob does not return to a neutral position passively.

---

## SpiRob Credit

The logarithmic-spiral SpiRob concept and original STL models are from:

> Zhanchi Wang, Nikolaos M. Freris, Xi Wei,
> *SpiRobs: Logarithmic spiral-shaped robots for versatile grasping across scales*,
> **Device**, Volume 3, Issue 4, 2025, 100646.
> https://doi.org/10.1016/j.device.2024.100646

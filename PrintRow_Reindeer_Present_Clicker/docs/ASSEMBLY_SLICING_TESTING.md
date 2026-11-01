# Printing, assembly and prototype testing

Status: **test-ready prototype files. Nothing has been physically printed or assembled yet.**
Everything below that mentions fit, feel or strength still needs checking on real prints.

---

## 0. Print the test kit FIRST (about 11.5 g)

File: `exports/3mf/PrintRow_Reindeer_T_fit_and_movement_test_kit.3mf` (or the STLs in `exports/stl/test_kit/`).
Any colour, PLA, same settings as below. The kit contains:

| Part | Purpose |
|---|---|
| `test_switch_coupon` | The real switch pillar, 14.0 mm plate and clip-relief pocket, cut from the product box geometry |
| `test_cap` | The real head pedestal with the real cavity, roof chamfer, boss and cross socket |
| `test_leg_slot_block` | The real rim pad with the leg snap slot and undercut |
| `test_leg_right_single_colour` | One real leg, for testing the snap |
| `test_socket_gauge_1/2/3` | Cross socket 1.25 / 1.35 / 1.45 mm wide (1–3 notches) |
| `test_plate_gauge_1..4` | 13.90 / 14.00 / 14.10 / 14.20 mm cutouts (1–4 notches) |

Test procedure (record results in the checklist):
1. Push your switch into each plate gauge. Note which one it **clicks into and holds without wobble**.
2. Push each socket gauge onto the stem. Note which one is **firm, without splitting**, and still removable by hand.
3. Push the switch into the coupon (the notch marks the front), then press the test cap on (its notch also marks the front).
   * The switch must click, the cap must return fully, and nothing may rub.
   * Press 50 times centred and 20 times on the cap edge. Watch and listen for rubbing or catching.
4. Snap the test leg into the slot block. It should click in with firm thumb pressure, sit flat on the rim and front
   face, and not pull out by hand.
5. If anything fails, send me the gauge numbers and measurements (see `docs/SWITCH_NOTES.md`).
   The parameters are in `source/params.py`, and `source/build_all.sh` rebuilds everything.

---

## 1. Print plates (Bambu, 0.4 mm nozzle, PLA)

| Plate | File (3MF) | Colours | Orientation (already set) | Supports / brim |
|---|---|---|---|---|
| A | `PrintRow_Reindeer_A_head_4colour.3mf` | brown, cream, dark brown, black | upright, flat bottom down | none / none |
| B | `PrintRow_Reindeer_B_box_red_white_band.3mf` | red + white band (z 10.5–16.5 mm) | upright, open top up | none / none |
| C | `PrintRow_Reindeer_C_ribbon_cage_and_bow_white.3mf` | white | cage upright on its ribbon cross; bow flat on its back | none / none |
| D | `PrintRow_Reindeer_D_legs.3mf` | brown + dark-brown hoof (or one colour) | legs lying on their inner side | none / none |

Plain STL fallback (identical geometry): `exports/stl/product/`. Files are named `<plate>_<part>__<colour>.stl`.
All colour STLs of one part share the same coordinates.

### Suggested starting settings (Bambu Studio "0.20 mm Standard" plus these)
* Layer height 0.20 mm; walls 2 (use 3 on the box and cage for stiffness); top 5 / bottom 3 layers; sparse infill 15 % grid or gyroid.
* **Supports: off. Brim: off.** The geometry was designed for this (see `reports/printability_report.json`).
  * Head: the cavity roof is a 12.6 mm bridge with 45° chamfers; the chin, ears and antlers are self-supporting (≥ 45°).
  * Box: the ribbon channel under the box is a 6.4 mm bridge; the plate lip overhangs 0.9 mm; the band and leg pads have 45° undersides.
  * Cage: stands on its 6 mm ribbon cross (428 mm² of bed contact). The straps are 1.2 mm thin walls, 31 mm tall. Turn on "slow down for overhangs" (default).
  * Legs: lying on their side, everything is a prism, so there are no overhangs except < 1 mm slots.
* Elephant's foot compensation: 0.10–0.15 mm (the head bottom and socket mouth already have small chamfers).
* Seam: "back" or "aligned" for the head, so the seam does not cross the face.

### Loading the 3MF in Bambu Studio (not tested here; please confirm)
These are **plain 3MF** files: geometry, part names and display colours only, with no slicer settings. Each multi-colour part is
one 3MF object made of aligned colour components.
* If Bambu Studio asks **"load as a single object with multiple parts?"**, answer **Yes**.
* Check in the object list that the head shows **4 parts under one object**. Then assign filaments: brown, cream, dark brown, black.
* If the parts appear as separate objects, or drop onto the plate separately: delete them and use the STL method.

**STL method (reliable in every slicer):** select all STLs for one part together (e.g. the four `A_head__*.stl`),
drag them in as one batch, and answer **Yes** to "load as a single object with multiple parts". Then assign a filament to each part.

> Note from testing: PrusaSlicer 2.7.2's command line loads these components as separate objects and drops them to
> the bed, so the colours misalign. It cannot answer the multi-part question. In PrusaSlicer's GUI, use the same "single object" answer or the STL method.
> When loaded as one multi-part object, the head sliced correctly (212 layers, all parts aligned).

### Colour-change options (affects time and purge waste)
* **Head, 4 colours:** about 206–209 filament changes per plate (my layer estimate 206; PrusaSlicer multi-material slice 209).
  **Purge waste is large relative to an 8.5 g head.** PrusaSlicer's default wipe tower used about 46 g for one head.
  Bambu's flush volumes differ, so slice in Bambu Studio to get the real figure. Ways to reduce it:
  1. **Print several heads per plate.** Changes happen per layer, so purge per head falls roughly with the number of heads.
  2. Enable "flush into objects' infill" / "flush into support". Lower flush multipliers for light-to-dark changes.
  3. **3-colour option:** assign the black eye part to the dark-brown filament (about 188 changes).
* **Box:** 2 changes per plate (red → white band → red). Interior walls inside the band zone are also white; that is intended and hidden.
* **Legs:** 2-colour about 36 changes per plate (PrusaSlicer). **1-colour (assign both parts dark brown or brown): 0 changes.**
* **Cage + bow:** 0 changes.

### Filament and time (PrusaSlicer 2.7.2 slice, my approximated Bambu-like profile, NOT Bambu Studio)
| Plate | Filament (net, no purge) | PrusaSlicer time estimate* |
|---|---|---|
| A head (merged geometry) | 8.5 g | 30 min |
| B box | 15.0 g (red 11.9 g, white 3.4 g) | 34 min |
| C cage + bow | 2.5 g | 22 min |
| D legs | 1.7 g | 11 min |
| T test kit | 11.5 g | 44 min |

\*Not a Bambu Studio estimate. Do not quote these times or use them for pricing until you have sliced in Bambu Studio.
Purge/flush waste is excluded and must come from Bambu Studio.

---

## 2. Bill of materials
* Printed: head, box, ribbon cage, bow, 2 legs (6 parts).
* 1 × MX-compatible mechanical keyboard switch (type to be confirmed, see `SWITCH_NOTES.md`).
* No glue, screws or magnets.

## 3. Assembly (no glue)
1. **Switch → box:** push the switch straight down into the 14.0 mm plate (pins down, either orientation) until both clips snap.
   If it is loose, try the 14.00 / 13.90 plate gauges first and adjust `SW_CUTOUT`.
2. **Ribbon cage → box:** lower the box into the cage from above with the cage straps aligned to the band gaps.
   The front strap (the one with the rail) goes to the front, where the leg pads are inside the rim.
   The side and back straps flex out slightly and their caps click over the rim. The ribbon cross sits flush in the channel under the box.
3. **Bow → cage:** slide the bow down onto the dovetail rail on the front strap until it stops on the rail top.
4. **Legs → box:** press each leg's split tab into its slot in the front rim until it clicks. The hoof sits over the bow and the
   leg lies on the rim. The hooves now stop the bow sliding up, so the bow is captured.
5. **Head → switch:** align the head square to the box (face forward) and press it straight down onto the stem until it seats.
6. Check: press the head 20 times centred and at the edges. Nothing may rub, and it must return fully.

## 4. Disassembly / switch replacement
1. Pull the head straight up off the stem, like a keycap.
2. Remove the switch with a standard MX switch puller from above: squeeze the two clips through the box opening.
   The 5 mm hole under the switch lets you push it up gently once the clips are released.
3. The legs are designed to stay in permanently (one-way barbs). To remove them, lever the tab prongs together from inside the slot. They may break.
4. The cage comes off by flexing the side and back straps outward over the rim.

## 5. Key clearances (digital sweep, see `reports/clearance_report.json`)
| Check (head moving 0 → 4.0 mm) | Minimum gap |
|---|---|
| Head ↔ box rim / walls | 1.06 mm (1.02 mm at 4.5 mm over-travel) |
| Head ↔ ribbon cage caps | 1.92 mm |
| Head ↔ each fixed leg | 1.55 mm |
| Head ↔ bow | > 6 mm |
| Head cavity ↔ switch housing (excluding the boss) | 1.49 mm |
| Head bottom ↔ switch plate at full travel | 3.0 mm |
| Worst case with a 1.5° tilt (off-centre press) | 0.75 mm, still clear |

## 6. Parameters you are most likely to tune (`source/params.py`)
`SW_CUTOUT`, `STEM_SLOT_W`, `STEM_SLOT_L`, `SOCKET_DEPTH`, `SW_STEM_TOP`, `LEG_BARB`, `LEG_SLOT_CLEAR`, `RAIL_CLEAR`,
`CAP_REACH`. After changing them, run `source/build_all.sh`. It regenerates all parts, re-runs the clearance sweep and checks,
and rebuilds the STL/3MF files.

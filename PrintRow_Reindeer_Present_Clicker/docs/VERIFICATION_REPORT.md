# Verification report

Date: 1 Nov 2026. **Every result in this document is DIGITAL** (CAD and mesh analysis, slicer software).
**No part has been printed, assembled, clicked or weighed.** Physical results go in `PRE_SALE_CHECKLIST.md`.

Raw data: `reports/*.json`, `reports/prusaslicer_check.txt`, `reports/viewer_check/*.png`, `renders/clearance_sweep_plot.png`.

## A. Motion and clearance (digital sweep, `source/check_clearance.py`)
Method: the complete moving head (all colour parts, boss included) is translated down 0 → 4.5 mm in 0.1 mm steps
(4.0 mm MX travel + 0.5 mm margin). The exact minimum gap (`manifold3d.min_gap`) and the boolean interference volume are computed
against each fixed part. The sweep is repeated with ±1.5° tilts about x and y (stem wobble / off-centre press) at
0, 1, 2, 3, 4 and 4.5 mm.

| Result | Value |
|---|---|
| Interference volume, any step, any fixed part (straight and tilted) | **0.000 mm³** |
| Min gap to box over 0–4.0 mm | 1.06 mm (1.02 mm at 4.5 mm) |
| Min gap to ribbon cage over 0–4.0 mm | 1.92 mm |
| Min gap to each fixed leg over 0–4.0 mm | 1.55 mm |
| Min gap to bow | > 6 mm (search limit) |
| Worst tilted case (1.5°, 4.5 mm, box) | 0.75 mm |
| Head cavity to switch housing envelope (boss excluded), full travel | 1.49 mm |
| Head bottom to switch plate, full travel | 3.0 mm |
| Boss entry into the switch top at full travel | 3.6 mm (normal keycap behaviour, needs a ≥ 5.5 mm opening: standard MX) |
| Static interference between fixed parts (box, cage, legs, bow) | 0.000 mm³ for all pairs |
| Leg snap tabs vs box when seated (barbs in the undercut) | 0.000 mm³ |
| Clearance-carve safety pass (head minus fixed parts inflated 1 mm and swept 4.5 mm) | removed 0.000 mm³, so no part of the head was inside the keep-out |

**Limits:** the switch is an MX-style *envelope* (unconfirmed dimensions), not a scan of your switch. The real tilt or wobble
of your switch, print tolerances and elephant's foot are not modelled beyond the 1.0 mm clearance target and the 1.5° tilt case.

## B. Mesh validity (`source/verify_exports.py`, `source/assemble.py`)
* All **23 STL** files: watertight, consistent winding, positive volume, zero non-manifold edges.
* Colour parts of each object are non-overlapping and share boundaries exactly (built by boolean partition).

## C. 3MF files open and contain geometry (independent readers)
| File | lib3mf 2.5 strict read | All meshes manifold + oriented | trimesh loader | assimp (independent) | PrusaSlicer 2.7.2 |
|---|---|---|---|---|---|
| A_head_4colour | OK, 0 warnings | yes | 4 meshes | parsed, rendered | opens; see note |
| B_box_red_white_band | OK, 0 warnings | yes | 2 meshes | parsed, rendered | opens; see note |
| C_ribbon_cage_and_bow_white | OK, 0 warnings | yes | 2 meshes | parsed, rendered | sliced OK |
| D_legs | OK, 0 warnings | yes | 4 meshes | parsed, rendered | sliced OK |
| T_fit_and_movement_test_kit | OK, 0 warnings | yes | 11 meshes | parsed, rendered | sliced OK |
| ASSEMBLY_PREVIEW (not for printing) | OK, 0 warnings | yes | 11 meshes | parsed, rendered | (not sliced) |

* Each 3MF contains only `3D/3dmodel.model`, `[Content_Types].xml` and `_rels/.rels`, with no `requiredextensions` and no slicer
  configuration. This avoids the "invalid configuration" class of error, and every file has geometry.
* Colour assignment per part was verified by parsing the model XML (base-material names and display colours).
  Note: the assimp → f3d preview draws some parts in the wrong colour (an assimp material-mapping quirk). The file itself is correct.
* **Note (PrusaSlicer behaviour):** PrusaSlicer's CLI loads each colour component as a separate object and drops it to the
  bed, which misaligns the colours (the head then slices at 161 instead of 212 layers). In the GUI, slicers ask whether to load
  such files as one multi-part object: answer Yes, or use the STL method in `ASSEMBLY_SLICING_TESTING.md`.
  When the same geometry was loaded as one multi-part object (`source/verify_multipart_prusaslicer.py`), PrusaSlicer sliced it
  correctly: head 212 layers / 209 tool changes; box 150 layers / 2 tool changes; legs 35 layers / 36 tool changes.
* **Bambu Studio: NOT tested** (it cannot be downloaded in this environment: GitHub and the Bambu servers are blocked by the
  session's network policy, and there is no Bambu Studio for this headless Linux container). Please open the 3MFs in Bambu Studio and record the result.

## D. Printability screen (`source/check_printability.py`, print orientation)
| Object | Bed contact | Down-facing > 60° (bridges/overhangs) | Comment |
|---|---|---|---|
| Head | 263 mm² | 126 mm² | 12.6 mm cavity-roof bridge (chamfered), 1.35 mm socket slots |
| Box | 801 mm² | 459 mm² | 6.4 mm ribbon-channel bridge (400 mm²), 0.9 mm plate lip; band and leg pads at 45° |
| Cage | 428 mm² | 169 mm² | cap undersides (1.4 mm overhang) and strap ends; 1.2 mm thin walls, 31 mm tall |
| Bow | 228 mm² | 26 mm² | 3.9 mm dovetail-groove bridge |
| Legs | 46 mm² each | 17 mm² each | < 1 mm slot roofs |
No support material is expected to be needed. **This is geometric screening only and must be confirmed by a real print.**

## E. Slicing (PrusaSlicer 2.7.2 with an approximated Bambu 0.4 mm / 0.20 mm PLA profile)
`source/slicer/prusaslicer_bambu_like_0.4_PLA.ini` is my approximation, **not** a Bambu profile.
| Plate | Net filament | PrusaSlicer time* | Filament changes |
|---|---|---|---|
| A head | 8.5 g | 30 min | 209 (PrusaSlicer MMU slice); 206 layer estimate; 188 with eyes in dark brown |
| B box | 15.0 g (11.9 red + 3.4 white) | 34 min | 2 |
| C cage + bow | 2.5 g | 22 min | 0 |
| D legs | 1.7 g | 11 min | 36 two-colour / 0 one-colour |
| T test kit | 11.5 g | 44 min | 0 |
\*Not Bambu Studio estimates. Purge: PrusaSlicer's default wipe tower used ≈ 46 g for a single 4-colour head and ≈ 7 g for the
two-colour legs. That is indicative only: Bambu flush volumes differ, and batching several heads per plate shares the purge.
**Do not use these numbers for pricing until they are re-sliced in Bambu Studio.**

## F. Independent viewer
The `assimp` (Open Asset Import Library) → `f3d` path rendered every 3MF headlessly: `reports/viewer_check/`.
This confirms the geometry is present and placed as intended. F3D cannot open 3MF directly in this build.

## G. Not verified (needs physical testing or your input)
* Switch type and every switch dimension (fit test).
* Snap-fit forces (legs, cage caps, bow rail, head press-fit) and their durability.
* Antler, ear and leg strength; drop behaviour; repeated-click durability.
* Real print quality without supports or brim (cage straps, head roof bridge, band underside).
* Bambu Studio import behaviour, real print times, flush waste, finished dimensions and weight.
* Safety assessment (see the checklist). The design is **not** safety-approved.

"""
DIGITAL ESTIMATE of AMS filament changes per plate (not a slicer result).

Sections every colour part of a print-oriented object at each 0.2 mm layer, finds which colours
appear on each layer, and counts changes assuming the slicer starts each layer with the colour it
finished the previous layer with (Bambu Studio does this).  Purge/flush grams depend on Bambu Studio's
flushing volumes and are NOT estimated here.

Run:  /opt/prvenv/bin/python source/estimate_colour_changes.py
"""
import glob
import json
import os

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "exports", "stl", "product")
LH, FLH = 0.2, 0.2


def present(mesh, z):
    s = mesh.section(plane_origin=(0, 0, z), plane_normal=(0, 0, 1))
    if s is None:
        return False
    try:
        p, _ = s.to_2D()
        return p.area > 0.02
    except Exception:
        return len(s.entities) > 0


def estimate(prefix, merge=None):
    parts = {os.path.basename(f)[:-4].split("__")[1]: trimesh.load(f)
             for f in sorted(glob.glob(os.path.join(EXP, prefix + "__*.stl")))}
    for src, dst in (merge or {}).items():   # e.g. print the eyes with the dark-brown filament
        parts[dst] = trimesh.util.concatenate([parts[dst], parts.pop(src)])
    zmax = max(m.bounds[1, 2] for m in parts.values())
    zs = np.arange(FLH / 2, zmax, LH)
    last, changes, layers_multi = None, 0, 0
    per_colour_layers = {k: 0 for k in parts}
    for z in zs:
        here = [k for k, m in parts.items() if present(m, z)]
        for k in here:
            per_colour_layers[k] += 1
        if not here:
            continue
        if len(here) > 1:
            layers_multi += 1
        order = sorted(here, key=lambda k: (k != last, k))
        if last is not None and order[0] != last:
            changes += 1
        changes += len(order) - 1
        last = order[-1]
    return {"layers": int(len(zs)), "layers_with_2plus_colours": layers_multi,
            "estimated_filament_changes": changes, "layers_per_colour": per_colour_layers}


def main():
    rep = {p: estimate(p) for p in ("A_head", "B_box", "D_leg_right", "D_leg_left")}
    rep["A_head_3colour_option_eyes_in_dark_brown"] = estimate("A_head", {"black": "dark_brown"})
    rep["D_legs_plate_total_if_two_colour"] = (rep["D_leg_right"]["estimated_filament_changes"]
                                               + rep["D_leg_left"]["estimated_filament_changes"])
    rep["note"] = ("Estimate only. Legs printed single-colour (both parts set to one filament) = 0 changes. "
                   "Cage and bow plate is single colour = 0 changes.")
    json.dump(rep, open(os.path.join(ROOT, "reports", "colour_change_estimate.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()

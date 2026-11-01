"""
Digital motion / clearance verification (no physical test implied).

* Sweeps the moving head (all colour parts + boss) straight down 0 -> SW_TRAVEL_CHECK (4.5 mm,
  = 4.0 mm MX travel + 0.5 mm margin) in 0.1 mm steps and reports, against every fixed part
  (box, ribbon cage, both legs, bow): exact minimum gap (manifold3d.min_gap) and interference volume.
* Repeats at +/-TILT_DEG about x and y (off-centre press rocking the stem) at several depths.
* Checks the head cavity against the switch-housing envelope, and reports how far the 5.5 mm
  boss enters the switch top opening (normal keycap behaviour).
* Checks static interference between the fixed parts (assembly fit).

Run:  /opt/prvenv/bin/python source/check_clearance.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from params import *  # noqa: E402,F401,F403
from assemble import M, load, union, mat4  # noqa: E402

ROOT = os.path.dirname(HERE)
FIN = os.path.join(ROOT, "build", "final", "product")
CQ = os.path.join(ROOT, "build", "cq")
REP = os.path.join(ROOT, "reports")


def rot(axis, deg, pivot):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    R = {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]),
         "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])}[axis]
    p = np.array(pivot)
    return mat4(R, p - R @ p)


def main():
    fixed = {n: load(os.path.join(FIN, f + ".stl")) for n, f in [
        ("box", "box"), ("cage", "cage_white"), ("leg_right", "leg_right"),
        ("leg_left", "leg_left"), ("bow", "bow_white")]}
    head = union([load(os.path.join(FIN, f"head_{c}.stl")) for c in ("brown", "cream", "dark_brown", "black")])
    boss_zone = M.cylinder(Z_CAVITY_CEIL - HEAD_Z0 + 3.0, BOSS_D / 2 + 1.8, BOSS_D / 2 + 1.8, 64).translate(
        (0, 0, HEAD_Z0 - 1.0))
    head_noboss = head - boss_zone
    switch = load(os.path.join(CQ, "switch_body.stl"))
    rep = {"travel_check_mm": SW_TRAVEL_CHECK, "clear_target_mm": CLEAR_MIN, "vertical": [], "tilt": []}

    # ---------------- vertical sweep
    worst = {k: (1e9, None) for k in fixed}
    for t in np.round(np.arange(0, SW_TRAVEL_CHECK + 1e-6, 0.1), 2):
        h = head.translate((0, 0, -t))
        row = {"t": float(t)}
        for k, f in fixed.items():
            g = h.min_gap(f, 6.0)
            iv = (h ^ f).volume()
            row[k] = {"gap": round(g, 3), "interference_mm3": round(iv, 4)}
            if g < worst[k][0]:
                worst[k] = (g, float(t))
        hs = head_noboss.translate((0, 0, -t))
        row["switch_housing_gap_excl_boss"] = round(hs.min_gap(switch, 6.0), 3)
        rep["vertical"].append(row)
    rep["vertical_worst_gap"] = {k: {"gap": round(v[0], 3), "at_t": v[1]} for k, v in worst.items()}

    # ---------------- tilt sweep (stem wobble / off-centre press)
    pivot = (0.0, 0.0, Z_HOUSING_TOP)
    tilt_min = (1e9, None)
    for t in (0.0, 1.0, 2.0, 3.0, 4.0, SW_TRAVEL_CHECK):
        for axis in ("x", "y"):
            for sgn in (1, -1):
                h = head.transform(rot(axis, sgn * TILT_DEG, pivot)).translate((0, 0, -t))
                gaps = {k: round(h.min_gap(f, 6.0), 3) for k, f in fixed.items()}
                inter = {k: round((h ^ f).volume(), 4) for k, f in fixed.items()}
                g = min(gaps.values())
                rep["tilt"].append({"t": t, "axis": axis, "deg": sgn * TILT_DEG, "gaps": gaps,
                                    "interference_mm3": inter})
                if g < tilt_min[0]:
                    tilt_min = (g, (t, axis, sgn * TILT_DEG, min(gaps, key=gaps.get)))
    rep["tilt_worst_gap"] = {"gap": round(tilt_min[0], 3), "case": tilt_min[1]}

    # ---------------- switch / boss
    rep["boss_entry_into_switch_top_at_full_travel_mm"] = round(SW_TRAVEL - (HEAD_Z0 - Z_HOUSING_TOP), 2)
    rep["cavity_roof_to_housing_top_at_full_travel_mm"] = round(Z_CAVITY_CEIL - SW_TRAVEL - Z_HOUSING_TOP, 2)
    rep["head_bottom_to_plate_at_full_travel_mm"] = round(HEAD_Z0 - SW_TRAVEL - PLATE_Z, 2)

    # ---------------- static assembly interference between fixed parts
    names = list(fixed)
    pairs = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            pairs[f"{a}~{b}"] = round((fixed[a] ^ fixed[b]).volume(), 4)
    rep["fixed_part_interference_mm3"] = pairs
    # snap engagement: untrimmed tab vs box (barbs must sit in the undercut when seated)
    for nm in ("right", "left"):
        tab = load(os.path.join(CQ, f"leg_{nm}_tab.stl"))
        rep[f"leg_{nm}_tab_vs_box_interference_mm3"] = round((tab ^ fixed["box"]).volume(), 4)

    json.dump(rep, open(os.path.join(REP, "clearance_report.json"), "w"), indent=1)

    # ---------------- plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ts = [r["t"] for r in rep["vertical"]]
        fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=130)
        for k in fixed:
            ax.plot(ts, [r[k]["gap"] for r in rep["vertical"]], label=k, lw=2)
        ax.plot(ts, [r["switch_housing_gap_excl_boss"] for r in rep["vertical"]], label="switch housing (excl. boss)",
                lw=2, ls="--")
        ax.axhline(CLEAR_MIN, color="k", lw=1, ls=":", label=f"{CLEAR_MIN} mm target")
        ax.axvline(SW_TRAVEL, color="grey", lw=1, ls=":")
        ax.text(SW_TRAVEL + 0.03, 0.2, "4.0 mm MX travel", fontsize=7, color="grey", rotation=90)
        ax.set_xlabel("head travel (mm)")
        ax.set_ylabel("minimum gap to part (mm)")
        ax.set_ylim(0, 6.2)
        ax.set_title("Digital clearance sweep - moving head vs fixed parts")
        ax.legend(fontsize=7, ncol=2, loc="upper right")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(ROOT, "renders", "clearance_sweep_plot.png"))
    except Exception as e:  # pragma: no cover
        print("plot failed:", e)

    summary = {k: rep[k] for k in rep if k not in ("vertical", "tilt")}
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

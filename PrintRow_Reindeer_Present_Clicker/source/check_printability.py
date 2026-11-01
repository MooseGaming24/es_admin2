"""
Digital printability checks on the PRINT-ORIENTED exports (z = build direction).

For every printed object (colour parts unioned first):
  * watertight / volume / bounding box / footprint area on the bed
  * downward-facing surface area by overhang angle (measured from vertical):
        45-60 deg  -> normally fine on Bambu printers without supports
        > 60 deg   -> bridges or overhangs; listed with their height and span so they can be judged
  * minimum z of each > 60 deg region (0 = on the bed, ignored)

This is a geometric screen, not a slicer.  Run:  /opt/prvenv/bin/python source/check_printability.py
"""
import glob
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from assemble import load, union, to_t  # noqa: E402

ROOT = os.path.dirname(HERE)
EXP = os.path.join(ROOT, "exports", "stl")


def groups():
    g = {}
    for f in sorted(glob.glob(os.path.join(EXP, "product", "*.stl"))):
        obj = os.path.basename(f).split("__")[0]
        g.setdefault(obj, []).append(f)
    for f in sorted(glob.glob(os.path.join(EXP, "test_kit", "*.stl"))):
        g[os.path.basename(f)[:-4]] = [f]
    return g


def analyse(files):
    m = union([load(f) for f in files])
    t = to_t(m)
    n = t.face_normals
    a = t.area_faces
    zc = t.triangles_center[:, 2]
    zmin = t.bounds[0, 2]
    off_bed = zc > zmin + 0.25
    down = -n[:, 2]
    band_45_60 = (down > np.cos(np.radians(45))) & (down <= np.cos(np.radians(30))) & off_bed
    steep = (down > np.cos(np.radians(30))) & off_bed            # > 60 deg from vertical
    bed = (down > 0.999) & ~off_bed
    regions = []
    if steep.any():
        idx = np.where(steep)[0]
        adj = t.face_adjacency
        keep = steep[adj[:, 0]] & steep[adj[:, 1]]
        groups = trimesh.graph.connected_components(adj[keep], nodes=idx, min_len=1)
        for gidx in groups:
            ar = float(a[gidx].sum())
            if ar < 0.5:
                continue
            v = t.vertices[t.faces[gidx].ravel()]
            ext = v.max(0) - v.min(0)
            regions.append({"area_mm2": round(ar, 1), "z_mm": round(float(v[:, 2].min()), 2),
                            "span_xy_mm": [round(float(ext[0]), 1), round(float(ext[1]), 1)]})
    regions.sort(key=lambda r: -r["area_mm2"])
    return {
        "watertight": bool(t.is_watertight),
        "volume_cm3": round(m.volume() / 1000, 3),
        "bbox_mm": [round(float(v), 2) for v in (t.bounds[1] - t.bounds[0])],
        "bed_contact_mm2": round(float(a[bed].sum()), 1),
        "overhang_45_60_mm2": round(float(a[band_45_60].sum()), 1),
        "overhang_gt60_mm2": round(float(a[steep].sum()), 1),
        "gt60_regions": regions[:12],
    }


def main():
    out = {k: analyse(v) for k, v in groups().items()}
    json.dump(out, open(os.path.join(ROOT, "reports", "printability_report.json"), "w"), indent=1)
    for k, v in out.items():
        print(f"{k:36s} wt={v['watertight']} vol={v['volume_cm3']:6.2f}cm3 bed={v['bed_contact_mm2']:7.1f} "
              f"o45-60={v['overhang_45_60_mm2']:6.1f} o>60={v['overhang_gt60_mm2']:6.1f} "
              f"top>60={v['gt60_regions'][:3]}")


if __name__ == "__main__":
    main()

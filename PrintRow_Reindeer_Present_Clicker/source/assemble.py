"""
PrintRow Reindeer Present Clicker - assembly, colour split, mechanism booleans and exports.

Inputs : build/cq/*.stl (mechanism_cq.py) and build/blender/*.stl (character_blender.py)
Outputs: build/final/product/*.stl   - every part in assembled PRODUCT coordinates
         exports/stl/product/*.stl   - print-oriented, colour parts aligned per part group
         exports/stl/test_kit/*.stl  - test kit
         reports/assemble_report.json

Run:  /opt/prvenv/bin/python source/assemble.py
"""
import json
import os
import sys

import manifold3d as m3d
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from params import *  # noqa: E402,F401,F403

ROOT = os.path.dirname(HERE)
CQ = os.path.join(ROOT, "build", "cq")
BL = os.path.join(ROOT, "build", "blender")
FIN = os.path.join(ROOT, "build", "final", "product")
EXP = os.path.join(ROOT, "exports", "stl", "product")
EXPT = os.path.join(ROOT, "exports", "stl", "test_kit")
REP = os.path.join(ROOT, "reports")
for d in (FIN, EXP, EXPT, REP):
    os.makedirs(d, exist_ok=True)

M = m3d.Manifold


# ----------------------------------------------------------------------------- conversion
def load(path):
    tm = trimesh.load(path, force="mesh", process=True)
    tm.merge_vertices()
    return to_m(tm, path)


def to_m(tm, label="mesh"):
    mesh = m3d.Mesh(vert_properties=np.asarray(tm.vertices, dtype=np.float32),
                    tri_verts=np.asarray(tm.faces, dtype=np.uint32))
    mf = M(mesh)
    if mf.status() != m3d.Error.NoError or mf.is_empty():
        # try a repair pass
        tm = tm.copy()
        trimesh.repair.fix_normals(tm)
        trimesh.repair.fill_holes(tm)
        mesh = m3d.Mesh(vert_properties=np.asarray(tm.vertices, dtype=np.float32),
                        tri_verts=np.asarray(tm.faces, dtype=np.uint32))
        mf = M(mesh)
        if mf.status() != m3d.Error.NoError:
            raise RuntimeError(f"{label}: not a valid manifold ({mf.status()})")
    return mf


def clean(mf, min_vol=0.05):
    """Remove degenerate slivers left by coincident surfaces."""
    if hasattr(mf, "simplify"):
        mf = mf.simplify(0.002)
    comps = [c for c in mf.decompose() if c.volume() > min_vol]
    return M.compose(comps) if len(comps) > 1 else comps[0]


def to_t(mf):
    me = mf.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(me.vert_properties)[:, :3], faces=np.asarray(me.tri_verts),
                           process=True)


def union(lst):
    lst = [x for x in lst if x is not None and not x.is_empty()]
    return M.batch_boolean(lst, m3d.OpType.Add) if len(lst) > 1 else lst[0]


def box(x0, x1, y0, y1, z0, z1):
    return M.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def save(mf, path):
    t = to_t(mf)
    t.export(path)
    return t


def mat4(R=np.eye(3), t=(0, 0, 0)):
    A = np.zeros((3, 4))
    A[:, :3] = R
    A[:, 3] = t
    return A


# ----------------------------------------------------------------------------- clearance carve
def capsule(r, h):
    return M.batch_hull([M.sphere(r, 24), M.sphere(r, 24).translate((0, 0, h))])


def swept_keepout(fixed, r=CLEAR_MIN, travel=SW_TRAVEL_CHECK):
    """Region the head must not occupy at rest: fixed parts inflated by r and swept UP by travel."""
    near = fixed ^ box(-30, 30, -30, 30, HEAD_Z0 - r - 1, HEAD_Z0 + 25)
    cap = capsule(r, travel)
    if hasattr(near, "minkowski_sum"):
        return near.minkowski_sum(cap), "minkowski_sum"
    # fallback: union of translates (conservative for convex capsule sampling)
    pieces = []
    for dz in np.arange(0, travel + 1e-6, 0.5):
        for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            pieces.append(near.translate((r * np.cos(a), r * np.sin(a), dz)))
        pieces.append(near.translate((0, 0, dz + r)))
        pieces.append(near.translate((0, 0, dz - r)))
    return union(pieces), "translate_union"


# ----------------------------------------------------------------------------- main
def main():
    rep = {"notes": []}
    # ---- fixed parts (product coordinates)
    box_m = load(os.path.join(CQ, "box.stl"))
    legs = {}
    for nm in ("right", "left"):
        core = load(os.path.join(CQ, f"leg_{nm}_core.stl")).minkowski_sum(M.sphere(1.2, 24))
        tab = load(os.path.join(CQ, f"leg_{nm}_tab.stl"))
        groove = load(os.path.join(CQ, f"leg_{nm}_groove.stl"))
        legs[nm] = (core + tab) - groove - box_m
    leg_r, leg_l = legs["right"], legs["left"]
    cage = load(os.path.join(CQ, "cage.stl"))
    fixed = union([box_m, leg_r, leg_l, cage])

    # ---- head features from Blender
    f = {n: load(os.path.join(BL, n + ".stl")) for n in [
        "head_body", "head_core", "antler_r", "antler_l", "ear_r", "ear_l", "earin_r", "earin_l",
        "muzzle", "nose", "eye_r", "eye_l", "eyehl_r", "eyehl_l", "head_core_muzzle"]}
    core = f["head_core"]
    above = box(-60, 60, -60, 60, HEAD_Z0, 120)

    # colour regions by priority (feature volumes trimmed so they never fill the head core)
    order = [
        ("cream", ["eyehl_r", "eyehl_l"]),
        ("black", ["eye_r", "eye_l"]),
        ("dark_brown", ["nose"]),
        ("cream", ["muzzle"]),
        ("cream", ["earin_r", "earin_l"]),
        ("dark_brown", ["antler_r", "antler_l"]),
    ]
    # brown = body + ears minus every other colour region (avoids coincident-surface slivers)
    envelope = union([f["head_body"], f["ear_r"], f["ear_l"]]) ^ above
    taken = None
    parts = {}
    for colour, names in order:
        v = union([f[n] for n in names])
        if names == ["muzzle"]:
            # plane trims only (no coincident surfaces with eyes/nose): keeps cream near the face
            # and removes the hidden interior part of the 45-degree chin hull below z = 33
            v = v ^ box(-30, 30, -40, -9.0, 33.0, 120)
        elif not any(n.startswith(("eye", "nose")) for n in names):
            v = v - core   # antlers / ear inners: keep colour to the outer ~1.8 mm
        v = v ^ above
        if taken is not None:
            v = v - taken
        taken = v if taken is None else taken + v
        parts[colour] = v if colour not in parts else parts[colour] + v
    parts["brown"] = envelope - taken

    # ---- mechanism interface
    cav = load(os.path.join(CQ, "head_cavity_cutter.stl"))
    sock = load(os.path.join(CQ, "head_socket_cutter.stl"))
    # bottom edge chamfer (elephant foot): remove a thin ring at the bottom outer edge
    ef_outer = M.cylinder(1.5, HEAD_RC + 3, HEAD_RC + 3, 64).translate((0, 0.0, HEAD_Z0 - 1.0))
    ef_inner = M.cylinder(2.0, HEAD_RC - 0.5 - 1.0, HEAD_RC + 1.5, 128).translate((0, 0.0, HEAD_Z0 - 1.0))
    foot = ef_outer - ef_inner          # 45-degree 0.5 mm chamfer on the outer bottom edge
    keepout, method = swept_keepout(fixed)
    rep["keepout_method"] = method
    carved = {}
    for k in list(parts):
        before = parts[k] - cav - sock - foot
        after = before - keepout
        carved[k] = round(before.volume() - after.volume(), 3)
        parts[k] = clean(after)
    rep["clearance_carve_removed_mm3"] = carved

    head_all = union(list(parts.values()))
    rep["head_volume_mm3"] = round(head_all.volume(), 1)
    rep["head_genus"] = head_all.genus()

    # ---- bow: print coordinates (back on z=0); groove from product -> print transform
    bow = union([load(os.path.join(BL, n + ".stl")) for n in
                 ["bow_knot", "bow_loop_r", "bow_loop_l", "bow_tail_r", "bow_tail_l"]])
    bow = bow - union([load(os.path.join(BL, n + ".stl")) for n in ["bow_dimple_r", "bow_dimple_l"]])
    bow = bow ^ box(-30, 30, -30, 30, 0, 20)
    yb = -(BOX_W / 2 + CAGE_GAP + CAGE_T)
    zk = (RING_Z[0] + RING_Z[1]) / 2
    # print (x, y, z) -> product (x, yb - z, zk + y)
    P2W = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)
    to_product = mat4(P2W, (0, yb, zk))
    to_print = mat4(P2W.T, -P2W.T @ np.array([0, yb, zk]))
    groove = load(os.path.join(CQ, "bow_groove_cutter.stl")).transform(to_print)
    bow = bow - groove
    bow_product = bow.transform(to_product)

    # ---- product-coordinate exports (renders / sweep)
    band_slab = box(-40, 40, -40, 40, RING_Z[0], RING_Z[1])
    box_white = box_m ^ band_slab
    box_red = box_m - band_slab
    prod = {"box_red": box_red, "box_white": box_white, "box": box_m, "cage_white": cage, "bow_white": bow_product,
            "leg_right": leg_r, "leg_left": leg_l}
    hoof_zone = box(-30, 30, -40, -18.2, 0, 27.6)
    for nm, lg in (("leg_right", leg_r), ("leg_left", leg_l)):
        prod[nm + "_dark_brown"] = lg ^ hoof_zone
        prod[nm + "_brown"] = lg - hoof_zone
    for k, v in parts.items():
        prod["head_" + k] = v
    for k, v in prod.items():
        save(v, os.path.join(FIN, k + ".stl"))
    save(fixed, os.path.join(FIN, "_fixed_union.stl"))
    save(head_all, os.path.join(FIN, "_head_union.stl"))

    # ---- print-oriented exports
    out = {}
    T_head = mat4(np.eye(3), (0, 0, -HEAD_Z0))
    for k, v in parts.items():
        out[f"A_head__{k}"] = v.transform(T_head)
    out["B_box__red"] = box_red
    out["B_box__white"] = box_white
    out["C_cage__white"] = cage
    out["C_bow__white"] = bow.translate((0, -45, 0))   # placed beside the cage on the same plate
    Ry_m90 = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], dtype=float)   # z' = x   (right leg)
    Ry_p90 = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], dtype=float)   # z' = -x  (left leg)
    for nm, R, dx in (("leg_right", Ry_m90, 0.0), ("leg_left", Ry_p90, 0.0)):
        whole = prod[nm]
        tmp = whole.transform(mat4(R))
        bb = tmp.bounding_box()
        shift = (-0.5 * (bb[0] + bb[3]) + (12 if nm == "leg_right" else -12), -0.5 * (bb[1] + bb[4]), -bb[2])
        T = mat4(R, shift)
        if nm == "leg_right":
            save(whole.transform(T), os.path.join(EXPT, "test_leg_right_single_colour.stl"))
        out[f"D_{nm}__brown"] = prod[nm + "_brown"].transform(T)
        out[f"D_{nm}__dark_brown"] = prod[nm + "_dark_brown"].transform(T)
    for k, v in out.items():
        save(v, os.path.join(EXP, k + ".stl"))

    # ---- test kit
    for fn in sorted(os.listdir(CQ)):
        if fn.startswith("test_"):
            tm = trimesh.load(os.path.join(CQ, fn), force="mesh")
            tm.export(os.path.join(EXPT, fn))

    # ---- dimensions
    allp = union([fixed, head_all, bow_product])
    bb = allp.bounding_box()
    rep["assembled_bbox_mm"] = {"x": round(bb[3] - bb[0], 2), "y": round(bb[4] - bb[1], 2),
                                "z": round(bb[5] - bb[2], 2)}
    rep["part_volumes_cm3"] = {k: round(v.volume() / 1000.0, 3) for k, v in out.items()}
    json.dump(rep, open(os.path.join(REP, "assemble_report.json"), "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()

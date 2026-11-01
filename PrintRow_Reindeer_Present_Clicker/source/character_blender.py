"""
PrintRow Reindeer Present Clicker - character modelling in Blender (bpy 5.2 module, headless).

Creates the reindeer head features and the bow as separate watertight meshes in
PRODUCT coordinates and saves:
    build/blender/<feature>.stl     (consumed by assemble.py for colour split + mechanism booleans)
    source/reindeer_character.blend (editable Blender source)

Printability rules baked in:
  * every downward-facing feature (muzzle, nose, eyes) is the convex hull of the feature and a
    copy shifted 45 degrees back-and-down into the head -> self-supporting chin/undersides;
  * ears tilt 50 deg up and have a hulled thick root; antler segments are all >= 50 deg from
    horizontal and >= 4.4 mm thick;
  * the head body has a 14 mm pedestal inside the box, ellipsoid above, flat bottom.

Run:  /opt/prvenv/bin/python source/character_blender.py
"""
import math
import os
import sys

import bpy  # noqa: E402  (must be imported before bmesh)
import bmesh
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from params import *  # noqa: E402,F401,F403

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "build", "blender")
os.makedirs(OUT, exist_ok=True)

CX, CY, CZ = HEAD_C
AX, AY, AZ = HEAD_A


# ----------------------------------------------------------------------------- helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def bm_from_obj(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    return bm


def ellipsoid_bm(c, a, rot=Matrix.Identity(3), seg=64, rings=32):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    m = Matrix.Translation(Vector(c)) @ rot.to_4x4() @ Matrix.Diagonal((a[0], a[1], a[2], 1.0))
    bm.transform(m)
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    return bm


def hull_bm(bms):
    pts = []
    for b in bms:
        pts.extend(v.co.copy() for v in b.verts)
        b.free()
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:], use_existing_faces=False)
    # remove interior leftovers
    junk = {v for v in res["geom_interior"] + res["geom_unused"] if isinstance(v, bmesh.types.BMVert)}
    junk = [v for v in junk if v.is_valid and not v.link_faces]
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def shifted(bm, d):
    b = bm.copy()
    b.transform(Matrix.Translation(Vector(d)))
    return b


def export_stl(ob, name):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, name + ".stl"), export_selected_objects=True,
                          apply_modifiers=True, ascii_format=False)


def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def head_surface_front(x, z):
    """Point + outward normal on the head ellipsoid, front (-y) side."""
    u = ((x - CX) / AX) ** 2 + ((z - CZ) / AZ) ** 2
    y = CY - AY * math.sqrt(max(1e-6, 1 - u))
    n = Vector(((x - CX) / AX ** 2, (y - CY) / AY ** 2, (z - CZ) / AZ ** 2)).normalized()
    return Vector((x, y, z)), n


# ----------------------------------------------------------------------------- head body
def smax(a, b, k=1.5):
    return 0.5 * (a + b + math.sqrt((a - b) ** 2 + k * k))


def head_body_bm(shrink=0.0, nseg=128):
    """Analytic body: ellipsoid above, smooth blend into the r=HEAD_RC pedestal below, flat bottom."""
    z0 = HEAD_Z0
    ztop = CZ + AZ - shrink
    zs = list(np.linspace(z0 + (shrink if shrink else 0), ztop - 0.05, 90))
    rings = []
    for z in zs:
        t = (z - CZ) / (AZ - shrink)
        f = math.sqrt(max(0.0, 1 - t * t))
        ex, ey = (AX - shrink) * f, (AY - shrink) * f
        if z < CZ:
            # pedestal blend (only below the equator)
            w = min(1.0, max(0.0, (CZ - z) / 6.0))
            rp = HEAD_RC - shrink
            ex = (1 - w) * ex + w * smax(ex, rp) if ex < rp + 3 else ex
            ey = (1 - w) * ey + w * smax(ey, rp) if ey < rp + 3 else ey
            ex, ey = max(ex, 0.1), max(ey, 0.1)
        rings.append((z, ex, ey))
    bm = bmesh.new()
    vrings = []
    for z, ex, ey in rings:
        ring = []
        for k in range(nseg):
            a = 2 * math.pi * k / nseg
            ring.append(bm.verts.new((CX + ex * math.cos(a), CY + ey * math.sin(a), z)))
        vrings.append(ring)
    for r0, r1 in zip(vrings[:-1], vrings[1:]):
        for k in range(nseg):
            bm.faces.new((r0[k], r0[(k + 1) % nseg], r1[(k + 1) % nseg], r1[k]))
    bm.faces.new(list(reversed(vrings[0])))
    top = bm.verts.new((CX, CY, CZ + AZ - shrink))
    for k in range(nseg):
        bm.faces.new((vrings[-1][k], vrings[-1][(k + 1) % nseg], top))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


# ----------------------------------------------------------------------------- features
def capsule_chain_obj(name, segs, voxel=0.16):
    """Union of capsules (p0, r0, p1, r1) -> voxel remesh -> smooth; returns object."""
    bm = bmesh.new()
    for p0, r0, p1, r1 in segs:
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        q = d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        cone = bmesh.new()
        bmesh.ops.create_cone(cone, cap_ends=True, cap_tris=False, segments=40,
                              radius1=r0, radius2=r1, depth=L)
        cone.transform(Matrix.Translation((p0 + p1) / 2) @ q)
        tmp = bpy.data.meshes.new("tmp")
        cone.to_mesh(tmp)
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        cone.free()
        for p, r in ((p0, r0), (p1, r1)):
            s = bmesh.new()
            bmesh.ops.create_uvsphere(s, u_segments=40, v_segments=20, radius=r)
            s.transform(Matrix.Translation(p))
            tmp = bpy.data.meshes.new("tmp")
            s.to_mesh(tmp)
            bm.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
            s.free()
    ob = new_obj(name, bm)
    m = ob.modifiers.new("remesh", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    m.use_smooth_shade = True
    s = ob.modifiers.new("smooth", "SMOOTH")
    s.factor = 0.5
    s.iterations = 4
    apply_mods(ob)
    return ob


def antler_segments(side):
    s = side
    return [
        ((s * 6.0, 1.0, 51.8), 3.6, (s * 8.8, 1.5, 60.0), 3.0),   # main beam
        ((s * 8.8, 1.5, 60.0), 3.0, (s * 7.6, 0.6, 66.0), 2.4),   # inner/upper tip
        ((s * 8.8, 1.5, 60.0), 2.8, (s * 12.0, 1.2, 64.2), 2.3),  # outer tip
        ((s * 8.0, 1.2, 57.0), 2.6, (s * 6.0, -1.0, 61.5), 2.2),  # front tine
    ]


def ear_bms(side):
    tilt = math.radians(50)
    d = Vector((side * math.cos(tilt), 0.0, math.sin(tilt)))
    attach = Vector((side * 14.0, 1.5, 47.5))
    centre = attach + d * 6.0
    a2 = Vector((-side * math.sin(tilt), 0.0, math.cos(tilt)))
    a3 = Vector((0, 1, 0))
    yaw = Matrix.Rotation(math.radians(-side * 12), 3, "Z")
    R = yaw @ Matrix((d, a2, a3)).transposed()
    ear = ellipsoid_bm(centre, (7.2, 4.4, 1.9), R)
    root = ellipsoid_bm(attach - d * 2.0, (3.4, 3.4, 2.6), yaw)
    outer = hull_bm([ear, root])
    front = yaw @ Vector((0, -1, 0))
    inner = ellipsoid_bm(centre + front * 1.45 - d * 0.4, (5.0, 2.7, 0.75), R)
    return outer, inner


def muzzle_nose_eyes():
    out = {}
    mc, ma = (0.0, -11.0, 39.0), (6.0, 5.4, 4.6)
    m = ellipsoid_bm(mc, ma)
    out["muzzle"] = hull_bm([m, shifted(m, (0, 5.0, -5.0))])
    nc, na = (0.0, -15.25, 41.9), (3.2, 2.2, 2.3)
    n = ellipsoid_bm(nc, na)
    out["nose"] = hull_bm([n, shifted(n, (0, 2.2, -2.2))])
    for side, tag in ((1, "r"), (-1, "l")):
        p, nrm = head_surface_front(side * 6.4, 44.8)
        c = p - nrm * 1.3
        e = ellipsoid_bm(c, (2.3, 2.3, 2.5), seg=48, rings=24)
        out[f"eye_{tag}"] = hull_bm([e, shifted(e, (0, 1.3, -1.3))])
        # highlight: small sphere on the eye surface, upper outer quadrant
        up = Vector((0, 0, 1))
        hl_dir = (-nrm * -1).normalized()
        hc = c + (hl_dir * 2.3 + up * 1.05 + Vector((side * 0.55, 0, 0)))
        hc = c + (hc - c).normalized() * 2.3
        out[f"eyehl_{tag}"] = ellipsoid_bm(hc, (0.75, 0.75, 0.75), seg=24, rings=12)
    return out


# ----------------------------------------------------------------------------- bow (print coords: back on z=0)
def bow_objects():
    objs = []
    # knot: rounded box
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.transform(Matrix.Diagonal((5.8, 6.2, 10.0, 1.0)))
    k = new_obj("bow_knot", bm)
    bev = k.modifiers.new("bev", "BEVEL")
    bev.width = 1.6
    bev.segments = 6
    apply_mods(k)
    objs.append(k)
    for s in (1, -1):
        rot = Matrix.Rotation(math.radians(s * 12), 3, "Z")
        lp = ellipsoid_bm((s * 6.6, 1.2, 0.0), (6.8, 4.6, 3.9), rot)
        objs.append(new_obj(f"bow_loop_{'r' if s > 0 else 'l'}", lp))
        dim = ellipsoid_bm((s * 7.6, 1.3, 3.7), (3.4, 1.9, 2.2), rot)
        objs.append(new_obj(f"bow_dimple_{'r' if s > 0 else 'l'}", dim))
        # tail: quad strip with V notch, extruded
        tail = bmesh.new()
        pts = [(s * 0.8, -1.0), (s * 3.8, -0.6), (s * 8.9, -8.4), (s * 7.1, -9.0),
               (s * 5.6, -10.4), (s * 4.6, -9.6), (s * 3.0, -10.8)]
        vs = [tail.verts.new((x, y, 0.0)) for x, y in pts]
        f = tail.faces.new(vs if s > 0 else list(reversed(vs)))
        r = bmesh.ops.extrude_face_region(tail, geom=[f])
        for v in r["geom"]:
            if isinstance(v, bmesh.types.BMVert):
                v.co.z = 2.6
        bmesh.ops.recalc_face_normals(tail, faces=tail.faces[:])
        t = new_obj(f"bow_tail_{'r' if s > 0 else 'l'}", tail)
        bv = t.modifiers.new("bev", "BEVEL")
        bv.width = 0.7
        bv.segments = 3
        bv.limit_method = "ANGLE"
        apply_mods(t)
        objs.append(t)
    return objs


# ----------------------------------------------------------------------------- main
def main():
    reset()
    meshes = {}
    body = new_obj("head_body", head_body_bm())
    meshes["head_body"] = body
    core = new_obj("head_core", head_body_bm(shrink=1.8, nseg=96))
    meshes["head_core"] = core
    meshes["head_core_muzzle"] = new_obj("head_core_muzzle", head_body_bm(shrink=2.2, nseg=80))
    for side, tag in ((1, "r"), (-1, "l")):
        meshes[f"antler_{tag}"] = capsule_chain_obj(f"antler_{tag}", antler_segments(side))
        outer, inner = ear_bms(side)
        meshes[f"ear_{tag}"] = new_obj(f"ear_{tag}", outer)
        meshes[f"earin_{tag}"] = new_obj(f"earin_{tag}", inner)
    for k, bm in muzzle_nose_eyes().items():
        meshes[k] = new_obj(k, bm)
    for ob in bow_objects():
        meshes[ob.name] = ob
    for name, ob in meshes.items():
        export_stl(ob, name)
    # editable source
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "reindeer_character.blend"))
    print("Blender features written:", sorted(meshes))


if __name__ == "__main__":
    main()

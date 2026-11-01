"""
Concept renders (Blender Cycles, CPU, headless).

Renders from build/final/product/*.stl (the exact exported geometry):
    renders/01_front.png 02_side_right.png 03_back.png 04_underside.png 05_three_quarter.png
    renders/06_cutaway_rest.png 07_cutaway_pressed.png 08_exploded.png
Labels are added with Pillow afterwards (renders/*_labelled.png).

Run:  /opt/prvenv/bin/python source/render_blender.py [--fast]
"""
import math
import os
import sys

import bpy  # noqa: E402  (before bmesh / mathutils users)
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from params import *  # noqa: E402,F401,F403

ROOT = os.path.dirname(HERE)
FIN = os.path.join(ROOT, "build", "final", "product")
SEC = os.path.join(ROOT, "build", "final", "section")
CQ = os.path.join(ROOT, "build", "cq")
OUT = os.path.join(ROOT, "renders")
FAST = "--fast" in sys.argv
os.makedirs(OUT, exist_ok=True)
os.makedirs(SEC, exist_ok=True)

PARTS = {  # file -> colour key
    "box_red": "red", "box_white": "white", "cage_white": "white", "bow_white": "white",
    "leg_right_brown": "brown", "leg_right_dark_brown": "dark_brown",
    "leg_left_brown": "brown", "leg_left_dark_brown": "dark_brown",
    "head_brown": "brown", "head_cream": "cream", "head_dark_brown": "dark_brown", "head_black": "black",
}
MOVING = {"head_brown", "head_cream", "head_dark_brown", "head_black", "switch_stem"}
def lin(c):
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


COL = {k: lin(v) for k, v in COLOURS.items()}
COL["switch"] = lin((0.25, 0.25, 0.27))
COL["stem"] = lin((0.85, 0.20, 0.15))


# ----------------------------------------------------------------------------- section geometry (manifold)
def make_sections(plane_x, tag):
    from assemble import load, box, save  # noqa
    d = os.path.join(SEC, tag)
    os.makedirs(d, exist_ok=True)
    half = box(-80, plane_x, -80, 80, -80, 160)
    srcs = {k: os.path.join(FIN, k + ".stl") for k in PARTS}
    srcs["switch_body"] = os.path.join(CQ, "switch_body.stl")
    srcs["switch_stem_up"] = os.path.join(CQ, "switch_stem_up.stl")
    for k, p in srcs.items():
        m = load(p) ^ half
        if not m.is_empty():
            save(m, os.path.join(d, k + ".stl"))
    return d


# ----------------------------------------------------------------------------- scene
def material(key):
    name = "mat_" + key
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    r, g, bl = COL[key]
    b.inputs["Base Color"].default_value = (r, g, bl, 1)
    b.inputs["Roughness"].default_value = 0.42 if key not in ("black",) else 0.25
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.35
    return m


def import_stl(path, key, name=None):
    bpy.ops.wm.stl_import(filepath=path)
    ob = bpy.context.selected_objects[0]
    ob.name = name or os.path.basename(path)[:-4]
    ob.data.materials.clear()
    ob.data.materials.append(material(key))
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
    except Exception:
        bpy.ops.object.shade_smooth()
    return ob


def setup_scene(floor=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 24 if FAST else 96
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.render.resolution_x = 1000 if FAST else 1400
    sc.render.resolution_y = 1000 if FAST else 1400
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.57, 0.60, 1)
    bg.inputs["Strength"].default_value = 0.30
    if floor:
        bpy.ops.mesh.primitive_plane_add(size=900, location=(0, 0, -0.02))
        pl = bpy.context.active_object
        m = bpy.data.materials.new("floor")
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.44, 0.47, 1)
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
        pl.data.materials.append(m)
    for loc, energy, size in (((-120, -160, 200), 0.75e6, 140), ((170, -60, 90), 0.22e6, 120), ((40, 200, 160), 0.4e6, 120)):
        bpy.ops.object.light_add(type="AREA", location=loc)
        L = bpy.context.active_object
        L.data.energy = energy
        L.data.size = size
        L.rotation_euler = (Vector((0, 0, 30)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return sc


def camera(loc, target, lens=85, ortho=None):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.active_object
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 5000
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    bpy.context.scene.camera = cam
    return cam


ANCHORS = {}


def render(name, anchors=None):
    sc = bpy.context.scene
    sc.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    if anchors:
        from bpy_extras.object_utils import world_to_camera_view
        W, Hh = sc.render.resolution_x, sc.render.resolution_y
        pts = {}
        for label, p in anchors.items():
            v = world_to_camera_view(sc, sc.camera, Vector(p))
            pts[label] = [round(v.x * W, 1), round((1 - v.y) * Hh, 1)]
        ANCHORS[name] = pts
        import json
        json.dump(ANCHORS, open(os.path.join(OUT, "_anchors.json"), "w"), indent=1)
    print("rendered", name)


def load_product(offsets=None, press=0.0, section=None, with_switch=False):
    src = section or FIN
    obs = {}
    for k, col in PARTS.items():
        p = os.path.join(src, k + ".stl")
        if not os.path.exists(p):
            continue
        ob = import_stl(p, col, k)
        if k in MOVING:
            ob.location.z -= press
        if offsets and k in offsets:
            ob.location += Vector(offsets[k])
        obs[k] = ob
    if with_switch:
        sb = os.path.join(section or CQ, "switch_body.stl")
        st = os.path.join(section or CQ, "switch_stem_up.stl")
        for p, key, nm in ((sb, "switch", "switch_body"), (st, "stem", "switch_stem")):
            if os.path.exists(p):
                ob = import_stl(p, key, nm)
                if nm == "switch_stem":
                    ob.location.z -= press
                if offsets and nm in offsets:
                    ob.location += Vector(offsets[nm])
                obs[nm] = ob
    return obs


def main():
    sec_mid = make_sections(0.0, "x0")
    sec_leg = make_sections((LEG_TAB_X0 + LEG_TAB_X1) / 2, "xleg")
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    tgt = (0, 0, 33)
    views = [
        ("01_front", (0, -300, 52), tgt, 70),
        ("02_side_right", (300, 0, 52), tgt, 70),
        ("03_back", (0, 300, 52), tgt, 70),
        ("05_three_quarter", (175, -230, 120), (0, 0, 31), 70),
    ]
    for name, loc, t, lens in views:
        if only and name not in only:
            continue
        setup_scene()
        load_product()
        camera(loc, t, lens)
        render(name + ".png")

    if not only or "04_underside" in only:
        setup_scene(floor=False)
        load_product(with_switch=True)
        camera((70, -95, -210), (0, 0, 20), 70)
        render("04_underside.png")

    # cutaways (material with x > plane removed), orthographic from +x
    for name, press, sec in (("06_cutaway_rest", 0.0, sec_mid), ("07_cutaway_pressed", SW_TRAVEL, sec_mid),
                             ("09_cutaway_leg_snap", 0.0, sec_leg)):
        if only and name not in only:
            continue
        setup_scene()
        load_product(press=press, section=sec, with_switch=True)
        camera((300, -2, 34), (0, -2, 34), ortho=84)
        if name == "06_cutaway_rest":
            an = {"Moving head (only moving part)": (0, 6, 46), "Keycap-style socket on the switch stem": (0, 0, 27.3),
                  "MX-compatible switch (type unconfirmed)": (0, 4.5, 22.5),
                  "14.0 mm plate, 1.5 mm thick (switch clips)": (0, 7.4, 18.6),
                  "Clip-relief pocket / pins": (0, 6.5, 12.0),
                  "Fixed leg (snaps into the rim)": (-10.5, -21.5, 32.5),
                  "Present box (fixed base)": (0, 16.9, 6.0), "Ribbon cage (fixed)": (0, 19.0, 24.0),
                  ">= 1.0 mm gap to box, cage & legs": (0, -14.6, 31.5)}
        elif name == "07_cutaway_pressed":
            an = {"Head pressed 4.0 mm (full MX travel)": (0, 6, 42),
                  "Cavity roof 1.6 mm above housing": (0, 4.5, 26.6),
                  "Head bottom 3.0 mm above plate": (0, 8.8, 22.0),
                  "Boss enters switch top (like a keycap)": (0, 0, 24.0),
                  "Still >= 1.0 mm from box & legs": (0, -14.6, 27.5)}
        else:
            xm = (LEG_TAB_X0 + LEG_TAB_X1) / 2
            an = {"Split snap tab with barbs (on leg)": (xm, -15.45, 25.6),
                  "Slot + undercut in thickened rim pad": (xm, -13.4, 21.0),
                  "Leg seats on rim top and front face": (xm, -18.0, 30.0),
                  "Hoof (dark brown)": (xm, -23.5, 23.0),
                  "Head never reaches the leg (>= 1.5 mm)": (xm, -11.0, 36.0)}
        render(name + ".png", an)

    if not only or "08_exploded" in only:
        setup_scene()
        off = {}
        for k in ("head_brown", "head_cream", "head_dark_brown", "head_black"):
            off[k] = (0, 0, 40)
        off["switch_body"] = (0, 0, 17)
        off["switch_stem"] = (0, 0, 17)
        for k in ("leg_right_brown", "leg_right_dark_brown"):
            off[k] = (10, -26, 14)
        for k in ("leg_left_brown", "leg_left_dark_brown"):
            off[k] = (-10, -26, 14)
        off["bow_white"] = (0, -40, 4)
        off["cage_white"] = (62, 30, 0)
        load_product(offsets=off, with_switch=True)
        camera((215, -245, 120), (14, -10, 36), 50)
        render("08_exploded.png", {
            "Head (brown/cream/dark brown/black) - moves": (0, 0, 98),
            "MX-compatible switch": (0, 0, 46),
            "Present box (red, white band)": (17, -17, 16),
            "Fixed legs (snap into rim pads)": (12, -46, 46),
            "Bow (slides onto rail, trapped by hooves)": (0, -61, 21),
            "Ribbon cage (snaps over box)": (80, 30, 26)})


if __name__ == "__main__":
    main()

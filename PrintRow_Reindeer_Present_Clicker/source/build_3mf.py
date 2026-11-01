"""
Write PLAIN (core-spec) 3MF files with lib3mf (3MF Consortium reference library).

Each multi-colour part is ONE components object whose components are the aligned colour meshes
(identity transforms), so slicers load it as one object with several parts and nothing can drift.
Every colour mesh carries a base-material display colour.  No slicer-specific config/metadata is
written (avoids the "invalid configuration" class of errors), only geometry, names and colours.

Plates are laid out for a 256 x 256 mm Bambu bed (centred on 128,128); smaller beds: press Arrange.

Run:  /opt/prvenv/bin/python source/build_3mf.py
"""
import glob
import os
import sys

import lib3mf
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from params import COLOURS  # noqa: E402

ROOT = os.path.dirname(HERE)
STL = os.path.join(ROOT, "exports", "stl")
OUT = os.path.join(ROOT, "exports", "3mf")
os.makedirs(OUT, exist_ok=True)
W = lib3mf.get_wrapper()
BED_C = np.array([128.0, 128.0, 0.0])

NICE = {"red": "Red", "white": "White", "brown": "Brown", "dark_brown": "Dark brown",
        "cream": "Cream", "black": "Black", "grey": "Any colour"}


def tf(t=(0, 0, 0)):
    m = lib3mf.Transform()
    for i in range(4):
        for j in range(3):
            m.Fields[i][j] = 0.0
    m.Fields[0][0] = m.Fields[1][1] = m.Fields[2][2] = 1.0
    m.Fields[3][0], m.Fields[3][1], m.Fields[3][2] = float(t[0]), float(t[1]), float(t[2])
    return m


class Doc:
    def __init__(self):
        self.model = W.CreateModel()
        self.model.SetUnit(lib3mf.ModelUnit.MilliMeter)
        md = self.model.GetMetaDataGroup()
        md.AddMetaData("", "Title", "PrintRow Reindeer Present Clicker", "string", True)
        md.AddMetaData("", "Designer", "PrintRow (original design)", "string", True)
        md.AddMetaData("", "Application", "PrintRow source pipeline (CadQuery + Blender + lib3mf)", "string", True)
        self.mats = self.model.AddBaseMaterialGroup()
        self.mat_idx = {}

    def mat(self, key):
        if key not in self.mat_idx:
            r, g, b = COLOURS.get(key, (0.6, 0.6, 0.6))
            col = W.RGBAToColor(int(r * 255), int(g * 255), int(b * 255), 255)
            self.mat_idx[key] = self.mats.AddMaterial(NICE.get(key, key), col)
        return self.mat_idx[key]

    def mesh(self, name, tm, colour):
        mo = self.model.AddMeshObject()
        mo.SetName(name)
        v = tm.vertices
        verts = [lib3mf.Position((float(a), float(b), float(c))) for a, b, c in v]
        tris = [lib3mf.Triangle((int(a), int(b), int(c))) for a, b, c in tm.faces]
        mo.SetGeometry(verts, tris)
        mo.SetObjectLevelProperty(self.mats.GetResourceID(), self.mat(colour))
        return mo

    def part(self, name, colour_meshes, offset):
        """colour_meshes: list of (colour, trimesh) sharing one coordinate frame."""
        comp = self.model.AddComponentsObject()
        comp.SetName(name)
        for colour, tm in colour_meshes:
            mo = self.mesh(f"{name} - {NICE.get(colour, colour)}", tm, colour)
            comp.AddComponent(mo, tf())
        self.model.AddBuildItem(comp, tf(offset))

    def single(self, name, tm, colour, offset):
        mo = self.mesh(name, tm, colour)
        self.model.AddBuildItem(mo, tf(offset))

    def write(self, fn):
        p = os.path.join(OUT, fn)
        self.model.QueryWriter("3mf").WriteToFile(p)
        return p


def load(path):
    t = trimesh.load(path, force="mesh", process=True)
    t.merge_vertices()
    return t


def centred(meshes):
    """Offset that puts the group's XY centre on the bed centre, z stays (already on z=0)."""
    b = np.vstack([m.bounds for m in meshes])
    c = (b.min(0) + b.max(0)) / 2
    return BED_C - np.array([c[0], c[1], 0.0])


def colour_parts(prefix):
    out = []
    for f in sorted(glob.glob(os.path.join(STL, "product", prefix + "__*.stl"))):
        out.append((os.path.basename(f)[:-4].split("__")[1], load(f)))
    return out


def main():
    written = []
    # A: head (4 colours)
    d = Doc()
    parts = colour_parts("A_head")
    d.part("Reindeer head (moving)", parts, centred([m for _, m in parts]))
    written.append(d.write("PrintRow_Reindeer_A_head_4colour.3mf"))

    # B: box
    d = Doc()
    parts = colour_parts("B_box")
    d.part("Present box (red, white band)", parts, centred([m for _, m in parts]))
    written.append(d.write("PrintRow_Reindeer_B_box_red_white_band.3mf"))

    # C: cage + bow (white)
    d = Doc()
    cage = load(os.path.join(STL, "product", "C_cage__white.stl"))
    bow = load(os.path.join(STL, "product", "C_bow__white.stl"))
    off = centred([cage, bow])
    d.single("Ribbon cage (white)", cage, "white", off)
    d.single("Bow (white)", bow, "white", off)
    written.append(d.write("PrintRow_Reindeer_C_ribbon_cage_and_bow_white.3mf"))

    # D: legs (brown + dark-brown hoof), single-colour option = assign both parts to one filament
    d = Doc()
    lr, ll = colour_parts("D_leg_right"), colour_parts("D_leg_left")
    off = centred([m for _, m in lr + ll])
    d.part("Leg right (fixed)", lr, off)
    d.part("Leg left (fixed)", ll, off)
    written.append(d.write("PrintRow_Reindeer_D_legs.3mf"))

    # T: test kit
    d = Doc()
    tk = {os.path.basename(f)[:-4]: load(f) for f in sorted(glob.glob(os.path.join(STL, "test_kit", "*.stl")))}
    layout = {"test_switch_coupon": (-22, 0), "test_cap": (14, 0), "test_leg_slot_block": (44, 0),
              "test_leg_right_single_colour": (44, -26)}
    x = -20
    for k in sorted(tk):
        if k.startswith("test_socket_gauge"):
            layout[k] = (x, -34)
            x += 15
    x = -26
    for k in sorted(tk):
        if k.startswith("test_plate_gauge"):
            layout[k] = (x, 36)
            x += 24
    for k, (px, py) in layout.items():
        m = tk[k]
        c = (m.bounds[0] + m.bounds[1]) / 2
        d.single(k.replace("test_", "TEST ").replace("_", " "), m, "grey",
                 BED_C + np.array([px - c[0], py - c[1], 0.0]))
    written.append(d.write("PrintRow_Reindeer_T_fit_and_movement_test_kit.3mf"))

    # Assembly preview (product coordinates; NOT a print plate)
    d = Doc()
    fin = os.path.join(ROOT, "build", "final", "product")
    groups = {
        "PREVIEW head": [("brown", "head_brown"), ("cream", "head_cream"), ("dark_brown", "head_dark_brown"),
                         ("black", "head_black")],
        "PREVIEW box": [("red", "box_red"), ("white", "box_white")],
        "PREVIEW cage": [("white", "cage_white")],
        "PREVIEW bow": [("white", "bow_white")],
        "PREVIEW leg right": [("brown", "leg_right_brown"), ("dark_brown", "leg_right_dark_brown")],
        "PREVIEW leg left": [("brown", "leg_left_brown"), ("dark_brown", "leg_left_dark_brown")],
    }
    for name, lst in groups.items():
        d.part(name, [(c, load(os.path.join(fin, f + ".stl"))) for c, f in lst], BED_C)
    written.append(d.write("PrintRow_Reindeer_ASSEMBLY_PREVIEW_not_for_printing.3mf"))
    for p in written:
        print("wrote", os.path.relpath(p, ROOT), os.path.getsize(p), "bytes")


if __name__ == "__main__":
    main()

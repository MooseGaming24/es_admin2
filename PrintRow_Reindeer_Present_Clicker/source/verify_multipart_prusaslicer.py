"""
INTERNAL verification (not a deliverable): prove the aligned colour parts slice as ONE multi-part
object in an independent slicer, and count real tool changes.

PrusaSlicer's CLI cannot answer the GUI question "load as a single object with multiple parts?",
so this script writes PrusaSlicer-native 3MF copies (single mesh + Metadata/Slic3r_PE_model.config
volume ranges, one extruder per colour) into build/slice/, then slices them with a 4-extruder,
single-nozzle (AMS-like) wipe-tower profile and counts tool changes in the G-code.

The purge/wipe-tower grams are PrusaSlicer's, NOT Bambu Studio's flush volumes.
Run:  /opt/prvenv/bin/python source/verify_multipart_prusaslicer.py
"""
import glob
import json
import os
import re
import subprocess
import zipfile

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "exports", "stl", "product")
OUT = os.path.join(ROOT, "build", "slice")
CFG = os.path.join(ROOT, "source", "slicer", "prusaslicer_bambu_like_0.4_PLA.ini")
os.makedirs(OUT, exist_ok=True)

ORDER = ["brown", "cream", "dark_brown", "black", "red", "white"]

CT = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
      '<Default Extension="config" ContentType="text/plain"/></Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        '</Relationships>')


def write_native(prefixes, path):
    objs = []
    for pre in prefixes:
        parts = {os.path.basename(f)[:-4].split("__")[1]: trimesh.load(f)
                 for f in sorted(glob.glob(os.path.join(EXP, pre + "__*.stl")))}
        objs.append((pre, parts))
    # one shared placement: centre each object, keep relative z/xy inside the object
    model = ['<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>']
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>']
    items = []
    used = set()
    for oid, (pre, parts) in enumerate(objs, start=1):
        allb = np.vstack([m.bounds for m in parts.values()])
        c = (allb.min(0) + allb.max(0)) / 2
        V, F, ranges = [], [], []
        for colour in sorted(parts, key=ORDER.index):
            m = parts[colour]
            base = sum(len(v) for v in V)
            t0 = sum(len(f) for f in F)
            V.append(m.vertices - [c[0], c[1], 0])
            F.append(m.faces + base)
            ranges.append((colour, t0, t0 + len(m.faces) - 1))
            used.add(colour)
        V, F = np.vstack(V), np.vstack(F)
        model.append(f'<object id="{oid}" type="model"><mesh><vertices>')
        model.extend(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{d:.5f}"/>' for a, b, d in V)
        model.append('</vertices><triangles>')
        model.extend(f'<triangle v1="{a}" v2="{b}" v3="{d}"/>' for a, b, d in F)
        model.append('</triangles></mesh></object>')
        dx = 128 + (oid - 1) * 40 - (len(objs) - 1) * 20
        items.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {dx} 128 0"/>')
        cfg.append(f'<object id="{oid}" instances_count="1"><metadata type="object" key="name" value="{pre}"/>')
        for colour, a, b in ranges:
            ext = ORDER.index(colour) + 1
            cfg.append(f'<volume firstid="{a}" lastid="{b}"><metadata type="volume" key="name" value="{colour}"/>'
                       f'<metadata type="volume" key="volume_type" value="ModelPart"/>'
                       f'<metadata type="volume" key="extruder" value="{ext}"/></volume>')
        cfg.append('</object>')
    model.append('</resources><build>' + "".join(items) + '</build></model>')
    cfg.append('</config>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CT)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", "".join(model))
        z.writestr("Metadata/Slic3r_PE_model.config", "\n".join(cfg))
    return used


def mmu_cfg():
    n = len(ORDER)
    kv = {}
    for ln in open(CFG):
        if "=" in ln and not ln.lstrip().startswith("#"):
            k, v = ln.split("=", 1)
            kv[k.strip()] = v.strip()
    kv.update({
        "single_extruder_multi_material": "1", "wipe_tower": "1", "wipe_tower_x": "20",
        "use_relative_e_distances": "1", "layer_gcode": "G92 E0",
        "wipe_tower_y": "200", "wipe_tower_width": "40",
        "nozzle_diameter": ",".join(["0.4"] * n), "filament_diameter": ",".join(["1.75"] * n),
        "filament_density": ",".join(["1.24"] * n), "filament_type": ",".join(["PLA"] * n),
        "temperature": ",".join(["220"] * n), "first_layer_temperature": ",".join(["220"] * n),
        "retract_length": ",".join(["0.8"] * n),
        "extruder_colour": "#9E6038;#F2E0BC;#54301C;#0F0F0F;#CC1419;#F5F5F0",
    })
    p = os.path.join(OUT, "mmu.ini")
    open(p, "w").write("".join(f"{k} = {v}\n" for k, v in kv.items()))
    return p


def main():
    rep = {}
    cfg = mmu_cfg()
    for name, pres in (("head", ["A_head"]), ("box", ["B_box"]), ("legs", ["D_leg_right", "D_leg_left"])):
        p3 = os.path.join(OUT, f"internal_prusaslicer_native_{name}.3mf")
        write_native(pres, p3)
        g = os.path.join(OUT, f"mmu_{name}.gcode")
        r = subprocess.run(["prusa-slicer", "--export-gcode", "--load", cfg, "-o", g, p3],
                           capture_output=True, text=True)
        entry = {"returncode": r.returncode}
        if r.returncode == 0:
            txt = open(g).read()
            lines = txt.splitlines()
            tools = [ln for ln in lines if re.match(r"^T\d+\s*$", ln)]
            changes = max(0, len(tools) - 1)
            entry.update({
                "layers": sum(1 for ln in lines if ln.startswith(";LAYER_CHANGE")),
                "tool_changes": changes,
                "filament_used_g": re.search(r"^; filament used \[g\] = (.*)$", txt, re.M).group(1),
                "total_filament_g": (re.search(r"^; total filament used \[g\] = (.*)$", txt, re.M) or
                                     re.search(r"^; filament used \[g\] = (.*)$", txt, re.M)).group(1),
                "wipe_tower_g_PrusaSlicer": (re.search(r"^; total filament used for wipe tower \[g\] = (.*)$", txt, re.M)
                                             or re.search(r"wipe tower \[g\] = (.*)$", txt, re.M) or [None, "n/a"])[1]
                if re.search(r"wipe tower \[g\]", txt) else "n/a",
            })
        else:
            entry["log_tail"] = (r.stdout + r.stderr)[-600:]
            # PrusaSlicer 2.7.2 segfaults on some wipe-tower runs; retry without the tower so the
            # multi-part slice and tool-change count are still verified (purge grams then n/a)
            nw = cfg.replace(".ini", "_nowipe.ini")
            open(nw, "w").write(open(cfg).read().replace("wipe_tower = 1", "wipe_tower = 0"))
            r2 = subprocess.run(["prusa-slicer", "--export-gcode", "--load", nw, "-o", g, p3],
                                capture_output=True, text=True)
            entry["retry_without_wipe_tower_returncode"] = r2.returncode
            if r2.returncode == 0:
                txt = open(g).read()
                lines = txt.splitlines()
                tools = [ln for ln in lines if re.match(r"^T\d+\s*$", ln)]
                entry.update({"layers": sum(1 for ln in lines if ln.startswith(";LAYER_CHANGE")),
                              "tool_changes": max(0, len(tools) - 1),
                              "filament_used_g": re.search(r"^; filament used \[g\] = (.*)$", txt, re.M).group(1),
                              "wipe_tower_g_PrusaSlicer": "n/a (tower disabled after crash)"})
        rep[name] = entry
    json.dump(rep, open(os.path.join(ROOT, "reports", "prusaslicer_multipart_check.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()

"""
Independent read-back verification of every exported 3MF and STL (digital checks only).

3MF:  lib3mf reader (3MF Consortium)  -> objects, components, triangle counts, manifold+oriented flag
      trimesh 3MF loader (independent) -> geometry count, total volume, bounds
STL:  trimesh -> watertight, winding, volume, bounds

Run:  /opt/prvenv/bin/python source/verify_exports.py
"""
import glob
import json
import os

import lib3mf
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lib3mf.get_wrapper()


def check_3mf(path):
    m = W.CreateModel()
    r = m.QueryReader("3mf")
    r.SetStrictModeActive(True)
    r.ReadFromFile(path)
    warnings = [r.GetWarning(i)[1] for i in range(r.GetWarningCount())]
    res = {"lib3mf_warnings": warnings, "objects": []}
    it = m.GetObjects()
    tri_total = 0
    while it.MoveNext():
        o = it.GetCurrentObject()
        if o.IsMeshObject():
            mo = m.GetMeshObjectByID(o.GetResourceID())
            n = mo.GetTriangleCount()
            tri_total += n
            res["objects"].append({"name": mo.GetName(), "type": "mesh", "triangles": n,
                                   "vertices": mo.GetVertexCount(),
                                   "manifold_and_oriented": bool(mo.IsManifoldAndOriented())})
        elif o.IsComponentsObject():
            co = m.GetComponentsObjectByID(o.GetResourceID())
            res["objects"].append({"name": co.GetName(), "type": "components",
                                   "components": co.GetComponentCount()})
    bi = m.GetBuildItems()
    n_items = 0
    while bi.MoveNext():
        n_items += 1
    res["build_items"] = n_items
    res["triangles_total"] = tri_total
    res["all_meshes_manifold"] = all(o.get("manifold_and_oriented", True) for o in res["objects"])
    sc = trimesh.load(path)
    geoms = sc.geometry if hasattr(sc, "geometry") else {"m": sc}
    res["trimesh_geometries"] = len(geoms)
    res["trimesh_total_volume_mm3"] = round(sum(abs(g.volume) for g in geoms.values()), 1)
    res["trimesh_bounds"] = [[round(float(x), 2) for x in row] for row in sc.bounds]
    res["trimesh_total_volume_mm3"] = float(res["trimesh_total_volume_mm3"])
    res["has_geometry"] = bool(tri_total > 0 and res["trimesh_total_volume_mm3"] > 0)
    return res


def main():
    rep = {"3mf": {}, "stl": {}}
    for p in sorted(glob.glob(os.path.join(ROOT, "exports", "3mf", "*.3mf"))):
        rep["3mf"][os.path.basename(p)] = check_3mf(p)
    for p in sorted(glob.glob(os.path.join(ROOT, "exports", "stl", "*", "*.stl"))):
        t = trimesh.load(p)
        rep["stl"][os.path.relpath(p, os.path.join(ROOT, "exports", "stl"))] = {
            "watertight": bool(t.is_watertight), "winding_consistent": bool(t.is_winding_consistent),
            "volume_mm3": round(float(t.volume), 2), "triangles": int(len(t.faces)),
            "bounds": [[round(float(x), 2) for x in row] for row in t.bounds]}
    json.dump(rep, open(os.path.join(ROOT, "reports", "export_verification.json"), "w"), indent=1)
    for k, v in rep["3mf"].items():
        print(f"{k:58s} geometry={v['has_geometry']} meshes_manifold={v['all_meshes_manifold']} "
              f"items={v['build_items']} tris={v['triangles_total']} trimesh_geoms={v['trimesh_geometries']} "
              f"vol={v['trimesh_total_volume_mm3']} warn={len(v['lib3mf_warnings'])}")
    bad = [k for k, v in rep["stl"].items() if not (v["watertight"] and v["winding_consistent"] and v["volume_mm3"] > 0)]
    print(f"STL files: {len(rep['stl'])}, failing: {bad}")


if __name__ == "__main__":
    main()

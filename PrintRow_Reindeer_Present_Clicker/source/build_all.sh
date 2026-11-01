#!/usr/bin/env bash
# Rebuild every PrintRow Reindeer Present Clicker output from the editable sources.
#   PY=/path/to/python-with-bpy-cadquery ./source/build_all.sh [--no-render]
# Requires: bpy 5.2.x, cadquery 2.8, manifold3d, trimesh, lib3mf, lxml, matplotlib (Python 3.13 venv),
#           prusa-slicer 2.7 (independent slicing check), optional: assimp-utils + f3d (viewer check).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-/opt/prvenv/bin/python}

echo "[1/9] mechanism (CadQuery)";          $PY source/mechanism_cq.py
echo "[2/9] character (Blender bpy)";        $PY source/character_blender.py > build/blender_log.txt 2>&1
echo "[3/9] assembly + colour split";        $PY source/assemble.py > /dev/null
echo "[4/9] clearance sweep";                $PY source/check_clearance.py > /dev/null
echo "[5/9] printability screen";            $PY source/check_printability.py > /dev/null
echo "[6/9] colour-change estimate";         $PY source/estimate_colour_changes.py > /dev/null
echo "[7/9] plain 3MF";                      $PY source/build_3mf.py
echo "[8/9] export verification";            $PY source/verify_exports.py
$PY source/verify_multipart_prusaslicer.py > /dev/null || true

echo "[9/9] independent slicer check (PrusaSlicer)"
mkdir -p build/slice
CFG=source/slicer/prusaslicer_bambu_like_0.4_PLA.ini
$PY - <<'EOF'
import sys, glob; sys.path.insert(0, "source")
from assemble import load, union, save, clean
save(clean(union([load(f) for f in glob.glob("exports/stl/product/A_head__*.stl")])), "build/slice/head_merged_for_estimate.stl")
save(clean(union([load(f) for f in glob.glob("exports/stl/product/B_box__*.stl")])), "build/slice/box_merged_for_estimate.stl")
EOF
: > reports/prusaslicer_check.txt
slice () {  # $1 input, $2 name, extra args...
  local in=$1 name=$2; shift 2
  if prusa-slicer --export-gcode --load $CFG "$@" -o build/slice/$name.gcode "$in" > build/slice/$name.log 2>&1; then
    { echo "== $name  (input: $in)  RESULT: sliced OK"
      grep -E "^; (filament used \[g\]|filament used \[mm\]|estimated printing time \(normal mode\))" build/slice/$name.gcode
      echo "; layers: $(grep -c '^;LAYER_CHANGE' build/slice/$name.gcode)"; } >> reports/prusaslicer_check.txt
  else
    { echo "== $name  (input: $in)  RESULT: PrusaSlicer refused"; tail -3 build/slice/$name.log; } >> reports/prusaslicer_check.txt
  fi
}
slice exports/3mf/PrintRow_Reindeer_A_head_4colour.3mf                 A_head_3mf_as_loaded
slice build/slice/head_merged_for_estimate.stl                         A_head_merged       --center 128,128
slice exports/3mf/PrintRow_Reindeer_B_box_red_white_band.3mf           B_box_3mf_as_loaded
slice build/slice/box_merged_for_estimate.stl                          B_box_merged        --center 128,128
slice exports/3mf/PrintRow_Reindeer_C_ribbon_cage_and_bow_white.3mf    C_cage_bow
slice exports/3mf/PrintRow_Reindeer_D_legs.3mf                         D_legs
slice exports/3mf/PrintRow_Reindeer_T_fit_and_movement_test_kit.3mf    T_test_kit
cat reports/prusaslicer_check.txt

if command -v assimp >/dev/null && command -v f3d >/dev/null; then
  mkdir -p build/viewer reports/viewer_check
  for f in exports/3mf/*.3mf; do
    n=$(basename "$f" .3mf)
    assimp export "$f" build/viewer/$n.obj > /dev/null 2>&1 && \
    timeout 120 xvfb-run -a f3d build/viewer/$n.obj --output reports/viewer_check/assimp_f3d_$n.png \
        --resolution 800,800 --up +Z --camera-direction=0.6,1,-0.5 > /dev/null 2>&1 && echo "viewer OK: $n" || echo "viewer FAILED: $n"
  done
fi

if [[ "${1:-}" != "--no-render" ]]; then
  echo "[render] Blender Cycles concept renders"; $PY source/render_blender.py > build/render_log.txt 2>&1
  $PY source/label_renders.py
fi
echo "done"

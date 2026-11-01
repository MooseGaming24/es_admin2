# Originality, third-party components and tool licences

## Originality
* All product geometry in this folder was created from scratch by the scripts in `source/`:
  CadQuery for the mechanism, box, legs, cage and test kit; Blender (bpy) for the head features and bow;
  manifold3d for the booleans.
* The owner-supplied image (`reference/visual_reference_owner_supplied.png`) was used **only as a visual reference** for the
  theme (a reindeer peeking out of a red present with a white ribbon). No geometry was traced, imported or measured from it.
* **No geometry from the PrintRow Santa clicker, 3DGOB, 3DeepDesigns or any other designer was opened, downloaded or used.**
  The licensed clicker ZIPs in Google Drive were deliberately not opened.
* No third-party 3D models, meshes, textures or fonts are embedded in the deliverable STL/3MF/STEP files.

## Third-party physical component
| Component | Source | Licence / notes |
|---|---|---|
| Mechanical keyboard switch (MX-compatible, type to be confirmed) | Purchased by PrintRow | Commercial off-the-shelf part. The mount only follows the publicly documented MX plate-mount interface (14 mm cutout, 1.5 mm plate). No supplier CAD files were used. |

## Software used (not distributed with the product files)
| Tool | Version | Source | Licence |
|---|---|---|---|
| Blender, as the `bpy` Python module | 5.2.3 LTS | PyPI package published by the Blender Foundation | GPL-2.0-or-later |
| CadQuery | 2.8.0 | PyPI (official) | Apache-2.0 |
| OpenCascade (via cadquery-ocp) | bundled | PyPI | LGPL-2.1 with exception |
| manifold3d | 3.5.4 | PyPI (official) | Apache-2.0 |
| trimesh | 5.2.0 | PyPI | MIT |
| lib3mf (3MF Consortium) | 2.5.0 | PyPI (official) | BSD-2-Clause |
| PrusaSlicer (independent slicing check) | 2.7.2 | Ubuntu 24.04 archive | AGPL-3.0 |
| Open Asset Import Library (`assimp`, independent 3MF reader) | Ubuntu 24.04 | Ubuntu archive | BSD-3-Clause |
| F3D viewer | 2.2.1 | Ubuntu 24.04 archive | BSD-3-Clause |
| DejaVu Sans font (render labels only) | system | Ubuntu archive | Bitstream Vera / public-domain-style licence |

Output files produced with these tools belong to PrintRow. GPL/AGPL terms apply to the tools themselves,
not to models made with them.

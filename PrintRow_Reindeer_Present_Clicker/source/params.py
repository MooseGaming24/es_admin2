"""
PrintRow Reindeer Present Clicker - shared design parameters (single source of truth).

Units: millimetres.  Coordinate system (assembled product):
    x = right, y = towards the BACK (the face looks towards -y), z = up, z=0 = desk.
    The switch is centred on x=0, y=0.

All switch numbers are for an MX-compatible switch and are UNCONFIRMED for the
owner's actual switch (see docs/SWITCH_NOTES.md).  Everything that touches the
switch is a parameter here so it can be tuned after the fit test.
"""

# ---------------------------------------------------------------- switch (MX-compatible, nominal)
SW_CUTOUT = 14.00          # square plate hole. Cherry MX spec: 14.00 +/-0.05
SW_PLATE_T = 1.50          # plate thickness the clips are designed for (1.5 +/-0.1)
SW_CLIP_RELIEF = 15.80     # pocket width directly under the plate (room for the clips)
SW_BELOW_PLATE = 5.00      # housing below plate top (plate top -> PCB plane)
SW_PIN_LEN = 3.30          # contact pins below housing (18.5 total - 15.2 body)
SW_POCKET_DEPTH = 10.00    # pocket depth below plate TOP (5.0 housing + 3.3 pins + 1.7 spare)
SW_HOUSING_TOP = 6.60      # top of housing above plate top (11.6 body - 5.0)
SW_HOUSING_W = 15.60       # top housing envelope (conservative square)
SW_STEM_TOP = 10.20        # stem top above plate top, unpressed (15.2 - 5.0)
SW_TRAVEL = 4.00           # total travel (MX nominal)
SW_TRAVEL_CHECK = 4.50     # travel used for clearance checks (adds 0.5 margin)

# ---------------------------------------------------------------- head socket (keycap-style)
STEM_SLOT_W = 1.35         # cross-slot width   (gauges: 1.25 / 1.35 / 1.45)
STEM_SLOT_L = 4.15         # cross-slot length  (gauges: 4.05 / 4.15 / 4.25)
SOCKET_DEPTH = 3.20        # cross depth. < stem protrusion (3.6) so the stem top seats on the socket roof
BOSS_D = 5.50              # boss OD. Must fit the switch top opening (MX keycap boss is 5.5)
BOSS_ENTRY_CHAMFER = 0.35  # chamfer at socket mouth (first-layer squish)
HEAD_CAVITY_W = 17.60      # square cavity in head around the switch housing (1.0 per side)
HEAD_CAVITY_CEIL = 12.20   # cavity roof above plate top -> 1.6 mm over housing at full travel

# ---------------------------------------------------------------- present box (red)
BOX_W = 36.0               # outer footprint, square
BOX_R = 5.0                # vertical corner radius
BOX_H = 30.0               # rim height (z of rim top)
WALL = 2.2
FLOOR = 2.6                # 1.35 mm remains above the ribbon channel
TOP_EDGE_FILLET = 0.6
BOTTOM_CHAMFER = 0.5
PLATE_Z = 19.0             # z of switch plate TOP  -> head bottom at 26.0 (4 mm inside the rim)
PILLAR_W = SW_CLIP_RELIEF + 2 * 1.9
PUSH_HOLE_D = 5.0          # through-hole under the switch (sound + access)

# derived switch heights in product coordinates
Z_STEM_TOP = PLATE_Z + SW_STEM_TOP
Z_HOUSING_TOP = PLATE_Z + SW_HOUSING_TOP
HEAD_Z0 = Z_STEM_TOP - SOCKET_DEPTH        # head bottom plane = boss bottom (26.0)
Z_CAVITY_CEIL = PLATE_Z + HEAD_CAVITY_CEIL

# ---------------------------------------------------------------- head envelope (brown)
HEAD_RC = 14.0             # pedestal radius inside the box (wall inner at 15.8 -> 1.8 gap)
HEAD_C = (0.0, 0.5, 42.0)  # ellipsoid centre
HEAD_A = (15.5, 14.5, 14.0)  # ellipsoid semi-axes x,y,z

# ---------------------------------------------------------------- legs (fixed to box)
LEG_X0, LEG_X1 = 7.0, 14.0         # leg occupies |x| in [7, 14]
LEG_PAD_X0, LEG_PAD_X1 = 7.6, 14.4  # thickened wall pad that receives the tab
LEG_PAD_INNER_Y = -12.9            # inner face of pad (wall inner face is -15.8)
LEG_TAB_X0, LEG_TAB_X1 = 9.0, 12.4  # tab width 3.4
LEG_TAB_Y = -15.45                 # tab centre (in the pad)
LEG_TAB_T = 2.0                    # tab thickness (two 0.7 prongs + 0.6 split)
LEG_TAB_DEPTH = 6.5
LEG_SLOT_CLEAR = 0.15              # per side
LEG_BARB = 0.35
LEG_BARB_Z = (3.4, 5.4)            # barb band below rim top
FIT_CLEAR = 0.15                   # general seat clearance between printed parts

# ---------------------------------------------------------------- ribbon cage (white)
CAGE_T = 1.2
CAGE_GAP = 0.15
STRAP_W = 6.0
RING_Z = (10.5, 16.5)      # horizontal ribbon band (now printed as a white layer band ON the box)
BAND_OUT = 1.35            # band stands 1.35 proud of the box = flush with the cage straps
CAP_T = 1.0                # cap over rim (sides + back only; no front cap -> muzzle room)
CAP_REACH = 1.25           # cap reaches 1.25 mm onto the 2.2 mm wall (strap flex to fit ~1.4 mm)
CHANNEL_D = 1.25           # cross-shaped ribbon channel in the box bottom (cage cross is 1.2 thick)
ROOF_CHAMFER = 2.5         # 45-degree chamfer round the head cavity roof (cuts the bridge to 12.6 mm)

# bow rail (dovetail) on the front strap
RAIL_Z = (8.0, 17.0)
RAIL_H = 1.5               # rail height off the strap face
RAIL_W_ROOT = 2.6
RAIL_W_TOP = 3.6
RAIL_CLEAR = 0.15

# ---------------------------------------------------------------- clearance policy
CLEAR_MIN = 1.0            # minimum head-to-fixed clearance through the whole stroke
TILT_DEG = 1.5             # off-centre press tilt allowance checked in the sweep

# ---------------------------------------------------------------- colours (display only)
COLOURS = {  # sRGB 0..1 (suggested filament look-alikes; display only)
    "red": (0.80, 0.08, 0.10),
    "white": (0.96, 0.96, 0.94),
    "brown": (0.62, 0.38, 0.22),
    "dark_brown": (0.33, 0.19, 0.11),
    "cream": (0.95, 0.88, 0.74),
    "black": (0.06, 0.06, 0.06),
}

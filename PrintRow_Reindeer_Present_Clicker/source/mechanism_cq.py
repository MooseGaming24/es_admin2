"""
PrintRow Reindeer Present Clicker - mechanism & base parts (CadQuery).

Builds, in PRODUCT coordinates (see params.py):
    box            red present body with switch pillar/plate, leg pads + snap slots, cage notches
    leg_right/left fixed front legs (snap tab into the rim pads)
    cage           white ribbon cage (band + 4 straps + rim caps + snap tabs + bow dovetail rail)
    head_cavity_cutter, head_socket_cutter   boolean tools applied to the Blender head
    switch_dummy_up / switch_dummy_down      MX-style envelope for renders and the sweep
and the test kit in its own print coordinates.

Run:  /opt/prvenv/bin/python source/mechanism_cq.py
Writes STEP (editable B-rep) to exports/step and intermediate STL to build/cq/.
"""
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from params import *  # noqa: E402,F401,F403

ROOT = os.path.dirname(HERE)
BUILD = os.path.join(ROOT, "build", "cq")
STEP = os.path.join(ROOT, "exports", "step")
os.makedirs(BUILD, exist_ok=True)
os.makedirs(STEP, exist_ok=True)

H = BOX_W / 2.0
FILLETS = []


def rbox(w, d, h, r, z0=0.0):
    """Rounded-corner (vertical edges) box centred on x,y."""
    return (cq.Workplane("XY").workplane(offset=z0)
            .sketch().rect(w, d).vertices().fillet(r).finalize()
            .extrude(h))


def blk(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def yz_prism(pts, x0, x1):
    """Polygon in the (y,z) plane extruded from x0 to x1."""
    wp = cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)
    return wp


# ---------------------------------------------------------------------------- box
def make_box():
    outer = rbox(BOX_W, BOX_W, BOX_H, BOX_R)
    outer = outer.faces(">Z").edges().fillet(TOP_EDGE_FILLET)
    outer = outer.faces("<Z").edges().chamfer(BOTTOM_CHAMFER)
    inner = rbox(BOX_W - 2 * WALL, BOX_W - 2 * WALL, BOX_H, BOX_R - WALL, z0=FLOOR)
    box = outer.cut(inner)

    # switch pillar + plate
    pillar = rbox(PILLAR_W, PILLAR_W, PLATE_Z - FLOOR + 0.01, 1.5, z0=FLOOR - 0.01)
    box = box.union(pillar)
    relief = blk(-SW_CLIP_RELIEF / 2, SW_CLIP_RELIEF / 2, -SW_CLIP_RELIEF / 2, SW_CLIP_RELIEF / 2,
                 PLATE_Z - SW_POCKET_DEPTH, PLATE_Z - SW_PLATE_T)
    hole = blk(-SW_CUTOUT / 2, SW_CUTOUT / 2, -SW_CUTOUT / 2, SW_CUTOUT / 2,
               PLATE_Z - SW_PLATE_T - 0.01, PLATE_Z + 1)
    push = (cq.Workplane("XY").circle(PUSH_HOLE_D / 2).extrude(PLATE_Z - SW_POCKET_DEPTH + 1)
            .translate((0, 0, -0.5)))
    box = box.cut(relief).cut(hole).cut(push)

    # leg pads on the inside of the front wall (45-degree underside, no supports)
    pad_drop = LEG_TAB_DEPTH + 2.0
    for s in (1, -1):
        x0, x1 = sorted((s * LEG_PAD_X0, s * LEG_PAD_X1))
        yw = -(H - WALL) - 0.6
        pts = [(yw, BOX_H - 0.01), (LEG_PAD_INNER_Y, BOX_H - 0.01),
               (LEG_PAD_INNER_Y, BOX_H - pad_drop),
               (yw, BOX_H - pad_drop - (yw - LEG_PAD_INNER_Y) * -1)]
        pad = yz_prism(pts, x0, x1)
        # keep the pad inside the outer shell outline
        pad = pad.intersect(rbox(BOX_W - 0.4, BOX_W - 0.4, BOX_H, BOX_R))
        box = box.union(pad)

        # snap slot with undercut for the barbs
        tx0, tx1 = sorted((s * LEG_TAB_X0, s * LEG_TAB_X1))
        c = LEG_SLOT_CLEAR
        half = LEG_TAB_T / 2 + c
        slot = blk(tx0 - c, tx1 + c, LEG_TAB_Y - half, LEG_TAB_Y + half,
                   BOX_H - LEG_TAB_DEPTH - 0.5, BOX_H + 1)
        under = blk(tx0 - c, tx1 + c, LEG_TAB_Y - half - LEG_BARB, LEG_TAB_Y + half + LEG_BARB,
                    BOX_H - LEG_TAB_DEPTH - 0.5, BOX_H - LEG_BARB_Z[0] + 0.05)
        lead = (cq.Workplane("XY").rect(tx1 - tx0 + 2 * c + 0.8, 2 * half + 0.8)
                .workplane(offset=-0.4).rect(tx1 - tx0 + 2 * c, 2 * half).loft()
                .translate(((tx0 + tx1) / 2, LEG_TAB_Y, BOX_H + 0.001)))
        box = box.cut(slot).cut(under).cut(lead)

    # horizontal ribbon band (white colour band, z = RING_Z): proud ring with a 45-degree underside,
    # interrupted where the cage straps pass (the gaps also locate the straps)
    z0, z1 = RING_Z
    bo = BAND_OUT
    def rr_wire(w, r, z):
        wr = cq.Workplane("XY").workplane(offset=z).rect(w, w).val()
        return wr.fillet2D(r, wr.Vertices())

    band = cq.Workplane("XY").add(cq.Solid.makeLoft([rr_wire(BOX_W - 0.2, BOX_R - 0.1, z0),
                                                     rr_wire(BOX_W + 2 * bo, BOX_R + bo, z0 + bo + 0.1)]))
    band = band.union(rbox(BOX_W + 2 * bo, BOX_W + 2 * bo, z1 - z0 - bo, BOX_R + bo, z0 + bo))
    band = band.cut(rbox(BOX_W - 1.0, BOX_W - 1.0, 40, BOX_R - 0.5, z0 - 5))
    gw = STRAP_W / 2 + 0.2
    band = band.cut(blk(-gw, gw, -40, 40, z0 - 1, z1 + 1)).cut(blk(-40, 40, -gw, gw, z0 - 1, z1 + 1))
    try:
        band = band.faces(">Z").edges().fillet(0.4)
    except Exception:
        pass
    box = box.union(band)

    # cross-shaped ribbon channel in the bottom (the cage's under-strap sits flush in it)
    hw = STRAP_W / 2 + 0.2
    box = box.cut(blk(-hw, hw, -H - 1, H + 1, -1, CHANNEL_D))
    box = box.cut(blk(-H - 1, H + 1, -hw, hw, -1, CHANNEL_D))
    return box


# ---------------------------------------------------------------------------- legs
LEG_ROUND = 1.2   # edge round applied in assemble.py by Minkowski sum with a sphere


def leg_profile_wire():
    y_out = -H                      # outer face of box
    y_in = -13.6                    # inner end of the leg (stays out of head path)
    z_r = BOX_H
    seat = [(y_in + 0.6, z_r), (y_out + 0.7, z_r), (y_out, z_r - 0.7), (y_out, 21.6)]
    curve = [(-19.2, 20.75), (-21.4, 20.55), (-23.4, 21.4), (-24.35, 23.3), (-24.2, 25.6),
             (-23.5, 27.6), (-23.2, 30.0), (-22.4, 32.6), (-20.6, 34.2), (-18.2, 34.75),
             (-15.8, 34.45), (-14.1, 33.4), (-13.45, 31.9), (y_in, z_r + 0.6)]
    return (cq.Workplane("YZ", origin=(LEG_X0 + LEG_ROUND, 0, 0))
            .moveTo(*seat[0]).lineTo(*seat[1]).lineTo(*seat[2]).lineTo(*seat[3])
            .spline(curve, includeCurrent=True).close())


def make_leg(side=1):
    """Returns (core, tab, groove) for the right leg (side=+1) or mirrored left leg.

    core   : profile eroded by LEG_ROUND and extruded LEG_ROUND inside both x faces.
             assemble.py adds a sphere(LEG_ROUND) Minkowski sum -> exact seats, rounded edges.
    tab    : snap tab with split prongs and barbs (kept sharp).
    groove : cloven-hoof groove cutter.
    """
    z_r = BOX_H
    core = (leg_profile_wire().offset2D(-LEG_ROUND, kind="arc")
            .extrude(LEG_X1 - LEG_X0 - 2 * LEG_ROUND))
    xm = (LEG_X0 + LEG_X1) / 2
    groove = blk(xm - 0.45, xm + 0.45, -26, -22.6, 20.0, 25.0)

    # snap tab: two prongs with barbs
    t = LEG_TAB_T
    tab = blk(LEG_TAB_X0, LEG_TAB_X1, LEG_TAB_Y - t / 2, LEG_TAB_Y + t / 2,
              z_r - LEG_TAB_DEPTH, z_r + 0.6)
    split = blk(LEG_TAB_X0 - 1, LEG_TAB_X1 + 1, LEG_TAB_Y - 0.3, LEG_TAB_Y + 0.3,
                z_r - LEG_TAB_DEPTH - 1, z_r - 1.5)
    tab = tab.cut(split)
    for sy in (1, -1):
        yb = LEG_TAB_Y + sy * t / 2
        za, zb = z_r - LEG_BARB_Z[1], z_r - LEG_BARB_Z[0]
        pts = [(yb - sy * 0.01, za), (yb + sy * LEG_BARB, zb - 0.6), (yb + sy * LEG_BARB, zb),
               (yb - sy * 0.01, zb)]
        tab = tab.union(yz_prism(pts, LEG_TAB_X0, LEG_TAB_X1))
    tip = yz_prism([(LEG_TAB_Y - t / 2 - 1, z_r - LEG_TAB_DEPTH - 0.01),
                    (LEG_TAB_Y - t / 2 + 0.45, z_r - LEG_TAB_DEPTH - 0.01),
                    (LEG_TAB_Y - t / 2 - 1, z_r - LEG_TAB_DEPTH + 1.45)], LEG_TAB_X0 - 1, LEG_TAB_X1 + 1)
    tip2 = tip.mirror("XZ", basePointVector=(0, LEG_TAB_Y, 0))
    tab = tab.cut(tip).cut(tip2)
    if side < 0:
        core, tab, groove = core.mirror("YZ"), tab.mirror("YZ"), groove.mirror("YZ")
    return core, tab, groove


# ---------------------------------------------------------------------------- cage
def make_cage():
    g, t = CAGE_GAP, CAGE_T
    cage = None
    hs = STRAP_W / 2
    o, i = H + g + t, H + g
    # front strap stops below the rim (no front cap: leaves room for the muzzle)
    cage = blk(-hs, hs, -o, -i, 0, BOX_H - 1.2)
    # back, left, right straps with rim caps
    cage = cage.union(blk(-hs, hs, i, o, 0, BOX_H + CAP_T))
    cage = cage.union(blk(-o, -i, -hs, hs, 0, BOX_H + CAP_T))
    cage = cage.union(blk(i, o, -hs, hs, 0, BOX_H + CAP_T))
    ci = H - CAP_REACH
    cage = cage.union(blk(-hs, hs, ci, o, BOX_H + 0.02, BOX_H + CAP_T))
    cage = cage.union(blk(-o, -ci, -hs, hs, BOX_H + 0.02, BOX_H + CAP_T))
    cage = cage.union(blk(ci, o, -hs, hs, BOX_H + 0.02, BOX_H + CAP_T))
    # ribbon cross under the box (flush in the box channel): big first layer, rigid cage, no brim
    cage = cage.union(blk(-hs, hs, -o, o, 0, CHANNEL_D - 0.05))
    cage = cage.union(blk(-o, o, -hs, hs, 0, CHANNEL_D - 0.05))
    # keep the switch push hole reachable from underneath (and let the click out)
    cage = cage.cut(cq.Workplane("XY").circle(PUSH_HOLE_D / 2 + 0.5).extrude(5).translate((0, 0, -1)))

    # dovetail rail for the bow on the front strap
    y0 = -o
    rail = (cq.Workplane("XY")
            .polyline([(-RAIL_W_ROOT / 2, y0 + 0.01), (RAIL_W_ROOT / 2, y0 + 0.01),
                       (RAIL_W_TOP / 2, y0 - RAIL_H), (-RAIL_W_TOP / 2, y0 - RAIL_H)]).close()
            .extrude(RAIL_Z[1] - RAIL_Z[0]).translate((0, 0, RAIL_Z[0])))
    # 45-degree ends on the rail
    rail = rail.cut(yz_prism([(y0 - RAIL_H - 1, RAIL_Z[1] - 0.8), (y0 - RAIL_H - 1, RAIL_Z[1] + 1),
                              (y0 - RAIL_H + 1.0 + 0.8, RAIL_Z[1] + 1)], -3, 3))
    cage = cage.union(rail)
    return cage


# ---------------------------------------------------------------------------- bow interface (cutter for the bow back)
def make_bow_groove_cutter():
    """Dovetail groove cut into the bow back, in PRODUCT coordinates.  Closed at the top."""
    c = RAIL_CLEAR
    y0 = -(H + CAGE_GAP + CAGE_T)
    g = (cq.Workplane("XY")
         .polyline([(-RAIL_W_ROOT / 2 - c, y0 + 0.5), (RAIL_W_ROOT / 2 + c, y0 + 0.5),
                    (RAIL_W_TOP / 2 + c, y0 - RAIL_H - c), (-RAIL_W_TOP / 2 - c, y0 - RAIL_H - c)]).close()
         .extrude(RAIL_Z[1] - RAIL_Z[0] + 20).translate((0, 0, RAIL_Z[1] - (RAIL_Z[1] - RAIL_Z[0] + 20))))
    return g


# ---------------------------------------------------------------------------- head interface cutters
def make_head_cutters():
    z0 = HEAD_Z0
    w = HEAD_CAVITY_W
    cav = blk(-w / 2, w / 2, -w / 2, w / 2, z0 - 2, Z_CAVITY_CEIL - ROOF_CHAMFER + 0.01)
    roof = (cq.Workplane("XY").rect(w, w).workplane(offset=ROOF_CHAMFER)
            .rect(w - 2 * ROOF_CHAMFER, w - 2 * ROOF_CHAMFER).loft()
            .translate((0, 0, Z_CAVITY_CEIL - ROOF_CHAMFER)))
    cav = cav.union(roof)
    # mouth chamfer (elephant foot)
    mouth = (cq.Workplane("XY").rect(HEAD_CAVITY_W + 1.0, HEAD_CAVITY_W + 1.0)
             .workplane(offset=0.5).rect(HEAD_CAVITY_W, HEAD_CAVITY_W).loft()
             .translate((0, 0, z0 - 0.001)))
    boss = cq.Workplane("XY").circle(BOSS_D / 2).extrude(Z_CAVITY_CEIL - z0 + 6).translate((0, 0, z0 - 3))
    # root fillet for the boss: a cone collar near the roof stays as material
    collar = (cq.Workplane("XY").circle(BOSS_D / 2).workplane(offset=1.7).circle(BOSS_D / 2 + 1.7).loft()
              .translate((0, 0, Z_CAVITY_CEIL - 1.2)))
    cavity_cutter = cav.union(mouth).cut(boss).cut(collar)

    sl, sw = STEM_SLOT_L, STEM_SLOT_W
    cross = (cq.Workplane("XY").rect(sl, sw).extrude(SOCKET_DEPTH + 1)
             .union(cq.Workplane("XY").rect(sw, sl).extrude(SOCKET_DEPTH + 1))
             .translate((0, 0, z0 - 1)))
    cham = (cq.Workplane("XY").circle(sl / 2 + BOSS_ENTRY_CHAMFER).workplane(offset=BOSS_ENTRY_CHAMFER)
            .circle(sl / 2).loft().translate((0, 0, z0 - 0.001)))
    socket_cutter = cross.union(cham)
    return cavity_cutter, socket_cutter


# ---------------------------------------------------------------------------- switch dummy (MX-like envelope)
def make_switch(pressed=0.0):
    zp = PLATE_Z
    body = blk(-7, 7, -7, 7, zp - SW_BELOW_PLATE, zp)
    top = (cq.Workplane("XY").rect(SW_HOUSING_W, SW_HOUSING_W).workplane(offset=SW_HOUSING_TOP)
           .rect(11.6, 11.6).loft().translate((0, 0, zp)))
    sw = body.union(top)
    pins = (cq.Workplane("XY").pushPoints([(-3.8, 2.5), (2.5, 5.0)]).circle(0.75)
            .extrude(SW_PIN_LEN).translate((0, 0, zp - SW_BELOW_PLATE - SW_PIN_LEN)))
    post = cq.Workplane("XY").circle(2.0).extrude(2.0).translate((0, 0, zp - SW_BELOW_PLATE - 2.0))
    sw = sw.union(pins).union(post)
    zt = zp + SW_STEM_TOP - pressed
    stem = (cq.Workplane("XY").rect(4.0, 1.17).extrude(3.6)
            .union(cq.Workplane("XY").rect(1.17, 4.0).extrude(3.6))
            .translate((0, 0, zt - 3.6)))
    slider = blk(-2.8, 2.8, -2.8, 2.8, zt - 3.6 - 4.0, zt - 3.6)
    stem = stem.union(slider)
    return sw, stem


# ---------------------------------------------------------------------------- test kit (own coordinates, z=0 bed)
def make_test_kit(box, cavity_cutter, socket_cutter):
    kit = {}
    # 1) switch coupon: the real pillar/plate/pocket (cut from the real box) on a small base
    zcut = PLATE_Z - SW_POCKET_DEPTH - 1.2
    pil = box.intersect(blk(-PILLAR_W / 2 - 0.01, PILLAR_W / 2 + 0.01, -PILLAR_W / 2 - 0.01, PILLAR_W / 2 + 0.01,
                            zcut, PLATE_Z + 0.01))
    base = rbox(PILLAR_W + 8, PILLAR_W + 8, 1.6, 3.0, zcut)
    cp = pil.union(base)
    cp = cp.cut(cq.Workplane("XY").circle(PUSH_HOLE_D / 2).extrude(30).translate((0, 0, zcut - 1)))
    # front marker notch on the base
    cp = cp.cut(blk(-1.0, 1.0, -PILLAR_W / 2 - 4.5, -PILLAR_W / 2 - 2.5, zcut - 1, zcut + 3))
    kit["test_switch_coupon"] = cp.translate((0, 0, -zcut))

    # 1b) leg-slot block: the real rim segment with one pad + snap slot (for one printed leg)
    zb = BOX_H - 11.0
    lb = box.intersect(blk(LEG_PAD_X0 - 2.0, LEG_PAD_X1 + 0.5, -H - 0.1, LEG_PAD_INNER_Y + 0.01, zb, BOX_H + 1))
    kit["test_leg_slot_block"] = lb.translate((0, 0, -zb))

    # 2) movement test cap: real head pedestal (r=14) with the real cavity, boss, socket
    z0 = HEAD_Z0
    cap = cq.Workplane("XY").circle(HEAD_RC).extrude(Z_CAVITY_CEIL - z0 + 4.0).translate((0, 0, z0))
    cap = cap.faces(">Z").edges().fillet(2.0)
    cap = cap.cut(cavity_cutter).cut(socket_cutter)
    # front marker notch (points to -y = front)
    cap = cap.cut(blk(-1, 1, -HEAD_RC - 1, -HEAD_RC + 1.2, Z_CAVITY_CEIL + 1.5, Z_CAVITY_CEIL + 5))
    kit["test_cap"] = cap.translate((0, 0, -z0))

    # 3) stem-socket gauges: 3 widths, marked 1/2/3 notches
    for n, w in enumerate((1.25, 1.35, 1.45), start=1):
        g = cq.Workplane("XY").circle(5.5).extrude(8.0)
        g = g.faces(">Z").edges().fillet(1.0)
        cr = (cq.Workplane("XY").rect(STEM_SLOT_L, w).extrude(SOCKET_DEPTH)
              .union(cq.Workplane("XY").rect(w, STEM_SLOT_L).extrude(SOCKET_DEPTH)).translate((0, 0, -0.01)))
        ch = (cq.Workplane("XY").circle(STEM_SLOT_L / 2 + 0.35).workplane(offset=0.35)
              .circle(STEM_SLOT_L / 2).loft().translate((0, 0, -0.01)))
        g = g.cut(cr).cut(ch)
        for k in range(n):
            g = g.cut(blk(-0.5, 0.5, 4.6, 6.0, 7.0 - 1.6 * k - 1.0, 7.0 - 1.6 * k))
        kit[f"socket_gauge_{n}_w{w:.2f}"] = g

    # 4) plate gauges 13.90 / 14.00 / 14.10 / 14.20 marked 1..4 edge notches
    for n, c in enumerate((13.90, 14.00, 14.10, 14.20), start=1):
        p = rbox(21, 21, SW_PLATE_T, 2.0)
        p = p.cut(blk(-c / 2, c / 2, -c / 2, c / 2, -1, 3))
        for k in range(n):
            p = p.cut(blk(-8 + 2.2 * k, -7 + 2.2 * k, 9.5, 11, -1, 3))
        kit[f"plate_gauge_{n}_{c:.2f}"] = p
    return kit


def export(obj, name, step=True):
    cq.exporters.export(obj, os.path.join(BUILD, name + ".stl"), tolerance=0.01, angularTolerance=0.1)
    if step:
        cq.exporters.export(obj, os.path.join(STEP, name + ".step"))


if __name__ == "__main__":
    box = make_box()
    export(box, "box")
    for sd, nm in ((1, "right"), (-1, "left")):
        core, tab, groove = make_leg(sd)
        export(core, f"leg_{nm}_core", step=False)
        export(tab, f"leg_{nm}_tab", step=False)
        export(groove, f"leg_{nm}_groove", step=False)
    export(make_cage(), "cage")
    export(make_bow_groove_cutter(), "bow_groove_cutter", step=False)
    cav, sock = make_head_cutters()
    export(cav, "head_cavity_cutter", step=False)
    export(sock, "head_socket_cutter", step=False)
    for p, tag in ((0.0, "up"), (SW_TRAVEL, "down")):
        sw, stem = make_switch(p)
        export(sw, "switch_body", step=False)
        export(stem, f"switch_stem_{tag}", step=False)
    for k, v in make_test_kit(box, cav, sock).items():
        export(v, "test_" + k if not k.startswith("test_") else k)
    print("CadQuery parts written to", BUILD)

"""Add titles, callouts and a disclaimer to the Blender renders, and build an overview sheet."""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "renders")
TITLES = {
    "01_front": "Front", "02_side_right": "Side (right)", "03_back": "Back",
    "04_underside": "Underside (ribbon cross, switch push hole)", "05_three_quarter": "Three-quarter",
    "06_cutaway_rest": "Cutaway at x = 0 - at rest", "07_cutaway_pressed": "Cutaway at x = 0 - pressed 4.0 mm",
    "08_exploded": "Exploded assembly", "09_cutaway_leg_snap": "Cutaway through a leg snap",
}
FOOT = "PrintRow Reindeer Present Clicker - digital concept render (not a photo of a print)"


def font(sz, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def label(name, anchors):
    src = os.path.join(R, name + ".png")
    if not os.path.exists(src):
        return None
    im = Image.open(src).convert("RGB")
    W, H = im.size
    pad_top, pad_bot = 70, 46
    side = 560 if anchors else 0
    canvas = Image.new("RGB", (W + side, H + pad_top + pad_bot), (250, 250, 248))
    canvas.paste(im, (0, pad_top))
    d = ImageDraw.Draw(canvas)
    d.text((24, 18), TITLES.get(name, name), fill=(30, 30, 30), font=font(34, True))
    d.text((24, H + pad_top + 12), FOOT, fill=(90, 90, 90), font=font(20))
    if anchors:
        items = sorted(anchors.items(), key=lambda kv: kv[1][1])
        n = len(items)
        for i, (txt, (x, y)) in enumerate(items):
            ty = pad_top + 60 + i * (H - 120) / max(1, n - 1)
            tx = W + 20
            d.line([(x, y + pad_top), (W + 10, ty)], fill=(20, 20, 20), width=2)
            d.ellipse([x - 6, y + pad_top - 6, x + 6, y + pad_top + 6], outline=(20, 20, 20), width=3,
                      fill=(255, 210, 0))
            d.multiline_text((tx, ty - 14), txt.replace(" (", "\n("), fill=(20, 20, 20), font=font(21))
    out = os.path.join(R, name + "_labelled.png")
    canvas.save(out)
    return out


def main():
    anchors = json.load(open(os.path.join(R, "_anchors.json"))) if os.path.exists(os.path.join(R, "_anchors.json")) else {}
    for n in TITLES:
        label(n, anchors.get(n + ".png"))
    # overview sheet: 4 views + hero
    names = ["01_front", "02_side_right", "03_back", "04_underside", "05_three_quarter", "08_exploded"]
    ims = [Image.open(os.path.join(R, n + ".png")).convert("RGB") for n in names if os.path.exists(os.path.join(R, n + ".png"))]
    if ims:
        s = 600
        sheet = Image.new("RGB", (3 * s, 2 * s + 60), (250, 250, 248))
        d = ImageDraw.Draw(sheet)
        for i, (n, im) in enumerate(zip(names, ims)):
            im = im.resize((s, s))
            x, y = (i % 3) * s, 60 + (i // 3) * s
            sheet.paste(im, (x, y))
            d.text((x + 12, y + 10), TITLES[n], fill=(20, 20, 20), font=font(24, True))
        d.text((14, 14), "PrintRow Reindeer Present Clicker - concept renders (digital, prototype stage)",
               fill=(20, 20, 20), font=font(28, True))
        sheet.save(os.path.join(R, "00_overview_sheet.png"))
    print("labelled renders written")


if __name__ == "__main__":
    main()

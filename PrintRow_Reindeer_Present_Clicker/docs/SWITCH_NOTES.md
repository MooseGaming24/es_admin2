# Switch notes: what is known, what is assumed, what I need from you

## 1. What I searched (1 Nov 2026)

| Source | Result |
|---|---|
| This workspace (`es_admin2` repo, whole container) | No PrintRow, clicker, STL/3MF or switch information. The repo is an unrelated FiveM admin script. |
| Google Drive: "PrintRow \| eBay Listing Drafts, Pricing & Descriptions" | Clicker listings say only "mechanical keyboard switch" / "mechanical keyboard-style switch". No brand, model, colour or dimensions. |
| Google Drive: social plan, licence register, teaser shot list, first-customer plan | Mention clickers (3DeepDesigns, 3DGOB Santa Clicker) but not the switch. |
| Google Drive: 3DeepDesigns clicker ZIPs (15–77 MB each) | Not opened. They are too large for the Drive connector, and they are another designer's licensed files. |
| Google Drive: product photos | No readable text, and no switch is identifiable. |
| Gmail (for a switch purchase receipt) | Could not search: the Gmail connector needs you to sign in again. |

**Result: the exact switch type is NOT confirmed.** I have not assumed a brand or model.

## 2. What the design assumes (adjustable)

The clickers you already sell use "mechanical keyboard switches". By far the most common family is the
**MX-compatible** footprint (Cherry MX, Gateron, Kailh BOX/Pro, Outemu, Akko, etc.), so the
mount is built around that footprint. **Every value below is a parameter** in `source/params.py`.

| Parameter | Value used | Basis |
|---|---|---|
| Plate cutout `SW_CUTOUT` | 14.00 mm square | Cherry MX spec 14.00 ± 0.05 mm (corroborated by search results; datasheet pages could not be opened from this session) |
| Plate thickness `SW_PLATE_T` | 1.50 mm | MX clips are designed for 1.5 ± 0.1 mm |
| Clip-relief pocket `SW_CLIP_RELIEF` | 15.80 mm | 0.9 mm per side under the plate for the clips |
| Plate top to bottom of housing `SW_BELOW_PLATE` | 5.0 mm | MX: plate top to PCB = 5 mm |
| Pin length `SW_PIN_LEN` | 3.3 mm | 18.5 mm overall height minus 15.2 mm body |
| Pocket depth below plate top | 10.0 mm | Housing + pins + 1.7 mm spare (fits 3-pin and 5-pin switches) |
| Housing top above plate `SW_HOUSING_TOP` | 6.6 mm | 11.6 mm body above PCB minus 5 mm |
| Stem top above plate `SW_STEM_TOP` | 10.2 mm | 15.2 mm body+stem minus 5 mm |
| Travel `SW_TRAVEL` | 4.0 mm (checked to 4.5 mm) | MX nominal |
| Cross socket `STEM_SLOT_L × STEM_SLOT_W` | 4.15 × 1.35 mm, 3.2 mm deep | Typical printed-keycap socket (gauges 1.25 / 1.35 / 1.45 mm wide in the test kit) |
| Boss OD `BOSS_D` | 5.5 mm | Standard keycap boss; it enters the switch top at the bottom of the stroke, like a keycap |

The search corroborated the plate cutout, plate thickness, 5 mm plate-to-PCB and 18.5 mm overall height. The 11.6 mm body
height appeared only as a code comment in a third-party model. The derived stem heights must be confirmed by
the fit test. If you send the measurements listed below, I can change the parameters and rebuild in one run.

**Not compatible without a redesign:** low-profile switches (e.g. Kailh Choc v1: 13.8 × 13.8 mm cutout,
3 mm travel, twin-rail stem) and Alps-style switches.

## 3. What I need from you (any one of these settles it)

1. The **exact switch name** from the bag, listing or receipt (e.g. "Gateron Yellow Pro 3.0 5-pin", "Outemu Blue 3-pin").
2. Or **photos**: the switch from the top, from the side next to a ruler, and the bottom (pins visible).
3. Or **calliper measurements**, with the switch sitting in a 1.5 mm plate:
   * plate top to housing top;
   * plate top to stem top (unpressed);
   * housing width at the plate and at the top;
   * stem cross arm width and length;
   * total travel (press fully and measure the stem drop);
   * housing depth below the plate, and pin length.
4. Whether it is **3-pin or 5-pin**. Both fit; the pocket is open underneath.

## 4. What the fit test will tell you (before you print the full product)

* **Plate gauges 1–4** (13.90 / 14.00 / 14.10 / 14.20 mm): which one the switch snaps into firmly and holds.
  If it is not 14.00, change `SW_CUTOUT`.
* **Socket gauges 1–3** (cross 1.25 / 1.35 / 1.45 mm wide): which one pushes on firmly but can be pulled
  off by hand. If it is not gauge 2, change `STEM_SLOT_W`.
* **Switch coupon + test cap**: press 50 times. The click must be crisp, the cap must not touch
  the coupon or the housing, and it must return fully. If the cap bottoms on the housing before the switch
  clicks, the stem is shorter than assumed. Send the measurements and I will adjust `SW_STEM_TOP` / `SOCKET_DEPTH`.

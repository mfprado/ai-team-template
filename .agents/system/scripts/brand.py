#!/usr/bin/env python3
"""Save the company's brand for the team: colours, font and logo.

  sh .agents/system/bin/py .agents/system/scripts/brand.py \
      --primary "#0B5FFF" [--background "#FFFFFF"] [--text "#1A1A1A"] [--font sans|serif] \
      [--logo "<image file>"] [--font-family "Montserrat"] [--font-file "<font file>" ...]

Writes, in the team's settings (shared with the team like any other change):
- .agents/brand.json         colours and font
- .agents/brand/logo-source.<ext>   the logo exactly as given: the only logo file shared with the team
- .agents/brand/logo.png, icon.png, icon.ico   made from it on each computer (not shared): the
  logo as PNG, a square icon (Mac folder icon) and the same icon for Windows
- .agents/brand/fonts/       the company's font files, when it provides them (.woff2, .woff, .ttf, .otf)

--font-family is the company's own typeface, as its design guide names it. The team page, the
flow diagrams, the apps and the reports use it: from its files when given, else from Google
Fonts. --font (sans or serif) is what to fall back to when it cannot load.

Making the PNG and the icons needs Pillow. Without it (e.g. while creating the team, before the
launcher has installed anything), the next launch makes them (setup.py, which runs with Pillow).

Every launch then uses them (setup.py): the team page's colours and the folder's icon.
Prints what it wrote, as JSON.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BRAND = ROOT / ".agents/brand.json"
FOLDER = ROOT / ".agents/brand"
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def colour(value):
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    if not HEX.match(value):
        raise argparse.ArgumentTypeError(f"'{value}' is not a colour like #0B5FFF")
    return value.upper()


def make_icons(logo, background):
    """logo.png, icon.png and icon.ico from any logo file Pillow reads. Raises ImportError without Pillow."""
    from PIL import Image

    image = Image.open(logo).convert("RGBA")
    FOLDER.mkdir(parents=True, exist_ok=True)
    image.save(FOLDER / "logo.png")
    # Square canvas with a small margin, so wide logos are not cut off.
    side = 512
    canvas = Image.new("RGBA", (side, side), background or (0, 0, 0, 0))
    image.thumbnail((int(side * 0.86), int(side * 0.86)), Image.LANCZOS)
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2), image)
    canvas.save(FOLDER / "icon.png")
    canvas.save(FOLDER / "icon.ico", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--primary", type=colour, required=True, help="main brand colour (buttons, highlights)")
    parser.add_argument("--background", type=colour, help="page background")
    parser.add_argument("--text", type=colour, help="text colour")
    parser.add_argument("--font", choices=["sans", "serif"], default="sans")
    parser.add_argument("--logo", help="logo image file (PNG, JPG, ...)")
    parser.add_argument("--font-family", help="the company's typeface, as its design guide names it")
    parser.add_argument("--font-file", action="append", default=[], help="a font file the company provides (repeatable)")
    args = parser.parse_args()

    brand = {"primary": args.primary, "font": args.font}
    if args.background:
        brand["background"] = args.background
    if args.text:
        brand["text"] = args.text
    if args.font_family:
        family = args.font_family.strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 \-]{0,60}", family):
            print(json.dumps({"error": f"'{family}' is not a typeface name like Montserrat or Open Sans."}))
            return 1
        brand["font_family"] = family
    fonts = FOLDER / "fonts"
    for font_file in args.font_file:
        source = Path(font_file).expanduser()
        if not source.is_file() or source.suffix.lower() not in (".woff2", ".woff", ".ttf", ".otf"):
            print(json.dumps({"error": f"'{source}' is not a font file (.woff2, .woff, .ttf or .otf)."}))
            return 1
        fonts.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, fonts / source.name)
    if args.logo:
        logo = Path(args.logo).expanduser()
        if not logo.is_file():
            print(json.dumps({"error": f"The logo file was not found: {logo}"}))
            return 1
        icons_later = False
        # The logo as given is what the team shares; the PNG and icons are made from it per computer.
        FOLDER.mkdir(parents=True, exist_ok=True)
        for old in FOLDER.glob("logo-source.*"):
            old.unlink()
        source = FOLDER / f"logo-source{logo.suffix.lower()}"
        shutil.copyfile(logo, source)
        try:
            make_icons(source, args.background)
        except ImportError:
            icons_later = True  # no Pillow here: the next launch makes them
        except OSError as e:
            print(json.dumps({"error": f"The logo could not be read as an image ({e})."}))
            return 1
        brand["logo"] = ".agents/brand/logo.png"
    BRAND.parent.mkdir(parents=True, exist_ok=True)
    BRAND.write_text(json.dumps(brand, indent=2) + "\n", encoding="utf-8")
    written = [str(BRAND.relative_to(ROOT))] + ([str(FOLDER.relative_to(ROOT))] if args.logo or args.font_file else [])
    result = {"brand": brand, "paths": written}
    if args.logo and icons_later:
        result["icons"] = "made on the next launch"
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())

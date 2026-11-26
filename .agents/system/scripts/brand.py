#!/usr/bin/env python3
"""Save the company's brand for the team: colours, font and logo.

  sh .agents/system/bin/py .agents/system/scripts/brand.py \
      --primary "#0B5FFF" [--background "#FFFFFF"] [--text "#1A1A1A"] [--font sans|serif] \
      [--logo "<image file>"]

Writes, in the team's settings (shared with the team like any other change):
- .agents/brand.json         colours and font
- .agents/brand/logo.png     the logo as given (converted to PNG)
- .agents/brand/icon.png     a square icon (Mac folder icon)
- .agents/brand/icon.ico     the same icon for Windows

Making the PNG and the icons needs Pillow. Without it (e.g. while creating the team, before the
launcher has installed anything), the logo is kept as given in .agents/brand/logo-source.<ext>
and the next launch makes the rest (setup.py, which runs with Pillow).

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
    args = parser.parse_args()

    brand = {"primary": args.primary, "font": args.font}
    if args.background:
        brand["background"] = args.background
    if args.text:
        brand["text"] = args.text
    if args.logo:
        logo = Path(args.logo).expanduser()
        if not logo.is_file():
            print(json.dumps({"error": f"The logo file was not found: {logo}"}))
            return 1
        icons_later = False
        try:
            make_icons(logo, args.background)
            for old in FOLDER.glob("logo-source.*"):
                old.unlink()
        except ImportError:
            # No Pillow here: keep the logo as given; the next launch makes the PNG and the icons.
            FOLDER.mkdir(parents=True, exist_ok=True)
            for old in FOLDER.glob("logo-source.*"):
                old.unlink()
            shutil.copyfile(logo, FOLDER / f"logo-source{logo.suffix.lower()}")
            icons_later = True
        except OSError as e:
            print(json.dumps({"error": f"The logo could not be read as an image ({e})."}))
            return 1
        brand["logo"] = ".agents/brand/logo.png"
    BRAND.parent.mkdir(parents=True, exist_ok=True)
    BRAND.write_text(json.dumps(brand, indent=2) + "\n", encoding="utf-8")
    written = [str(BRAND.relative_to(ROOT))] + ([str(FOLDER.relative_to(ROOT))] if args.logo else [])
    result = {"brand": brand, "paths": written}
    if args.logo and icons_later:
        result["icons"] = "made on the next launch"
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())

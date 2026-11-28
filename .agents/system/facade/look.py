"""The team page's look, made from the company's brand (.agents/brand.json).

Colours come from the brand (or flow_page.DEFAULT); type is the company's own typeface when the
brand names it (font_family, with its files in .agents/brand/fonts/ or from Google Fonts),
else Bricolage Grotesque, or Newsreader when the brand asks for a serif. The one bold element is the request to paste for each skill,
set large in the page's type on a wash of the brand colour: asking the AI in your own words is
what the page is about. Everything else stays quiet.
"""

import base64
import html
import json
import os
from pathlib import Path

from flow_page import company_font, mix, on, palette

BRAND_DIR = Path(__file__).resolve().parents[2] / "brand"


def is_dark_brand(brand):
    """True when the brand's own page is dark (light text on a dark background)."""
    return on(palette(brand)["background"]) == "#FFFFFF"


def in_mode(brand, dark):
    """The brand in night (dark=True) or day colours. The brand's own look is one of the two;
    the other swaps background and text, with the background a deep shade of the text colour."""
    if dark == is_dark_brand(brand):
        return brand
    c = palette(brand)
    if dark:
        return {**brand, "background": mix(c["text"], "#000000", 0.35), "text": c["background"]}
    return {**brand, "background": mix(c["text"], "#FFFFFF", 0.92), "text": c["background"]}


def chosen_mode(brand):
    """The brand in the mode the address asks for (?mode=night or ?mode=day). The team page sets it,
    and passes it to the apps it opens, so they follow the person's choice too."""
    try:
        import streamlit as st
        mode = st.query_params.get("mode")
    except Exception:  # not running inside Streamlit
        mode = None
    return in_mode(brand, mode == "night") if mode in ("night", "day") else brand


def tokens(brand):
    c = palette(chosen_mode(brand))
    light = on(c["background"]) != "#FFFFFF"
    return {
        **c,
        "card": "#FFFFFF" if light else mix(c["background"], c["text"], 0.06),
        "panel": mix(c["background"], c["text"], 0.035),
        "wash": mix(c["background"], c["primary"], 0.12 if light else 0.2),
        "rule": mix(c["background"], c["text"], 0.13),
    }


BACK = {"en": "← Back to the team page", "es": "← Volver a la página del equipo"}
COPY = {"en": "Copy", "es": "Copiar"}
COPIED = {"en": "Copied!", "es": "¡Copiado!"}


def team_language():
    try:
        return json.loads((BRAND_DIR.parent / "team.json").read_text(encoding="utf-8")).get("language", "en")
    except (OSError, ValueError):
        return "en"


def back_link():
    """A link back to the team page, for apps started from it (run_app.py sets TEAM_PAGE_URL).

    The team page itself never has TEAM_PAGE_URL, so it shows no link."""
    url = os.environ.get("TEAM_PAGE_URL", "")
    if not url.startswith("http://localhost:"):
        return ""
    try:
        language = json.loads((BRAND_DIR.parent / "team.json").read_text(encoding="utf-8")).get("language", "en")
    except (OSError, ValueError):
        language = "en"
    return (f'<a class="team-back" href="{html.escape(url)}" target="_self">'
            f'{BACK.get(language, BACK["en"])}</a>')


def loading_css():
    """While the page works, Streamlit shows its own running icon (top right). Show the company's
    logo instead, gently pulsing; without a logo, a dot in the brand colour does the same."""
    logo = BRAND_DIR / "logo.png"
    try:
        picture = f"url(data:image/png;base64,{base64.b64encode(logo.read_bytes()).decode()})"
        mark = f"background:{picture} center / contain no-repeat;"
    except OSError:
        mark = "background:var(--accent); border-radius:50%; transform:scale(.55);"
    return f"""
/* Loading: the company's logo instead of Streamlit's running icon */
[data-testid="stStatusWidget"] img {{ display:none !important; }}
[data-testid="stStatusWidget"] > div:first-child {{ display:flex; align-items:center; gap:.5rem; }}
[data-testid="stStatusWidget"] > div:first-child::before {{ content:""; display:block; flex:none; width:1.6rem;
  height:1.6rem; {mark} animation:brand-loading 1.1s ease-in-out infinite; }}
@keyframes brand-loading {{
  0%, 100% {{ opacity:.45; transform:scale(.82); }}
  50% {{ opacity:1; transform:scale(1); }}
}}
"""


def css(brand):
    k = tokens(brand)
    font_css, font = company_font(brand, BRAND_DIR)
    return f"""<style>
{font_css}
:root {{ --ink:{k['text']}; --paper:{k['background']}; --accent:{k['primary']}; --on-accent:{k['on_primary']};
  --wash:{k['wash']}; --rule:{k['rule']}; --muted:{k['muted']}; --card:{k['card']}; --panel:{k['panel']}; }}

/* Type: one family, its optical size doing the work */
html, body, [data-testid="stApp"], [data-testid="stMarkdownContainer"], button, input, textarea, select,
[data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"], h1, h2, h3, h4, h5, h6, [data-testid="stHeading"] *
{{ font-family:{font} !important; }}
[data-testid="stApp"] {{ background:var(--paper); color:var(--ink); }}
[data-testid="stMarkdownContainer"] p {{ line-height:1.55; max-width:68ch; }}
h1 {{ font-size:2.75rem !important; font-weight:720 !important; letter-spacing:-0.025em; line-height:1.05 !important;
  font-variation-settings:'opsz' 96; padding-bottom:.35rem !important; }}
h2, h3 {{ font-weight:650 !important; letter-spacing:-0.01em; font-variation-settings:'opsz' 48; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color:var(--muted) !important; opacity:1 !important;
  font-size:.92rem; }}
p code, li code, label code {{ color:var(--muted) !important; background:var(--wash) !important; border-radius:5px;
  font-size:.78em !important; }}
[data-testid="stDecoration"], [data-testid="stAppDeployButton"] {{ display:none !important; }}
[data-testid="stHeader"] {{ background:transparent !important; }}
[data-testid="stHeading"]:has(h1) {{ margin-bottom:1rem; }}
hr {{ border-color:var(--rule) !important; }}

/* Sidebar: the team's identity, then the sections as a list */
[data-testid="stSidebar"] {{ background:var(--panel); border-right:1px solid var(--rule); }}
.team-name {{ font-size:1.9rem; font-weight:760; letter-spacing:-0.025em; line-height:1.05; margin:.2rem 0 .35rem;
  font-variation-settings:'opsz' 96; color:var(--ink); }}
.champion {{ color:var(--muted); font-size:.9rem; margin-bottom:.9rem; }}
.sync {{ display:flex; gap:.5rem; align-items:baseline; font-size:.88rem; color:var(--muted); margin:.4rem 0 .2rem; }}
.sync .dot {{ width:.55rem; height:.55rem; border-radius:50%; flex:none; transform:translateY(-.05rem); }}
.sync.ok .dot {{ background:#2E9E5B; }} .sync.warn .dot {{ background:#D98A1C; }}
.st-key-menu button {{ justify-content:flex-start; border:0 !important; background:transparent !important;
  color:var(--ink) !important; border-radius:8px; padding:.5rem .75rem; min-height:2.4rem; }}
.st-key-menu button > div {{ justify-content:flex-start; }}
.st-key-menu button:hover {{ background:var(--wash) !important; }}
.st-key-artmenu-folded, .st-key-docsmenu-folded {{ display:none; }}
.st-key-artmenu, .st-key-docsmenu {{ padding-left:.6rem; gap:.1rem !important; border-left:1px solid var(--rule); margin-left:1rem; width:calc(100% - 1rem) !important; box-sizing:border-box; }}
.st-key-artmenu [data-testid="stCaptionContainer"], .st-key-docsmenu [data-testid="stCaptionContainer"] {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; margin:.5rem 0 0 .6rem; }}
.st-key-artmenu button, .st-key-docsmenu button {{ min-height:2rem !important; padding:.2rem .6rem !important; }}
.st-key-artmenu button p {{ font-size:.88rem !important; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.st-key-menu [data-testid="stBaseButton-primary"] {{ background:var(--wash) !important; font-weight:650;
  box-shadow:inset 3px 0 0 var(--accent); }}
.st-key-menu [data-testid="stBaseButton-primary"] p {{ font-weight:650; }}

/* The logo: an app icon */
[class*="st-key-to-perms-"] button {{ color:var(--accent) !important; padding:0 !important; min-height:0; font-size:.88rem; }}
[class*="st-key-to-perms-"] button:hover {{ text-decoration:underline; }}
/* The hidden frame that runs the copy feedback takes no room */
[data-testid="stIFrame"][height="0"], iframe[height="0"] {{ display:none; }}
/* Reopening the menu shows a side-panel icon, not an arrow (an arrow reads as "back"). */
[data-testid="stSidebarCollapsedControl"] button svg {{ display:none; }}
[data-testid="stSidebarCollapsedControl"] button::before {{ content:""; width:20px; height:20px; background:currentColor;
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2'%3E%3Crect x='3' y='4' width='18' height='16' rx='3'/%3E%3Cpath d='M9 4v16'/%3E%3C/svg%3E") center/contain no-repeat;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2'%3E%3Crect x='3' y='4' width='18' height='16' rx='3'/%3E%3Cpath d='M9 4v16'/%3E%3C/svg%3E") center/contain no-repeat; }}
/* Sidebar header: the logo, and the team's name to its right */
.team-head {{ display:flex; align-items:center; gap:.75rem; margin:.2rem 0 .35rem; }}
.team-head img {{ width:40px; height:40px; object-fit:contain; flex:none; }}
.team-head .team-name {{ margin:0; }}
[data-testid="stSidebar"] [data-testid="stImage"] img {{ border-radius:14px; }}

/* Artifacts and history: lists like the skills */
[class*="st-key-art-"] button {{ justify-content:flex-start; text-align:left; padding:.1rem 0 !important;
  background:transparent !important; border:0 !important; }}
[class*="st-key-art-"] button > div {{ justify-content:flex-start; flex-direction:row-reverse; gap:.35rem; }}
[class*="st-key-art-"] button p {{ font-size:1.1rem !important; font-weight:650; color:var(--ink); }}
[class*="st-key-art-"] button:hover p {{ color:var(--accent); }}
.change {{ padding:.8rem 0 .85rem; border-bottom:1px solid var(--rule); line-height:1.45; }}
.change .note {{ color:var(--muted); font-size:.9rem; margin-top:.2rem; }}
.change .when {{ margin-left:.9rem; opacity:.8; }}
.change .flag {{ color:#D98A1C; font-size:.85rem; margin-top:.25rem; }}
button p {{ white-space:nowrap; }}

/* Ideas: each a card; its comments indented under it */
.idea-text {{ font-size:1.05rem; font-weight:620; line-height:1.4; color:var(--ink); }}
.idea-who {{ color:var(--muted); font-size:.85rem; margin:.2rem 0 .6rem; line-height:1.4; }}
[class*="st-key-ideacard-"] {{ gap:.7rem; }}
[class*="st-key-ideacard-"][class*="-folded"] [data-testid="stElementContainer"] {{ height:auto !important; }}
[class*="st-key-ideacard-"] [data-testid="stTextInput"] input {{ background:transparent; }}
[class*="st-key-ideacard-"] [data-testid="stTextInput"] > div > div {{ background:transparent !important;
  border:1px solid var(--rule) !important; }}
[class*="st-key-ideacard-"] [data-testid="stFormSubmitButton"] button {{ background:transparent !important; }}
.idea-comment {{ border-left:2px solid var(--rule); padding:.35rem 0 .35rem 1rem; margin:.2rem 0 .9rem .1rem; line-height:1.55; white-space:pre-wrap; }}
.idea-comment .who {{ color:var(--muted); font-size:.85rem; margin-top:.1rem; }}
[class*="st-key-ideacard-"] [data-testid="stForm"] {{ padding:0; margin-top:.2rem; }}
/* New idea box: in the page's colours, whatever the browser theme */
[class*="st-key-new-idea"] textarea, .st-key-new-idea-title input, [class*="st-key-comment-"] textarea {{ background:var(--card) !important; color:var(--ink) !important;
  border:1px solid var(--rule) !important; border-radius:10px !important; }}
[class*="st-key-new-idea"] textarea::placeholder, .st-key-new-idea-title input::placeholder {{ color:var(--muted) !important; opacity:1; }}
[class*="st-key-ideacard-"] [data-testid="stExpander"] details {{ background:transparent !important; }}
[class*="st-key-ideaassign-"] button {{ min-height:0; padding:.1rem .6rem !important; font-size:.8rem; border-radius:999px;
  background:transparent !important; color:var(--muted) !important; border:1px dashed var(--rule) !important; white-space:nowrap; }}
.idea-owner {{ font-size:.85rem; font-weight:600; color:var(--accent); }}
.idea-description {{ color:var(--ink); opacity:.85; line-height:1.5; margin:.1rem 0 .4rem; white-space:pre-wrap; }}
[class*="st-key-ideacard-"] [data-testid="stExpander"] details {{ border:none !important; }}
[class*="st-key-ideacard-"] [data-testid="stExpander"] summary {{ padding:.2rem 0 !important; color:var(--muted); font-size:.9rem; }}
/* Status tag: a small pill, coloured by status */
[class*="st-key-ideatag-"] button {{ border-radius:999px; min-height:0; padding:.15rem .8rem !important; font-size:.8rem; font-weight:600; white-space:nowrap; }}
[class*="st-key-ideatag-new-"] button {{ background:var(--wash) !important; color:var(--accent) !important; border-color:var(--accent) !important; }}
[class*="st-key-ideatag-planned-"] button {{ background:transparent !important; color:#D9A400 !important; border-color:#D9A400 !important; }}
[class*="st-key-ideatag-done-"] button {{ background:transparent !important; color:#2E9E5B !important; border-color:#2E9E5B !important; }}
[class*="st-key-ideatag-archived-"] button {{ background:transparent !important; color:var(--muted) !important; border-color:var(--rule) !important; }}

/* Cards that open: the whole card is clickable (an invisible button covers it) */
[class*="st-key-skillcard-"], [class*="st-key-artcard-"] {{ position:relative; }}
[class*="st-key-cardhit-"] {{ position:absolute !important; inset:-1rem; z-index:1; margin:0 !important; }}
[class*="st-key-cardhit-"] div, [class*="st-key-cardhit-"] button {{ width:100% !important; height:100% !important; }}
[class*="st-key-cardhit-"] button {{ opacity:0; cursor:pointer; }}
[class*="st-key-share-"] {{ position:relative; z-index:2; }}
[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-cardhit-"]:hover) {{ border-color:var(--accent) !important; }}
/* Only the hovered card's title (a rule on the page's wrapper would colour every card) */
[class*="st-key-skillcard-"]:has([class*="st-key-cardhit-"]:hover) [class*="st-key-skill-"] p,
[class*="st-key-artcard-"]:has([class*="st-key-cardhit-"]:hover) [class*="st-key-art-"] p {{ color:var(--accent); }}

/* Buttons */
[data-testid="stBaseButton-secondary"] {{ border:1px solid var(--rule) !important; background:var(--card) !important;
  color:var(--ink) !important; border-radius:8px !important; }}
[data-testid="stBaseButton-secondary"]:hover {{ border-color:var(--accent) !important; color:var(--accent) !important; }}
[data-testid="stBaseButton-primary"] {{ border-radius:8px !important; }}
button:focus-visible {{ outline:2px solid var(--accent) !important; outline-offset:2px; }}

/* Containers: quiet surfaces, no shadows */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {{ border-radius:14px; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:var(--rule) !important; }}
[data-testid="stExpander"] details {{ border:1px solid var(--rule) !important; border-radius:10px !important; background:var(--card); }}
[data-testid="stExpander"] summary p {{ font-weight:550; }}

/* Skills: each row is the skill's name, large, with what it does underneath */
[class*="st-key-skill-"] button {{ justify-content:flex-start; text-align:left; padding:.2rem 0 !important;
  background:transparent !important; border:0 !important; }}
[class*="st-key-skill-"] button > div {{ justify-content:flex-start; }}
[class*="st-key-skill-"] button p {{ font-size:1.3rem !important; font-weight:680; letter-spacing:-0.012em;
  font-variation-settings:'opsz' 48; color:var(--ink); }}
[class*="st-key-skill-"] button:hover p {{ color:var(--accent); }}
/* Ideas: the title is the button that opens or folds the card */
[class*="st-key-ideaopen-"] button {{ justify-content:flex-start; text-align:left; padding:0 !important; min-height:0;
  background:transparent !important; border:0 !important; }}
[class*="st-key-ideaopen-"] button > div {{ justify-content:flex-start; }}
[class*="st-key-ideaopen-"] button p {{ font-size:1.05rem !important; font-weight:620; line-height:1.4; color:var(--ink); text-align:left;
  white-space:normal !important; overflow-wrap:anywhere; }}
[class*="st-key-ideaopen-"] button, [class*="st-key-ideaopen-"] button > div {{ white-space:normal !important; max-width:100%; min-width:0; }}
[class*="st-key-ideaopen-"] button:hover p {{ color:var(--accent); }}

/* Examples of what to ask: the page's type, quieter than the skill's own request */
[class*="st-key-example-"] [data-testid="stCode"] pre {{ background:transparent !important; border:1px dashed var(--rule);
  border-radius:12px !important; padding:.8rem 7.5rem .8rem 1.1rem !important; }}
[class*="st-key-example-"] [data-testid="stCode"] code {{ font-family:{font} !important; background:transparent !important;
  color:var(--ink) !important; font-size:1rem !important; white-space:pre-wrap !important; }}

/* Requests to paste: the copy button is always visible and says what it does */
[data-testid="stCodeCopyButton"] {{ opacity:1 !important; visibility:visible !important; width:auto !important;
  height:auto !important; top:50% !important; right:.6rem !important; transform:translateY(-50%) !important;
  display:flex !important; align-items:center; gap:.35rem; padding:.35rem .8rem !important; border-radius:999px !important;
  background:var(--accent) !important; color:var(--on-accent) !important; border:none !important; font-weight:600; font-size:.85rem; }}
[data-testid="stCodeCopyButton"]:hover, [data-testid="stCodeCopyButton"]:active, [data-testid="stCodeCopyButton"]:focus {{
  top:50% !important; transform:translateY(-50%) !important; filter:brightness(1.08); }}
[data-testid="stCodeCopyButton"] svg {{ stroke:var(--on-accent) !important; color:var(--on-accent) !important; }}
[data-testid="stCodeCopyButton"]::after {{ content:"{COPY.get(team_language(), COPY["en"])}"; }}
/* After a click: the button pops and says it copied, for a moment (app.py adds .copied) */
[data-testid="stCodeCopyButton"]:active {{ transform:translateY(-50%) scale(.92) !important; }}
[data-testid="stCodeCopyButton"].copied {{ background:#2E9E5B !important; animation:copied .35s ease-out; }}
[data-testid="stCodeCopyButton"].copied::after {{ content:"{COPIED.get(team_language(), COPIED["en"])}"; }}
@keyframes copied {{ 0% {{ transform:translateY(-50%) scale(.9); }} 60% {{ transform:translateY(-50%) scale(1.08); }}
  100% {{ transform:translateY(-50%) scale(1); }} }}
[data-testid="stCode"] div:has(> [data-testid="stCodeCopyButton"]) {{ opacity:1 !important; }}
[data-testid="stCode"] pre {{ padding-right:7.5rem !important; }}

/* The request to paste: the page's one loud element */
[class*="st-key-ask-"] [data-testid="stCode"] pre {{ background:var(--wash) !important; border-radius:14px !important;
  padding:1.1rem 7.5rem 1.1rem 1.25rem !important; }}
[class*="st-key-ask-"] [data-testid="stCode"] code {{ font-family:{font} !important; background:transparent !important;
  color:var(--ink) !important; font-size:1.35rem !important; font-weight:560; letter-spacing:-0.01em;
  white-space:pre-wrap !important; font-variation-settings:'opsz' 36; line-height:1.3; }}

/* Night or day: a sun or moon next to the team's name */
.st-key-modeswitch {{ margin-top:.2rem; }}  /* level with the logo and the team's name (40px tall) */
.st-key-modeswitch button {{ color:var(--muted) !important; padding:0 !important; min-height:0; height:40px; }}
.st-key-modeswitch button:hover {{ color:var(--accent) !important; }}
.st-key-modeswitch button span {{ font-size:1.4rem !important; }}
/* Streamlit's own buttons (hide or show the menu, the ⋮ menu): visible, day or night */
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapsedControl"] button,
[data-testid="stMainMenu"] button, [data-testid="stToolbar"] button {{ color:var(--ink) !important; }}
[data-testid="stSidebarCollapseButton"] button:hover, [data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="stMainMenu"] button:hover {{ background:var(--wash) !important; color:var(--accent) !important; }}
/* Tables (st.table): in the page's colours, day or night */
[data-testid="stTable"] table {{ color:var(--ink); background:transparent; }}
[data-testid="stTable"] th, [data-testid="stTable"] td {{ color:var(--ink) !important; border-color:var(--rule) !important;
  background:transparent !important; }}
[data-testid="stTable"] th {{ color:var(--muted) !important; font-weight:600; }}
/* Radio choices: an empty ring when not chosen, the brand colour when chosen */
[data-testid="stRadio"] label > div:first-child:not([data-testid]) {{ background:var(--card) !important;
  box-shadow:inset 0 0 0 1.5px var(--muted); }}
[data-testid="stRadio"] label:has(input:checked) > div:first-child:not([data-testid]) {{ background:var(--accent) !important;
  box-shadow:none; }}
[data-testid="stRadio"] label > div:first-child:not([data-testid]) > div {{ background:var(--card) !important; }}
/* "Working..." messages: on the page, not on a dark band */
[data-testid="stSpinner"], [data-testid="stSpinner"] > div {{ background:transparent !important; color:var(--ink) !important; }}
[data-testid="stSpinner"] i {{ border-color:var(--rule) !important; border-top-color:var(--accent) !important; }}
/* Hover hints (the "?" and the sun or moon): readable, day or night */
[data-testid="stTooltipContent"], [data-baseweb="tooltip"] > div {{ background:var(--ink) !important; }}
[data-testid="stTooltipContent"], [data-testid="stTooltipContent"] * {{ color:var(--paper) !important; }}
/* Switches: the track always shows against the page, day or night */
/* (the track and its knob have no test id; the "?" help icon next to a label does) */
[data-testid="stCheckbox"] label > div:first-child:not([data-testid]) {{ background:var(--rule) !important; }}
[data-testid="stCheckbox"] label > div:first-child:not([data-testid]) > div {{ background:var(--card) !important; box-shadow:0 0 0 1px var(--muted); }}
[data-testid="stCheckbox"] label:has(input:checked) > div:first-child:not([data-testid]) {{ background:var(--accent) !important; }}
/* Text boxes and menus: in the page's colours, day or night */
input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"],
[data-baseweb="base-input"] {{ background:var(--card) !important; color:var(--ink) !important; }}
input::placeholder, textarea::placeholder {{ color:var(--muted) !important; opacity:1; }}
[data-baseweb="popover"] > div, [data-baseweb="popover"] ul, [data-baseweb="menu"],
[data-baseweb="popover"] li, [data-baseweb="popover"] [role="option"] {{ background:var(--card) !important; color:var(--ink) !important; }}
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [aria-selected="true"] {{ background:var(--wash) !important; }}
[data-baseweb="popover"] li *, [data-baseweb="popover"] [role="option"] * {{ color:var(--ink) !important; }}
[data-baseweb="select"], [data-baseweb="select"] *, [data-baseweb="popover"] li {{ font-family:inherit; }}
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] p, label {{ color:var(--ink); }}

/* Popovers (an artifact's "What it is"): readable on the brand, dark brands included */
[data-testid="stPopoverBody"] {{ background:var(--card) !important; border:1px solid var(--rule) !important; }}
[data-testid="stPopoverBody"], [data-testid="stPopoverBody"] * {{ color:var(--ink) !important; }}

{loading_css()}
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} }}
.team-back {{ display:inline-block; margin:0 0 6px; padding:6px 12px; border:1px solid var(--rule);
  border-radius:4px; color:var(--ink) !important; text-decoration:none !important; font-size:.9rem; }}
.team-back:hover {{ border-color:var(--accent); color:var(--accent) !important; }}
</style>""" + back_link()


def team_header(logo, name, champion):
    """The logo with the team's name to its right, and the AI Champion underneath."""
    try:
        img = f'<img alt="" src="data:image/png;base64,{base64.b64encode(logo.read_bytes()).decode()}">'
    except OSError:
        img = ""
    return (f'<div class="team-head">{img}<div class="team-name">{html.escape(name)}</div></div>'
            f'<div class="champion">{html.escape(champion)}</div>')


def sync_badge(text, ok):
    return f'<div class="sync {"ok" if ok else "warn"}"><span class="dot"></span><span>{text}</span></div>'

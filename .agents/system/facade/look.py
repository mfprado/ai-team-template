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


def tokens(brand):
    c = palette(brand)
    light = on(c["background"]) != "#FFFFFF"
    return {
        **c,
        "card": "#FFFFFF" if light else mix(c["background"], c["text"], 0.06),
        "panel": mix(c["background"], c["text"], 0.035),
        "wash": mix(c["background"], c["primary"], 0.12 if light else 0.2),
        "rule": mix(c["background"], c["text"], 0.13),
    }


BACK = {"en": "← Back to the team page", "es": "← Volver a la página del equipo"}


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
.st-key-menu [data-testid="stBaseButton-primary"] {{ background:var(--wash) !important; font-weight:650;
  box-shadow:inset 3px 0 0 var(--accent); }}
.st-key-menu [data-testid="stBaseButton-primary"] p {{ font-weight:650; }}

/* The logo: an app icon */
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

/* Cards that open: the whole card is clickable (an invisible button covers it) */
[class*="st-key-skillcard-"], [class*="st-key-artcard-"] {{ position:relative; }}
[class*="st-key-cardhit-"] {{ position:absolute !important; inset:-1rem; z-index:1; margin:0 !important; }}
[class*="st-key-cardhit-"] div, [class*="st-key-cardhit-"] button {{ width:100% !important; height:100% !important; }}
[class*="st-key-cardhit-"] button {{ opacity:0; cursor:pointer; }}
[class*="st-key-share-"] {{ position:relative; z-index:2; }}
[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-cardhit-"]:hover) {{ border-color:var(--accent) !important; }}
[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-cardhit-"]:hover) [class*="st-key-skill-"] p,
[data-testid="stVerticalBlockBorderWrapper"]:has([class*="st-key-cardhit-"]:hover) [class*="st-key-art-"] p {{ color:var(--accent); }}

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

/* Examples of what to ask: the page's type, quieter than the skill's own request */
[class*="st-key-example-"] [data-testid="stCode"] pre {{ background:transparent !important; border:1px dashed var(--rule);
  border-radius:12px !important; padding:.8rem 3rem .8rem 1.1rem !important; }}
[class*="st-key-example-"] [data-testid="stCode"] code {{ font-family:{font} !important; background:transparent !important;
  color:var(--ink) !important; font-size:1rem !important; white-space:pre-wrap !important; }}

/* The request to paste: the page's one loud element */
[class*="st-key-ask-"] [data-testid="stCode"] pre {{ background:var(--wash) !important; border-radius:14px !important;
  padding:1.1rem 3rem 1.1rem 1.25rem !important; }}
[class*="st-key-ask-"] [data-testid="stCode"] code {{ font-family:{font} !important; background:transparent !important;
  color:var(--ink) !important; font-size:1.35rem !important; font-weight:560; letter-spacing:-0.01em;
  white-space:pre-wrap !important; font-variation-settings:'opsz' 36; line-height:1.3; }}

/* Popovers (an artifact's "What it is"): readable on the brand, dark brands included */
[data-testid="stPopoverBody"] {{ background:var(--card) !important; border:1px solid var(--rule) !important; }}
[data-testid="stPopoverBody"], [data-testid="stPopoverBody"] * {{ color:var(--ink) !important; }}

{loading_css()}
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} }}
.team-back {{ display:inline-block; margin:0 0 6px; padding:6px 12px; border:1px solid var(--rule);
  border-radius:4px; color:var(--ink) !important; text-decoration:none !important; font-size:.9rem; }}
.team-back:hover {{ border-color:var(--accent); color:var(--accent) !important; }}
</style>""" + back_link()


def sync_badge(text, ok):
    return f'<div class="sync {"ok" if ok else "warn"}"><span class="dot"></span><span>{text}</span></div>'

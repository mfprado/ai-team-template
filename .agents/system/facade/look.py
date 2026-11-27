"""The team page's look, made from the company's brand (.agents/brand.json).

Colours come from the brand (or the default below); type is Bricolage Grotesque, or Newsreader
when the brand asks for a serif. The one bold element is the request to paste for each skill,
set large in the page's type on a wash of the brand colour: asking the AI in your own words is
what the page is about. Everything else stays quiet.
"""

from flow_page import mix, on, palette

FONTS = {
    "sans": ("Bricolage Grotesque", "Bricolage+Grotesque:opsz,wght@12..96,300..800",
             "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"),
    "serif": ("Newsreader", "Newsreader:opsz,wght@6..72,300..700", "Georgia, 'Times New Roman', serif"),
}


def tokens(brand):
    c = palette(brand)
    light = on(c["background"]) != "#FFFFFF"
    return {
        **c,
        "card": "#FFFFFF" if light else mix(c["background"], c["text"], 0.06),
        "panel": mix(c["background"], c["text"], 0.035),
        "wash": mix(c["background"], c["primary"], 0.12),
        "rule": mix(c["background"], c["text"], 0.13),
    }


def css(brand):
    k = tokens(brand)
    name, query, fallback = FONTS["serif" if brand.get("font") == "serif" else "sans"]
    font = f"'{name}', {fallback}"
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family={query}&display=swap');
:root {{ --ink:{k['text']}; --paper:{k['background']}; --accent:{k['primary']}; --on-accent:{k['on_primary']};
  --wash:{k['wash']}; --rule:{k['rule']}; --muted:{k['muted']}; --card:{k['card']}; --panel:{k['panel']}; }}

/* Type: one family, its optical size doing the work */
html, body, [data-testid="stApp"], [data-testid="stMarkdownContainer"], button, input, textarea, select,
[data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"] {{ font-family:{font} !important; }}
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

/* Buttons */
[data-testid="stBaseButton-secondary"] {{ border:1px solid var(--rule) !important; background:var(--card) !important;
  color:var(--ink) !important; border-radius:8px !important; }}
[data-testid="stBaseButton-secondary"]:hover {{ border-color:var(--accent) !important; color:var(--accent) !important; }}
[data-testid="stBaseButton-primary"] {{ border-radius:8px !important; }}
button:focus-visible {{ outline:2px solid var(--accent) !important; outline-offset:2px; }}

/* Containers: quiet surfaces, no shadows */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {{ border-radius:14px; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:var(--rule) !important; }}
div[data-testid="stVerticalBlockBorderWrapper"][class*="st-key-skillcard"] {{ background:var(--card); }}
[data-testid="stExpander"] details {{ border:1px solid var(--rule) !important; border-radius:10px !important; background:var(--card); }}
[data-testid="stExpander"] summary p {{ font-weight:550; }}

/* Skills: each row is the skill's name, large, with what it does underneath */
[class*="st-key-skill-"] button {{ justify-content:flex-start; text-align:left; padding:.2rem 0 !important;
  background:transparent !important; border:0 !important; }}
[class*="st-key-skill-"] button > div {{ justify-content:flex-start; }}
[class*="st-key-skill-"] button p {{ font-size:1.3rem !important; font-weight:680; letter-spacing:-0.012em;
  font-variation-settings:'opsz' 48; color:var(--ink); }}
[class*="st-key-skill-"] button:hover p {{ color:var(--accent); }}

/* The request to paste: the page's one loud element */
[class*="st-key-ask-"] [data-testid="stCode"] pre {{ background:var(--wash) !important; border-radius:14px !important;
  padding:1.1rem 3rem 1.1rem 1.25rem !important; }}
[class*="st-key-ask-"] [data-testid="stCode"] code {{ font-family:{font} !important; background:transparent !important;
  color:var(--ink) !important; font-size:1.35rem !important; font-weight:560; letter-spacing:-0.01em;
  white-space:pre-wrap !important; font-variation-settings:'opsz' 36; line-height:1.3; }}

@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} }}
</style>"""


def sync_badge(text, ok):
    return f'<div class="sync {"ok" if ok else "warn"}"><span class="dot"></span><span>{text}</span></div>'

"""A skill's flow diagram as an HTML page in the company's design, shown in each skill on the
team page. Clicking a step opens a card with its details, the tools it uses and, for a check,
where each answer leads. Colours, font and logos come from .agents/brand.json and .agents/brand/.

The page draws the diagram with Mermaid in the browser (loaded from a CDN) and fetches only the
tool logos the diagram names (Iconify). Without internet, the diagram's text is shown instead.
"""

import base64
import io
import json
import re

# Tools in a flow diagram, each on its own line, joined to the steps that use them:
#   GM@{ icon: "logos:google-gmail", label: "Gmail" }      a tool with a logo
#   DB["Sales database"]:::tool                            a tool without one
#   B -.- GM                                               step B uses Gmail
TOOL_LOGO = r'^\s*(\w+)@\{[^}]*?icon:\s*"([\w-]+):([\w-]+)"[^}]*?label:\s*"([^"]*)"[^}]*\}\s*$'
TOOL_PLAIN = r'^\s*(\w+)\["?([^"\]]+?)"?\]:::tool\s*$'
TOOL_LINK = r'^\s*(\w+)\s*-\.-\s*(\w+)\s*$'
# Details for a step, as a Mermaid comment (other viewers ignore it):  %% B: what happens here
DETAIL = r'^\s*%%\s*(\w+)\s*:\s*(.+)$'
# An arrow with an answer on it:  C -- Yes --> E
BRANCH = r'^\s*(\w+)\s*--\s*([^->][^>]*?)\s*-->\s*(\w+)'

# The team page's type (look.py): Bricolage Grotesque, or Newsreader for a serif brand.
FONTS = {"sans": "'Bricolage Grotesque', -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
         "serif": "'Newsreader', Georgia, 'Times New Roman', serif"}
FONT_URLS = {"sans": "Bricolage+Grotesque:opsz,wght@12..96,300..800", "serif": "Newsreader:opsz,wght@6..72,300..700"}
# Without a brand: pine green on a cool white.
DEFAULT = {"primary": "#1F6F5C", "background": "#F5F7F6", "text": "#17201D"}


def rgb(hex_colour):
    return [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]


def mix(a, b, amount):
    """a moved `amount` (0..1) of the way towards b."""
    return "#" + "".join(f"{round(x + (y - x) * amount):02X}" for x, y in zip(rgb(a), rgb(b)))


def on(colour):
    """Readable text on a background of this colour."""
    r, g, b = rgb(colour)
    return "#FFFFFF" if 0.299 * r + 0.587 * g + 0.114 * b < 150 else "#111827"


def image_data(path, box):
    """A brand image, shrunk to fit `box` (w, h), as a data URI. None if missing or unreadable."""
    if not path.is_file():
        return None
    try:
        from PIL import Image  # comes with Streamlit
        image = Image.open(path).convert("RGBA")
        image.thumbnail(box)
        out = io.BytesIO()
        image.save(out, format="PNG")
        return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode()
    except Exception:  # a damaged image must never break the page
        return None


FAMILY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 \-]{0,60}$")
FONT_FILES = {".woff2": "woff2", ".woff": "woff", ".ttf": "truetype", ".otf": "opentype"}
WEIGHTS = [("thin", 100), ("extralight", 200), ("light", 300), ("medium", 500), ("semibold", 600),
           ("extrabold", 800), ("bold", 700), ("black", 900)]


def company_font(brand, brand_dir):
    """How to load the company's own typeface, and the font stack that puts it first.

    brand.json's `font_family` names it ("Montserrat"). Its files in .agents/brand/fonts/ are used
    when there (any typeface the company provides); otherwise it is asked from Google Fonts. Our
    default type (Bricolage Grotesque, or Newsreader for a serif brand) stays behind it.
    Returns (CSS that loads the fonts, the font-family value).
    """
    kind = "serif" if brand.get("font") == "serif" else "sans"
    family = str(brand.get("font_family") or "").strip()
    css = f"@import url('https://fonts.googleapis.com/css2?family={FONT_URLS[kind]}&display=swap');\n"
    if not FAMILY.match(family):
        return css, FONTS[kind]
    files = sorted(f for f in (brand_dir / "fonts").glob("*") if f.suffix.lower() in FONT_FILES) \
        if (brand_dir / "fonts").is_dir() else []
    if files:
        for f in files:
            name = re.sub(r"[^a-z]", "", f.stem.lower())
            weight = next((w for key, w in WEIGHTS if key in name), 400)
            style = "italic" if "italic" in name else "normal"
            data = base64.b64encode(f.read_bytes()).decode()
            css += (f"@font-face{{font-family:'{family}';src:url(data:font/{FONT_FILES[f.suffix.lower()]};base64,{data}) "
                    f"format('{FONT_FILES[f.suffix.lower()]}');font-weight:{weight};font-style:{style};font-display:swap}}\n")
    else:
        query = family.replace(" ", "+")
        # A static family fails if a weight is missing: ask for the usual weights, then the plain family.
        css = (f"@import url('https://fonts.googleapis.com/css2?family={query}:wght@400;500;600;700&display=swap');\n"
               f"@import url('https://fonts.googleapis.com/css2?family={query}&display=swap');\n") + css
    return css, f"'{family}', {FONTS[kind]}"


def palette(brand):
    colours = {k: brand.get(k) or v for k, v in DEFAULT.items()}
    p, bg, tx = colours["primary"], colours["background"], colours["text"]
    return {
        "primary": p, "background": bg, "text": tx, "on_primary": on(p),
        "check": mix(bg, p, 0.14),          # checks: a light tint of the brand colour
        "muted": mix(tx, bg, 0.35),         # secondary text
        "line": mix(bg, tx, 0.14),          # chip and badge borders
        "border": mix(bg, tx, 0.28),        # step boxes
        "edge": mix(bg, tx, 0.45),          # arrows
        "font": FONTS["serif" if brand.get("font") == "serif" else "sans"],
    }


TEXT = {
    "en": {"uses": "Uses", "then": "Then", "none": "No more details for this step."},
    "es": {"uses": "Usa", "then": "Después", "none": "Este paso no tiene más detalles."},
}


def build(diagram, brand, brand_dir, language="en"):
    """The full HTML document."""
    c = palette(brand)
    font_css, c["font"] = company_font(brand, brand_dir)
    company_icon = image_data(brand_dir / "icon.png", (64, 64))
    config = {
        "startOnLoad": False, "securityLevel": "strict", "theme": "base",
        "flowchart": {"useMaxWidth": False, "htmlLabels": True, "curve": "linear", "wrappingWidth": 190,
                      "padding": 12, "nodeSpacing": 34, "rankSpacing": 30, "diagramPadding": 14},
        "themeVariables": {
            "fontFamily": c["font"], "fontSize": "14px",
            "primaryColor": c["background"], "primaryBorderColor": c["border"], "primaryTextColor": c["text"],
            "lineColor": c["edge"], "textColor": c["text"], "edgeLabelBackground": c["background"],
        },
        # Simple and quiet, in the company's colours, with thin lines. Steps: white boxes with a
        # fine border. Checks: tinted with the brand colour. Start and end: the brand colour.
        "themeCSS": (f".node rect{{rx:6px;ry:6px;fill:{c['background']};stroke:{c['border']};stroke-width:1px}}"
                     f".node polygon{{fill:{c['check']};stroke:{c['primary']};stroke-width:1px}}"
                     f".node.done rect{{fill:{c['primary']};stroke:{c['primary']}}}"
                     f".node.done .nodeLabel{{color:{c['on_primary']}}}"
                     f".node .nodeLabel{{line-height:1.35}}"
                     f".flowchart-link{{stroke:{c['edge']} !important;stroke-width:1px !important}}"
                     f".marker{{fill:{c['edge']} !important;stroke:{c['edge']} !important}}"
                     f".edgeLabel,.edgeLabel p{{color:{c['muted']};font-size:12px}}"
                     f".node{{cursor:pointer}}"
                     f".node:hover rect,.node:hover polygon{{stroke:{c['primary']};stroke-width:1.5px}}"),
    }
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Flow</title>
<style>{font_css}</style>
<style>
html,body{{margin:0;background:{c['background']};color:{c['text']};font-family:{c['font']}}}
main{{padding:0}}
#tools{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:2px 0 6px}}
.chip{{display:flex;align-items:center;gap:6px;padding:3px 10px 3px 5px;border:1px solid {c['line']};
  border-radius:999px;font-size:13px;background:{c['background']};color:{c['text']}}}
#flow{{text-align:center}}
#raw{{display:none;white-space:pre-wrap;font-size:13px;color:{c['muted']}}}
#shade{{display:none;position:absolute;left:0;top:0;width:100%;background:{c['background']}B3}}
#card{{display:none;position:absolute;left:50%;transform:translateX(-50%);width:min(420px,calc(100% - 32px));
  box-sizing:border-box;background:{c['background']};color:{c['text']};border:1px solid {c['border']};
  border-top:3px solid {c['primary']};border-radius:8px;padding:16px 18px 14px;
  box-shadow:0 10px 30px rgba(0,0,0,.12);text-align:left}}
#card h2{{margin:0 28px 8px 0;font-size:17px;line-height:1.3}}
#card p{{margin:0 0 10px;line-height:1.5;font-size:14px}}
#card .label{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:{c['muted']};margin:10px 0 6px}}
#card .chips{{display:flex;flex-wrap:wrap;gap:6px}}
#card ul{{margin:0;padding-left:18px;font-size:14px;line-height:1.6}}
#card .none{{color:{c['muted']};font-size:13px}}
#close{{position:absolute;top:10px;right:12px;border:0;background:none;font-size:20px;line-height:1;
  color:{c['muted']};cursor:pointer}}
</style></head>
<body><main>
<div id="tools"></div>
<div id="flow"></div>
<pre id="raw"></pre>
</main>
<div id="shade"></div>
<div id="card" role="dialog" aria-modal="true"><button id="close" aria-label="Close">&times;</button>
  <div id="card-body"></div></div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
  integrity="sha384-rbtjAdnIQE/aQJGEgXrVUlMibdfTSa4PQju4HDhN3sR2PmaKFzhEafuePsl9H/9I" crossorigin="anonymous"></script>
<script>
const source = {json.dumps(diagram)};
const TOOL_LOGO = new RegExp({json.dumps(TOOL_LOGO)});
const TOOL_PLAIN = new RegExp({json.dumps(TOOL_PLAIN)});
const TOOL_LINK = new RegExp({json.dumps(TOOL_LINK)});
const SVGNS = "http://www.w3.org/2000/svg";
const COMPANY = {json.dumps(company_icon)};
const C = {json.dumps(c)};
const T = {json.dumps(TEXT.get(language, TEXT["en"]))};
// Details for a step, as a Mermaid comment (other viewers ignore it):  %% B: what happens here
const DETAIL = new RegExp({json.dumps(DETAIL)});
// An arrow with an answer on it:  C -- Yes --> E
const BRANCH = new RegExp({json.dumps(BRANCH)});

function fit() {{
  // Inside the team page, Streamlit gives the frame and its wrapper a fixed height: grow both.
  const h = Math.ceil(document.body.getBoundingClientRect().height) + 16;
  try {{
    if (window.frameElement) {{
      window.frameElement.style.height = h + "px";
      window.frameElement.parentElement.style.height = h + "px";
    }}
  }} catch (e) {{}}
}}
window.addEventListener("resize", fit);
function plain() {{
  const raw = document.getElementById("raw");
  raw.textContent = source; raw.style.display = "block"; fit();
}}

function splitTools(src) {{
  // Take the tools and their dotted links out of the diagram: they become logos.
  const tools = {{}}, uses = {{}}, rest = [];
  const lines = src.split("\\n");
  for (const line of lines) {{
    let m = line.match(TOOL_LOGO);
    if (m) {{ tools[m[1]] = {{label: m[4], set: m[2], name: m[3]}}; continue; }}
    m = line.match(TOOL_PLAIN);
    if (m) {{ tools[m[1]] = {{label: m[2]}}; continue; }}
  }}
  for (const line of lines) {{
    if (TOOL_LOGO.test(line) || TOOL_PLAIN.test(line)) continue;
    const m = line.match(TOOL_LINK);
    if (m && (tools[m[1]] || tools[m[2]])) {{
      const [step, tool] = tools[m[2]] ? [m[1], m[2]] : [m[2], m[1]];
      (uses[step] ||= []).push(tool);
      continue;
    }}
    rest.push(line);
  }}
  return {{tools, uses, diagram: rest.join("\\n")}};
}}

async function loadLogos(tools) {{
  // One request per logo collection, for only the logos named here.
  const wanted = {{}};
  for (const t of Object.values(tools)) if (t.set) (wanted[t.set] ||= new Set()).add(t.name);
  await Promise.all(Object.entries(wanted).map(async ([set, names]) => {{
    try {{
      const r = await fetch(`https://api.iconify.design/${{set}}.json?icons=${{[...names].join(",")}}`);
      if (!r.ok) return;
      const pack = await r.json();
      for (const t of Object.values(tools)) {{
        if (t.set !== set) continue;
        let name = t.name, extra = {{}};
        while (!(pack.icons || {{}})[name] && (pack.aliases || {{}})[name]) {{
          extra = {{...pack.aliases[name], ...extra}}; name = pack.aliases[name].parent;
        }}
        const icon = (pack.icons || {{}})[name];
        if (icon) t.logo = {{body: icon.body, w: extra.width || icon.width || pack.width || 16,
                            h: extra.height || icon.height || pack.height || 16}};
      }}
    }} catch (e) {{}}
  }}));
}}

function logo(t, size) {{
  // The tool's logo; else the company's (in-house tools); else its initial in a circle.
  const svg = document.createElementNS(SVGNS, "svg");
  svg.setAttribute("width", size); svg.setAttribute("height", size);
  if (t.logo) {{
    svg.setAttribute("viewBox", `0 0 ${{t.logo.w}} ${{t.logo.h}}`);
    svg.innerHTML = t.logo.body;
  }} else if (COMPANY) {{
    svg.setAttribute("viewBox", "0 0 20 20");
    const img = document.createElementNS(SVGNS, "image");
    img.setAttribute("href", COMPANY); img.setAttribute("width", 20); img.setAttribute("height", 20);
    svg.appendChild(img);
  }} else {{
    svg.setAttribute("viewBox", "0 0 20 20");
    svg.innerHTML = `<circle cx="10" cy="10" r="10" fill="${{C.primary}}"/><text x="10" y="14" text-anchor="middle"
      font-size="11" font-weight="600" fill="${{C.on_primary}}" font-family="sans-serif"></text>`;
    svg.querySelector("text").textContent = t.label.trim().charAt(0).toUpperCase();
  }}
  return svg;
}}

function badge(svg, layer, step, tools) {{
  // Small logos on the top-right corner of the step that uses them. They go in their own
  // layer, outside the step: Mermaid's styles for steps would repaint the logos.
  const node = svg.querySelector(`g.node[id^="flowchart-${{step}}-"]`);
  if (!node) return;
  const box = node.getBBox(), size = 22, gap = 3;
  const m = layer.getScreenCTM().inverse().multiply(node.getScreenCTM());
  const corner = new DOMPoint(box.x + box.width, box.y).matrixTransform(m);
  tools.forEach((t, i) => {{
    const g = document.createElementNS(SVGNS, "g");
    const x = corner.x - (i + 1) * (size + gap) + 6, y = corner.y - size / 2 - 2;
    g.innerHTML = `<circle cx="${{x + size / 2}}" cy="${{y + size / 2}}" r="${{size / 2 + 2}}"
      fill="${{C.background}}" stroke="${{C.line}}"/>`;
    const icon = logo(t, size - 6);
    icon.setAttribute("x", x + 3); icon.setAttribute("y", y + 3);
    const title = document.createElementNS(SVGNS, "title"); title.textContent = t.label;
    g.appendChild(title); g.appendChild(icon); layer.appendChild(g);
  }});
}}

function esc(text) {{
  const d = document.createElement("div"); d.textContent = text; return d.innerHTML;
}}

function closeCard() {{
  document.getElementById("card").style.display = "none";
  document.getElementById("shade").style.display = "none";
}}

function openCard(node, id, info) {{
  // The step's details, next to the box that was clicked.
  const label = node.textContent.trim();
  const body = document.getElementById("card-body");
  let out = `<h2>${{esc(label)}}</h2>`;
  if (info.details[id]) out += `<p>${{esc(info.details[id])}}</p>`;
  const used = (info.uses[id] || []).map(t => info.tools[t]);
  if (used.length) out += `<div class="label">${{esc(T.uses)}}</div><div class="chips"></div>`;
  const branches = info.branches[id] || [];
  if (branches.length) {{
    out += `<div class="label">${{esc(T.then)}}</div><ul>` + branches.map(b =>
      `<li><strong>${{esc(b.answer)}}</strong>: ${{esc(info.label(b.to))}}</li>`).join("") + `</ul>`;
  }}
  if (!info.details[id] && !used.length && !branches.length) out += `<p class="none">${{esc(T.none)}}</p>`;
  body.innerHTML = out;
  const chips = body.querySelector(".chips");
  for (const t of used) {{
    const chip = document.createElement("span"); chip.className = "chip";
    chip.appendChild(logo(t, 20)); chip.appendChild(document.createTextNode(t.label));
    chips.appendChild(chip);
  }}
  const shade = document.getElementById("shade"), card = document.getElementById("card");
  shade.style.height = document.documentElement.scrollHeight + "px";
  shade.style.display = "block"; card.style.display = "block";
  const box = node.getBoundingClientRect(), page = document.documentElement.scrollHeight;
  let top = window.scrollY + box.bottom + 8;
  if (top + card.offsetHeight > page - 8) top = Math.max(8, window.scrollY + box.top - card.offsetHeight - 8);
  card.style.top = top + "px";
  document.getElementById("close").focus();
}}

function clickable(svg, source, tools, uses) {{
  const details = {{}}, branches = {{}};
  for (const line of source.split("\\n")) {{
    let m = line.match(DETAIL);
    if (m) {{ details[m[1]] = m[2].trim(); continue; }}
    m = line.match(BRANCH);
    if (m) (branches[m[1]] ||= []).push({{answer: m[2].trim(), to: m[3]}});
  }}
  const nodeOf = id => svg.querySelector(`g.node[id^="flowchart-${{id}}-"]`);
  const info = {{details, branches, tools, uses, label: id => (nodeOf(id) || {{textContent: id}}).textContent.trim()}};
  for (const node of svg.querySelectorAll("g.node")) {{
    const id = (node.id.match(/^flowchart-(\\w+)-\\d+$/) || [])[1];
    if (!id) continue;
    node.setAttribute("tabindex", "0"); node.setAttribute("role", "button");
    node.addEventListener("click", () => openCard(node, id, info));
    node.addEventListener("keydown", e => {{ if (e.key === "Enter" || e.key === " ") openCard(node, id, info); }});
  }}
}}
document.getElementById("close").addEventListener("click", closeCard);
document.getElementById("shade").addEventListener("click", closeCard);
document.addEventListener("keydown", e => {{ if (e.key === "Escape") closeCard(); }});

(async () => {{
  try {{
    const {{tools, uses, diagram}} = splitTools(source);
    await loadLogos(tools);
    const row = document.getElementById("tools");
    for (const t of Object.values(tools)) {{
      const chip = document.createElement("span"); chip.className = "chip";
      chip.appendChild(logo(t, 20)); chip.appendChild(document.createTextNode(t.label));
      row.appendChild(chip);
    }}
    try {{ await document.fonts.ready; }} catch (e) {{}}  // measure the boxes in the page's type
    mermaid.initialize({json.dumps(config)});
    const r = await mermaid.render("flow-svg", diagram);
    document.getElementById("flow").innerHTML = r.svg;
    const svg = document.querySelector("#flow svg");
    const layer = document.createElementNS(SVGNS, "g");
    svg.appendChild(layer);
    for (const [step, ids] of Object.entries(uses)) badge(svg, layer, step, ids.map(id => tools[id]));
    clickable(svg, source, tools, uses);
    svg.style.maxWidth = "100%"; svg.style.height = "auto";
    fit();
  }} catch (e) {{ plain(); }}
}})();
</script>
</body></html>
"""

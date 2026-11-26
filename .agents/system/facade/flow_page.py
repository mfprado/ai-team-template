"""A skill's flow diagram as an HTML page in the company's design.

One builder for both places the flow is seen: inside each skill card on the team page
(embedded) and as a page of its own opened in the browser (standalone, with a header carrying
the company's logo). Colours, font and logos come from .agents/brand.json and .agents/brand/.

The page draws the diagram with Mermaid in the browser (loaded from a CDN) and fetches only the
tool logos the diagram names (Iconify). Without internet, the diagram's text is shown instead.
"""

import base64
import html
import io
import json

# Tools in a flow diagram, each on its own line, joined to the steps that use them:
#   GM@{ icon: "logos:google-gmail", label: "Gmail" }      a tool with a logo
#   DB["Sales database"]:::tool                            a tool without one
#   B -.- GM                                               step B uses Gmail
TOOL_LOGO = r'^\s*(\w+)@\{[^}]*?icon:\s*"([\w-]+):([\w-]+)"[^}]*?label:\s*"([^"]*)"[^}]*\}\s*$'
TOOL_PLAIN = r'^\s*(\w+)\["?([^"\]]+?)"?\]:::tool\s*$'
TOOL_LINK = r'^\s*(\w+)\s*-\.-\s*(\w+)\s*$'

FONTS = {"sans": "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
         "serif": "Georgia, 'Times New Roman', serif"}
DEFAULT = {"primary": "#4F6BED", "background": "#FFFFFF", "text": "#1F2937"}


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


def palette(brand):
    colours = {k: brand.get(k) or v for k, v in DEFAULT.items()}
    p, bg, tx = colours["primary"], colours["background"], colours["text"]
    return {
        "primary": p, "background": bg, "text": tx, "on_primary": on(p),
        "check": mix(bg, p, 0.14),          # checks: a light tint of the brand colour
        "muted": mix(tx, bg, 0.35),         # secondary text
        "line": mix(bg, tx, 0.14),          # chip and badge borders
        "font": FONTS["serif" if brand.get("font") == "serif" else "sans"],
    }


def build(diagram, brand, brand_dir, title="", summary="", team="", standalone=False):
    """The full HTML document. `standalone` adds the company header and fills the window."""
    c = palette(brand)
    company_icon = image_data(brand_dir / "icon.png", (64, 64))
    header_logo = image_data(brand_dir / "logo.png", (360, 96)) if standalone else None
    config = {
        "startOnLoad": False, "securityLevel": "strict", "theme": "base",
        "flowchart": {"useMaxWidth": False, "htmlLabels": True, "curve": "basis", "wrappingWidth": 200,
                      "padding": 10, "nodeSpacing": 30, "rankSpacing": 32, "diagramPadding": 14},
        "themeVariables": {
            "fontFamily": c["font"], "fontSize": "15px",
            "primaryColor": c["background"], "primaryBorderColor": c["primary"], "primaryTextColor": c["text"],
            "lineColor": c["primary"], "textColor": c["text"], "edgeLabelBackground": c["background"],
        },
        # Steps: outlined boxes. Checks: hexagons tinted with the brand colour.
        # Start and end: filled with the brand colour.
        "themeCSS": (f".node polygon{{fill:{c['check']};stroke:{c['primary']};stroke-width:1.5px}}"
                     f".node rect{{rx:8px;ry:8px}}"
                     f".node.done rect,.node.done circle{{fill:{c['primary']};stroke:{c['primary']}}}"
                     f".node.done .nodeLabel{{color:{c['on_primary']}}}"
                     f".edgeLabel,.edgeLabel p{{color:{c['muted']}}}"),
    }
    header = ""
    if standalone:
        logo = f'<img class="logo" src="{header_logo}" alt="">' if header_logo else ""
        header = (f'<header>{logo}<div><div class="team">{html.escape(team)}</div>'
                  f'<h1>{html.escape(title)}</h1></div></header>'
                  + (f'<p class="summary">{html.escape(summary)}</p>' if summary else ""))
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title or "Flow")}</title>
<style>
html,body{{margin:0;background:{c['background']};color:{c['text']};font-family:{c['font']}}}
main{{{"max-width:960px;margin:0 auto;padding:28px 20px 40px" if standalone else "padding:0"}}}
header{{display:flex;align-items:center;gap:16px;padding-bottom:14px;margin-bottom:14px;
  border-bottom:3px solid {c['primary']}}}
header .logo{{max-height:48px;max-width:180px}}
header .team{{font-size:13px;color:{c['muted']};text-transform:uppercase;letter-spacing:.06em}}
header h1{{margin:2px 0 0;font-size:26px;color:{c['text']}}}
.summary{{margin:0 0 18px;color:{c['muted']};line-height:1.5}}
#tools{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:2px 0 6px}}
.chip{{display:flex;align-items:center;gap:6px;padding:3px 10px 3px 5px;border:1px solid {c['line']};
  border-radius:999px;font-size:13px;background:{c['background']};color:{c['text']}}}
#flow{{text-align:center}}
#raw{{display:none;white-space:pre-wrap;font-size:13px;color:{c['muted']}}}
</style></head>
<body><main>{header}
<div id="tools"></div>
<div id="flow"></div>
<pre id="raw"></pre>
</main>
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
    mermaid.initialize({json.dumps(config)});
    const r = await mermaid.render("flow-svg", diagram);
    document.getElementById("flow").innerHTML = r.svg;
    const svg = document.querySelector("#flow svg");
    const layer = document.createElementNS(SVGNS, "g");
    svg.appendChild(layer);
    for (const [step, ids] of Object.entries(uses)) badge(svg, layer, step, ids.map(id => tools[id]));
    svg.style.maxWidth = "100%"; svg.style.height = "auto";
    fit();
  }} catch (e) {{ plain(); }}
}})();
</script>
</body></html>
"""

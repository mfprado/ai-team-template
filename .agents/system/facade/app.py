"""Team page: see what the team's AI workspace has and manage its settings.

Opened by the team launcher (Streamlit, on this computer only). It never creates skills.
Changes to settings are shared like any other change: the AI Champion's go straight to the
team; anyone else's become a change request the Champion approves (propose_change.py).
"""

import datetime
import json
import platform
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import flow_page  # next to this file

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / ".agents/system"
# Only documents are opened directly; anything else (e.g. .command, .bat, .exe) could run.
SAFE_TO_OPEN = {".html", ".htm", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".csv",
                ".txt", ".md", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt"}

T = {
    "en": {
        "title": "{team} AI workspace", "champion": "AI Champion: {name}",
        "sync": "Get the team's latest", "synced": "Up to date with the team.",
        "sync_fail": "Could not get the team's latest changes right now.",
        "tab_skills": "Skills", "tab_perms": "Permissions", "tab_artifacts": "Artifacts", "tab_history": "History",
        "tab_ideas": "Ideas", "ideas_intro": "Ideas for the team's workspace. Anyone can add one or update its status.",
        "no_ideas": "No ideas yet.", "new_idea": "Your idea", "add_idea": "Add idea",
        "idea_summary": "New idea: {text}", "set_status": "Status", "save_status": "Save status",
        "status_summary": "Idea {n}: {status}",
        "versions": "Earlier versions", "current": "Current version", "go_back": "Go back to this version",
        "go_back_confirm": "**{skill}** will go back to how it was on {date}, for the whole team. You can always come back to a later version here. Go back?",
        "go_back_summary": "Skill {skill}: back to the version from {date}", "no_versions": "No earlier versions yet.",
        "no_skills": "Your team has no skills yet. A skill is a task the AI does the same way for everyone, like a weekly report.",
        "try_asking": "To start, open Claude or Codex in this folder and paste:",
        "ask_skill": "Help me bring an automation I already use to the team.",
        "no_shared": "No shared artifacts yet. Reports, dashboards and small apps the team shares appear here.",
        "ask_report": "Make a report about <topic> and share it with the team.",
        "no_private": "Nothing private on this computer.",
        "up_to_date": "Up to date with the team", "not_synced": "Could not get the team's latest",
        "unshared": "You have changes not shared with the team", "behind": "The team has newer changes",
        "menu": "Menu",
        "how_to_ask": "To use it, open Claude or Codex in this folder and paste this (or say it in your own words):",
        "default_ask": "Use the {name} skill.",
        "no_flow": "No diagram of the steps yet. To add one, paste this in Claude or Codex:",
        "ask_flow": "Add the flow diagram to the {name} skill.",
        "details": "See the step-by-step instructions the AI follows",
        "details_intro": "This is what the AI reads when you ask for this. You do not need it to use the skill.",
        "perms_intro": "What the AI is not allowed to do in this folder. Switch a rule off only if the team agrees.",
        "blocked": "Blocked", "asks": "Asks first", "changed": "You changed:", "on": "on", "off": "off",
        "apply": "Apply for the whole team", "applying": "Sharing the change...",
        "note": "Short message you can send to {name}:",
        "shared": "Shared with the team", "private": "Only on this computer", "no_files": "Nothing here yet.",
        "open": "Open", "show_folder": "Show in folder", 
        "recent": "Recent changes",
        "sensitive": "Changes how the AI works for everyone", "changed_what": "changed",
        "what": {"skill": "skill {x}", "perms": "permissions", "docs": "documents", "reports": "artifacts",
                 "rules": "team rules", "system": "system", "other": "other files"},
        "ago": {"now": "just now", "min": "{n} min ago", "h": "{n} h ago", "d": "{n} days ago"},
        "perm_summary": "Permissions: {items}",
        "reports_intro": "Artifacts are reports, dashboards and small apps made with the AI. Ask the assistant for a new one any time.",
        "shared_by": "by {who}", "view": "View", "back": "Back to the list",
        "open_link": "Open it", "link_note": "This one lives in Claude or Codex. It opens in a new browser tab.",
        "share_team": "Share with the team", "share_confirm": "Everyone on the team will be able to see **{title}**. Share it?",
        "share_yes": "Yes, share it", "share_no": "Cancel", "close": "Close", "share_summary": "Shared artifact: {title}",
                "save": "Save for the whole team",
    },
    "es": {
        "title": "Espacio de IA de {team}", "champion": "IA Champion: {name}",
        "sync": "Traer lo último del equipo", "synced": "Al día con el equipo.",
        "sync_fail": "No se pudieron traer los últimos cambios del equipo ahora.",
        "tab_skills": "Skills", "tab_perms": "Permisos", "tab_artifacts": "Artefactos", "tab_history": "Historial",
        "tab_ideas": "Ideas", "ideas_intro": "Ideas para el espacio del equipo. Cualquiera puede sumar una o cambiar su estado.",
        "no_ideas": "Todavía no hay ideas.", "new_idea": "Tu idea", "add_idea": "Agregar idea",
        "idea_summary": "Nueva idea: {text}", "set_status": "Estado", "save_status": "Guardar estado",
        "status_summary": "Idea {n}: {status}",
        "versions": "Versiones anteriores", "current": "Versión actual", "go_back": "Volver a esta versión",
        "go_back_confirm": "**{skill}** va a volver a como estaba el {date}, para todo el equipo. Siempre podés volver a una versión más nueva desde acá. ¿Volver?",
        "go_back_summary": "Skill {skill}: vuelve a la versión del {date}", "no_versions": "Todavía no hay versiones anteriores.",
        "no_skills": "Tu equipo todavía no tiene skills. Una skill es una tarea que la IA hace igual para todos, como un reporte semanal.",
        "try_asking": "Para empezar, abrí Claude o Codex en esta carpeta y pegá:",
        "ask_skill": "Ayudame a traer al equipo una automatización que ya uso.",
        "no_shared": "Todavía no hay artefactos compartidos. Acá aparecen los reportes, tableros y pequeñas apps que comparte el equipo.",
        "ask_report": "Hacé un reporte sobre <tema> y compartilo con el equipo.",
        "no_private": "No hay nada privado en esta computadora.",
        "up_to_date": "Al día con el equipo", "not_synced": "No se pudo traer lo último del equipo",
        "unshared": "Tenés cambios sin compartir con el equipo", "behind": "El equipo tiene cambios más nuevos",
        "menu": "Menú",
        "how_to_ask": "Para usarla, abrí Claude o Codex en esta carpeta y pegá esto (o pedilo con tus palabras):",
        "default_ask": "Usá la skill {name}.",
        "no_flow": "Todavía no tiene el diagrama de los pasos. Para agregarlo, pegá esto en Claude o Codex:",
        "ask_flow": "Agregá el diagrama de flujo a la skill {name}.",
        "details": "Ver las instrucciones paso a paso que sigue la IA",
        "details_intro": "Esto es lo que lee la IA cuando le pedís esto. No lo necesitás para usar la skill.",
        "perms_intro": "Lo que la IA no puede hacer en esta carpeta. Apagá una regla solo si el equipo está de acuerdo.",
        "blocked": "Bloqueado", "asks": "Pide confirmación", "changed": "Cambiaste:", "on": "activada", "off": "desactivada",
        "apply": "Aplicar para todo el equipo", "applying": "Compartiendo el cambio...",
        "note": "Mensaje corto que podés mandarle a {name}:",
        "shared": "Compartidos con el equipo", "private": "Solo en esta computadora", "no_files": "Todavía no hay nada.",
        "open": "Abrir", "show_folder": "Ver en la carpeta", 
        "recent": "Cambios recientes", "changed_what": "cambió",
        "sensitive": "Cambia cómo funciona la IA para todos",
        "what": {"skill": "la skill {x}", "perms": "los permisos", "docs": "documentos", "reports": "artefactos",
                 "rules": "reglas del equipo", "system": "el sistema", "other": "otros archivos"},
        "ago": {"now": "recién", "min": "hace {n} min", "h": "hace {n} h", "d": "hace {n} días"},
        "perm_summary": "Permisos: {items}",
        "reports_intro": "Los artefactos son reportes, tableros y pequeñas apps hechos con la IA. Pedile uno nuevo al asistente cuando quieras.",
        "shared_by": "de {who}", "view": "Ver", "back": "Volver a la lista",
        "open_link": "Abrir", "link_note": "Este está en Claude o Codex. Se abre en otra pestaña del navegador.",
        "share_team": "Compartir con el equipo", "share_confirm": "Todo el equipo va a poder ver **{title}**. ¿Lo compartís?",
        "share_yes": "Sí, compartir", "share_no": "Cancelar", "close": "Cerrar", "share_summary": "Artefacto compartido: {title}",
                "save": "Guardar para todo el equipo",
    },
}


def run(*args):
    return subprocess.run(list(args), cwd=ROOT, capture_output=True, text=True)


def git(*args):
    return run("git", *args)


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def front_matter(text):
    fields, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line and not line.startswith((" ", "\t")):
                    k, v = line.split(":", 1)
                    fields[k.strip()] = v.strip().strip("\"'")
            body = text[end + 4:]
    return fields, body


def skill_card(name, description):
    """Plain words for a skill: a title, what it does, and a request to paste.

    Descriptions are written for the AI: "<what it does>. Use when someone says "<request>", ..."
    The first part is the summary; the first quoted request is the one to paste.
    """
    title = name.replace("-", " ").capitalize()
    parts = re.split(r"\s*\b(?:Use (?:it )?when|Usar? cuando|Usala cuando)\b", description, maxsplit=1)
    summary, when = parts[0].strip() or description, parts[1] if len(parts) > 1 else ""
    asks = re.findall(r'["\u201c]([^"\u201d]{3,})["\u201d]', when)
    return title, summary, asks[0] if asks else None



def short(text, limit=140):
    """The first sentence, cut at a word if still long: one line in the closed list."""
    first = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]
    return first if len(first) <= limit else first[:limit].rsplit(" ", 1)[0] + "…"


FLOW = re.compile(r"```mermaid[ \t]*\n(.*?)\n[ \t]*```[ \t]*\n?", re.S)


def skill_flow(body):
    """A skill's flow diagram (its first mermaid block) and the instructions without it."""
    m = FLOW.search(body)
    if not m:
        return None, body
    return m.group(1).strip(), body[:m.start()] + body[m.end():]

def show_flow(diagram):
    """The skill's flow, in the company's design (flow_page.py). Clicking a step shows its details."""
    brand = load_json(ROOT / ".agents/brand.json", {})
    page = flow_page.build(diagram, brand, ROOT / ".agents/brand", language=team.get("language", "en"))
    # A first guess at the height; the diagram then sizes its frame to fit.
    components.html(page, height=min(900, 60 * diagram.count("\n")))


def ago(ts, t):
    secs = max(0, int(datetime.datetime.now().timestamp()) - ts)
    if secs < 60:
        return t["ago"]["now"]
    if secs < 3600:
        return t["ago"]["min"].format(n=secs // 60)
    if secs < 86400:
        return t["ago"]["h"].format(n=secs // 3600)
    return t["ago"]["d"].format(n=secs // 86400)


def describe_paths(paths, t):
    found = []
    for p in paths:
        m = re.match(r"\.agents/skills/([^/]+)/", p)
        if m:
            item = t["what"]["skill"].format(x=m.group(1))
        elif p == ".agents/permissions.json":
            item = t["what"]["perms"]
        elif p.startswith(("documents/", "documentos/")):
            item = t["what"]["docs"]
        elif p.startswith(("artifacts/", "artefactos/")):
            item = t["what"]["reports"]
        elif p.startswith((".agents/rules/", ".agents/team.json", ".agents/brand")):
            item = t["what"]["rules"]
        elif p.startswith((".agents/system/", "AGENTS.md", "CLAUDE.md")):
            item = t["what"]["system"]
        elif p.startswith((".claude/", ".codex/")):
            continue  # generated copies: not interesting
        else:
            item = t["what"]["other"]
        if item not in found:
            found.append(item)
    return ", ".join(found)


def show_in_folder(path):
    """Reveal a file in Finder / File Explorer without opening (running) it."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", "-R", str(path)], check=False)
    elif system == "Windows":
        subprocess.run(["explorer", f"/select,{path}"], check=False)
    else:
        webbrowser.open(path.parent.as_uri())


def share(summary, paths):
    """Share a change with the team (published or change request) and show the outcome."""
    result = run(sys.executable, "-I", str(CORE / "scripts/propose_change.py"), "--summary", summary, "--paths", *paths)
    try:
        outcome = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        outcome = {"status": "blocked", "message": result.stderr.strip() or result.stdout.strip()}
    (st.success if outcome.get("status") == "published" else st.warning)(outcome.get("message", ""))


def sync_status():
    """One honest line: in step with the team, or what is different."""
    if not st.session_state.get("synced"):
        return f":orange-background[{t['not_synced']}]"
    unsaved = bool(git("status", "--porcelain").stdout.strip())
    ahead = git("rev-list", "--count", "origin/main..HEAD").stdout.strip() not in ("", "0")
    behind = git("rev-list", "--count", "HEAD..origin/main").stdout.strip() not in ("", "0")
    if unsaved or ahead:
        return f":orange-background[{t['unshared']}]"
    if behind:
        return f":orange-background[{t['behind']}]"
    return f":green-background[{t['up_to_date']}]"


def rule_label(rule):
    what = rule.get("pattern") or rule.get("tool", "")
    return f"{rule.get('reason') or what}  ·  `{what}`"


# ---------- page ----------

team = load_json(ROOT / ".agents/team.json", {})
t = T.get(team.get("language"), T["en"])
champion = team.get("champion", {}).get("name") or "the AI Champion"

logo = ROOT / ".agents/brand/logo.png"
icon = ROOT / ".agents/brand/icon.png"
st.set_page_config(page_title=t["title"].format(team=team.get("team", "Team")), layout="centered",
                   page_icon=str(icon) if icon.exists() else None)
# Section picker that survives reruns (st.tabs jumps back to the first tab when a switch changes).
SECTIONS = [t["tab_skills"], t["tab_artifacts"], t["tab_ideas"], t["tab_perms"], t["tab_history"]]
ICONS = dict(zip(SECTIONS, [":material/auto_awesome:", ":material/bar_chart:", ":material/lightbulb:",
                            ":material/shield:", ":material/history:"]))

with st.sidebar:
    if logo.exists():
        st.image(str(logo), width=140)
    st.markdown(f"### {team.get('team', 'Team')}")
    st.caption(t["champion"].format(name=champion))
    refresh = st.button(t["sync"], icon=":material/refresh:", use_container_width=True)
    if refresh or "synced" not in st.session_state:
        git("fetch", "--quiet")  # then fast-forward, keeping unsaved work (whatever pull.rebase says)
        st.session_state.synced = git("merge", "--ff-only", "--autostash", "--quiet", "@{upstream}").returncode == 0
    st.markdown(sync_status())
    st.divider()
    if st.session_state.get("section") not in SECTIONS:
        st.session_state.section = SECTIONS[0]
    # Menu buttons read like a list: icon and text on the left.
    st.markdown("<style>.st-key-menu button{justify-content:flex-start}"
                ".st-key-menu button>div{justify-content:flex-start}</style>", unsafe_allow_html=True)
    menu = st.container(key="menu")
    for name in SECTIONS:
        current = st.session_state.section == name
        if menu.button(name, icon=ICONS[name], type="primary" if current else "secondary",
                     use_container_width=True, key=f"menu-{name}") and not current:
            st.session_state.section = name
            st.rerun()
    section = st.session_state.section

st.title(section)


def empty_state(text, prompt=None):
    """A friendly empty section: what goes here and, when useful, a request to paste."""
    with st.container(border=True):
        st.write(text)
        if prompt:
            st.caption(t["try_asking"])
            st.code(prompt, language="text")


# Skills: what each does, a request to paste, and earlier versions to go back to
@st.dialog(" ")
def confirm_go_back(name, title, commit, date):
    st.write(t["go_back_confirm"].format(skill=title, date=date))
    yes, no = st.columns(2)
    if yes.button(t["go_back"], type="primary"):
        path = f".agents/skills/{name}"
        with st.spinner(t["applying"]):
            git("restore", f"--source={commit}", "--staged", "--worktree", "--", path)
            run(sys.executable, "-I", str(CORE / "scripts/sync.py"))
            share(t["go_back_summary"].format(skill=title, date=date), [path])
        if st.button(t["close"]):
            st.rerun()
    elif no.button(t["share_no"]):
        st.rerun()


def skill_versions(name, title):
    log = git("log", "--format=%H\x1f%an\x1f%at\x1f%s", "--", f".agents/skills/{name}").stdout.splitlines()
    versions = [l.split("\x1f") for l in log if l.count("\x1f") == 3]
    if len(versions) < 2:
        st.caption(t["no_versions"])
    for i, (commit, who, ts, subject) in enumerate(versions):
        date = datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
        col1, col2 = st.columns([3, 2], vertical_alignment="center")
        col1.write(f"**{subject}**  \n{who} · {date}")
        if i == 0:
            col2.caption(t["current"])
        elif col2.button(t["go_back"], key=f"back-{name}-{commit}"):
            confirm_go_back(name, title, commit, date)



if section == t["tab_skills"]:
    skills = []
    for skill_md in sorted((ROOT / ".agents/skills").glob("*/SKILL.md")):
        fields, body = front_matter(skill_md.read_text(encoding="utf-8"))
        skills.append((skill_md.parent.name, fields.get("description", ""), body))
    if not skills:
        empty_state(t["no_skills"], t["ask_skill"])
    # A list: one row per skill (name and what it does). A click opens it: the flow diagram, the
    # request to paste, the instructions and earlier versions. A second click closes it.
    st.markdown("<style>[class*='st-key-skill-'] button{justify-content:flex-start;text-align:left}"
                "[class*='st-key-skill-'] button>div{justify-content:flex-start}"
                "[class*='st-key-skill-'] button p{font-size:1.05rem;font-weight:600}</style>",
                unsafe_allow_html=True)
    opened = st.session_state.get("open_skill")
    for name, description, body in skills:
        title, summary, ask = skill_card(name, description)
        flow, instructions = skill_flow(body)
        is_open = opened == name
        with st.container(border=True):
            if st.button(title, key=f"skill-{name}", type="tertiary", use_container_width=True,
                         icon=":material/expand_less:" if is_open else ":material/expand_more:"):
                st.session_state.open_skill = None if is_open else name
                st.rerun()
            if not is_open:
                st.caption(short(summary))
                continue
            st.write(summary)
            if flow:
                show_flow(flow)
            st.caption(t["how_to_ask"])
            st.code(ask or t["default_ask"].format(name=name), language="text")
            if not flow:
                st.caption(t["no_flow"])
                st.code(t["ask_flow"].format(name=name), language="text")
            with st.expander(t["details"]):
                st.caption(t["details_intro"])
                st.markdown(instructions)
            with st.expander(t["versions"]):
                skill_versions(name, title)

# Ideas: anyone adds one or sets its status
if section == t["tab_ideas"]:
    st.write(t["ideas_intro"])
    listed = run(sys.executable, "-I", str(CORE / "scripts/ideas.py"), "list")
    try:
        ideas = json.loads(listed.stdout or "[]")
    except ValueError:
        ideas = []
    if not ideas:
        st.caption(t["no_ideas"])
    keys = ["new", "planned", "done"]
    labels = {"en": {"new": "New", "planned": "Planned", "done": "Done"},
              "es": {"new": "Nueva", "planned": "En camino", "done": "Hecha"}}[team.get("language", "en") if team.get("language") in ("en", "es") else "en"]
    for idea in reversed(ideas):
        col1, col2 = st.columns([4, 1.4])
        col1.write(f"**{idea['text']}**  \n{idea['who']} · {idea['date']}")
        choice = col2.selectbox(t["set_status"], keys, index=keys.index(idea["key"]),
                                format_func=labels.get, key=f"idea-{idea['id']}", label_visibility="collapsed")
        if choice != idea["key"] and col2.button(t["save_status"], key=f"save-{idea['id']}"):
            run(sys.executable, "-I", str(CORE / "scripts/ideas.py"), "status", "--id", str(idea["id"]), "--to", choice)
            share(t["status_summary"].format(n=idea["id"], status=labels[choice]), ["IDEAS.md"])
    st.divider()
    with st.form("new-idea", clear_on_submit=True):
        text = st.text_area(t["new_idea"], max_chars=500)
        if st.form_submit_button(t["add_idea"], type="primary") and text.strip():
            run(sys.executable, "-I", str(CORE / "scripts/ideas.py"), "add", "--text", text)
            share(t["idea_summary"].format(text=" ".join(text.split())[:80]), ["IDEAS.md"])
            git("fetch", "--quiet", "origin")

# Permissions: switches; changes are shared via propose_change.py
if section == t["tab_perms"]:
    st.write(t["perms_intro"])
    perms_path = ROOT / ".agents/permissions.json"
    perms = load_json(perms_path, {"rules": []})
    changes = []
    for tier, label in (("deny", t["blocked"]), ("ask", t["asks"])):
        st.subheader(label)
        for i, rule in enumerate(perms.get("rules", [])):
            if rule.get("tier", "deny") != tier:
                continue
            current = rule.get("enabled", True) is not False
            wanted = st.toggle(rule_label(rule), value=current, key=f"rule-{i}")
            if wanted != current:
                changes.append((i, wanted))
    if changes:
        st.divider()
        st.write(t["changed"])
        items = []
        for i, wanted in changes:
            rule = perms["rules"][i]
            items.append(f"{rule.get('reason') or rule.get('pattern')} ({t['on'] if wanted else t['off']})")
            st.write(f"- {items[-1]}")
        if st.button(t["apply"], type="primary"):
            with st.spinner(t["applying"]):
                for i, wanted in changes:
                    if wanted:
                        perms["rules"][i].pop("enabled", None)
                    else:
                        perms["rules"][i]["enabled"] = False
                perms_path.write_text(json.dumps(perms, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                run(sys.executable, "-I", str(CORE / "scripts/sync.py"))
                share(t["perm_summary"].format(items="; ".join(items)), [".agents/permissions.json"])

# Reports: hosted links (Claude or Codex) and files, viewed inside the page
def artifact_folders():
    base = ROOT / ("artefactos" if team.get("language") == "es" else "artifacts")
    return base, base / ("privado" if team.get("language") == "es" else "private")


def report_items():
    base, private = artifact_folders()
    items = []
    for folder, is_private in ((base, False), (private, True)):
        for link in load_json(folder / "links.json", []):
            items.append({"kind": "link", "title": link.get("title", link.get("url")), "url": link.get("url"),
                          "who": link.get("by"), "when": link.get("date"), "private": is_private, "key": link.get("url")})
        if folder.is_dir():
            for p in folder.rglob("*"):
                if not p.is_file() or p.name in ("links.json", ".gitkeep", ".DS_Store") or (not is_private and private in p.parents):
                    continue
                items.append({"kind": "file", "title": p.stem.replace("-", " ").replace("_", " ").capitalize(), "path": p,
                              "who": None, "when": ago(int(p.stat().st_mtime), t), "private": is_private, "key": str(p)})
    return items


def share_report(item):
    """Move a private report to the team's folder and share it (published or change request)."""
    base, private = artifact_folders()
    if item["kind"] == "link":
        mine = [l for l in load_json(private / "links.json", []) if l.get("url") != item["url"]]
        (private / "links.json").write_text(json.dumps(mine, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        team_links = [l for l in load_json(base / "links.json", []) if l.get("url") != item["url"]]
        team_links.append({"title": item["title"], "url": item["url"], "by": item["who"] or git("config", "user.name").stdout.strip(),
                           "date": item["when"] or f"{datetime.date.today()}"})
        (base / "links.json").write_text(json.dumps(team_links, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        target = base / "links.json"
    else:
        target = base / item["path"].relative_to(private)
        while target.exists():
            target = target.with_name(f"{target.stem}-2{target.suffix}")
        target.parent.mkdir(parents=True, exist_ok=True)
        item["path"].rename(target)
    share(t["share_summary"].format(title=item["title"]), [str(target.relative_to(ROOT))])


@st.dialog(" ")
def confirm_share(item):
    st.write(t["share_confirm"].format(title=item["title"]))
    yes, no = st.columns(2)
    if yes.button(t["share_yes"], type="primary"):
        with st.spinner(t["applying"]):
            share_report(item)
        st.session_state.pop("viewing", None)
        if st.button(t["close"]):
            st.rerun()
    elif no.button(t["share_no"]):
        st.rerun()


def show_report(item):
    head, action = st.columns([3, 2])
    head.subheader(item["title"])
    if item["private"] and action.button(t["share_team"], type="primary", use_container_width=True):
        confirm_share(item)
    if item["kind"] == "link":
        st.caption(t["link_note"])
        st.link_button(t["open_link"], item["url"])
        return
    p = item["path"]
    if p.suffix.lower() in (".html", ".htm"):
        # White by default (reports written without a background are unreadable on a dark page).
        page = "<style>html{background:#fff;color:#111}</style>" + p.read_text(encoding="utf-8", errors="replace")
        components.html(page, height=720, scrolling=True)
    elif p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".svg"):
        st.image(str(p))
    elif p.suffix.lower() in (".md", ".txt", ".csv"):
        st.markdown(p.read_text(encoding="utf-8", errors="replace")) if p.suffix.lower() == ".md" else st.text(p.read_text(encoding="utf-8", errors="replace"))
    elif p.suffix.lower() in SAFE_TO_OPEN:
        if st.button(t["open"]):
            webbrowser.open(p.as_uri())
    elif st.button(t["show_folder"]):
        show_in_folder(p)


if section == t["tab_artifacts"]:
    items = report_items()
    viewing = next((i for i in items if i["key"] == st.session_state.get("viewing")), None)
    if viewing:
        if st.button(f"← {t['back']}"):
            st.session_state.pop("viewing", None)
            st.rerun()
        show_report(viewing)
    else:
        st.write(t["reports_intro"])
        for heading, group in ((t["shared"], [i for i in items if not i["private"]]),
                               (t["private"], [i for i in items if i["private"]])):
            st.subheader(heading)
            if not group:
                empty_state(t["no_private"]) if heading == t["private"] else empty_state(t["no_shared"], t["ask_report"])
            for item in group:
                col1, col2 = st.columns([4, 1])
                meta = " · ".join(x for x in (t["shared_by"].format(who=item["who"]) if item["who"] else "", item["when"] or "") if x)
                col1.write(f"**{item['title']}**" + (f"  ·  {meta}" if meta else ""))
                if col2.button(t["view"], key=f"view-{item['key']}"):
                    st.session_state.viewing = item["key"]
                    st.rerun()

# History: who changed what, in plain words
if section == t["tab_history"]:
    st.subheader(t["recent"])
    out = git("log", "-n", "30", "--format=\x1e%an\x1f%at\x1f%s", "--name-only").stdout
    for record in out.split("\x1e")[1:]:
        lines = [l for l in record.splitlines() if l.strip()]
        author, ts, subject = lines[0].split("\x1f")
        what = describe_paths(lines[1:], t)
        sensitive = any(l == ".agents/permissions.json" or l.startswith((".agents/rules/", ".agents/system/", ".agents/team.json")) for l in lines[1:])
        flag = f"  \n  :orange[**{t['sensitive']}**]" if sensitive else ""
        st.write(f"- **{author}** {t['changed_what']} {what or '—'} · {ago(int(ts), t)}  \n  {subject}{flag}")

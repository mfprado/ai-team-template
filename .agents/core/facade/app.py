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

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / ".agents/core"
# Only documents are opened directly; anything else (e.g. .command, .bat, .exe) could run.
SAFE_TO_OPEN = {".html", ".htm", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".csv",
                ".txt", ".md", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt"}

T = {
    "en": {
        "title": "{team} AI workspace", "champion": "AI Champion: {name}",
        "sync": "Get the team's latest", "synced": "Up to date with the team.",
        "sync_fail": "Could not get the team's latest changes right now.",
        "tab_skills": "Skills", "tab_perms": "Permissions", "tab_artifacts": "Artifacts", "tab_history": "History",
        "tab_ideas": "Ideas", "ideas_intro": "Ideas for the team's workspace. Anyone can add one; {name} decides what happens with each.",
        "no_ideas": "No ideas yet.", "new_idea": "Your idea", "add_idea": "Add idea",
        "idea_summary": "New idea: {text}", "set_status": "Status", "save_status": "Save status",
        "status_summary": "Idea {n}: {status}", "waiting": "waiting for {name}",
        "team_skills": "Team skills", "system_skills": "System skills", "no_skills": "Your team has no skills yet. A skill is a task the AI does the same way for everyone, like a weekly report.",
        "try_asking": "To start, open Claude or Codex in this folder and paste:",
        "ask_skill": "Help me bring an automation I already use to the team.",
        "no_shared": "No shared artifacts yet. Reports, dashboards and small apps the team shares appear here.",
        "ask_report": "Make a report about <topic> and share it with the team.",
        "no_private": "Nothing private on this computer.",
        "up_to_date": "Up to date", "not_synced": "Not up to date", "menu": "Menu",
        "how_to_ask": "To use it, open Claude or Codex in this folder and paste this (or say it in your own words):",
        "default_ask": "Use the {name} skill.",
        "details": "See the step-by-step instructions the AI follows",
        "details_intro": "This is what the AI reads when you ask for this. You do not need it to use the skill.",
        "perms_intro": "What the AI is not allowed to do in this folder. Switch a rule off only if the team agrees.",
        "blocked": "Blocked", "asks": "Asks first", "changed": "You changed:", "on": "on", "off": "off",
        "apply": "Apply for the whole team", "applying": "Sharing the change...",
        "note": "Short message you can send to {name}:",
        "shared": "Shared with the team", "private": "Only on this computer", "no_files": "Nothing here yet.",
        "open": "Open", "show_folder": "Show in folder", "pending": "Changes waiting for {name}'s approval", "no_pending": "Nothing waiting for approval.",
        "recent": "Recent changes",
        "sensitive": "Changes how the AI works for everyone", "changed_what": "changed",
        "what": {"skill": "skill {x}", "perms": "permissions", "docs": "documents", "reports": "artifacts",
                 "rules": "team rules", "system": "system", "other": "other files"},
        "ago": {"now": "just now", "min": "{n} min ago", "h": "{n} h ago", "d": "{n} days ago"},
        "perm_summary": "Permissions: {items}",
        "tab_settings": "Settings",
        "reports_intro": "Artifacts are reports, dashboards and small apps made with the AI. Ask the assistant for a new one any time.",
        "shared_by": "by {who}", "view": "View", "back": "Back to the list",
        "open_link": "Open it", "link_note": "This one lives in Claude or Codex. It opens in a new browser tab.",
        "share_team": "Share with the team", "share_confirm": "Everyone on the team will be able to see **{title}**. Share it?",
        "share_yes": "Yes, share it", "share_no": "Cancel", "close": "Close", "share_summary": "Shared artifact: {title}",
        "settings_intro": "Only you ({name}) see these settings.",
        "direct_label": "Teammates' changes wait for my approval before they reach everyone",
        "direct_help": "Off (the usual): everyone's changes reach the team straight away, and History shows who changed what. On: teammates' changes wait in History until you approve them.",
        "direct_summary": "Settings: teammates' changes wait for approval ({state})",
        "save": "Save for the whole team",
    },
    "es": {
        "title": "Espacio de IA de {team}", "champion": "IA Champion: {name}",
        "sync": "Traer lo último del equipo", "synced": "Al día con el equipo.",
        "sync_fail": "No se pudieron traer los últimos cambios del equipo ahora.",
        "tab_skills": "Skills", "tab_perms": "Permisos", "tab_artifacts": "Artefactos", "tab_history": "Historial",
        "tab_ideas": "Ideas", "ideas_intro": "Ideas para el espacio del equipo. Cualquiera puede sumar una; {name} decide qué se hace con cada una.",
        "no_ideas": "Todavía no hay ideas.", "new_idea": "Tu idea", "add_idea": "Agregar idea",
        "idea_summary": "Nueva idea: {text}", "set_status": "Estado", "save_status": "Guardar estado",
        "status_summary": "Idea {n}: {status}", "waiting": "esperando a {name}",
        "team_skills": "Skills del equipo", "system_skills": "Skills del sistema", "no_skills": "Tu equipo todavía no tiene skills. Una skill es una tarea que la IA hace igual para todos, como un reporte semanal.",
        "try_asking": "Para empezar, abrí Claude o Codex en esta carpeta y pegá:",
        "ask_skill": "Ayudame a traer al equipo una automatización que ya uso.",
        "no_shared": "Todavía no hay artefactos compartidos. Acá aparecen los reportes, tableros y pequeñas apps que comparte el equipo.",
        "ask_report": "Hacé un reporte sobre <tema> y compartilo con el equipo.",
        "no_private": "No hay nada privado en esta computadora.",
        "up_to_date": "Al día", "not_synced": "No está al día", "menu": "Menú",
        "how_to_ask": "Para usarla, abrí Claude o Codex en esta carpeta y pegá esto (o pedilo con tus palabras):",
        "default_ask": "Usá la skill {name}.",
        "details": "Ver las instrucciones paso a paso que sigue la IA",
        "details_intro": "Esto es lo que lee la IA cuando le pedís esto. No lo necesitás para usar la skill.",
        "perms_intro": "Lo que la IA no puede hacer en esta carpeta. Apagá una regla solo si el equipo está de acuerdo.",
        "blocked": "Bloqueado", "asks": "Pide confirmación", "changed": "Cambiaste:", "on": "activada", "off": "desactivada",
        "apply": "Aplicar para todo el equipo", "applying": "Compartiendo el cambio...",
        "note": "Mensaje corto que podés mandarle a {name}:",
        "shared": "Compartidos con el equipo", "private": "Solo en esta computadora", "no_files": "Todavía no hay nada.",
        "open": "Abrir", "show_folder": "Ver en la carpeta", "pending": "Pedidos de cambio esperando a {name}", "no_pending": "No hay pedidos de cambio esperando.",
        "recent": "Cambios recientes", "changed_what": "cambió",
        "sensitive": "Cambia cómo funciona la IA para todos",
        "what": {"skill": "la skill {x}", "perms": "los permisos", "docs": "documentos", "reports": "artefactos",
                 "rules": "reglas del equipo", "system": "el sistema", "other": "otros archivos"},
        "ago": {"now": "recién", "min": "hace {n} min", "h": "hace {n} h", "d": "hace {n} días"},
        "perm_summary": "Permisos: {items}",
        "tab_settings": "Configuración",
        "reports_intro": "Los artefactos son reportes, tableros y pequeñas apps hechos con la IA. Pedile uno nuevo al asistente cuando quieras.",
        "shared_by": "de {who}", "view": "Ver", "back": "Volver a la lista",
        "open_link": "Abrir", "link_note": "Este está en Claude o Codex. Se abre en otra pestaña del navegador.",
        "share_team": "Compartir con el equipo", "share_confirm": "Todo el equipo va a poder ver **{title}**. ¿Lo compartís?",
        "share_yes": "Sí, compartir", "share_no": "Cancelar", "close": "Cerrar", "share_summary": "Artefacto compartido: {title}",
        "settings_intro": "Solo vos ({name}) ves esta configuración.",
        "direct_label": "Los cambios del equipo esperan mi aprobación antes de llegar a todos",
        "direct_help": "Apagado (lo habitual): los cambios de todos llegan al equipo enseguida, e Historial muestra quién cambió qué. Prendido: los cambios del equipo esperan en Historial hasta que los apruebes.",
        "direct_summary": "Configuración: los cambios del equipo esperan aprobación ({state})",
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
        elif p.startswith("documents/"):
            item = t["what"]["docs"]
        elif p.startswith("artifacts/"):
            item = t["what"]["reports"]
        elif p.startswith(".agents/local/"):
            item = t["what"]["rules"]
        elif p.startswith((".agents/core/", "AGENTS.md", "CLAUDE.md")):
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
    (st.success if outcome.get("status") in ("published", "requested") else st.warning)(outcome.get("message", ""))
    if outcome.get("note_for_champion"):
        st.write(t["note"].format(name=champion))
        st.code(outcome["note_for_champion"], language=None)


def is_champion():
    email = git("config", "user.email").stdout.strip().lower()
    return bool(email) and email == str(team.get("champion", {}).get("email", "")).lower()


def rule_label(rule):
    what = rule.get("pattern") or rule.get("tool", "")
    return f"{rule.get('reason') or what}  ·  `{what}`"


# ---------- page ----------

team = load_json(ROOT / ".agents/local/team.json", {})
t = T.get(team.get("language"), T["en"])
champion = team.get("champion", {}).get("name") or "the AI Champion"

logo = ROOT / ".agents/local/brand/logo.png"
icon = ROOT / ".agents/local/brand/icon.png"
st.set_page_config(page_title=t["title"].format(team=team.get("team", "Team")), layout="centered",
                   page_icon=str(icon) if icon.exists() else None)
# Section picker that survives reruns (st.tabs jumps back to the first tab when a switch changes).
SECTIONS = [t["tab_skills"], t["tab_artifacts"], t["tab_ideas"], t["tab_perms"], t["tab_history"]]
ICONS = dict(zip(SECTIONS, [":material/auto_awesome:", ":material/bar_chart:", ":material/lightbulb:",
                            ":material/shield:", ":material/history:"]))
if is_champion():
    SECTIONS.append(t["tab_settings"])
    ICONS[t["tab_settings"]] = ":material/settings:"

with st.sidebar:
    if logo.exists():
        st.image(str(logo), width=140)
    st.markdown(f"### {team.get('team', 'Team')}")
    st.caption(t["champion"].format(name=champion))
    status, refresh = st.columns([3, 1], vertical_alignment="center")
    if "synced" not in st.session_state or refresh.button(":material/refresh:", help=t["sync"]):
        st.session_state.synced = git("pull", "--ff-only", "--quiet").returncode == 0
    status.markdown(f":green-background[{t['up_to_date']}]" if st.session_state.get("synced")
                    else f":orange-background[{t['not_synced']}]", help=None if st.session_state.get("synced") else t["sync_fail"])
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


# Skills: read only
if section == t["tab_skills"]:
    system = set(load_json(CORE / "manifest.json", {}).get("system_skills", []))
    skills = []
    for skill_md in sorted((ROOT / ".agents/skills").glob("*/SKILL.md")):
        fields, body = front_matter(skill_md.read_text(encoding="utf-8"))
        skills.append((skill_md.parent.name, fields.get("description", ""), body))
    for heading, group in ((t["team_skills"], [s for s in skills if s[0] not in system]),
                           (t["system_skills"], [s for s in skills if s[0] in system])):
        st.subheader(heading)
        if not group:
            empty_state(t["no_skills"], t["ask_skill"])
        for name, description, body in group:
            title, summary, ask = skill_card(name, description)
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(summary)
                st.caption(t["how_to_ask"])
                st.code(ask or t["default_ask"].format(name=name), language="text")
                with st.expander(t["details"]):
                    st.caption(t["details_intro"])
                    st.markdown(body)

# Ideas: anyone adds; the AI Champion sets the status
if section == t["tab_ideas"]:
    st.write(t["ideas_intro"].format(name=champion))
    listed = run(sys.executable, "-I", str(CORE / "scripts/ideas.py"), "list")
    try:
        ideas = json.loads(listed.stdout or "[]")
    except ValueError:
        ideas = []
    # Ideas still waiting in change requests (not yet in the team's version)
    known = {(i["date"], i["who"], i["text"]) for i in ideas}
    waiting = []
    line = re.compile(r"^- \[[^\]]+\] (\d{4}-\d{2}-\d{2}) · (.+?) — (.+)$")
    for b in git("branch", "-r", "--list", "origin/change/*").stdout.split():
        for l in git("show", f"{b}:IDEAS.md").stdout.splitlines():
            m = line.match(l)
            if m and m.groups() not in known and m.groups() not in waiting:
                waiting.append(m.groups())
    for date, who, text in reversed(waiting):
        col1, col2 = st.columns([4, 1.4])
        col1.write(f"**{text}**  \n{who} · {date}")
        col2.caption(t["waiting"].format(name=champion))
    if not ideas and not waiting:
        st.caption(t["no_ideas"])
    champion_here = is_champion()
    for idea in reversed(ideas):
        col1, col2 = st.columns([4, 1.4])
        col1.write(f"**{idea['text']}**  \n{idea['who']} · {idea['date']}")
        if champion_here:
            keys = ["new", "planned", "done"]
            labels = {"en": {"new": "New", "planned": "Planned", "done": "Done"},
                      "es": {"new": "Nueva", "planned": "En camino", "done": "Hecha"}}[team.get("language", "en") if team.get("language") in ("en", "es") else "en"]
            choice = col2.selectbox(t["set_status"], keys, index=keys.index(idea["key"]),
                                    format_func=labels.get, key=f"idea-{idea['id']}", label_visibility="collapsed")
            if choice != idea["key"] and col2.button(t["save_status"], key=f"save-{idea['id']}"):
                run(sys.executable, "-I", str(CORE / "scripts/ideas.py"), "status", "--id", str(idea["id"]), "--to", choice)
                share(t["status_summary"].format(n=idea["id"], status=labels[choice]), ["IDEAS.md"])
        else:
            col2.write(f"`{idea['status']}`")
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

# Settings: only the AI Champion
if section == t.get("tab_settings") and is_champion():
    st.caption(t["settings_intro"].format(name=champion))
    current = bool(team.get("changes_need_approval"))
    wanted = st.toggle(t["direct_label"], value=current, help=t["direct_help"])
    if wanted != current and st.button(t["save"], type="primary"):
        team_file = ROOT / ".agents/local/team.json"
        data = load_json(team_file, {})
        if wanted:
            data["changes_need_approval"] = True
        else:
            data.pop("changes_need_approval", None)
        team_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with st.spinner(t["applying"]):
            share(t["direct_summary"].format(state=t["on"] if wanted else t["off"]), [".agents/local/team.json"])

# History: who changed what, in plain words
if section == t["tab_history"]:
    pending = [b.strip().removeprefix("origin/") for b in git("branch", "-r", "--list", "origin/change/*").stdout.splitlines()]
    if pending or team.get("changes_need_approval"):
        st.subheader(t["pending"].format(name=champion))
    if not pending and team.get("changes_need_approval"):
        st.caption(t["no_pending"])
    for b in pending:
        log = git("log", "-1", "--format=%an\x1f%at\x1f%s", f"origin/{b}").stdout.strip().split("\x1f")
        if len(log) == 3:
            st.write(f"- **{log[0]}** · {ago(int(log[1]), t)} · {log[2]}")

    st.subheader(t["recent"])
    out = git("log", "-n", "30", "--format=\x1e%an\x1f%at\x1f%s", "--name-only").stdout
    for record in out.split("\x1e")[1:]:
        lines = [l for l in record.splitlines() if l.strip()]
        author, ts, subject = lines[0].split("\x1f")
        what = describe_paths(lines[1:], t)
        sensitive = any(l == ".agents/permissions.json" or l.startswith((".agents/local/", ".agents/core/")) for l in lines[1:])
        flag = f"  \n  :orange[**{t['sensitive']}**]" if sensitive else ""
        st.write(f"- **{author}** {t['changed_what']} {what or '—'} · {ago(int(ts), t)}  \n  {subject}{flag}")

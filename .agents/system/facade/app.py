"""Team page: see what the team's AI workspace has and manage its settings.

Opened by the team launcher (Streamlit, on this computer only). It never creates skills.
Changes to settings are shared like any other change: the AI Champion's go straight to the
team; anyone else's become a change request the Champion approves (propose_change.py).
"""

import base64
import datetime
import html
import json
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import flow_page  # next to this file
import look

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / ".agents/system"
# Only documents are opened directly; anything else (e.g. .command, .bat, .exe) could run.
SAFE_TO_OPEN = {".html", ".htm", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".csv",
                ".txt", ".md", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt"}

T = {
    "en": {
        "title": "{team} AI workspace", "champion": "AI Champion: {name}",
        "sync": "Get the team's latest", "night": "Night mode", "day": "Day mode", "synced": "Up to date with the team.",
        "sync_fail": "Could not get the team's latest changes right now.",
        "tab_skills": "Skills", "tab_perms": "General permissions", "tab_artifacts": "Artifacts", "tab_history": "History",
        "tab_docs": "Documents", "docs_intro": "What is in the team's documents folder. Click one to see it here.", "no_docs": "The documents folder is empty. Put the team's documents there (or ask the AI assistant to).", "tab_ideas": "Ideas", "ideas_intro": "Ideas for the team's workspace. Anyone can add one or update its status.",
        "no_ideas": "No ideas yet.", "comment": "Comment", "comment_hint": "Add a comment", "comment_send": "Comment",
        "comment_summary": "Comment on idea {n}", "new_idea": "Title", "new_idea_hint": "Your idea in a few words", "new_idea_text": "Description", "new_idea_text_hint": "Tell the team more: what it would solve, who it helps (optional)", "comments_n": "Comments ({n})", "idea_flow": "See the workflow", "done_n": "Show done ideas ({n})", "archived_n": "Show archived ideas ({n})", "take_idea": "I'll take it", "drop_idea": "Let it go", "taken_by": "{who} is on it", "assign_summary": "Idea {n}: {who} is on it", "unassign_summary": "Idea {n}: free again", "add_idea": "Add", "days": ["today", "yesterday", "{n} days ago"],
        "idea_summary": "New idea: {text}", "set_status": "Status", "save_status": "Save status",
        "status_summary": "Idea {n}: {status}",
        "versions": "Earlier versions", "perms_title": "Permissions", "current": "Current version", "go_back": "Go back to this version",
        "go_back_confirm": "**{skill}** will go back to how it was on {date}, for the whole team. You can always come back to a later version here. Go back?",
        "go_back_summary": "Skill {skill}: back to the version from {date}", "no_versions": "No earlier versions yet.",
        "no_skills": "Your team has no skills yet. A skill is a task the AI does the same way for everyone, like a weekly report.",
        "try_asking": "For example, ask your AI assistant:",
        "ask_skill": "Help me bring an automation I already use to the team.",
        "no_shared": "Nothing shared yet.",
        "ask_report": "Make a report on this month's sales by region.",
        "no_private": "What you make with the AI shows up here. Share it when it is ready.",
        "up_to_date": "Up to date with the team", "not_synced": "Could not get the team's latest",
        "unshared": "You have changes not shared with the team",
        "pending_what": "Not shared yet: {what}.", "saved_changes": "changes saved on this computer",
        "share_pending": "Share with the team",
        "pending_confirm": "This saves for the whole team: {what}. Everyone will have it the next time they get the team's latest.",
        "pending_summary": "Shared: {what}", "behind": "The team has newer changes",
        "menu": "Menu",
        "how_to_ask": "To use it, open your AI assistant in this folder and paste this (or say it in your own words):",
        "default_ask": "Use the {name} skill.",
        "no_flow": "No diagram of the steps yet. To add one, paste this in your AI assistant:",
        "ask_flow": "Add the flow diagram to the {name} skill.",
        "details": "See the step-by-step instructions the AI follows",
        "details_intro": "This is what the AI reads when you ask for this. You do not need it to use the skill.",
        "perms_intro": "What the AI is not allowed to do in this folder, in every conversation and every skill. Switch a rule off only if the team agrees. What each skill may do without asking is in that skill.",
        "skill_perms": "Can do without asking, while this skill runs:", "general_perms_link": "The general permissions still apply",
        "no_skill_perms": "Nothing: it asks before every action.",
        "perm_off_confirm": "From now on, **{skill}** will ask before: {perm}. This applies to the whole team.",
        "perm_on_confirm": "From now on, **{skill}** will do this without asking: {perm}. This applies to the whole team.",
        "perm_on": "Switch on", "perm_off": "Switch off", "rule_help": "For the AI assistant: {rule}",
        "perm_off_summary": "Skill {skill}: asks again before {perm}",
        "perm_on_summary": "Skill {skill}: {perm} without asking",
        "add_perm": "To let it do something else without asking, ask your AI assistant, for example:",
        "ask_perm": "Let the {name} skill create Gmail drafts without asking.",
        "blocked": "Blocked", "asks": "Asks first", "changed": "You changed:", "on": "on", "off": "off",
        "apply": "Apply for the whole team", "applying": "Sharing the change...",
        "note": "Short message you can send to {name}:",
        "shared": "Shared with the team", "private": "Only on this computer", "no_files": "Nothing here yet.",
        "open": "Open", "show_folder": "Show in folder", 
        "recent": "Recent changes", "no_history": "Nothing saved for the team yet. Every change shows up here, with who made it.",
        "sensitive": "Changes how the AI works for everyone", "changed_what": "changed",
        "what": {"skill": "skill {x}", "perms": "permissions", "docs": "documents", "reports": "artifacts",
                 "rules": "team rules", "brand": "the company's brand", "ideas": "the ideas", "system": "system", "other": "other files"},
        "ago": {"now": "just now", "min": "{n} min ago", "h": "{n} h ago", "d": "{n} days ago"},
        "perm_summary": "Permissions: {items}",
        "reports_intro": "Reports, presentations, dashboards and apps made with the AI.",
        "shared_by": "by {who}", "view": "View", "back": "Back to the list", "about_artifact": "What it is and how to make it again", "app_failed": "The app could not start. Ask the AI assistant to look at it.", "app_opening": "Starting the app. It can take a few seconds the first time.",
        "open_link": "Open it", "open_browser": "Open in the browser", "what_it_is": "What it is", "link_note": "This one lives in your AI assistant. It opens in a new browser tab.",
        "share_team": "Share with the team", "share_confirm": "**{title}** moves to the team's artifacts and is saved for the whole team: everyone will be able to see it and change it.",
        "share_yes": "Share", "share_no": "Cancel", "delete": "Delete", "delete_yes": "Delete it", "delete_confirm": "**{title}** is only on this computer: deleting it cannot be undone.", "deleted": "Deleted: {title}.", "close": "Close", "share_summary": "Shared artifact: {title}",
                "save": "Save for the whole team",
    },
    "es": {
        "title": "Espacio de IA de {team}", "champion": "IA Champion: {name}",
        "sync": "Traer lo último del equipo", "night": "Modo noche", "day": "Modo día", "synced": "Al día con el equipo.",
        "sync_fail": "No se pudieron traer los últimos cambios del equipo ahora.",
        "tab_skills": "Skills", "tab_perms": "Permisos generales", "tab_artifacts": "Artefactos", "tab_history": "Historial",
        "tab_docs": "Documentos", "docs_intro": "Lo que hay en la carpeta de documentos del equipo. Hacé clic en uno para verlo acá.", "no_docs": "La carpeta de documentos está vacía. Poné ahí los documentos del equipo (o pedíselo al asistente de IA).", "tab_ideas": "Ideas", "ideas_intro": "Ideas para el espacio del equipo. Cualquiera puede sumar una o cambiar su estado.",
        "no_ideas": "Todavía no hay ideas.", "comment": "Comentario", "comment_hint": "Sumá un comentario", "comment_send": "Comentar",
        "comment_summary": "Comentario en la idea {n}", "new_idea": "Título", "new_idea_hint": "Tu idea en pocas palabras", "new_idea_text": "Descripción", "new_idea_text_hint": "Contale más al equipo: qué resolvería, a quién ayuda (opcional)", "comments_n": "Comentarios ({n})", "idea_flow": "Ver el flujo", "done_n": "Mostrar las hechas ({n})", "archived_n": "Mostrar las archivadas ({n})", "take_idea": "Me la asigno", "drop_idea": "Soltarla", "taken_by": "La tiene {who}", "assign_summary": "Idea {n}: la tiene {who}", "unassign_summary": "Idea {n}: quedó libre", "add_idea": "Agregar", "days": ["hoy", "ayer", "hace {n} días"],
        "idea_summary": "Nueva idea: {text}", "set_status": "Estado", "save_status": "Guardar estado",
        "status_summary": "Idea {n}: {status}",
        "versions": "Versiones anteriores", "perms_title": "Permisos", "current": "Versión actual", "go_back": "Volver a esta versión",
        "go_back_confirm": "**{skill}** va a volver a como estaba el {date}, para todo el equipo. Siempre podés volver a una versión más nueva desde acá. ¿Volver?",
        "go_back_summary": "Skill {skill}: vuelve a la versión del {date}", "no_versions": "Todavía no hay versiones anteriores.",
        "no_skills": "Tu equipo todavía no tiene skills. Una skill es una tarea que la IA hace igual para todos, como un reporte semanal.",
        "try_asking": "Por ejemplo, pedile a tu asistente de IA:",
        "ask_skill": "Ayudame a traer al equipo una automatización que ya uso.",
        "no_shared": "Todavía no hay nada compartido.",
        "ask_report": "Hacé un reporte de las ventas del mes por región.",
        "no_private": "Lo que hagas con la IA aparece acá. Compartilo cuando esté listo.",
        "up_to_date": "Al día con el equipo", "not_synced": "No se pudo traer lo último del equipo",
        "unshared": "Tenés cambios sin compartir con el equipo", "behind": "El equipo tiene cambios más nuevos",
        "pending_what": "Falta compartir: {what}.", "saved_changes": "cambios guardados en esta computadora",
        "share_pending": "Compartir con el equipo",
        "pending_confirm": "Se guarda para todo el equipo: {what}. Todos lo van a tener la próxima vez que traigan lo último del equipo.",
        "pending_summary": "Compartido: {what}",
        "menu": "Menú",
        "how_to_ask": "Para usarla, abrí tu asistente de IA en esta carpeta y pegá esto (o pedilo con tus palabras):",
        "default_ask": "Usá la skill {name}.",
        "no_flow": "Todavía no tiene el diagrama de los pasos. Para agregarlo, pegá esto en tu asistente de IA:",
        "ask_flow": "Agregá el diagrama de flujo a la skill {name}.",
        "details": "Ver las instrucciones paso a paso que sigue la IA",
        "details_intro": "Esto es lo que lee la IA cuando le pedís esto. No lo necesitás para usar la skill.",
        "perms_intro": "Lo que la IA no puede hacer en esta carpeta, en cualquier conversación y en cualquier skill. Apagá una regla solo si el equipo está de acuerdo. Lo que cada skill puede hacer sin preguntar está en esa skill.",
        "skill_perms": "Puede hacer sin preguntar, mientras corre esta skill:", "general_perms_link": "Los permisos generales siguen valiendo",
        "no_skill_perms": "Nada: pregunta antes de cada acción.",
        "perm_off_confirm": "Desde ahora, **{skill}** va a preguntar antes de: {perm}. Vale para todo el equipo.",
        "perm_on_confirm": "Desde ahora, **{skill}** va a hacer esto sin preguntar: {perm}. Vale para todo el equipo.",
        "perm_on": "Encender", "perm_off": "Apagar", "rule_help": "Para el asistente de IA: {rule}",
        "perm_off_summary": "Skill {skill}: vuelve a preguntar antes de {perm}",
        "perm_on_summary": "Skill {skill}: {perm} sin preguntar",
        "add_perm": "Para que haga otra cosa sin preguntar, pedíselo a tu asistente de IA, por ejemplo:",
        "ask_perm": "Dejá que la skill {name} cree borradores en Gmail sin preguntar.",
        "blocked": "Bloqueado", "asks": "Pide confirmación", "changed": "Cambiaste:", "on": "activada", "off": "desactivada",
        "apply": "Aplicar para todo el equipo", "applying": "Compartiendo el cambio...",
        "note": "Mensaje corto que podés mandarle a {name}:",
        "shared": "Compartidos con el equipo", "private": "Solo en esta computadora", "no_files": "Todavía no hay nada.",
        "open": "Abrir", "show_folder": "Ver en la carpeta", 
        "recent": "Cambios recientes", "no_history": "Todavía no hay nada guardado para el equipo. Acá aparece cada cambio, con quién lo hizo.", "changed_what": "cambió",
        "sensitive": "Cambia cómo funciona la IA para todos",
        "what": {"skill": "la skill {x}", "perms": "los permisos", "docs": "documentos", "reports": "artefactos",
                 "rules": "reglas del equipo", "brand": "la marca de la empresa", "ideas": "las ideas", "system": "el sistema", "other": "otros archivos"},
        "ago": {"now": "recién", "min": "hace {n} min", "h": "hace {n} h", "d": "hace {n} días"},
        "perm_summary": "Permisos: {items}",
        "reports_intro": "Reportes, presentaciones, tableros y apps hechos con la IA.",
        "shared_by": "de {who}", "view": "Ver", "back": "Volver a la lista", "about_artifact": "Qué es y cómo volver a hacerlo", "app_failed": "La app no pudo arrancar. Pedile al asistente de IA que la revise.", "app_opening": "Abriendo la app. La primera vez puede tardar unos segundos.",
        "open_link": "Abrir", "open_browser": "Abrir en el navegador", "what_it_is": "Qué es", "link_note": "Este está en tu asistente de IA. Se abre en otra pestaña del navegador.",
        "share_team": "Compartir con el equipo", "share_confirm": "**{title}** pasa a los artefactos del equipo y se guarda para todos: cualquiera va a poder verlo y cambiarlo.",
        "share_yes": "Compartir", "share_no": "Cancelar", "delete": "Borrar", "delete_yes": "Borrarlo", "delete_confirm": "**{title}** está solo en esta computadora: si lo borrás, no se puede recuperar.", "deleted": "Borrado: {title}.", "close": "Cerrar", "share_summary": "Artefacto compartido: {title}",
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
    brand = look.in_mode(load_json(ROOT / ".agents/brand.json", {}), st.session_state.night)  # day or night, like the page
    page = flow_page.build(diagram, brand, ROOT / ".agents/brand", language=team.get("language", "en"))
    # A first guess at the height; the diagram then sizes its frame to fit.
    components.html(page, height=min(900, 60 * diagram.count("\n")))


MONTHS = {"en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(),
          "es": "ene feb mar abr may jun jul ago sep oct nov dic".split()}


def nice_date(iso):
    """2026-11-27 as people say it: today, yesterday, 3 days ago, or 27 Nov."""
    try:
        day = datetime.date.fromisoformat(iso)
    except ValueError:
        return iso
    days = (datetime.date.today() - day).days
    if 0 <= days <= 6:
        return t["days"][min(days, 2)].format(n=days)
    months = MONTHS.get(team.get("language"), MONTHS["en"])
    when = f"{day.day} {months[day.month - 1]}" if team.get("language") == "es" else f"{months[day.month - 1]} {day.day}"
    return when if day.year == datetime.date.today().year else f"{when} {day.year}"


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
        elif p == "IDEAS.md" or p.startswith(".agents/ideas/"):
            item = t["what"]["ideas"]
        elif p.startswith(".agents/brand"):
            item = t["what"]["brand"]
        elif p.startswith((".agents/rules/", ".agents/team.json")):
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
    """Save a change for the team (propose_change.py); its outcome shows at the top of the page."""
    result = run(sys.executable, "-I", str(CORE / "scripts/propose_change.py"), "--summary", summary,
                 *(["--paths", *paths] if paths else []))  # no paths: everything not yet shared
    try:
        outcome = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        outcome = {"status": "blocked", "message": result.stderr.strip() or result.stdout.strip()}
    flash(outcome.get("status") == "published", outcome.get("message", ""))


def flash(ok, message):
    """A message for the top of the page after the next refresh (windows close on their own)."""
    st.session_state.flash = (ok, message)
    if not st.session_state.get("in_dialog"):
        st.rerun()


def pending_changes():
    """Files changed here and not yet shared, as git paths (generated copies included)."""
    paths = []
    for line in git("status", "--porcelain").stdout.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if path:
            paths.append(path)
    return paths


@st.dialog(" ")
def confirm_share_pending(what):
    st.write(t["pending_confirm"].format(what=what))
    yes, no, _ = st.columns([1, 1, 2])
    if yes.button(t["share_yes"], type="primary", use_container_width=True):
        st.session_state.in_dialog = True
        with st.spinner(t["applying"]):
            share(t["pending_summary"].format(what=what), [])
        st.rerun()
    elif no.button(t["share_no"], use_container_width=True):
        st.rerun()


def sync_status():
    """One honest line: in step with the team, or what is different. (text, all good?)"""
    if not st.session_state.get("synced"):
        return t["not_synced"], False
    unsaved = bool(git("status", "--porcelain").stdout.strip())
    ahead = git("rev-list", "--count", "origin/main..HEAD").stdout.strip() not in ("", "0")
    behind = git("rev-list", "--count", "HEAD..origin/main").stdout.strip() not in ("", "0")
    if unsaved or ahead:
        return t["unshared"], False
    if behind:
        return t["behind"], False
    return t["up_to_date"], True


def rule_label(rule):
    return rule.get("reason") or rule.get("pattern") or rule.get("tool", "")


# ---------- page ----------

team = load_json(ROOT / ".agents/team.json", {})
t = T.get(team.get("language"), T["en"])
champion = team.get("champion", {}).get("name") or "the AI Champion"

logo = ROOT / ".agents/brand/logo.png"
icon = ROOT / ".agents/brand/icon.png"
st.set_page_config(page_title=t["title"].format(team=team.get("team", "Team")), layout="centered",
                   page_icon=str(icon) if icon.exists() else None)
brand = load_json(ROOT / ".agents/brand.json", {})
# Night or day: the person's choice, kept in the address so a reload remembers it.
if "night" not in st.session_state:
    choice = st.query_params.get("mode")
    st.session_state.night = look.is_dark_brand(brand) if choice not in ("night", "day") else choice == "night"
st.query_params["mode"] = "night" if st.session_state.night else "day"
st.markdown(look.css(look.in_mode(brand, st.session_state.night)), unsafe_allow_html=True)
# Copy buttons: show "Copied!" for a moment after a click (the copy itself blurs the button,
# so CSS alone cannot tell). The script runs in a hidden frame of the same page.
components.html("""<script>
const doc = window.parent.document;
if (!doc.body.dataset.copyFeedback) {
  doc.body.dataset.copyFeedback = "1";
  doc.addEventListener("click", e => {
    const b = e.target.closest('[data-testid="stCodeCopyButton"]');
    if (!b) return;
    b.classList.add("copied");
    setTimeout(() => b.classList.remove("copied"), 1500);
  }, true);
}
</script>""", height=0)
# Section picker that survives reruns (st.tabs jumps back to the first tab when a switch changes).
SECTIONS = [t["tab_artifacts"], t["tab_docs"], t["tab_skills"], t["tab_ideas"], t["tab_perms"], t["tab_history"]]
ICONS = dict(zip(SECTIONS, [":material/bar_chart:", ":material/folder:", ":material/auto_awesome:",
                            ":material/lightbulb:", ":material/shield:", ":material/history:"]))

with st.sidebar:
    name_col, mode_col = st.columns([6, 1], vertical_alignment="top")
    name_col.markdown(look.team_header(logo, team.get("team", "Team"), t["champion"].format(name=champion)),
                      unsafe_allow_html=True)

    def flip_mode():
        st.session_state.night = not st.session_state.night

    # Sun in night mode (to go to day), moon in day mode (to go to night).
    with mode_col.container(key="modeswitch"):
        st.button("", icon=":material/light_mode:" if st.session_state.night else ":material/dark_mode:",
                  type="tertiary", help=t["day" if st.session_state.night else "night"], on_click=flip_mode)
    refresh = st.button(t["sync"], icon=":material/refresh:", use_container_width=True)
    if refresh or "synced" not in st.session_state:
        git("fetch", "--quiet")  # then fast-forward, keeping unsaved work (whatever pull.rebase says)
        st.session_state.synced = git("merge", "--ff-only", "--autostash", "--quiet", "@{upstream}").returncode == 0
    status, ok = sync_status()
    st.markdown(look.sync_badge(status, ok), unsafe_allow_html=True)
    if status == t["unshared"]:
        # Say what is waiting, and let the person share it from here.
        what = describe_paths(pending_changes(), t) or t["saved_changes"]
        st.caption(t["pending_what"].format(what=what))
        if st.button(t["share_pending"], icon=":material/group:", use_container_width=True, key="share-pending"):
            confirm_share_pending(what)
    st.divider()
    if st.session_state.get("section") not in SECTIONS:
        st.session_state.section = SECTIONS[0]
    menu = st.container(key="menu")
    for name in SECTIONS:
        current = st.session_state.section == name
        folded = st.session_state.get(f"fold-{name}", False)
        if menu.button(name, icon=ICONS[name], type="primary" if current else "secondary",
                     use_container_width=True, key=f"menu-{name}"):
            if current and not st.session_state.get("viewing") and not st.session_state.get("viewing_doc"):
                # Clicking the open section again hides or shows its list underneath.
                st.session_state[f"fold-{name}"] = not folded
                st.rerun()
            # A section's own entry takes you back to its start (out of an artifact, a skill).
            st.session_state.section = name
            st.session_state.pop("viewing", None)
            st.session_state.pop("viewing_doc", None)
            st.rerun()
        if name == t["tab_docs"] and current:
            docs_menu = menu.container(key="docsmenu-folded" if folded else "docsmenu")  # filled in the Documents section
        if name == t["tab_artifacts"] and current:
            # Filled further down, once the artifacts are listed: one entry per artifact.
            artifact_menu = menu.container(key="artmenu-folded" if folded else "artmenu")
    section = st.session_state.section

if not ((section == t["tab_artifacts"] and st.session_state.get("viewing"))
        or (section == t["tab_docs"] and st.session_state.get("viewing_doc"))):  # an open artifact gets the whole page
    st.title(section)
st.session_state.pop("in_dialog", None)
if "flash" in st.session_state:
    ok, message = st.session_state.pop("flash")
    if message:
        (st.success if ok else st.warning)(message, icon=":material/check_circle:" if ok else ":material/warning:")


def card_hit(key, on_click):
    """An invisible button over the whole card (look.py): a click anywhere on it opens it."""
    st.button(" ", key=f"cardhit-{abs(hash(key)) % 10**9}", on_click=on_click)


def empty_state(text, prompt=None):
    """A friendly empty section: what goes here and, when useful, a request to paste."""
    with st.container(border=True):
        st.write(text)
        if prompt:
            st.caption(t["try_asking"])
            with st.container(key=f"example-{abs(hash(prompt)) % 10**6}"):
                st.code(prompt, language="text")


# Skills: what each does, a request to paste, and earlier versions to go back to
@st.dialog(" ")
def confirm_go_back(name, title, commit, date):
    st.write(t["go_back_confirm"].format(skill=title, date=date))
    yes, no = st.columns(2)
    if yes.button(t["go_back"], type="primary"):
        path = f".agents/skills/{name}"
        st.session_state.in_dialog = True
        with st.spinner(t["applying"]):
            git("restore", f"--source={commit}", "--staged", "--worktree", "--", path)
            run(sys.executable, "-I", str(CORE / "scripts/sync.py"))
            share(t["go_back_summary"].format(skill=title, date=date), [path])
        st.rerun()
    elif no.button(t["share_no"]):
        st.rerun()


def skill_permissions(name):
    """What the skill may do without asking (skill_permissions.py), in plain words."""
    listed = run(sys.executable, "-I", str(CORE / "scripts/skill_permissions.py"), "list", "--skill", name,
                 "--language", team.get("language", "en"))
    try:
        return json.loads(listed.stdout or "[]")
    except ValueError:
        return []


@st.dialog(" ")
def confirm_skill_permission(name, title, perm, wanted, key):
    """Switch one of a skill's permissions on or off, for the whole team, after an OK."""
    st.write(t["perm_on_confirm" if wanted else "perm_off_confirm"].format(skill=title, perm=perm["plain"]))
    yes, no, _ = st.columns([1, 1, 2])
    if yes.button(t["perm_on"] if wanted else t["perm_off"], type="primary", use_container_width=True):
        st.session_state.in_dialog = True
        with st.spinner(t["applying"]):
            run(sys.executable, "-I", str(CORE / "scripts/skill_permissions.py"), "on" if wanted else "off",
                "--skill", name, "--rule", perm["rule"])
            run(sys.executable, "-I", str(CORE / "scripts/sync.py"))
            share(t["perm_on_summary" if wanted else "perm_off_summary"].format(skill=title, perm=perm["plain"]),
                  [f".agents/skills/{name}"])
        st.rerun()
    elif no.button(t["share_no"], use_container_width=True):
        st.session_state[f"{key}-undo"] = True  # the switch goes back to how it was
        st.rerun()


def show_skill_permissions(name, title):
    st.caption(t["skill_perms"])
    perms = skill_permissions(name)
    if not perms:
        st.write(t["no_skill_perms"])
    stale = asked = False
    for i, perm in enumerate(perms):
        key = f"perm-{name}-{i}"
        # The switch's value lives in the session only (setting it there and as a default clashes).
        if key not in st.session_state or st.session_state.pop(f"{key}-undo", False):
            st.session_state[key] = perm["on"]
        wanted = st.toggle(perm["plain"], key=key, help=t["rule_help"].format(rule=perm["rule"]),
                           on_change=lambda k=key: st.session_state.update(perm_touched=k))
        if wanted == perm["on"]:
            continue
        if st.session_state.get("perm_touched") == key:
            # Only the switch just touched asks (one window at a time).
            st.session_state.pop("perm_touched")
            asked = True
            confirm_skill_permission(name, title, perm, wanted, key)
        else:
            # Changed without an answer (window closed, or another switch touched): back to what is saved.
            st.session_state[f"{key}-undo"] = True
            stale = True
    if stale and not asked:  # a window open now stays open; the others go back on the next refresh
        st.rerun()
    # A link to the general permissions, which apply on top of these.
    st.button(t["general_perms_link"], key=f"to-perms-{name}", type="tertiary",
              icon=":material/arrow_forward:", on_click=lambda: st.session_state.update(section=t["tab_perms"]))
    st.caption(t["add_perm"])
    with st.container(key=f"example-perm-{name}"):
        st.code(t["ask_perm"].format(name=name), language="text")


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
    opened = st.session_state.get("open_skill")
    for name, description, body in skills:
        title, summary, ask = skill_card(name, description)
        flow, instructions = skill_flow(body)
        is_open = opened == name
        with st.container(border=True, key=f"skillcard-{name}"):
            if st.button(title, key=f"skill-{name}", type="tertiary", use_container_width=True,
                         icon=":material/expand_less:" if is_open else ":material/expand_more:"):
                st.session_state.open_skill = None if is_open else name
                st.rerun()
            if not is_open:
                st.caption(short(summary))
                card_hit(f"skill-{name}", lambda n=name: st.session_state.update(open_skill=n))
                continue
            st.write(summary)
            if flow:
                show_flow(flow)
            st.caption(t["how_to_ask"])
            with st.container(key=f"ask-{name}"):
                st.code(ask or t["default_ask"].format(name=name), language="text")
            with st.expander(t["perms_title"]):
                show_skill_permissions(name, title)
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
    # Every save happens in the click's callback, before the page is drawn again: the list stays
    # as it was while the change is sent to the team, then shows the result (no half-drawn cards).
    keys = ["new", "planned", "done", "archived"]
    labels = {"en": {"new": "New", "planned": "Planned", "done": "Done", "archived": "Archived"},
              "es": {"new": "Nueva", "planned": "En camino", "done": "Hecha", "archived": "Archivada"}}[team.get("language", "en") if team.get("language") in ("en", "es") else "en"]

    def ideas_script(*args):
        run(sys.executable, "-I", str(CORE / "scripts/ideas.py"), *args)

    def save_from_callback(summary):
        st.session_state.in_dialog = True  # inside a callback: the page refreshes on its own afterwards
        share(summary, ["IDEAS.md"])

    def add_idea():
        title = st.session_state.get("new-idea-title", "").strip()
        text = st.session_state.get("new-idea-text", "").strip()
        if title:
            ideas_script("add", "--title", title, "--text", text)
            save_from_callback(t["idea_summary"].format(text=" ".join(title.split())[:80]))

    def change_status(n, current):
        choice = st.session_state.get(f"idea-{n}")
        if not choice:  # clicking the current state again clears the control: keep it
            st.session_state[f"idea-{n}"] = current
        elif choice != current:
            ideas_script("status", "--id", n, "--to", choice)
            save_from_callback(t["status_summary"].format(n=n, status=labels[choice]))

    def assign(n, who):
        if who:
            ideas_script("assign", "--id", n)
            save_from_callback(t["assign_summary"].format(n=n, who=who))
        else:
            ideas_script("assign", "--id", n, "--clear")
            save_from_callback(t["unassign_summary"].format(n=n))

    def add_comment(n):
        text = st.session_state.get(f"comment-{n}", "").strip()
        if text:
            ideas_script("comment", "--id", n, "--text", text)
            save_from_callback(t["comment_summary"].format(n=n))

    # A form sends the title, the description and the click together; it clears itself after saving.
    # A form sends the title, the description and the click together; it clears itself after saving.
    with st.form("new-idea", clear_on_submit=True, border=False):
        st.text_input(t["new_idea"], max_chars=120, placeholder=t["new_idea_hint"], key="new-idea-title",
                      label_visibility="collapsed")
        st.text_area(t["new_idea_text"], max_chars=1000, height=110, placeholder=t["new_idea_text_hint"],
                     key="new-idea-text", label_visibility="collapsed")
        st.form_submit_button(t["add_idea"], type="primary", on_click=add_idea)
    if not ideas:
        st.caption(t["no_ideas"])

    def idea_card(idea):
        n = str(idea["id"])
        # Folded like a skill card: title, author, status and owner always; a click on the title
        # opens the description, the workflow and the comments. A second click folds it again.
        is_open = st.session_state.get("open_idea") == n
        # The key says open or folded, so look.py can drop the height the diagram gave its frame
        # (Streamlit reuses that wrapper, which would stay as an empty space after folding).
        with st.container(border=True, key=f"ideacard-{n}-{'open' if is_open else 'folded'}"):
            head, tag = st.columns([5, 1.7], vertical_alignment="top")
            if head.button(idea["text"], key=f"ideaopen-{n}", type="tertiary", use_container_width=True,
                           icon=":material/expand_less:" if is_open else ":material/expand_more:"):
                st.session_state.open_idea = None if is_open else n
                st.rerun()
            head.markdown(f'<div class="idea-who">{html.escape(idea["who"])}, {nice_date(idea["date"])}</div>',
                          unsafe_allow_html=True)
            # The status is a small coloured tag; clicking it opens the three states to pick another.
            if st.session_state.get(f"idea-{n}") != idea["key"]:
                st.session_state[f"idea-{n}"] = idea["key"]  # follow the file (e.g. after getting the team's latest)
            with tag.container(key=f"ideatag-{idea['key']}-{n}"):
                with st.popover(labels[idea["key"]], use_container_width=True):
                    st.segmented_control(t["set_status"], keys, format_func=labels.get, key=f"idea-{n}",
                                         label_visibility="collapsed", on_change=change_status,
                                         args=(n, idea["key"]))
            # One person per idea, so two people don't work on the same thing: who has it, under the
            # title; the button to take it (or let it go) under the status tag.
            owner, me = idea.get("assignee", ""), idea.get("me", "")
            if owner:
                head.markdown(f'<div class="idea-owner">{html.escape(t["taken_by"].format(who=owner))}</div>',
                              unsafe_allow_html=True)
            with tag.container(key=f"ideaassign-{n}"):
                if owner and owner == me:
                    st.button(t["drop_idea"], key=f"drop-{n}", use_container_width=True,
                              on_click=assign, args=(n, ""))
                elif not owner and idea["key"] not in ("done", "archived"):
                    st.button(t["take_idea"], key=f"take-{n}", use_container_width=True,
                              on_click=assign, args=(n, me or "?"))
            comments = idea.get("comments", [])
            if not is_open:
                if comments:
                    st.caption(t["comments_n"].format(n=len(comments)))
                return
            if idea.get("description"):
                st.markdown(f'<div class="idea-description">{html.escape(idea["description"])}</div>',
                            unsafe_allow_html=True)
            if idea.get("flow"):  # shown open, as on a skill: a diagram drawn while folded has no size
                show_flow(idea["flow"])
            with st.expander(t["comments_n"].format(n=len(comments))):
                for c in comments:
                    st.markdown(f'<div class="idea-comment"><div>{html.escape(c["text"])}</div>'
                                f'<div class="who">{html.escape(c["who"])}, {nice_date(c["date"])}</div></div>',
                                unsafe_allow_html=True)
                with st.form(f"comment-form-{n}", clear_on_submit=True, border=False):
                    st.text_area(t["comment"], placeholder=t["comment_hint"], key=f"comment-{n}",
                                 height=90, max_chars=1000, label_visibility="collapsed")
                    st.form_submit_button(t["comment_send"], on_click=add_comment, args=(n,))

    # Grouped by status, newest first; done ideas stay folded away at the end.
    for key in keys:
        group = [i for i in reversed(ideas) if i["key"] == key]
        if not group:
            continue
        if key in ("done", "archived"):  # a switch, not an expander: comments inside a card already fold
            if st.toggle(t[f"{key}_n"].format(n=len(group)), key=f"show-{key}-ideas"):
                for idea in group:
                    idea_card(idea)
        else:
            st.subheader(f"{labels[key]} · {len(group)}")
            for idea in group:
                idea_card(idea)

# Permissions: switches; changes are shared via propose_change.py
if section == t["tab_perms"]:
    st.write(t["perms_intro"])
    perms_path = ROOT / ".agents/permissions.json"
    perms = load_json(perms_path, {"rules": []})
    changes = []
    for tier, label in (("deny", t["blocked"]), ("ask", t["asks"])):
        st.subheader(label)
        # Rules with the same reason are one switch: people see what is protected, not each command.
        groups = {}
        for i, rule in enumerate(perms.get("rules", [])):
            if rule.get("tier", "deny") == tier:
                groups.setdefault(rule_label(rule), []).append(i)
        for reason, ids in groups.items():
            current = all(perms["rules"][i].get("enabled", True) is not False for i in ids)
            what = ", ".join(perms["rules"][i].get("pattern") or perms["rules"][i].get("tool", "") for i in ids)
            wanted = st.toggle(reason, value=current, key=f"rule-{ids[0]}", help=t["rule_help"].format(rule=what))
            if wanted != current:
                changes.append((ids, wanted))
    if changes:
        st.divider()
        st.write(t["changed"])
        items = []
        for ids, wanted in changes:
            items.append(f"{rule_label(perms['rules'][ids[0]])} ({t['on'] if wanted else t['off']})")
            st.write(f"- {items[-1]}")
        if st.button(t["apply"], type="primary"):
            with st.spinner(t["applying"]):
                for ids, wanted in changes:
                    for i in ids:
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
        if not folder.is_dir():
            continue
        # One entry per artifact folder (<type>/<date>-<name>/ with index.html or README.md,
        # new_artifact.py); loose files from before are listed one by one.
        artifacts = []
        for p in sorted(folder.rglob("*")):
            if (not is_private and (p == private or private in p.parents)) or any(a in p.parents for a in artifacts):
                continue
            if p.is_dir() and ((p / "index.html").is_file() or (p / "README.md").is_file()):
                artifacts.append(p)
                items.append({"kind": "folder", "title": artifact_title(p), "path": p, "type": p.parent.name,
                              "who": None, "when": ago(int(p.stat().st_mtime), t), "private": is_private, "key": str(p)})
            elif p.is_file() and p.name not in ("links.json", ".gitkeep", ".DS_Store"):
                items.append({"kind": "file", "title": p.stem.replace("-", " ").replace("_", " ").capitalize(), "path": p,
                              "who": None, "when": ago(int(p.stat().st_mtime), t), "private": is_private, "key": str(p)})
    return items


def artifact_title(folder):
    """The README's title, else the folder's name without its date."""
    try:
        for line in (folder / "README.md").read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", folder.name).replace("-", " ").capitalize()


def artifact_group(item):
    """The heading an artifact is listed under: its type folder, links apart."""
    if item["kind"] == "link":
        return "Links"
    return (item.get("type") or "").capitalize()


def artifact_icon(item):
    """App (Streamlit) gets an app icon, HTML a code icon, links a link icon."""
    if item["kind"] == "link":
        return ":material/link:"
    p = item["path"]
    if item["kind"] == "folder" and (p / "app.py").is_file():
        return ":material/apps:"
    if (item["kind"] == "folder" and (p / "index.html").is_file()) or p.suffix.lower() in (".html", ".htm"):
        return ":material/code:"
    return ":material/description:"


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
        # Folders and files: the same script the AI uses (moves it, then saves it for the team).
        result = run(sys.executable, "-I", str(CORE / "scripts/share_artifact.py"), "--path", str(item["path"]))
        try:
            outcome = json.loads(result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            outcome = {"ok": False, "message": result.stderr.strip() or result.stdout.strip()}
        flash(bool(outcome.get("ok")), outcome.get("message") or outcome.get("problem", ""))
        return
    share(t["share_summary"].format(title=item["title"]), [str(target.relative_to(ROOT))])


@st.dialog(" ")
def confirm_share(item):
    st.write(t["share_confirm"].format(title=item["title"]))
    yes, no, _ = st.columns([1, 1, 2])
    if yes.button(t["share_yes"], type="primary", use_container_width=True):
        st.session_state.in_dialog = True
        with st.spinner(t["applying"]):
            share_report(item)
        st.session_state.pop("viewing", None)
        st.rerun()
    elif no.button(t["share_no"], use_container_width=True):
        st.rerun()


def delete_private(item):
    """Delete one of your own artifacts. Only inside the private folder, which is never saved for the team."""
    _, private = artifact_folders()
    if item["kind"] == "link":
        mine = [l for l in load_json(private / "links.json", []) if l.get("url") != item["url"]]
        (private / "links.json").write_text(json.dumps(mine, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return True
    target = Path(item["path"]).resolve()
    if private.resolve() not in target.parents:
        return False  # never outside the private folder
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink(missing_ok=True)
    return True


@st.dialog(" ")
def confirm_delete(item):
    st.write(t["delete_confirm"].format(title=item["title"]))
    yes, no, _ = st.columns([1, 1, 2])
    if yes.button(t["delete_yes"], type="primary", use_container_width=True):
        st.session_state.in_dialog = True
        if delete_private(item):
            flash(True, t["deleted"].format(title=item["title"]))
        st.session_state.pop("viewing", None)
        st.rerun()
    elif no.button(t["share_no"], use_container_width=True):
        st.rerun()


def app_port(folder):
    """The port of this app artifact when it is already running (run_app.py keeps them in .git/apps.json)."""
    try:
        port = load_json(ROOT / ".git/apps.json", {}).get(str(Path(folder).relative_to(ROOT)))
        with socket.create_connection(("127.0.0.1", int(port)), timeout=0.5):
            return int(port)
    except (OSError, TypeError, ValueError):
        return None


def start_app(folder):
    """Start a Streamlit app artifact in the background (run_app.py), without opening the browser:
    the team page shows it inside itself."""
    runner = [str(CORE / "facade/run_app.py"), str(folder), "--no-browser"]
    uv = shutil.which("uv") or next((str(u) for u in (Path.home() / ".local/bin/uv", Path.home() / ".local/bin/uv.exe")
                                     if u.is_file()), None)
    if uv:
        extra = ["--with-requirements", str(folder / "requirements.txt")] if (folder / "requirements.txt").is_file() else []
        command = [uv, "run", "--quiet", "--no-project", "--python", "3.12", "--with", "streamlit==1.41.1", *extra, *runner]
    else:
        command = [sys.executable, *runner]  # this page already runs with Streamlit
    subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def artifact_about(item):
    """The 'What it is' section of the artifact's README, for the info button; '' when there is none."""
    if item["kind"] != "folder" or not (item["path"] / "README.md").is_file():
        return ""
    text = (item["path"] / "README.md").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^##\s+(What it is|Qué es)\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    about = (m.group(2) if m else "").strip()
    # The placeholder new_artifact.py leaves ("(One or two lines.)") is not an explanation.
    return "" if not about or re.fullmatch(r"\(.*\)", about) else about


def enter_artifact(item):
    """One click on the artifact's name: it opens inside this page (apps too, started in the background)."""
    if item["kind"] == "folder" and (item["path"] / "app.py").is_file():
        if not app_port(item["path"]):
            start_app(item["path"])
        st.session_state.viewing = item["key"]
    elif item["kind"] == "file" and item["path"].suffix.lower() in SAFE_TO_OPEN \
            and item["path"].suffix.lower() not in (".html", ".htm", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".md", ".txt", ".csv"):
        webbrowser.open(item["path"].as_uri())
    else:
        st.session_state.viewing = item["key"]


PDF_VIEWER = """<style>html,body{margin:0;background:#525659}canvas{display:block;margin:12px auto;max-width:96%;
box-shadow:0 1px 4px rgba(0,0,0,.4);background:#fff}</style><div id="pages"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
const bytes = Uint8Array.from(atob("__DATA__"), c => c.charCodeAt(0));
pdfjsLib.getDocument({data: bytes, standardFontDataUrl: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/standard_fonts/"}).promise.then(async pdf => {
  for (let n = 1; n <= pdf.numPages; n++) {
    const page = await pdf.getPage(n), view = page.getViewport({scale: 2});
    const c = document.createElement("canvas"); c.width = view.width; c.height = view.height;
    document.getElementById("pages").appendChild(c);
    await page.render({canvasContext: c.getContext("2d"), viewport: view}).promise;
  }
});
</script>"""


IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
               ".webp": "image/webp", ".svg": "image/svg+xml"}


def inline_images(text, md_path):
    """Markdown shown on the page cannot load images saved next to it, so embed them.

    Relative image links (inline `![x](img.png)` and reference `[id]: img.png`) are
    read from disk and turned into data URIs. Web links, data URIs and files outside
    the team folder are left as they are.
    """
    def embed(target):
        clean = target.strip().strip("<>").split(" ")[0]
        if not clean or re.match(r"^[a-z]+:", clean, re.I):
            return None
        f = (md_path.parent / clean.replace("%20", " ")).resolve()
        kind = IMAGE_TYPES.get(f.suffix.lower())
        if not kind or not f.is_file() or ROOT.resolve() not in f.parents:
            return None
        return f"data:{kind};base64," + base64.b64encode(f.read_bytes()).decode()

    def inline(m):
        uri = embed(m.group(2))
        return f"{m.group(1)}({uri})" if uri else m.group(0)

    def reference(m):
        uri = embed(m.group(2))
        return f"{m.group(1)}{uri}" if uri else m.group(0)

    text = re.sub(r"(!\[[^\]]*\])\(([^)]+)\)", inline, text)
    return re.sub(r"(?m)^(\s*\[[^\]]+\]:\s*)(\S+)\s*$", reference, text)


def show_report(item):
    # Pages and apps show their own title; the row is left out when it would be empty.
    titled = item["kind"] == "link" or (item["kind"] == "file" and item["path"].suffix.lower() not in (".html", ".htm", ".md"))
    if titled or item["private"]:
        head, action = st.columns([3, 2])
        if titled:
            head.subheader(item["title"])
        if item["private"] and action.button(t["share_team"], type="primary", use_container_width=True):
            confirm_share(item)
    p = item["path"]
    if item["kind"] == "folder" and (p / "app.py").is_file():
        # The app itself, inside the page: opening it shows what it is for.
        port = app_port(p)
        if not port:
            with st.spinner(t["app_opening"]):
                for _ in range(120):  # up to a minute for the first start
                    time.sleep(0.5)
                    if (port := app_port(p)):
                        break
        if port:
            components.iframe(f"http://localhost:{port}/?embed=true&mode={'night' if st.session_state.night else 'day'}", height=820, scrolling=True)
        else:
            st.warning(t["app_failed"])
        return
    if item["kind"] == "folder":
        entry = p / "index.html"
        if entry.is_file():
            page = "<style>html{background:#fff;color:#111}</style>" + entry.read_text(encoding="utf-8", errors="replace")
            components.html(page, height=720, scrolling=True)
        return
    if p.suffix.lower() in (".html", ".htm"):
        # White by default (reports written without a background are unreadable on a dark page).
        page = "<style>html{background:#fff;color:#111}</style>" + p.read_text(encoding="utf-8", errors="replace")
        components.html(page, height=720, scrolling=True)
    elif p.suffix.lower() == ".pdf":
        # Drawn page by page with PDF.js: the browser's own PDF viewer does not run inside the page's frame.
        data = base64.b64encode(p.read_bytes()).decode()
        components.html(PDF_VIEWER.replace("__DATA__", data), height=720, scrolling=True)
    elif p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".svg"):
        st.image(str(p))
    elif p.suffix.lower() == ".md":
        st.markdown(inline_images(p.read_text(encoding="utf-8", errors="replace"), p))
    elif p.suffix.lower() in (".txt", ".csv"):
        st.text(p.read_text(encoding="utf-8", errors="replace"))
    elif st.button(t["show_folder"]):  # a file the page cannot show or open
        show_in_folder(p)


def open_bar(state_key, path):
    """What opens (an artifact, a document) gets the whole window: no top margin, full width, as tall
    as the window, with one thin row on top: back on the left, the folder on the right.
    The page's top bar stays see-through so the back arrow under it can be clicked.
    Returns True when the folder button was clicked."""
    st.markdown("<style>[data-testid='stMainBlockContainer']{max-width:100%!important;padding:.5rem 2rem 0}"
                "header[data-testid='stHeader']{background:transparent;pointer-events:none}"
                "header[data-testid='stHeader'] *{pointer-events:auto}"
                "iframe[src*='embed=true'],iframe[srcdoc]{height:calc(100vh - 110px)!important}"
                ".st-key-artbar{padding:0 2.5rem}</style>",  # clear of the sidebar toggle and the menu
                unsafe_allow_html=True)
    # No back arrow: the section's entry in the side menu goes back to the list.
    _, folder = st.container(key="artbar").columns([20, 1], vertical_alignment="center")
    return bool(path) and folder.button("", icon=":material/folder_open:", type="tertiary", help=t["show_folder"])


def docs_folder():
    return ROOT / ("documentos" if team.get("language") == "es" else "documents")


def doc_files():
    """Every file in the documents folder, by subfolder (hidden files left out)."""
    base = docs_folder()
    if not base.is_dir():
        return []
    return sorted((p for p in base.rglob("*") if p.is_file() and not any(part.startswith(".") for part in p.relative_to(base).parts)),
                  key=lambda p: (str(p.parent.relative_to(base)).lower(), p.name.lower()))


def doc_icon(p):
    ext = p.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".svg"):
        return ":material/image:"
    if ext in (".csv", ".xlsx", ".xls"):
        return ":material/table_chart:"
    if ext in (".html", ".htm"):
        return ":material/code:"
    return ":material/description:"


if section == t["tab_artifacts"]:
    items = report_items()
    # Sidebar: every artifact under the Artifacts entry, to jump from one to another.
    last_group = None
    for item in sorted(items, key=lambda i: (artifact_group(i), i["title"].lower())):
        if artifact_group(item) != last_group:
            last_group = artifact_group(item)
            artifact_menu.caption(last_group)
        here = st.session_state.get("viewing") == item["key"]
        if item["kind"] == "link":
            artifact_menu.link_button(item["title"], item["url"], icon=artifact_icon(item), type="tertiary",
                                      use_container_width=True)
        elif artifact_menu.button(item["title"], icon=artifact_icon(item), type="primary" if here else "tertiary",
                                  use_container_width=True, key=f"artmenu-{item['key']}"):
            enter_artifact(item)
            st.rerun()
    viewing = next((i for i in items if i["key"] == st.session_state.get("viewing")), None)
    if viewing:
        if open_bar("viewing", viewing.get("path")):
            p = viewing["path"]
            show_in_folder(p / "index.html" if (p / "index.html").is_file() else p / "app.py" if (p / "app.py").is_file() else p)
        show_report(viewing)
    else:
        st.write(t["reports_intro"])
        # The team's first; then yours, only on this computer until you share it.
        for heading, group in ((t["shared"], [i for i in items if not i["private"]]),
                               (t["private"], [i for i in items if i["private"]])):
            st.subheader(heading)
            if not group:
                if heading == t["private"]:
                    empty_state(t["no_private"], team.get("example_ask") or t["ask_report"])
                else:
                    empty_state(t["no_shared"])
            # Grouped by type (presentations, dashboards, apps...), each with a small heading.
            by_type = {}
            for item in group:
                by_type.setdefault(artifact_group(item), []).append(item)
            rows = []
            for type_name in sorted(by_type):
                rows.append(type_name)
                rows.extend(by_type[type_name])
            i = 0
            for item in rows:
                if isinstance(item, str):
                    if len(by_type) > 1 or item:
                        st.markdown(f"**{html.escape(item)}**")
                    continue
                i += 1
                with st.container(border=True, key=f"artrow-{heading == t['private']}-{i}"):
                    about = artifact_about(item)
                    cols = st.columns([9, 1, 1, 1] if item["private"] else [11, 1], vertical_alignment="center", gap="small")
                    if item["kind"] == "link":
                        cols[0].link_button(item["title"], item["url"], type="tertiary", use_container_width=True,
                                            icon=":material/open_in_new:")
                    elif cols[0].button(item["title"], key=f"art-{item['key']}", type="tertiary", use_container_width=True,
                                        icon=artifact_icon(item)):
                        enter_artifact(item)
                        st.rerun()
                    if about:
                        with cols[1].popover("", icon=":material/info:", help=t["what_it_is"]):
                            st.markdown(about)
                    if item["private"] and cols[2].button("", key=f"share-{item['key']}", icon=":material/group:",
                                                          help=t["share_team"]):
                        confirm_share(item)
                    if item["private"] and cols[3].button("", key=f"delete-{item['key']}", icon=":material/delete:",
                                                          help=t["delete"]):
                        confirm_delete(item)

# Documents: a viewer of the team's documents folder
if section == t["tab_docs"]:
    base = docs_folder()
    files = doc_files()
    last = None
    for f in files:
        group = f.parent.relative_to(base).as_posix()  # same "/" on Windows
        fold_key = f"docfold-{group}"
        if group != last:
            last = group
            if group != ".":
                # A folder's name opens or closes its list of documents.
                folded = st.session_state.get(fold_key, False)
                if docs_menu.button(group, key=f"docgroup-{abs(hash(group)) % 10**9}", type="tertiary",
                                    icon=":material/chevron_right:" if folded else ":material/expand_more:",
                                    use_container_width=True):
                    st.session_state[fold_key] = not folded
                    st.rerun()
        if group != "." and st.session_state.get(fold_key, False):
            continue
        if docs_menu.button(f.name, icon=doc_icon(f), key=f"docmenu-{f}", use_container_width=True,
                            type="primary" if st.session_state.get("viewing_doc") == str(f) else "tertiary"):
            st.session_state.viewing_doc = str(f)
            st.rerun()
    doc = next((f for f in files if str(f) == st.session_state.get("viewing_doc")), None)
    if doc:
        if open_bar("viewing_doc", doc):
            show_in_folder(doc)
        show_report({"kind": "file", "path": doc, "title": doc.stem, "private": False, "key": str(doc)})
    else:
        st.write(t["docs_intro"])
        if st.button(t["show_folder"], icon=":material/folder_open:"):
            base.mkdir(exist_ok=True)
            show_in_folder(base)
        if not files:
            empty_state(t["no_docs"])
        last = None
        for f in files:
            group = f.parent.relative_to(base).as_posix()  # same "/" on Windows
            if group != last:
                last = group
                if group != ".":
                    st.markdown(f"**{html.escape(group)}**")
            if st.button(f.name, icon=doc_icon(f), key=f"doc-{f}", type="tertiary"):
                st.session_state.viewing_doc = str(f)
                st.rerun()

# History: who changed what, in plain words
if section == t["tab_history"]:
    out = git("log", "-n", "30", "--format=\x1e%an\x1f%at\x1f%s", "--name-only").stdout
    if not out.strip():
        empty_state(t["no_history"])
    for record in out.split("\x1e")[1:]:
        lines = [l for l in record.splitlines() if l.strip()]
        author, ts, subject = lines[0].split("\x1f")
        what = describe_paths(lines[1:], t)
        sensitive = any(l == ".agents/permissions.json" or l.startswith((".agents/rules/", ".agents/system/", ".agents/team.json")) for l in lines[1:])
        # One block per change: who and what, then the change in their words and when.
        flag = f'<div class="flag">{html.escape(t["sensitive"])}</div>' if sensitive else ""
        st.markdown(f'<div class="change"><div><strong>{html.escape(author)}</strong> {t["changed_what"]} '
                    f'{html.escape(what or t["what"]["other"])}</div>'
                    f'<div class="note">{html.escape(subject)}<span class="when">{ago(int(ts), t)}</span></div>'
                    f'{flag}</div>', unsafe_allow_html=True)

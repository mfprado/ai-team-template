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
        "tab_skills": "Skills", "tab_perms": "Permissions", "tab_artifacts": "Reports", "tab_history": "History",
        "tab_ideas": "Ideas", "ideas_intro": "Ideas for the team's workspace. Anyone can add one; {name} decides what happens with each.",
        "no_ideas": "No ideas yet.", "new_idea": "Your idea", "add_idea": "Add idea",
        "idea_summary": "New idea: {text}", "set_status": "Status", "save_status": "Save status",
        "status_summary": "Idea {n}: {status}", "waiting": "waiting for {name}",
        "team_skills": "Team skills", "system_skills": "System skills", "no_skills": "The team has no skills yet. Ask the assistant to bring one in.",
        "how_to_ask": "To use it, open Claude or Codex in this folder and ask for it in your own words.",
        "details": "Show the full instructions",
        "perms_intro": "What the AI is not allowed to do in this folder. Switch a rule off only if the team agrees.",
        "blocked": "Blocked", "asks": "Asks first", "changed": "You changed:", "on": "on", "off": "off",
        "apply": "Apply for the whole team", "applying": "Sharing the change...",
        "note": "Short message you can send to {name}:",
        "shared": "Shared reports", "private": "Only on this computer", "no_files": "Nothing here yet.",
        "open": "Open", "show_folder": "Show in folder", "pending": "Change requests waiting for {name}", "no_pending": "No change requests waiting.",
        "recent": "Recent changes", "changed_what": "changed",
        "what": {"skill": "skill {x}", "perms": "permissions", "docs": "documents", "reports": "reports",
                 "rules": "team rules", "system": "system", "other": "other files"},
        "ago": {"now": "just now", "min": "{n} min ago", "h": "{n} h ago", "d": "{n} days ago"},
        "perm_summary": "Permissions: {items}",
    },
    "es": {
        "title": "Espacio de IA de {team}", "champion": "IA Champion: {name}",
        "sync": "Traer lo último del equipo", "synced": "Al día con el equipo.",
        "sync_fail": "No se pudieron traer los últimos cambios del equipo ahora.",
        "tab_skills": "Skills", "tab_perms": "Permisos", "tab_artifacts": "Reportes", "tab_history": "Historial",
        "tab_ideas": "Ideas", "ideas_intro": "Ideas para el espacio del equipo. Cualquiera puede sumar una; {name} decide qué se hace con cada una.",
        "no_ideas": "Todavía no hay ideas.", "new_idea": "Tu idea", "add_idea": "Agregar idea",
        "idea_summary": "Nueva idea: {text}", "set_status": "Estado", "save_status": "Guardar estado",
        "status_summary": "Idea {n}: {status}", "waiting": "esperando a {name}",
        "team_skills": "Skills del equipo", "system_skills": "Skills del sistema", "no_skills": "El equipo todavía no tiene skills. Pedile al asistente que traiga una.",
        "how_to_ask": "Para usarla, abrí Claude o Codex en esta carpeta y pedila con tus palabras.",
        "details": "Ver las instrucciones completas",
        "perms_intro": "Lo que la IA no puede hacer en esta carpeta. Apagá una regla solo si el equipo está de acuerdo.",
        "blocked": "Bloqueado", "asks": "Pide confirmación", "changed": "Cambiaste:", "on": "activada", "off": "desactivada",
        "apply": "Aplicar para todo el equipo", "applying": "Compartiendo el cambio...",
        "note": "Mensaje corto que podés mandarle a {name}:",
        "shared": "Reportes compartidos", "private": "Solo en esta computadora", "no_files": "Todavía no hay nada.",
        "open": "Abrir", "show_folder": "Ver en la carpeta", "pending": "Pedidos de cambio esperando a {name}", "no_pending": "No hay pedidos de cambio esperando.",
        "recent": "Cambios recientes", "changed_what": "cambió",
        "what": {"skill": "la skill {x}", "perms": "los permisos", "docs": "documentos", "reports": "reportes",
                 "rules": "reglas del equipo", "system": "el sistema", "other": "otros archivos"},
        "ago": {"now": "recién", "min": "hace {n} min", "h": "hace {n} h", "d": "hace {n} días"},
        "perm_summary": "Permisos: {items}",
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

st.set_page_config(page_title=t["title"].format(team=team.get("team", "Team")), layout="centered")
st.title(t["title"].format(team=team.get("team", "Team")))
st.caption(t["champion"].format(name=champion))

if "synced" not in st.session_state or st.button(t["sync"]):
    ok = git("pull", "--ff-only", "--quiet").returncode == 0
    st.session_state.synced = ok
st.caption(t["synced"] if st.session_state.get("synced") else t["sync_fail"])

# Section picker that survives reruns (st.tabs jumps back to the first tab when a switch changes).
SECTIONS = [t["tab_skills"], t["tab_ideas"], t["tab_perms"], t["tab_artifacts"], t["tab_history"]]
section = st.radio("section", SECTIONS, horizontal=True, key="section", label_visibility="collapsed")
st.divider()

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
            st.info(t["no_skills"])
        for name, description, body in group:
            with st.expander(name):
                st.write(description)
                st.caption(t["how_to_ask"])
                if st.checkbox(t["details"], key=f"detail-{name}"):
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

# Reports: open files from the artifacts folder
if section == t["tab_artifacts"]:
    base = ROOT / "artifacts"
    private = base / "private"
    for heading, folder, files in (
        (t["shared"], base, [p for p in base.rglob("*") if p.is_file() and private not in p.parents and p.name != ".gitkeep"] if base.is_dir() else []),
        (t["private"], private, [p for p in private.rglob("*") if p.is_file()] if private.is_dir() else []),
    ):
        st.subheader(heading)
        if not files:
            st.caption(t["no_files"])
        for p in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True):
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{p.relative_to(folder)}**  ·  {ago(int(p.stat().st_mtime), t)}")
            if p.suffix.lower() in SAFE_TO_OPEN:
                if col2.button(t["open"], key=f"open-{p}"):
                    webbrowser.open(p.as_uri())
            elif col2.button(t["show_folder"], key=f"open-{p}"):
                show_in_folder(p)

# History: who changed what, in plain words
if section == t["tab_history"]:
    pending = [b.strip().removeprefix("origin/") for b in git("branch", "-r", "--list", "origin/change/*").stdout.splitlines()]
    st.subheader(t["pending"].format(name=champion))
    if not pending:
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
        st.write(f"- **{author}** {t['changed_what']} {what or '—'} · {ago(int(ts), t)}  \n  {subject}")

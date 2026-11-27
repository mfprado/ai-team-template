# Rule: setup problems on a computer

Applies at the end of setting up a team folder (create-team-repo), when the team launcher fails,
when a "TEAM CHECKS" message appears, or when someone says the AI or the team page does not work
on their computer. Most of these happen on Windows.

## 1. Check the computer

```
sh .agents/system/bin/py -I .agents/system/scripts/doctor.py
```

It changes nothing. It prints each check with `ok`, and for a failed one a `problem` and a
`fix`. If the command itself fails (no `sh` or no Python), go straight to "run_launcher" below.

## 2. Fix what failed, in this order

Tell the person in one plain sentence what you are fixing; never show them the JSON. Fix one
thing, run the check again, then go on.

- **`fix_sh_first`**: fix the `sh` check first; the others depend on it.
- **`run_launcher`**: run the team launcher, which installs and repairs Git, uv, Python, the team's
  git checks and Codex's trust. On a Mac run it yourself:
  `TEAM_PAGE_NO_BROWSER=1 bash "<Team>-IA.command" < /dev/null` (the launcher's name is in
  `.agents/team.json`, key `launcher`). On Windows ask the person to double-click the launcher
  (the shortcut with the company icon, or the `.bat`), then read `.git/launch.log` instead of
  asking them to copy the window.
- **`add_git_sh_to_path`** (Windows): Git is installed but Windows cannot find its `sh`, so Codex
  cannot run the team checks. This changes a setting on their computer: ask first, in one
  sentence ("Codex needs a Git tool that Windows can't find yet. Can I add it to your settings?").
  On yes, add the check's `folder` to the person's own PATH (never the system one) with:
  ```
  powershell -NoProfile -Command "$f='<folder>'; $p=[Environment]::GetEnvironmentVariable('Path','User'); if (($p -split ';') -notcontains $f) { [Environment]::SetEnvironmentVariable('Path', ($p.TrimEnd(';') + ';' + $f), 'User') }"
  ```
  Never use `setx` (it cuts long PATHs). Then tell them to close and open Codex again.
- **`gh_login`**: GitHub's tool needs their sign-in. Ask them to double-click the launcher: it
  opens the GitHub sign-in in their browser. Never ask for a password or token.
- **`contact_champion`**: something this rule does not cover. Explain it in plain words and
  suggest they contact their AI Champion.

## 3. Finish

Run the check once more. When `ok` is true, say in one line that the computer is ready. If a
check still fails after its fix, stop, explain in plain words what is left, and do not work
around the team checks.

## Things to know

- On Windows, Claude Code runs commands in Git Bash, which has its own `sh`. Codex does not, so a
  folder can work in Claude Code and fail in Codex. The check looks at Windows' own settings.
- The first session after setup can be slow on Windows while the team page starts; that is not
  a problem to fix.
- A blue "Windows protected your PC" box when opening the launcher: click **More info**, then
  **Run anyway**.
- If the company blocks installing uv (PowerShell policy) or signing in to GitHub, the person's
  IT team has to allow it: say so plainly and stop.

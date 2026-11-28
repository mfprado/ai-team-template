# Rule: setup problems on a computer

Applies at the end of setting up a team folder (create-team-repo), when the team launcher fails,
when a "TEAM CHECKS" message appears, or when someone says the AI or the team page does not work
on their computer. Most of these happen on Windows.

## 1. Check the computer

```
sh .agents/system/bin/py -I .agents/system/scripts/doctor.py
```

It changes nothing. It prints each check with `ok`, and for a failed one a `problem` and a
`fix`. If the command itself fails (no `sh` or no Python), go straight to "run_setup" below.

## 2. Fix what failed, in this order

Tell the person in one plain sentence what you are fixing; never show them the JSON. Fix one
thing, run the check again, then go on. Do the fixes yourself: the person should not have to
approve steps, click through windows or run anything.

- **`fix_sh_first`**: fix the `sh` check first; the others depend on it.
- **`run_setup`**: run `sh .agents/system/bin/setup` yourself, without asking (same command on Mac
  and Windows). It installs uv and Python, turns on the team's git checks, trusts the folder in
  Codex, puts Git's `sh` on the person's own PATH on Windows (so Codex can run the team checks)
  and repairs the team checks. It writes what it did to `.git/launch.log`. If the session started
  before uv was installed, the team scripts still find it; nothing needs restarting except Codex,
  which reads the PATH when it opens. On Windows, run it in Git Bash (the Bash tool), not
  PowerShell: `sh` is only on PowerShell's PATH after the setup. The first run takes 2 to 4
  minutes: give it a 10-minute timeout, or run it in the background and wait for
  `Setup finished.` in `.git/launch.log` (it never asks anything, so it cannot hang waiting for
  the person).
- **`run_launcher`**: only for what needs the person: Git or GitHub's tool is missing (an
  installer asks them to confirm). Ask them to double-click the launcher (the shortcut with the
  company icon, or the `.bat` / `.command`), then read `.git/launch.log` instead of asking them to
  copy the window.
- **`gh_login`**: GitHub's tool needs their sign-in. Ask them to double-click the launcher: it
  opens the GitHub sign-in in their browser. Never ask for a password or token.
- **`contact_champion`**: something this rule does not cover. Explain it in plain words and
  suggest they contact their AI Champion.

## 3. Finish

Run the check once more. When `ok` is true, say in one line that the computer is ready. If a
check still fails after its fix, stop, explain in plain words what is left, and do not work
around the team checks.

## Things to know

- On Windows, Claude Code has two shells: Bash (Git Bash, with its own `sh`) and PowerShell. Run
  the team's `sh ...` commands in Bash. Codex has no Git Bash, so a folder can work in Claude Code
  and fail in Codex until the setup puts Git's `sh` on the PATH. The check looks at Windows' own
  settings.
- After the setup changes the PATH, Codex only sees it once it is closed and opened again. Tell
  the person in one line if they use Codex.
- The first session after setup can be slow on Windows while the team page starts; that is not
  a problem to fix.
- A blue "Windows protected your PC" box when opening the launcher: click **More info**, then
  **Run anyway**.
- If the company blocks installing uv (PowerShell policy) or signing in to GitHub, the person's
  IT team has to allow it: say so plainly and stop.

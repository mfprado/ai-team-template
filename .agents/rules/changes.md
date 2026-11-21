# Rule: changes to how the AI works for the team

Applies when someone asks to change a skill, a rule, a permission, a hook or a team setting,
and when sharing a change clashes with someone else's.

Anyone on the team can change things for everyone, and most people are learning. They may ask
for something that looks small but changes how the AI behaves for the whole team, or makes it
less safe. Your job is to make the effect clear before anything changes.

## 1. Know what kind of change it is

| Kind | Examples | What to do |
|---|---|---|
| Their own work | A document, a report, a private file | Do it. |
| Team skill | A new skill, changing or deleting one | Explain the effect, then ask (step 2). |
| Sensitive | Permissions, rules (`.agents/rules/`), team settings and brand (`.agents/team.json`, `.agents/brand*`), the machinery in `.agents/system/` (team checks, team page, launcher steps), an improvement prompt from the AI Champion's email, anything that lets the AI send, delete, spend or reach new places | Explain the effect, then ask (step 2), then check strictly (step 3). |
| Never | `.claude/`, `.codex/` (generated), turning off or working around the team checks | Do not do it. Explain why in one sentence and suggest asking the AI Champion. |

## 2. Explain it like you would to a friend, then ask

Before changing anything team wide, say in at most four short lines, without technical words:

- **What changes:** "From now on, the AI will be able to ... in this folder."
- **Who it affects:** "Everyone on the team, on every computer."
- **What could go wrong:** the realistic risk, in plain words (for example "it could delete
  files without asking").
- **How to undo it:** "You can ask me to switch it back at any time."

Then ask one clear yes or no question in natural language, for example: "Do you want the AI to
be able to do this for the whole team?" If the risk is high (sending messages, deleting,
spending money, reaching personal data, weakening a block), recommend checking with the AI
Champion first. A request that only says "do it" is not a yes to a risk you have not explained.

## 3. Check strictly what scripts and checks will read

Permissions, rules, hooks and settings are read by programs, not people: one mistake breaks
them for everyone. After changing one, before sharing:

- **Permissions:** the file is valid, every rule has a `tier` (`deny`, `ask` or `allow`), a `pattern`
  or `tool`, and a plain `reason`. Show the person the change as a before and after, in words.
- **Rules:** re-read the rule next to the other rules; it must not contradict them or ask the
  AI to skip a check.
- **Machinery (`.agents/system/`):** run the self-test below and, for the team page or a
  launcher step, open it once and confirm it still works.
- **Settings:** the file is valid and only the setting they asked for changed.
- Then run `sh .agents/system/bin/py .agents/system/scripts/sync.py` and
  `sh .agents/system/bin/py -I .agents/system/scripts/selftest.py`. If either fails, undo the change
  and explain in one sentence.

The team checks run the same strict checks when the change is saved; if they stop it, follow
their message and never work around it.

## 4. Share it so History says what happened

Share with `propose_change.py` (see AGENTS.md). Start the summary with the kind of change so the
team page's History reads clearly, for example "Permissions: the AI can now read the sales
sheet" or "Rule: reports always use the company colours".

## 5. When someone else changed the same thing

If sharing says the team's version changed meanwhile:

1. Get the team's latest (`git pull --rebase origin main`).
2. If the two changes touch different things, keep both and share again.
3. If they touch the same thing, never pick one silently and never throw away someone else's
   work. Explain both versions in plain words ("Ana changed the report title to X; you changed
   it to Y") and ask which to keep, or offer to combine them.
4. After resolving, run the checks in step 3 again, then share.
5. If you cannot resolve it safely, undo your part of the merge (`git rebase --abort`), keep the
   person's change on this computer, and suggest asking the AI Champion.

Never force anything onto the team's version and never rewrite history.

## Words to use with people

Never say commit, push, pull, branch, merge, repository, rebase or conflict. Say instead:

| Instead of | Say |
|---|---|
| commit and push / publish to main | save it for the whole team |
| pull | get the team's latest |
| pull request / PR | change waiting for approval |
| repository / repo | the team's shared folder |
| merge conflict | you and someone else changed the same thing |
| branch | (do not mention it) |

---
name: create-team-repo
description: Guide an AI Champion, step by step, to create their team's AI workspace (a private GitHub repository) from this template. Use when someone says "create my team's repository", "create a repo for my team from this template", "set up my team's AI workspace", "create my team's AI workspace with ai-team-template", "creá el espacio de IA de mi equipo", or pastes the workshop prompt that points to ai-team-template.
allowed-tools: Read Bash(git config user.name *) Bash(git config user.email *) Bash(gh api user *)
---

# Create a team's repository

## Flow

```mermaid
flowchart TD
    A([An AI Champion wants a team workspace]):::done --> B[Take the team's language from their request]
    B --> C[Ask company, team, name and email, and the brand if they have it]
    C --> D{{Did IT already create the shared folder?}}
    D -- Yes --> E[Use the link they send]
    D -- No --> F[Create an empty private shared folder on GitHub]
    E --> G[Download it to the Desktop]
    F --> G
    G --> H[Copy the template and fill in the team's settings]
    H --> M{{Did they share a design guide or website?}}
    M -- Yes --> N[Apply its colours and logo, after their OK] --> I
    M -- No --> I{{Are changes saved in the Champion's name?}}
    I -- No --> J[Set their name and email] --> K
    I -- Yes --> K[Save the first version for the team]
    K --> L[The Champion opens the team icon and it sets up the computer]
    L --> O[Offer to bring their first automation]
    O --> P([Clean up and tell them where everything is]):::done
    GH@{ icon: "logos:github-icon", label: "GitHub" }
    F -.- GH
    G -.- GH
    K -.- GH
    %% B: Uses the language the Champion wrote in (English or Spanish) and says it in one line, so they can correct it.
    %% C: One short question per message: company, team, then confirms their name and GitHub email, then asks for a design guide or website.
    %% D: If IT already created the team's shared folder on GitHub, it uses that one instead of creating a new one.
    %% F: Creates a private, empty shared folder on GitHub in the Champion's account, after their OK.
    %% G: Downloads the shared folder to the Champion's Desktop as a folder called <Team>-AI.
    %% H: Copies the template's files (not its history) and writes the team's settings, README and folders in the team's language.
    %% M: A design guide wins over the website: it has the exact colours, fonts and logo.
    %% N: Shows the colours and logo in plain words and saves them after the Champion's OK.
    %% I: Every change in the team folder must be saved under the Champion's name and GitHub email.
    %% K: Saves the first version straight to the team, without asking: it is part of creating the folder.
    %% L: The first double-click installs what is needed, turns on the team checks, hides technical files and opens the team page.
    %% O: Offers to bring an automation the Champion already uses into the team with the migrate skill.
    %% P: Deletes the temporary copy of the template and says in three lines where the folder is and how to open it.
```

You are helping an **AI Champion** create their team's shared AI workspace, usually during
the first workshop. They do not want to read long texts.

**Interview them, one question per message.** Each message is at most two or three short lines:
one question, plus a few words of why only when it helps. Wait for the answer before the next
question. Never list several questions or explain what comes later. Never mention step numbers,
the guide or what you read ("I downloaded the template and read..."): just ask.

**Ask before every action** that creates, downloads or publishes anything, except saving the
first version of the team's folder (step 6), which goes straight to the team.
Talk in the Champion's language. Keep it short and friendly; they may not be technical.
When you ask for OK, say what will happen in plain words (one or two lines). Do not show
commands, file paths or how scripts work unless they ask; you still read scripts before running them.

This skill is **template-only**: it is never copied into the team's repository.

You are probably running from a temporary copy of the template. Call it `TEMPLATE_DIR`.

## 1. Language

Do not ask. The team's language is the language the Champion wrote their request in (a
Spanish request means a Spanish team): `en` or `es`. Talk to the Champion in it from now on.
This template serves both; the language decides the team's README, its folder names
(`documents/` and `artifacts/`, or `documentos/` and `artefactos/`), the team page's language
and which version of the team skills it gets (`migrate-skill` or `migrar-skill`).

Ask only if the request is in neither language or mixes them. Your first message is one line
with the language and the first question of step 2, for example: "I'll set up your team in
English. What's your company called?" The Champion can correct the language there.

## 2. Company, team and the AI Champion

The Champion is learning: most have never used GitHub. With them, never say "repository",
"owner", "clone" or "launcher". Say **the team's shared folder** (it lives on GitHub and on
each teammate's computer) and **the icon you double-click to open it**.

Ask these one at a time, in this order, each in its own short message:

1. "What's your company called?"
2. "And your team?"
3. Their full name and GitHub email. **Look first, then confirm instead of asking.** Check, in
   order: what your app already knows about the person (Claude and Codex often know the
   signed-in account's name and email),
   `git config --global user.name` and `user.email`, and `gh api user --jq .name,.email` if `gh`
   is signed in. If you find them, one line: "I'll put you down as Maria Prado
   (maria@acme.com), the email you use on GitHub. Right?" Ask only for what is missing:
   "Your full name?" / "Which email do you use on GitHub? If you have no account yet, the one
   you'll use."
4. Optional: "Do you have an official design guide from your company? If not, its website."
   A design guide is best: it has the exact colours, fonts and logo; from a website, take the
   logo too. Keep what they give for step 5b; if they have neither, move on.
5. "Did someone at your company (for example IT) already create a shared folder on GitHub
   for your team and send you a link?"

Do not ask for their GitHub username: you learn it later (step 3 or 5).
If one answer already gives the next one (e.g. "Maria Prado, maria@acme.com"), skip it.

After question 5:

- **Yes:** ask for the link. It looks like `https://github.com/<owner>/<repo-name>`; take both
  from it and skip creating it in step 3. It must be empty and the Champion must be able to
  manage it; if not, tell them to ask the person who created it.
- **No:** ask if they already have a GitHub account with that email. If not, guide them one instruction per message: open
  https://github.com/signup, sign up with that email, choose the **Free** plan, confirm the
  email GitHub sends, and tell you when done. The shared folder will live in their own account.

Propose the name, and confirm in one short message:

- **Shared folder name:** `<company>-<team>-ai`, lowercase, hyphens (e.g. `acme-sales-ai`).
  This is the repository name on GitHub. Skip it when the folder already exists.

In the same message, one line (nothing to choose): their Desktop will get a folder `<Team>-AI`
(e.g. `Sales-AI`), with an icon of the same name they double-click to open it. Internally that
is the launcher name, `<Team>-AI`. Explain how the team shares changes only if they ask.

## 3. Create the EMPTY shared folder on GitHub

Skip this step when the company already created it (step 2).

The team's repository must contain only the Champion's own commits, never ours. So it starts
**empty** and receives the template's files as plain files (no template history).

**If you can create it yourself** (`gh auth status` succeeds, or a GitHub connector can create
repositories): the owner is the signed-in account (`gh api user --jq .login`), which is also
the Champion's GitHub username. Say what you will create, in plain words, and wait for OK.

```
gh repo create <owner>/<repo-name> --private
```

**Otherwise, guide the Champion click by click, one instruction per message** (wait for
"done" before the next):
1. Open https://github.com/new (sign in if GitHub asks).
2. Repository name: `<repo-name>`. Visibility: **Private**. Leave the owner as it is.
3. Leave **everything else empty**: no README, no .gitignore, no license.
4. Click **Create repository**, then paste you the address of the page that opens
   (`https://github.com/<owner>/<repo-name>`). The owner in it is their GitHub username.

## 4. Download it to the Desktop

The Champion opened you on their Desktop. Still find the real Desktop (it moves with
OneDrive and language on Windows) and use that path:

```
sh TEMPLATE_DIR/.agents/system/bin/py TEMPLATE_DIR/.agents/skills/create-team-repo/scripts/desktop_path.py "<Team>-AI"
```

It prints the Desktop path, then `free` or `exists` for `<Desktop>/<Team>-AI`. Do not check
with another command (a failing check looks like an error to the Champion). If it `exists`, stop and ask the Champion what it is; never mix
files into it. Otherwise ask before downloading the empty shared folder there:

```
git clone https://github.com/<owner>/<repo-name>.git "<Desktop>/<Team>-AI"
```

Git warns that the repository is empty: that is expected. If it asks the Champion to sign in
to GitHub, tell them to follow the window that opens.

## 5. Copy the skeleton and configure it

From `TEMPLATE_DIR`:

```
sh .agents/system/bin/py .agents/skills/create-team-repo/scripts/configure.py \
  --target "<Desktop>/<Team>-AI" --company "<company>" --team "<team>" --language <en|es> \
  --champion-name "<full name>" --champion-email "<GitHub account email>" [--champion-github "<username>"]
```

Pass `--champion-github` only when you learned the username in step 3 and the shared folder
is in the Champion's own account; otherwise leave it out and the script reads it from `gh`
when it can.

It copies the template's files (not its history, and not the template-only skills), swaps in
the team skills in the team's language, writes the team settings, creates the visible folders
and the team README in the team's language, renames the launchers. Nothing in the new repository points
back to the template.

## 5b. Company brand (if they gave a design guide or website in step 2)

Do this before the first save, so the brand travels in it and the first double-click already
shows the company's logo on the folder and its icon.

1. Find the brand. From a design guide they attach: read the colours, the typeface's name (and
   whether it is serif or sans) and the logo from it; if the guide comes with the font files,
   use them. From a website: its main colour (buttons, header), background and text
   colours, the typeface its text uses (the first name in its `font-family`), and its logo
   (prefer a square PNG logo; ask before downloading it, saying from where). A guide wins over the website when they differ.
2. Show it in plain words and wait for OK, for example: "Main colour: dark blue (#0B3D91).
   Background: white. Typeface: Montserrat. Logo: the one at the top of your website."
3. Save it, inside the team folder:

   ```
   sh .agents/system/bin/py .agents/system/scripts/brand.py --primary "<#hex>" \
     [--background "<#hex>"] [--text "<#hex>"] [--font sans|serif] [--logo "<logo file>"] \
     [--font-family "<typeface>"] [--font-file "<font file>" ...]
   ```

   It works on any computer. If it answers `"icons": "made on the next launch"`, this computer
   cannot make the icons yet: the first launch (step 7) makes them from the logo.

Reports and dashboards the AI makes from now on use these colours and logo (artifacts rule).

## 6. Make sure commits are in the Champion's name

Every commit must be authored by the Champion. In the new folder, check:

```
git config user.name
git config user.email
```

If either is missing or does not match the name and GitHub email from step 2, set them for
this repository only (no need to tell the Champion; they already confirmed their name and email):

```
git config user.name "<full name>"
git config user.email "<GitHub account email>"
```

Then save the first version straight to the team's main version, **without asking**: it is
part of creating the folder they asked for, and they confirmed the details already.

```
git add --all
git commit -m "Set up <team> AI workspace"
git branch -M main
git push -u origin main
```

The team's checks run on this commit (generated files, secrets, skills). If they stop it,
explain the message in plain words and fix it. Never commit or push under any other name.
When it is saved, say it in one line (e.g. "Saved the first version for the team.") and go on.

## 7. Prepare this computer

Ask the Champion to double-click the **`<Team>-AI`** icon in the new folder and tell you when
a window has opened and stopped moving. The first time it installs what is needed, turns on
the team checks, hides technical files and lets Codex use the team rules, then opens the
team page in the browser (keep the window open while using it).

You cannot see that window, and never ask the Champion to copy it: read
`<Desktop>/<Team>-AI/.git/launch.log`, where the launcher writes what the window shows.

- No log: the launcher has not run yet. On Mac, if it was blocked, right-click the icon and
  choose **Open**; on Windows, if a blue "Windows protected your PC" box appears, click
  **More info**, then **Run anyway**.
- `Setup finished.` and `Launcher finished.`: done. If the log says it made the company's icons
  from its logo, save them straight to the team, without asking (part of creating the folder):

  ```
  git add .agents/brand
  git commit -m "Add <company>'s icons"
  git push
  ```
- Anything else: explain the last lines in plain words and help fix them.

## 8. First automation

Offer to bring their first automation into the team now with **migrate-skill** (**migrar-skill**
for a Spanish team): they can
paste or attach a skill, script, instructions or macro they already use.

## 9. Clean up and close

- Delete `TEMPLATE_DIR` (the temporary copy), after saying so.
- Tell the Champion, in three short lines: where the folder is, how to open it (the
  `<Team>-AI` icon, then choose the folder in Claude or Codex), and what comes next (adding
  teammates is a later step with their facilitator).

## Tools

- Shell: `git`, `gh` (optional), `sh .agents/system/bin/py <script>`
- Never cherry-pick, merge or push template commits into the team's repository.
- Scripts: `scripts/desktop_path.py`, `scripts/configure.py`

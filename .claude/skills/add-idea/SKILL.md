---
name: add-idea
description: Add an idea for the team's AI workspace to the team's ideas, and when the idea is about a way of working, draw its workflow as a diagram the team sees on the team page. Use when someone says "I have an idea", "it would be nice if", "we could automate", "add an idea", or describes a process they would like the AI to help with.
allowed-tools: Bash(sh .agents/system/bin/py -I .agents/system/scripts/ideas.py *) Bash(sh .agents/system/bin/py -I .agents/system/scripts/propose_change.py *)
---

# Add an idea

## Flow

```mermaid
flowchart TD
    A([Someone shares an idea]):::done --> B{{Does it have a short title?}}
    B -- No --> C[Ask for a title in a few words] --> D
    B -- Yes --> D{{Is it about a way of working?}}
    D -- No --> F[Save the idea]
    D -- Yes --> E[Draw the workflow and show it] --> G{{Does it look right?}}
    G -- No --> H[Correct the diagram] --> G
    G -- Yes --> F
    F --> I([Save it for the team]):::done
    %% A: The person describes something that would help the team, in their own words.
    %% B: The title is the person's own: a few words that name the idea.
    %% C: One short question. Never invent the title for them.
    %% D: A way of working: steps people follow, who does what, which tools, what comes out (a report each Monday, answering client emails, onboarding someone).
    %% E: Draws the whole flow at once from what the person said, and shows it in the chat.
    %% F: Adds the idea to the team's ideas, with its description, and the diagram if there is one.
    %% I: Shares it with the team straight away; it shows on the team page, under Ideas.
```

## Steps

1. **Title.** Use the person's own words. If they did not give a short title, ask for one in a
   few words (one short question). Never make it up.

2. **Is it a way of working?** If the idea describes steps people follow (who starts it, what
   happens next, which tools, what comes out), draw its workflow. If it is something else (a
   tool to try, a training, a page), skip to step 4.

3. **Draw the workflow at once**, from what the person told you, and show it in the chat as a
   `mermaid` block. Use the same style as the team's skills:
   - `flowchart TD`, steps in short plain words, in the team's language.
   - The first and last steps rounded and marked done: `A([...]):::done`.
   - Questions as `{{...?}}` with `-- Yes -->` / `-- No -->` (`-- Sí -->` / `-- No -->` in Spanish).
   - One `%% <letter>: <one plain sentence>` line per step saying what happens there.
   - At most about 12 steps. Mark guesses as questions in the notes instead of inventing details.

   Ask in one line whether it looks right. Correct it until they say yes.

4. **Save the idea**, with the description in the person's own words:

   ```
   sh .agents/system/bin/py -I .agents/system/scripts/ideas.py add --title "<title>" --text "<description>"
   ```

   It answers with the idea's `id`. If there is a diagram, write it to a temporary file (outside
   the team folder) and attach it:

   ```
   sh .agents/system/bin/py -I .agents/system/scripts/ideas.py flow --id <id> --file "<temporary file>"
   ```

5. **Save it for the team** straight away:

   ```
   sh .agents/system/bin/py -I .agents/system/scripts/propose_change.py --summary "New idea: <title>" --paths IDEAS.md .agents/ideas
   ```

   Tell them in one line that the idea is on the team page, under Ideas, with its workflow if it
   has one ("See the workflow").

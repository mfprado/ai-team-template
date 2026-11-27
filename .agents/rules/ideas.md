# Rule: team ideas

Applies when someone shares an idea for the team ("I have an idea", "it would be nice if...",
"we could..."), asks what ideas there are, or wants to update one.

Follow the team's idea skill (`add-idea`, or `agregar-idea` in Spanish) to add one: it also draws
the workflow when the idea is about a way of working. To list ideas or update one, use the script.

The team's ideas live in `IDEAS.md` at the top of the team's folder, one line per idea with
date, who, the idea's title and its status, an optional description, with its comments indented under it. Use the script, never edit the file by hand:

```
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py add --title "<short title>" --text "<the idea in more detail, optional>"
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py list
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py status --id <n> --to <new|planned|done>
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py comment --id <n> --text "<the comment, in the person's words>"
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py assign --id <n>            # the person takes it
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py assign --id <n> --to "<name>"
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py assign --id <n> --clear
```

- The title is the person's: ask them for a short one (a few words) if they did not give it. Put
  any detail in `--text`, in their own words. The script adds the date and their name.
- Anyone on the team can change an idea's status.
- Anyone can comment on an idea; comments show under it on the team page.
- An idea can have one person working on it, so two people don't do the same thing. Before someone
  starts on an idea, check `list`: if someone else has it, tell them who and suggest they talk first.
- After adding or updating, save it for the team straight away
  (`propose_change.py --paths IDEAS.md .agents/ideas`).

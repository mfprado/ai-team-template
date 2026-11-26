# Rule: team ideas

Applies when someone shares an idea for the team ("I have an idea", "it would be nice if...",
"we could..."), asks what ideas there are, or wants to update one.

The team's ideas live in `IDEAS.md` at the top of the team's folder, one line per idea with
date, who, the idea and its status. Use the script, never edit the file by hand:

```
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py add --text "<the idea, in the person's words>"
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py list
sh .agents/system/bin/py -I .agents/system/scripts/ideas.py status --id <n> --to <new|planned|done>
```

- Write the idea in the person's own words, short; the script adds the date and their name.
- Anyone on the team can change an idea's status.
- After adding or updating, offer to share it with the team as usual
  (`propose_change.py --paths IDEAS.md`).

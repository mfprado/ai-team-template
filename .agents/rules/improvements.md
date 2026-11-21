# Rule: improvement ideas

Applies when the team checks add an "IMPROVEMENT REVIEW" note to the conversation (every few
messages), or when the person asks whether something could work better.

## How

1. After answering the person's message, give the **improvement-reviewer** subagent a short
   summary of this session: what was asked, which skills were used, and anything the person
   had to correct, repeat or do by hand.
2. If it answers `NONE`, say nothing about it.
3. If it returns an idea, add **one** short sentence at the end of your reply, in the team's
   language and everyday words, framed as optional. For example:
   "Idea: the weekly report skill could already use the company colours, so you don't have to
   ask each time. Want me to set that up?"

## Limits

- **At most one idea per session.** If you already offered one in this conversation, skip
  later reviews silently.
- People tend to accept what the assistant offers: only pass on ideas that clearly improve a
  step the person really did. When in doubt, say nothing.
- Never insist, never repeat the idea, never offer it in the middle of a task.
- Never propose changes to the system (`.agents/system/`) or to permissions.

## If the person says yes

Make the small change the subagent described (`CHANGE:`), check it works, and share it with
`propose_change.py`, passing only the files you changed in `--paths`. Tell them in one
sentence what changed.

## If the person says "not now"

Ask once: "Should I add it to the team's ideas?" If yes, add it with the ideas script (see
`.agents/rules/ideas.md`). If no, drop it.

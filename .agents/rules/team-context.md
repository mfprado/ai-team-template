# Rule: team context

Applies when the team folder has no `.agents/team-context.md` yet, when someone asks to set up
or update how the team works ("update the team context", "actualizá el contexto del equipo"),
when `create-team-repo` reaches its team context step, or when something you learn clearly
contradicts what the file says.

`.agents/team-context.md` is how the team works, written once by interviewing the AI Champion
and kept up to date. **Read it before any task for the team**: it tells you who does what,
which tools the team uses and how, and what a good result looks like here, so you do not have
to ask again and your answers fit this team.

## The interview

Keep it short: **three questions**, one per message, two or three short lines each; wait for
the answer. Say once, at the start, that it takes about 3 minutes and that it is so the AI
assistant works the way the team does. Ask a follow-up only when an answer is too vague to
write down; never more than one per question.

1. **What the team does and for whom**: its purpose, who it works for (internal areas,
   clients, kinds of client) and what it delivers.
2. **Tools**: which ones the team uses and what each one is for.
3. **Roles**: who is on the team, what each role does, and who decides or approves. Roles, not
   private details about people.

Do not ask about rhythm, processes, formats, glossary or care points: the team fills those in
later, as they come up in daily work ("add this to the team context").

The Champion helps the team adopt AI; they are not always the one who sets the team's standards
or limits. Write what they said as a first draft, and mark what is missing or unsure as **to
confirm with the team's leader**.

Never write passwords, tokens or personal data of clients or third parties in the file; if the
Champion shares any, tell them it is not needed and leave it out.

## The file

Write `.agents/team-context.md` in the team's language, short and scannable, with these
sections (translated): **Purpose**, **Tools and how we use them** (one short line per tool),
**Structure and roles**, then **To confirm with the leader** (the open points) and **Last
updated** (date and who). Later updates may add **Rhythm**, **Main processes**, **Where time
goes**, **Formats and examples**, **Glossary** or **Care points** when they come up.
Show it to the Champion in a short summary, adjust what they point out, then save it for the
whole team straight away (`propose_change.py --paths .agents/team-context.md`).

When updating, change only the sections that changed and update **Last updated**.

Also set the team's example request: one short sentence, in the team's language, that someone
on this team would really ask for as a report (built from **Purpose** and **Tools**, e.g.
"Hacé un resumen semanal de los tickets abiertos por cliente."). Write it in
`.agents/team.json` under the key `example_ask` and save it with the context file. The team
page shows it as the example of what to ask for; without it, it shows a generic one.

## Better solutions for the team

With the interview done, propose 2 or 3 concrete ideas that fit this team best (a skill, a
report or dashboard, a template, an automation with the tools they already use), each in one
line with the time it would save. Base them on what the team does and the tools it already has. Add the ones the Champion likes to the team's ideas
(`.agents/rules/ideas.md`). The interview is only setup: do not offer to build any of them
now. The team builds ideas later, once they understand how the team page and the AI assistant
work.

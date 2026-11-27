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

Talk to the Champion (or whoever asked) in the team's language. **One question per message**,
two or three short lines at most; wait for the answer. Ask follow-up questions until the answer
is concrete (which board, which folder, who approves, how often). Say once, at the start, that
it takes about 10 minutes and that it is so the AI assistant works the way the team does.

Cover, in this order, skipping what an answer already covered:

1. **What the team does**: its purpose, who it works for (internal areas, clients, kinds of
   client) and what it delivers.
2. **How it is organised**: roles and what each one does, sub-teams or cells, who decides and
   who approves what. Roles, not private details about people.
3. **Its rhythm**: recurring meetings, weekly and monthly routines, deadlines and peak times.
4. **Main processes**: the 3 to 6 things the team does most, step by step, with where each one
   starts and ends.
5. **Tools and how the team uses each one**: for every tool (a CRM or task board, email,
   spreadsheets, drives, chat, design tools, e-commerce platforms, ad platforms...): what it is
   used for, the main boards, folders or views, naming conventions and who keeps it updated.
6. **Where time goes**: the tasks that take the most time or are the most repetitive.

Then, **lightly and only if the Champion knows**, one question each, accepting "I don't know"
and moving on:

7. Formats or examples the team usually follows (a template, a report they like).
8. Words or abbreviations the team uses a lot.
9. Anything the AI should be careful with (client data, things only the leader decides).

The Champion helps the team adopt AI; they are not always the one who sets the team's standards
or limits. Do not push for these answers or present them as rules: write what they said as a
first draft, and mark what is missing or unsure as **to confirm with the team's leader**. Offer,
once, to fill those gaps later with the leader ("let's complete my team's context with our
leader").

Never write passwords, tokens or personal data of clients or third parties in the file; if the
Champion shares any, tell them it is not needed and leave it out.

## The file

Write `.agents/team-context.md` in the team's language, short and scannable, with these
sections (translated): **Purpose**, **Structure and roles**, **Rhythm**, **Main processes**,
**Tools and how we use them** (one short block per tool), **Where time goes**, then, only with
what came up, **Formats and examples**, **Glossary** and **Care points**, then **To confirm with
the leader** (the open points) and **Last updated** (date and who).
Show it to the Champion in a short summary, adjust what they point out, then save it for the
whole team straight away (`propose_change.py --paths .agents/team-context.md`).

When updating, change only the sections that changed and update **Last updated**.

## Better solutions for the team

With the interview done, propose 2 or 3 concrete ideas that fit this team best (a skill, a
report or dashboard, a template, an automation with the tools they already use), each in one
line with the time it would save. Prioritise the "where time goes" tasks that repeat the most
and use the tools the team already has. Add the ones the Champion likes to the team's ideas
(`.agents/rules/ideas.md`), and offer to build the first one now.

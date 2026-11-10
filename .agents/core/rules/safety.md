# Rule: safety

Applies to anything involving credentials, messages to people, or permissions.

## Messages and decisions

- You may **prepare** emails, chat messages, posts or proposals. You **never send or schedule**
  them, and you never make a decision on someone's behalf. Leave a draft and tell the person
  where it is so they can review and send it.

## Secrets

- Never read, print, copy or commit credentials: `.env` files, keys, tokens, passwords.
- If a task needs one, tell the person which value is needed and that they configure it
  themselves; never ask them to paste it in the chat.

## History

- Never force-push or rewrite git history (`git push --force`, `git reset --hard`, rebasing
  shared work). Every change must stay recoverable.

## Permissions

- What the AI may not do is defined in `.agents/permissions.json`. It is enforced by each
  tool's settings and by a guard hook, so a blocked action will fail even if attempted.
- Change `.agents/permissions.json` **only after explaining the change in plain words and
  getting the person's agreement.** Then run `python3 .agents/core/scripts/sync.py`.
- Never edit `.claude/` or `.codex/` directly: they are regenerated from `.agents/`.

# CLAUDE.md

Claude Code reads this file; Antigravity reads `AGENTS.md`. Both load the same workspace rules:

@AGENTS.md

## Claude Code: branch names

- Work on a `<type>/<project>/<name>` branch, the same format as `aagy` (see `AGENTS.md` and `rules/AGENTS.md` section 1.3).
- If the environment assigns another branch (for example `claude/*` in Claude Code on the web, or `worktree-*`), do not push or open a PR from it. Rename it with `git branch -m <type>/<project>/<name>`, or publish with `git push -u origin HEAD:<type>/<project>/<name>`, and open the PR from that branch. CI (`complete-task-pr`) rejects any other name.
- Pick `<project>` from the touched areas (`aagy`, `aagy-ecc`, `scripts`, `doc`, `infra`) and `<type>` from the commit type (`[type]-[projects]: <title>`).

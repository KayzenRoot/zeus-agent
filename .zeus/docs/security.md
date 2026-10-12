# Security
Repository is PUBLIC by explicit owner decision, 2026-10-12. Public visibility does not grant write access; repository owner maintains ACLs.
Never commit .env files containing secrets, API keys, OAuth tokens, logs, session transcripts, private model prompts, personal data, or machine state. Inspect staged changes before pushing. If leaked, revoke credentials immediately (removing from Git history alone is insufficient).
Preserve upstream auth protections, including REST and websocket session tokens; do not open dashboard on public interfaces by default. Never expose secrets in Zeus activity feed.
Owner must configure branch protection/ruleset and trusted collaborators in GitHub repository settings if desired; this integration currently has no verified administrative settings write.
MIT copyright/permission notice must be retained.

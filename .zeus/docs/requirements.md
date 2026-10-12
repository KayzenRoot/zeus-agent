# Requirements
R1 Import upstream source AND original Git history into existing KayzenRoot/zeus-agent (do not create another repository).
R2 Preserve MIT license and upstream attribution. Keep a Git remote named `upstream` for controlled syncing.
R3 All *user-facing* Hermes Agent branding should become Zeus Agent across titles, copy, app chrome, logo, favicons, SVGs, onboarding, and user documentation. Keep attribution clear.
R4 Preserve functional internal names, package IDs, database keys, env vars, API names, and external protocol compatibility until independently tested migration.
R5 Reuse the current web dashboard/TUI PTY integration instead of reimplementing chat.
R6 All work is local-first. No credentials or private operational data may be committed to this public repository.
R7 Add agent activity monitor, trace/log inspector, and task status only in subsequent reviewed increments.
R8 Changes require tests, reviewable commits, and evidence before merge.

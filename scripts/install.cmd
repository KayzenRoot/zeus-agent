@echo off
setlocal
REM ZEUS-001: Fail-closed Windows CMD entrypoint for this fork.
REM The inherited Hermes installer used remote PowerShell execution.
REM This wrapper must never execute upstream code or mutate a user profile.
REM A verified Zeus-owned installer will be implemented and tested separately.

1>&2 echo zeus-release-unapproved: Zeus Windows installation is not yet available.
1>&2 echo Use the isolated source-development instructions in .zeus\docs\windows-validation.md.
1>&2 echo Do not run third-party Hermes installers to install Zeus.
exit /b 2

# Test / Benchmark Plan
Before changes: import verification (upstream SHA ancestor, LICENSE, expected tree), capture baseline failing tests and local platform.
After each user-facing rebrand: targeted static string/asset inventory excluding legal attribution and internal compatibility names; test that original imports still resolve; package manager lockfile consistency; unit and UI smoke tests; browser dashboard startup and authentication; check screens, favicon, app title, icon.
`python -m compileall` targets modified Python files; `npm run check` / workspace checks once dependencies installed; run existing upstream test entrypoints supported by the checked-out version.
Compare pre/post local startup time, dashboard memory and chat stability against measurements, not assumptions. No runtime testing claimed until conducted.

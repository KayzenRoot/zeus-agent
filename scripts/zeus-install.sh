#!/usr/bin/env bash
# Zeus-owned local installer (issue #5, flow B).
# Installs from this verified checkout into an isolated root; never runs an
# upstream installer. Full contract: scripts/zeus_install_local.py --help.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$here/zeus_install_local.py" "$@"

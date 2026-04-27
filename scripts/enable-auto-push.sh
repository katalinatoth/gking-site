#!/bin/sh
# Run once per clone: registers .githooks so post-commit auto-pushes to origin.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
git config core.hooksPath .githooks
chmod +x .githooks/post-commit 2>/dev/null || true
echo "Set core.hooksPath to .githooks — commits will run post-commit (git push)."
echo "One-off skip: SKIP_AUTO_PUSH=1 git commit ..."
echo "Turn off: git config hooks.skip-auto-push true"

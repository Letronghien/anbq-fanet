#!/usr/bin/env bash
# anbq-sync.sh -- link the repo's modules and scratch files into the isolated ns-3 tree.
# Symlinks, so a `git apply` in $ANBQ_REPO is what gets compiled; nothing is copied by hand.
# Idempotent; run again after a patch adds a module or an anbq-* scratch file.
set -euo pipefail
source "$(dirname "$(readlink -f "$0")")/anbq-env.sh"
[ -d "$ANBQ_NS3/src" ] || { echo "no ns-3 tree at $ANBQ_NS3 (run anbq-setup-ns3.sh)"; exit 1; }
for m in "$ANBQ_REPO"/src/*/; do
  m=${m%/}; name=$(basename "$m"); dst="$ANBQ_NS3/src/$name"
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then echo "refusing: $dst exists and is not a symlink"; exit 1; fi
  ln -sfn "$m" "$dst"; echo "module  $name -> $m"
done
for f in "$ANBQ_REPO"/scratch/anbq-*; do
  dst="$ANBQ_NS3/scratch/$(basename "$f")"
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then echo "refusing: $dst exists and is not a symlink"; exit 1; fi
  ln -sfn "$f" "$dst"; echo "scratch $(basename "$f")"
done
# drop links whose target left the repo
for l in "$ANBQ_NS3"/scratch/anbq-* "$ANBQ_NS3"/src/*; do
  [ -L "$l" ] && [ ! -e "$l" ] && { rm "$l"; echo "removed stale link $l"; }
done
true

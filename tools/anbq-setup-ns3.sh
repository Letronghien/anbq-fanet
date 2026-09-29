#!/usr/bin/env bash
# anbq-setup-ns3.sh -- Step 0: create the isolated ns-3.48 tree of Paper 2.
#
#   bash ~/anbq-repo/tools/anbq-setup-ns3.sh            # clone, patch, link, configure, build (-j 2, nice 19)
#   JOBS=6 bash ~/anbq-repo/tools/anbq-setup-ns3.sh     # faster when Paper-1 runs are not using the CPUs
#   SKIP_BUILD=1 bash ...                               # stop after configure
#
# Fresh upstream ns-3.48 (not a copy of the Paper-1 tree, whose CMake cache holds absolute paths)
# + the Paper-1 energy patch. Never writes outside $ANBQ_HOME.
set -euo pipefail
source "$(dirname "$(readlink -f "$0")")/anbq-env.sh"
JOBS=${JOBS:-2}
case "$(readlink -m "$ANBQ_NS3")/" in
  "$(readlink -m "$HOME/nbqmaodv-fanet")"/*|"$(readlink -m "$P1_REPO")"/*) echo "ANBQ_NS3 is inside Paper 1 -- refusing"; exit 1;;
esac
[ -e "$ANBQ_NS3" ] && { echo "$ANBQ_NS3 already exists; remove it first if you really want a new tree"; exit 1; }
mkdir -p "$ANBQ_HOME" "$ANBQ_RESULTS"

echo "== clone $NS3_TAG"
git clone -q --depth 1 --branch "$NS3_TAG" https://gitlab.com/nsnam/ns-3-dev.git "$ANBQ_NS3" 2>/dev/null \
  || git clone -q --depth 1 --branch "$NS3_TAG" https://github.com/nsnam/ns-3-dev-git.git "$ANBQ_NS3"
echo "ns-3 commit: $(git -C "$ANBQ_NS3" rev-parse HEAD)"

echo "== apply ns3-patches"
for p in "$ANBQ_REPO"/ns3-patches/*.patch; do
  git -C "$ANBQ_NS3" apply --check "$p" && git -C "$ANBQ_NS3" apply "$p" && echo "applied $(basename "$p")"
done

echo "== link repo modules and scratch files"
bash "$ANBQ_REPO/tools/anbq-sync.sh"

MODS="$ANBQ_BASE_MODULES"
for m in "$ANBQ_REPO"/src/*/; do MODS="$MODS;$(basename "$m")"; done
echo "== configure (optimized) modules: $MODS"
cd "$ANBQ_NS3"
./ns3 configure --build-profile=optimized --disable-examples --disable-tests --enable-modules="$MODS"
[ "${SKIP_BUILD:-0}" = 1 ] && { echo "SKIP_BUILD=1: stopping after configure"; exit 0; }

echo "== build (-j $JOBS, nice 19)"
nice -n 19 ./ns3 build -j "$JOBS"
echo "== binaries"; ls build/scratch/ | grep -- '-optimized$' || true
echo "done. Next: bash $ANBQ_REPO/tools/anbq-verify-step0.sh"

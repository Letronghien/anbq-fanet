#!/usr/bin/env bash
# anbq-verify-step0.sh -- the new tree must reproduce Paper 1 exactly.
# 1) module sources: repo copy == Paper-1 repo == what the Paper-1 tree compiled
# 2) short runs (AODV, NBQ-MAODV; K0 and K1; 2 seeds): CSV + METRICS lines byte-identical between the
#    Paper-1 binaries and the new anbq-scenario-* binaries. ~1-2 min on one core.
set -uo pipefail
source "$(dirname "$(readlink -f "$0")")/anbq-env.sh"
ok=1
echo "== 1. module sources"
for ref in "$P1_REPO/src/nbqmaodv" "$P1_NS3/src/nbqmaodv"; do
  if [ -d "$ref" ]; then
    if diff -rq "$ref" "$ANBQ_REPO/src/nbqmaodv" >/dev/null; then echo "IDENTICAL  $ref"
    else echo "DIFFERENT  $ref"; diff -rq "$ref" "$ANBQ_REPO/src/nbqmaodv"; ok=0; fi
  else echo "missing    $ref (skipped)"; fi
done
bin() { ls "$1"/build/scratch/*"$2"-optimized 2>/dev/null | head -1; }
echo "== 2. short runs"
ARGS="--mobility=gm --simTime=40 --warmup=10 --nUav=12 --totalLoad=24 --area=1000 --bsPos=center"
for mod in aodv nbqmaodv; do
  proto=$([ $mod = aodv ] && echo AODV || echo NBQ-MAODV)
  b1=$(bin "$P1_NS3" "fanet-scenario-$mod"); b2=$(bin "$ANBQ_NS3" "anbq-scenario-$mod")
  [ -n "$b1" ] && [ -n "$b2" ] || { echo "binary missing: '$b1' '$b2'"; ok=0; continue; }
  for ch in "--channel=range" "--channel=fading --nakagamiM=10 --txPowerDbm=-1.9"; do
    for s in 1 2; do
      o1=$(cd "$P1_NS3" && "$b1" --protocol=$proto $ARGS --run=$s $ch 2>&1 | grep -E '^# METRICS|^[A-Z-]+,[0-9]+,')
      o2=$(cd "$ANBQ_NS3" && "$b2" --protocol=$proto $ARGS --run=$s $ch 2>&1 | grep -E '^# METRICS|^[A-Z-]+,[0-9]+,')
      tag="$proto ${ch%% *} seed $s"
      if [ -n "$o1" ] && [ "$o1" = "$o2" ]; then echo "IDENTICAL  $tag  ($(echo "$o1" | tail -1))"
      else echo "DIFFERENT  $tag"; diff <(echo "$o1") <(echo "$o2"); ok=0; fi
    done
  done
done
[ $ok = 1 ] && echo "STEP 0 VERIFIED: the isolated tree reproduces Paper 1" || { echo "STEP 0 FAILED"; exit 1; }

# anbq-env.sh -- paths of the A-NBQ project (sourced by the other anbq-*.sh tools).
# Override any of them by exporting the variable before calling a tool.
ANBQ_REPO=${ANBQ_REPO:-$HOME/anbq-repo}              # git clone of anbq-fanet (source of truth)
ANBQ_HOME=${ANBQ_HOME:-$HOME/anbq-fanet}             # work area: ns-3 tree + results
ANBQ_NS3=${ANBQ_NS3:-$ANBQ_HOME/ns-3-anbq}           # isolated ns-3.48 tree (own build/ and CMake cache)
ANBQ_RESULTS=${ANBQ_RESULTS:-$ANBQ_HOME/results}
P1_REPO=${P1_REPO:-$HOME/nbqmaodv-repo}              # Paper 1 (read only)
P1_NS3=${P1_NS3:-$HOME/nbqmaodv-fanet/ns-3-nbq}      # Paper 1 ns-3 tree (read only)
NS3_TAG=${NS3_TAG:-ns-3.48}
# upstream modules the scenarios need; every module under $ANBQ_REPO/src is added automatically
ANBQ_BASE_MODULES=${ANBQ_BASE_MODULES:-"aodv;applications;energy;flow-monitor;internet;mobility;network;propagation;wifi"}

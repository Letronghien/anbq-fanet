# Step 0 — isolated project on the VM

Goal: Paper 2 compiles and runs in its own ns-3 tree, so nothing done here can change a Paper-1 build,
binary or result, and every A-NBQ file is recognisable by its `anbq-` prefix.

## Layout on the VM

| Path | Role | Written by |
|---|---|---|
| `~/anbq-repo` | git clone of `anbq-fanet`; the only place patches are applied | you (`git apply`) |
| `~/anbq-fanet/ns-3-anbq` | fresh upstream ns-3.48 + `ns3-patches/`, own `build/` and `cmake-cache/` | `tools/anbq-setup-ns3.sh` |
| `~/anbq-fanet/results` | all Paper-2 outputs | Paper-2 tools |
| `~/nbqmaodv-repo`, `~/nbqmaodv-fanet` | Paper 1 | **read only** for Paper 2 |

Repo modules (`src/*`) and scratch files (`scratch/anbq-*`) are **symlinked** into the ns-3 tree by
`tools/anbq-sync.sh`, so a patch applied in `~/anbq-repo` is exactly what gets compiled.
Run `anbq-sync.sh` again whenever a patch adds a module or a scratch file.

## Naming

- Scratch programs: `anbq-scenario-<module>.cc`, shared code `anbq-core.h`, `anbq-channel.h`, calibration
  `anbq-linkcal.cc` → binaries `ns3.48-anbq-scenario-<module>-optimized` (distinct from Paper-1 `fanet-*` in `ps`/`htop`).
- Tools `tools/anbq-*.sh|py`, docs `docs/anbq-*.md`, patches `anbq-step<n>.patch`, outputs `anbq-step<n>-*`.
- The baseline module keeps its Paper-1 name `nbqmaodv` (it is the Paper-1 baseline, byte-identical).
  The new module will be `anbqmaodv`.

## Imported from Paper 1 (nbqmaodv-fanet @ 5725ea6)

- `src/nbqmaodv/` — verbatim.
- `ns3-patches/wifi-radio-energy-model-predictive-off.patch` — verbatim.
- `scratch/anbq-{core.h,channel.h,scenario-aodv.cc,scenario-nbqmaodv.cc,linkcal.cc}` — from `scratch/fanet-*`;
  only the file names (and `#include`s / comments naming them) changed, plus one provenance comment line.
- Not imported: PMAODV, QMAODV, SA-QMAODV (Paper 2 compares A-NBQ with AODV, NBQ-MAODV and the oracle).
  Their Paper-1 results stay citable from the Paper-1 repo.

## Verification (`tools/anbq-verify-step0.sh`)

1. `src/nbqmaodv` identical to the Paper-1 repo and to the Paper-1 ns-3 tree.
2. Short runs (AODV, NBQ-MAODV × K0, K1 × seeds 1, 2): `# METRICS` and CSV lines byte-identical between the
   Paper-1 binaries and the new ones. Step 0 is accepted only if all are identical.

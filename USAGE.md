# Professional League of Legends Research: Reproduction Guide

This repository provides a reproducible analysis pipeline for the map-side study,
along with source code for related exploratory analyses, reports, and presentations.

## Directory guide

| Path | Contents |
|---|---|
| `run_all.py`, `src/` | Main map-side analysis: data audits, regressions, team-strength controls, path decomposition, robustness, predictive models, tables, and figures |
| `data/derived/` | Analysis-ready data: 86,074 team-game records from 43,037 games |
| `results/`, `figures/` | Main analysis outputs and figures |
| `tests/`, `.github/workflows/` | Automated checks and continuous integration configuration |
| `docs/` | Methods, research scope, and result documentation |
| `supplementary.zip` | Complete supplementary materials; extraction restores `supplementary/`, including early analyses, top-lane research, report builders, and presentation source code |
| `docs/SOURCE_INDEX.md` | Index of all source files |

## Run the main analysis

Open a terminal at the repository root. Python 3.13 is recommended. Create a separate environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python run_all.py
```

In Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.
`requirements.txt` specifies broader compatible version ranges;
`requirements-tested.txt` records the direct dependency versions used for verification.

The default run reads `data/derived/redblue_teamgames.csv.gz` directly. This file is
losslessly compressed and requires no manual extraction or additional raw-data download.
Outputs are written to the repository's `results/` and `figures/` directories.
The predictive-model step takes longer than the standard regressions.

## Rebuild from raw data

Place the yearly Oracle's Elixir CSV files in `data/raw/`, using the filenames in
that directory's README, then run:

```bash
python run_all.py --from-raw
```

Alternatively, set the `LOL_RAW_DIR` environment variable to an existing raw-data
directory. The code does not depend on the original project's parent directory.
Download the raw CSV files separately; see `LICENSE` and `data/raw/README.md` for
attribution and terms. Later downloads may contain updates, so the sample and
results may differ from the committed snapshot.

## Verification

```bash
python -m unittest discover -s tests
python src/audit_data.py
python src/paper_claim_audit.py
```

The tests check headline results, documented values, file structure, and runtime
configuration. The data audit checks paired team records, outcomes, map sides,
and mirrored variables.

See [reproduction and verification](docs/VERIFICATION.md) for recorded checks and known limitations.

## Supplementary code

The complete supplementary materials are in `supplementary.zip`.
`supplementary/README.md` documents historical scripts, required inputs, and execution
boundaries. Run `python -m zipfile -e supplementary.zip .` at the repository root
to restore all files. Install `requirements-supplementary.txt` before building Word
reports or running additional exploratory analyses.

The default pipeline does not call supplementary scripts. Historical reports and
early results should not be treated as current manuscript conclusions. The current
mathematical manuscript excludes counter-pick and TOST/FDR claims; see
`docs/PAPER_STATUS.md` for details.

This is an observational study. First-objective fields lack reliable event timestamps,
so decomposition and predictive results cannot be interpreted as causal effects or
strictly real-time forecasts made at minute 15.

# Reproduction and Verification

This document records the analysis environment, completed checks, and known limitations.
The main analysis reads the committed `data/derived/redblue_teamgames.csv.gz` by default.
See the [reproduction guide](../USAGE.md) and [data documentation](../data/raw/README.md)
for rebuilding from raw inputs.

## Verification commands

After installing the dependencies in `requirements-tested.txt`, run these commands
at the repository root:

```bash
python -m unittest discover -s tests
python src/audit_data.py
python src/paper_claim_audit.py
```

Run `python run_all.py` for the complete analysis and figures.
[GitHub continuous integration](https://github.com/CSNOOB6226/lol-blue-side-advantage/actions)
runs unit tests, the data audit, and the documented-results audit; it does not run
the complete analysis pipeline.

## Complete analysis verification (2026-10-10)

The following records come from a working copy based on commit `5642429`, using
macOS and Python 3.13. Direct dependency versions are in `requirements-tested.txt`.

| Check | Result |
|---|---|
| Complete analysis, `python run_all.py` | All steps passed; 75.449 seconds |
| Main repository unit tests | 16 passed; 0.153 seconds |
| `make check` | Passed; 0.183 seconds |
| Headline README values versus regenerated results | Consistent |
| Nested Elo model | Full rank and converged; pseudo-R² = 0.0926 |

The mean blue-side gold lead at minute 15 was 274.61, with 95% CI [246.26, 302.95].
This complete-pipeline record is from macOS; a complete run on Ubuntu has not yet
been verified.

## Data and supplementary materials

The main dataset contains 86,074 team-game records from 43,037 games.
The SHA-256 checksum of the decompressed CSV content is:

```text
99594186fae7af18af0c83711b6eaf2491e8efc98804014c478b07f6686dfe90
```

`supplementary.zip` contains 192 files under the top-level `supplementary/` directory,
including 65 Python files and 45 JavaScript modules. Together with the main analysis
and tests, the repository provides 137 source files. See the
[supplementary guide](../supplementary/README.md) for purposes, optional dependencies,
and required inputs, and the [source index](SOURCE_INDEX.md) for full paths.

Some historical manuscript link targets, Word templates, and original report images
are not distributed in the source archive. Related report builders may require
separately supplied documents, images, or system fonts.

## Earlier verification records

| Date | Scope and results |
|---|---|
| 2026-09-24 | All 14 main-analysis steps completed; 13 main repository unit tests and 6 supplementary manuscript-audit tests passed; syntax checks passed for 91 Python files and 45 JavaScript modules. |
| 2026-10-01 | Unit tests, data audit, and result audit passed; data content and model specifications were unchanged, and the complete analysis was not rerun. |
| 2026-10-07 | On macOS with Python 3.13.12, 13 unit tests, the structural data audit, and the results/documentation consistency audit passed; syntax checks passed for 91 Python files, and the data checksum matched; the complete analysis was not rerun. |

## Scope and limitations

- Recorded analysis runs used the packaged derived dataset. They did not download or update raw CSV files, or execute a complete `--from-raw` rebuild.
- A historical run of `team_strength.py` produced a `statsmodels` maximum-likelihood convergence warning. The program completed and regression checks for the published outputs passed. This does not establish reliable convergence for every model; review optimizer diagnostics before citing detailed model estimates.
- Supplementary research, Word builders, and presentation source code passed syntax and inventory checks, but historical reports and presentations were not all regenerated. See the [supplementary guide](../supplementary/README.md) for additional inputs, fonts, and calling interfaces.

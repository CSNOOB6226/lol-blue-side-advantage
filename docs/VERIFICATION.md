# Reproduction and checks

The main analysis reads the committed `data/derived/redblue_teamgames.csv.gz`.
See [USAGE.md](../USAGE.md) for setup and
[data/raw/README.md](../data/raw/README.md) for rebuilding from raw inputs.

## Environment and commands

Python 3.10 or later is required. The main pipeline has run successfully on macOS
with Python 3.13 and the direct dependency versions in
[`requirements-tested.txt`](../requirements-tested.txt). This file pins the direct
dependencies, rather than every transitive dependency. A complete Linux pipeline
run has not been verified.

From the repository root, install the dependencies and run:

```bash
python -m pip install -r requirements-tested.txt
python -m unittest discover -s tests
python src/audit_data.py
python src/paper_claim_audit.py
python run_all.py
```

The tests cover data structure, documented results, and runtime configuration.
`audit_data.py` checks paired team records, outcomes, sides, and mirrored variables.
`paper_claim_audit.py` compares the README and methods notes with committed results
and checks that the expected figures are present.
[GitHub checks](https://github.com/CSNOOB6226/lol-blue-side-advantage/actions)
run these tests and checks, but do not run the complete analysis.

## Dataset

The dataset contains 86,074 team-game records from 43,037 games.
The SHA-256 checksum of the decompressed CSV content is:

```text
99594186fae7af18af0c83711b6eaf2491e8efc98804014c478b07f6686dfe90
```

The completed runs used this derived dataset. A complete `--from-raw` rebuild has
not been verified; later raw downloads may also differ from the committed snapshot.

## Known limitations

- An earlier run of `team_strength.py` produced a `statsmodels` maximum-likelihood
  convergence warning. The script completed and published-output checks passed;
  a later nested Elo fit converged. Check optimizer diagnostics before using
  detailed model estimates, since these results do not guarantee convergence for
  every specification.
- Supplementary code has been checked for syntax, but the historical reports and
  presentations have not all been regenerated. Some builders require original
  documents, images, templates, or system fonts that are not included. See the
  [supplementary guide](../supplementary/README.md) for inputs and usage, and the
  [source index](SOURCE_INDEX.md) for file paths.
- Repository checks cover the main analysis and its documentation. They do not
  verify every claim in the separately maintained manuscript or its Word output;
  see [manuscript scope](PAPER_STATUS.md).

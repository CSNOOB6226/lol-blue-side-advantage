# Manuscript scope

The current manuscript is the second revision, mathematical version. Extract
[`supplementary.zip`](../supplementary.zip) at the repository root to access:

```text
supplementary/side_advantage/manuscript/revised_manuscript/manuscript_en_math_revised.md
```

The manuscript focuses on map side, early objectives, 15-minute economy, and
predictive model comparisons. The folder README lists its sources and figures.
Counter-pick analyses and their TOST/FDR results are outside the current manuscript
because reveal order does not establish actual counter-pick intent. Those outputs
remain in the repository as historical supplementary analyses.

`make check` runs tests and compares documented repository results with committed
tables and figures. The fixed-effects check compares all three README estimates
with the results CSV at the displayed precision and rejects missing or non-finite
values. The manuscript reports the same estimates: +5.79, +5.49, and +4.57 percentage
points. These checks do not validate the manuscript text or its rendered Word
document; changes to either need a separate review.

The literature search and screening plan is in
[`LITERATURE_REVIEW.md`](LITERATURE_REVIEW.md). Run `python run_all.py` to regenerate
the main repository outputs. The first-draft submission-readiness document is
historical and does not describe the second revision.

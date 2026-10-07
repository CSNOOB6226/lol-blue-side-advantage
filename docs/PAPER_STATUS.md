# Manuscript scope and audit coverage

Reviewed 2026-09-14 (UTC).

The complete supplementary materials are preserved in
[`supplementary.zip`](../supplementary.zip). Extract it at the repository root
to access the manuscript path below.

The current manuscript is the second revision, mathematical version:
`supplementary/红蓝方研究/论文/第二版_改写稿/manuscript_en_math_revised.md`. Its folder README explicitly selects version 02. It prioritizes
map side, early objectives, and 15-minute economy, with predictive triangulation.
Counter-pick analyses and their TOST/FDR results were removed because reveal order
cannot establish actual counter-pick intent. Existing repository outputs remain
supplementary historical analyses; their presence does not make them current paper claims.

`make check` audits repository README claims and committed output inventory. It does
not validate the external manuscript or its rendered Word document. The fixed-effects
headline is checked against all three CSV estimates at the displayed precision;
non-finite or missing estimates fail. The current manuscript also reports +5.79,
+5.49, and +4.57 percentage points, consistent with those results at this review.

Before submission, reconcile the current manuscript with regenerated tables, complete
the search and screening log in `docs/LITERATURE_REVIEW.md`, and choose a public
code/data availability destination. The first-draft submission-readiness document
is historical and should not be treated as an audit of the second revision.

# Methods and interpretation

This study uses professional *League of Legends* match data to examine map side,
draft priority, and early-game economy. Statistical inference, associational
decomposition, and prediction address different questions. The observational
design does not establish a causal effect of map side or draft priority.

中文说明：当前研究报告的是关联。蓝方与一选权并非随机分配；路径分解不是因果中介，
机器学习比较也不能验证因果机制。历史后手时机分析保留为补充材料。

## Data and paired observations

The committed panel, `data/derived/redblue_teamgames.csv.gz`, contains **43,037
games and 86,074 team-games** from **80 non-Chinese league labels**, covering
10 January 2022 to 2 June 2026. The 2026 season is partial. LPL and LDL are
excluded because the required economic and objective fields are largely missing.
The raw-data builder removes void/remake games without one winner and one loser.

Every game contributes two dependent rows: one blue team and one red team, with
opposite outcomes and mirror-symmetric opponent differences. `audit_data.py`
checks these structural assumptions before downstream analysis. Inferential
regressions use game-clustered standard errors where applicable; bootstrap
procedures resample whole games. Predictive folds keep both rows together.

| Analysis | Estimation sample | Dependence treatment |
|---|---:|---|
| Pooled side association and team fixed effects | 86,074 team-games | Game-clustered standard errors |
| 2026 side + first-pick joint model | 9,878 team-games / 4,939 games | Game-clustered standard errors |
| Gold-at-15 composition and predictive comparison | 86,070 team-games / 43,035 games | Game clustering or grouped prediction, respectively |
| Supplementary reform diagnostic | 24 leagues / 109 league-years | League-clustered standard errors |

Samples vary with the fields required by each model. The 2026 joint model
excludes 61 games with missing first-pick status; the predictive sample excludes
two games with incomplete feature values. These model samples should not be
confused with the full panel.

## Map side, first pick, and team strength

`model_draft_value.py` fits season-specific logistic regressions of win/loss on
blue side. Odds ratios describe win odds for blue relative to red; they are not
probability ratios or percentage-point effects.

Before 2026, blue side and first-pick status coincide in the observed nonmissing
draft data, preventing separate coefficient estimation. In 2026, red-side first
pick occurs often enough to fit `result ~ blue + firstPick`. This separation
creates estimable associations, not random assignment: team preferences,
strength, tournament procedures, and series state can influence allocation.

The 2026 joint estimates are blue-side OR **1.269** (95% CI **[1.115, 1.443]**)
and first-pick OR **0.939** (95% CI **[0.825, 1.068]**). First pick has no
detectable independent association in this sample. Its interval is too wide to
establish practical equivalence, so a non-significant coefficient does not show
that first pick has no value.

`team_strength.py` constructs pre-match Elo sequentially within each league-season
(initial rating 1500, K = 24), using no current-match outcome in the rating
predictor. `fixed_effects_controls.py` adds own-team-season and opponent-team
fixed effects in pooled linear probability models. These controls test sensitivity
to measured or stable team strength; they do not eliminate all selection bias,
roster changes, preparation differences, or within-series adaptation.

## Objectives, economy, and associational paths

`paper_tables.py` reports side differences in objective ownership, gold, and
experience, and models gold difference at 15 minutes using objective indicators
and season dummies. Binary outcomes use a linear probability interpretation;
gold and experience differences retain their natural units.

The source identifies first-objective ownership but does not provide reliable
event timestamps for first herald, dragon, tower, or blood in every file used
here. Some recorded events may occur after minute 15. Objective-to-gold estimates
are therefore associations with the economic snapshot, not verified pre-15
contributions or causal gold valuations.

`mediation_path.py` decomposes a linear blue-side win association into a residual
component and products of side-to-state and state-to-win coefficients. The main
channels are first herald, first dragon, gold difference at 15, and first tower.
Intervals use a **600-replicate game-cluster bootstrap**, preserving both team
rows from each sampled game. `mediation_full.py` checks an expanded state set.

This is an **associational path decomposition**, not causal mediation. The
channels are mutually dependent and sequentially ordered; their ownership is
not randomized, and sequential ignorability is not established. Components
depend on the included variables and season. An unexplained component does not
identify camera angle, map geometry, or any other single omitted mechanism.

## Predictive comparison

`ml_validation.py` compares Logistic Regression, Random Forest, and **XGBoost**
on the same ten features: side; gold and XP differences at 10 and 15 minutes;
first herald, dragon, tower, and blood; and void-grub count. Void grubs are coded
as zero before the mechanic existed.

Five-fold **GroupKFold** groups by `gameid`, preventing one game's mirrored
rows from appearing in both training and testing. Logistic standardization is
fitted inside each training fold. Fixed model settings and random seeds support
reproduction. Two chronological checks train through 2024/test 2025 and train
through 2025/test 2026. Metrics are AUC, log loss, and Brier score; random-forest
permutation importance is calculated on held-out folds.

Mean grouped-fold AUC is **0.8343** for Logistic Regression, **0.8328** for Random
Forest, and **0.8331** for XGBoost. The models have similar predictive discrimination
under the tested feature set and settings. AUC is not classification accuracy.
Because objective timestamps are unavailable, this feature set should be
described as a match-state predictive benchmark, not a pre-game model or a
strictly real-time 15-minute forecast. Similar AUC does not prove that all
nonlinear models are unnecessary, nor does feature importance measure causality.

## Supplementary analyses

**Reform diagnostic.** `did_first_selection.py` fits a weighted league-season
difference-in-differences model and event study. Treatment intensity is each
league's 2026 share of first-pick team-games played on red side. The main estimate
is **+4.04 percentage points** per unit of intensity (95% CI **[-4.07, +12.15]**,
p = 0.329). The panel is small, intensity is endogenous, and pre-reform trends
are not sufficiently flat. The result remains a supplementary diagnostic;
it cannot establish that the rule caused, prevented, or failed to prevent a
change in side advantage. Its outcome is blue win rate relative to 50%, which
differs from the blue-minus-red probability contrast used in team-game models.

**Historical reveal-order analysis.** Role-level reveal gaps are observable
timing proxies, not direct measures of counter-pick intent or successful
counter-picking. The 2025–2026 five-role family applies Benjamini–Hochberg
correction: **0/10 survive FDR**. Under the prespecified OR bounds
`[1/1.10, 1.10]`, **10/10 counter-pick tests are statistically equivalent to null**
in those historical models. This means equivalence within the chosen bounds for
the tested reveal-gap association, not proof of exactly zero effect or evidence
that all counter-picking strategies are ineffective. First-pick equivalence is
not established. These analyses and `matchup_quality.py` remain supplementary;
they are outside the current manuscript's central claims.

## Reproduction and scope

`python run_all.py` regenerates analyses and figures from the committed panel;
`python run_all.py --from-raw` rebuilds the panel first. See
[README.md](../README.md) for headline findings and commands,
[VERIFICATION.md](VERIFICATION.md) for verification coverage, and
[PAPER_STATUS.md](PAPER_STATUS.md) for the current manuscript scope.
`report_bilingual.md` records an earlier analysis. For the current interpretation
and scope, use this methods note and `PAPER_STATUS.md`.

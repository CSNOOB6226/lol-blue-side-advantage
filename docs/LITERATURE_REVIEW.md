# Literature review protocol and seed set

This file turns the paper's literature gap into a reproducible task. It is a
protocol, not a claim that the search is complete. The machine-readable seed set
is in [`literature_seed.csv`](literature_seed.csv).

## Review question

What empirical evidence explains map-side, draft-priority, champion-selection,
early-objective, and team-strength associations with winning in professional
*League of Legends*?

## Sources and search strings

Search OpenAlex, Scopus, Web of Science, ACM Digital Library, IEEE Xplore, and
Google Scholar. Record the exact run date, database, result count, and exported
file for every search.

Use this core query, adapting syntax without changing its concepts:

```text
("League of Legends" OR MOBA) AND
("blue side" OR "red side" OR map-side OR draft OR "first pick" OR
 counterpick OR champion OR objective OR herald OR dragon OR tower OR
 "team strength") AND
(win OR performance OR advantage OR prediction)
```

Run a second, broader methods query:

```text
(esport* OR "electronic sport*") AND
(competitive balance OR home advantage OR side advantage OR draft advantage)
```

## Eligibility rules

Include peer-reviewed empirical work about LoL or closely comparable team MOBAs
when it measures match performance, drafting, side assignment, objectives, or
team/player strength. Include systematic reviews for citation chasing. Exclude
opinion pieces, purely technical game-playing agents, papers without accessible
method details, and prediction studies that use post-outcome leakage without a
separate pre-game or early-game analysis.

Screen title/abstract, then full text. For every excluded full text, record one
reason. Deduplicate by DOI first, then normalized title. Use backward and forward
citation chasing on every included paper.

## Extraction fields

For each included study record: citation, DOI/URL, game version and dates, amateur
or professional setting, sample size, unit of observation, outcome, predictors,
handling of repeated teams/games, leakage controls, effect sizes and intervals,
causal language, limitations, and the exact manuscript claim it supports or
contradicts.

## Seed set and immediate relevance

The seed file starts with three verified sources. Novak et al. is the closest
performance-model comparison because it uses a mixed-effects model with team
effects. Sharpe et al. supplies the newest systematic map of LoL performance
indicators. Bahrololloomi et al. frames predictive work on roles and performance.
These are starting points, not a complete or balanced review.

## Completion standard

The literature blocker is cleared only when the search log is filled for every
database, duplicate removal and both screening stages are documented, uncertain
records receive a documented second-pass audit, and all substantive manuscript
claims are linked to either a source or a generated result. Report the final flow
with PRISMA-style counts.


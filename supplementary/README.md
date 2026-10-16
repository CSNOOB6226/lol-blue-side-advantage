# Supplementary research and historical sources

Related analyses, report builders and presentation sources are included in
[supplementary.zip](../supplementary.zip). The default analysis does not require extraction.

From the repository root, run:

```bash
python -m zipfile -e supplementary.zip .
```

The archive extracts into `supplementary/`. The main analysis entry point remains
`run_all.py` at the repository root.

| Directory | Contents and requirements |
|---|---|
| `side_advantage/blue_side_project/` | Historical analysis pipeline, panel and result tables. Run numbered scripts in order. Panel reconstruction reads root `data/raw/` or `LOL_RAW_DIR`; create `figures/` before plotting. `api/riot_api.py` is optional and reads credentials from environment variables. |
| `side_advantage/code/early_exploration/` | Early mechanism and mediation explorations; raw inputs come from root `data/raw/` or `LOL_RAW_DIR`. |
| `side_advantage/manuscript/revised_manuscript/` | English manuscript sources, figures and document builders. Some figure builders require locally available fonts. |
| `side_advantage/reports/` | Historical reports, interpretation guides and builders. Some require report images or Word templates that are not distributed. |
| `side_advantage/github_stuff/lol_paper_audit/` | Early manuscript audit tool and unit tests. Its input conventions differ from the main results audit. |
| `side_advantage/archive/` | Superseded report builders and exploratory scripts. Older samples are not used for the current conclusions. |
| `related_research/analysis/` | Top-lane resource allocation, champion archetypes and related explorations with data panels and result tables. Some scripts use paths relative to `supplementary/related_research/`. |
| `related_research/topics/code/` | Weak-side top lane, carry top-lane gold thresholds, data preparation and machine learning. Analysis tables are in `related_research/topics/data/`; rebuilding requires annual raw CSVs in that directory's `raw/` subdirectory. |
| `related_research/topics/2026_non_chinese_league_research_topics/` | Historical research-topic report builder. |
| `related_research/draft_exploration_archive/` | Historical draft-priority explorations and data. |
| `related_research/publishing/` | Report builders and checks. `build_topic1_docs.py` requires `inputs/topic1_source.txt`; document checks require the corresponding generated Word files. |
| `related_research/publishing/presentations/toplane-strategy/` | Modular top-lane strategy slides and source data. |
| `related_research/publishing/presentations/research-report/` | Research-report slides and image assets. Re-cropping requires rendered report-page images in `related_research/publishing/reports/research-report/docx-render/`. |
| `related_research/publishing/reports/literature-review/` | Literature-review report builders and checks. The contact-sheet utility reads generated images in `rendered_lit_report/`. |

## Optional dependencies

From the repository root:

```bash
python -m pip install -r requirements-supplementary.txt
```

Presentation `.mjs` files define modular slide pages. The calling application must
supply the `presentation` and `ctx` drawing interfaces; these modules are not standalone
command-line exporters. Referenced images are included in the corresponding `assets/` directories.

## Verification scope

The main analysis has recorded execution and result checks. Supplementary Python and
JavaScript sources are checked for syntax, and the independent manuscript audit has unit tests.
Historical research and report/presentation builders have not all been re-executed;
prepare external documents, fonts and inputs according to each script. Original team and
player names in source data retain their original spelling.

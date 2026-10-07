# Raw data (not committed)

The analysis uses **Oracle's Elixir** professional match data (one row per player
per game, plus team-summary rows). These CSVs are large and distributed under
Oracle's Elixir's own terms, so they are **not** stored in this repository.

## How to obtain

1. Go to **https://oracleselixir.com/tools/downloads**.
2. Download the yearly match-data CSVs for **2022, 2023, 2024, 2025, 2026**.
3. Place them in this folder (`data/raw/`). Either the English or the
   author's Chinese filenames are recognised (see `src/config.py::RAW_FILES`), e.g.:

   ```
   data/raw/2022_LoL_esports_match_data_from_OraclesElixir.csv
   data/raw/2023_LoL_esports_match_data_from_OraclesElixir.csv
   data/raw/2024_LoL_esports_match_data_from_OraclesElixir.csv
   data/raw/2025_LoL_esports_match_data_from_OraclesElixir.csv
   data/raw/2026_LoL_esports_match_data_from_OraclesElixir.csv
   ```

China (LPL/LDL) is **excluded automatically** by the build script, because
Oracle's Elixir's early-timing columns for those leagues are largely missing.

## You may not even need these

`data/derived/redblue_teamgames.csv.gz` (the analysis-ready team-game table) **is**
committed. Every model, table and figure reads that derived file, so you can
reproduce all results without the raw CSVs. You only need the raw files to
regenerate the derived table from scratch (`python src/build_dataset.py`).

## External input directory

Set `LOL_RAW_DIR` to an existing raw-data directory to avoid copying large files.
For example: `LOL_RAW_DIR=/path/to/raw python run_all.py --from-raw`.
The packaged derived table uses the original data snapshot; newer downloads can
change the sample and estimates.

"""Shared paths, input-file discovery, and analysis constants.

Raw data are read from data/raw/ by default. Set LOL_RAW_DIR to use another
input directory without changing the source code. See data/raw/README.md.
"""
from __future__ import annotations
import os

# ---------------------------------------------------------------- paths
SRC_DIR      = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.dirname(SRC_DIR)
RAW_DIR      = os.path.join(REPO_ROOT, "data", "raw")
DERIVED_DIR  = os.path.join(REPO_ROOT, "data", "derived")
RESULTS_DIR  = os.path.join(REPO_ROOT, "results")
FIGURES_DIR  = os.path.join(REPO_ROOT, "figures")

# Optional external raw-data directory; defaults to the repository data/raw/.
RAW_DIR = os.path.abspath(os.path.expanduser(os.environ.get("LOL_RAW_DIR", RAW_DIR)))

for _d in (DERIVED_DIR, RESULTS_DIR, FIGURES_DIR):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------- raw files
# year -> candidate filenames (first that exists wins)
RAW_FILES = {
    2022: ["2022年英雄联盟职业比赛原始数据.csv",
           "2022_LoL_esports_match_data_from_OraclesElixir.csv"],
    2023: ["2023年英雄联盟职业比赛原始数据.csv",
           "2023_LoL_esports_match_data_from_OraclesElixir.csv"],
    2024: ["2024年英雄联盟职业比赛原始数据.csv",
           "2024_LoL_esports_match_data_from_OraclesElixir.csv"],
    2025: ["2025年英雄联盟职业比赛原始数据.csv",
           "2025_LoL_esports_match_data_from_OraclesElixir.csv"],
    # 2026 primary file already excludes China; the generic name is also accepted
    2026: ["2026年非中国赛区比赛数据.csv",
           "2026年英雄联盟职业比赛原始数据.csv",
           "2026_LoL_esports_match_data_from_OraclesElixir.csv"],
}

DERIVED_TEAMGAMES = os.path.join(DERIVED_DIR, "redblue_teamgames.csv.gz")


def find_raw(year: int) -> str | None:
    """Return the path to the raw CSV for ``year`` or ``None`` if missing."""
    for fn in RAW_FILES[year]:
        p = os.path.join(RAW_DIR, fn)
        if os.path.isfile(p):
            return p
    return None


# ---------------------------------------------------------------- constants
# China leagues are excluded (LPL/LDL early-timing columns are largely missing in
# Oracle's Elixir, so they cannot support this analysis).
# EXACT match only: a substring test ("LPL" in s) would wrongly drop LPLOL,
# the Portuguese league (Liga Portuguesa), which must stay in the sample.
def is_china(league: str) -> bool:
    return str(league).strip() in {"LPL", "LDL"}


# Professional blind/counter pick schedule. The team holding the *first* overall
# pick reveals on global slots {1,4,5,8,9}; the other team on {2,3,6,7,10} and
# therefore owns the last pick (the canonical "counter-pick" slot).
SCHED_FIRST  = {1: 1, 2: 4, 3: 5, 4: 8, 5: 9}   # team with first overall pick
SCHED_SECOND = {1: 2, 2: 3, 3: 6, 4: 7, 5: 10}  # the other team (last pick)

ROLES = ["top", "jng", "mid", "bot", "sup"]

# columns pulled from the raw player+team rows
RAW_COLS = [
    "gameid", "league", "year", "date", "patch", "side", "position",
    "playername", "champion", "teamname", "teamid", "result",
    "firstPick", "pick1", "pick2", "pick3", "pick4", "pick5",
    "datacompleteness",
    "firstblood", "firstdragon", "dragons", "opp_dragons",
    "firstherald", "heralds", "void_grubs", "opp_void_grubs",
    "firsttower", "firstbaron",
    "golddiffat10", "xpdiffat10", "golddiffat15", "xpdiffat15",
    "visionscore",
]

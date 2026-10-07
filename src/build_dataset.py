"""
Build the derived team-game table used by every downstream analysis.

Input  : raw Oracle's Elixir CSVs for 2022-2026 (see config.find_raw / data/raw).
Output : data/derived/redblue_teamgames.csv.gz  (one row per team per game)

For each team-game we record:
  * identity / context : gameid, year, league, patch, date, side, blue, result, firstPick
  * early objectives   : firstblood, firstdragon, firstherald, firsttower, firstbaron,
                         void_grubs, dragons, team_vision
  * early economy      : golddiffat10/15, xpdiffat10/15
  * per-lane draft info: {role}_champ, {role}_go (global reveal slot),
                         {role}_gap (my slot - opp slot; >0 = I revealed later),
                         {role}_cp  (1 = I counter-picked = revealed last),
                         {role}_gd15, {role}_xp15 (that lane's 15-min diffs)
  * reconstruction QA  : n_lanes_matched, clean_reconstruction

The derived file is small enough to commit, so figures/tables reproduce without
the multi-hundred-MB raw CSVs.
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C


def _global_order(pickidx: float, first_pick: int) -> float:
    if pd.isna(pickidx):
        return np.nan
    sched = C.SCHED_FIRST if first_pick == 1 else C.SCHED_SECOND
    return sched[int(pickidx)]


def build_year(year: int) -> pd.DataFrame | None:
    path = C.find_raw(year)
    if path is None:
        print(f"  [{year}] raw file NOT found -> skipped")
        return None
    raw = pd.read_csv(path, usecols=lambda c: c in C.RAW_COLS, low_memory=False)
    raw = raw[~raw["league"].map(C.is_china)]
    if "datacompleteness" in raw:
        raw = raw[raw["datacompleteness"] == "complete"]
    raw["year"] = year

    team = raw[raw["position"] == "team"].copy()
    players = raw[raw["position"].isin(C.ROLES)].copy()

    # firstPick per (gameid, side) — robust to it living on player rows
    fp = (raw.dropna(subset=["firstPick"])
             .drop_duplicates(["gameid", "side"])[["gameid", "side", "firstPick"]]
             .rename(columns={"firstPick": "firstPick_side"}))
    team = team.drop(columns=[c for c in ["firstPick"] if c in team]).merge(
        fp, on=["gameid", "side"], how="left").rename(columns={"firstPick_side": "firstPick"})

    # team vision = sum of the 5 players' vision
    vis = (players.groupby(["gameid", "side"])["visionscore"].sum()
                  .rename("team_vision").reset_index())

    # ---- per-lane reveal-order reconstruction ----------------------------
    picks = team[["gameid", "side", "pick1", "pick2", "pick3", "pick4", "pick5"]]
    # player rows also carry (usually blank) pick*/firstPick columns; drop them so
    # the merge below does not create pick1_x / pick1_y and break the match.
    drop_from_players = ["firstPick", "pick1", "pick2", "pick3", "pick4", "pick5"]
    lane = players.drop(columns=[c for c in drop_from_players if c in players]) \
                  .merge(picks, on=["gameid", "side"], how="left") \
                  .merge(team[["gameid", "side", "firstPick"]], on=["gameid", "side"], how="left")

    def pidx(r):
        for i in range(1, 6):
            if r.get(f"pick{i}") == r["champion"]:
                return i
        return np.nan
    lane["pickidx"] = lane.apply(pidx, axis=1)
    lane["go"] = lane.apply(lambda r: _global_order(r["pickidx"], r["firstPick"]), axis=1)

    # opponent's per-lane global order (same role, other side)
    opp = lane[["gameid", "side", "position", "go"]].copy()
    opp["side"] = opp["side"].map({"Blue": "Red", "Red": "Blue"})
    opp = opp.rename(columns={"go": "opp_go"})
    lane = lane.merge(opp, on=["gameid", "side", "position"], how="left")
    lane["gap"] = lane["go"] - lane["opp_go"]
    lane["cp"] = (lane["gap"] > 0).astype("float")
    lane.loc[lane["gap"].isna(), "cp"] = np.nan

    # pivot lane info to wide (one column block per role)
    wide_parts = []
    for role in C.ROLES:
        rr = lane[lane["position"] == role][
            ["gameid", "side", "champion", "go", "gap", "cp",
             "golddiffat15", "xpdiffat15"]].copy()
        rr = rr.rename(columns={
            "champion": f"{role}_champ", "go": f"{role}_go", "gap": f"{role}_gap",
            "cp": f"{role}_cp", "golddiffat15": f"{role}_gd15", "xpdiffat15": f"{role}_xp15"})
        wide_parts.append(rr)
    wide = wide_parts[0]
    for p in wide_parts[1:]:
        wide = wide.merge(p, on=["gameid", "side"], how="outer")

    # ---- assemble team-game rows -----------------------------------------
    keep = ["gameid", "year", "league", "patch", "date", "side", "result",
            "teamname", "teamid",
            "firstPick", "firstblood", "firstdragon", "firstherald", "firsttower",
            "firstbaron", "void_grubs", "dragons", "opp_dragons",
            "golddiffat10", "xpdiffat10", "golddiffat15", "xpdiffat15"]
    keep = [c for c in keep if c in team.columns]
    out = team[keep].merge(vis, on=["gameid", "side"], how="left") \
                    .merge(wide, on=["gameid", "side"], how="left")
    out["blue"] = (out["side"] == "Blue").astype(int)

    # reconstruction QA
    go_cols = [f"{r}_go" for r in C.ROLES]
    out["n_lanes_matched"] = out[go_cols].notna().sum(axis=1)
    # a game is "clean" only if BOTH teams matched all 5 lanes
    per_game = out.groupby("gameid")["n_lanes_matched"].transform("min")
    out["clean_reconstruction"] = (per_game == 5).astype(int)

    print(f"  [{year}] team-games={len(out):6d}  "
          f"leagues={out.league.nunique():3d}  "
          f"firstPick==1 is Blue {100*out.loc[out.firstPick==1,'blue'].mean():5.1f}%  "
          f"clean-reconstruction {100*out.clean_reconstruction.mean():5.1f}%")
    return out


def main():
    print("Building derived team-game table (non-China, complete rows)...")
    frames = []
    for y in (2022, 2023, 2024, 2025, 2026):
        df = build_year(y)
        if df is not None:
            frames.append(df)
    if not frames:
        raise SystemExit("No raw data found. See data/raw/README.md.")
    allg = pd.concat(frames, ignore_index=True)

    # drop void/remake games: a valid game must have exactly one win and one loss.
    # (A handful of OE rows are flagged "complete" yet record 0/0 with blank stats.)
    good = allg.groupby("gameid")["result"].transform(
        lambda s: ((s == 1).sum() == 1) and ((s == 0).sum() == 1))
    dropped = int((~good).sum())
    if dropped:
        print(f"  dropped {dropped} team-game rows from {dropped//2} void/remake game(s) "
              f"(results not exactly one win + one loss)")
    allg = allg[good].reset_index(drop=True)

    allg.to_csv(C.DERIVED_TEAMGAMES, index=False)
    mb = os.path.getsize(C.DERIVED_TEAMGAMES) / 1e6
    print(f"\nWrote {C.DERIVED_TEAMGAMES}  ({len(allg):,} rows, {allg.shape[1]} cols, {mb:.1f} MB)")


if __name__ == "__main__":
    main()

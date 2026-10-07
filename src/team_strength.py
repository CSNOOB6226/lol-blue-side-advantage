"""
Team-strength control via pre-game Elo (closes the "is blue side just strong teams
on blue?" gap, and quantifies how little draft explains vs raw team strength).

Elo is updated sequentially by date WITHIN each (year, league); the rating used as a
covariate is each team's rating BEFORE the game, so it never uses the outcome being
predicted (non-circular). rating_diff = own_pre_elo - opponent_pre_elo.

Questions answered:
  * Does the blue-side OR survive controlling team strength?   (yes -> not an artifact)
  * Does first-pick stay null controlling strength?            (yes)
  * How much of winning does crude team strength explain vs every draft lever?
    (McFadden R^2 decomposition: strength >> map side >> all draft timing ~ 0)

Outputs: results/team_strength.txt, results/team_strength_R2.csv
"""
from __future__ import annotations
import os, sys
from collections import defaultdict
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from utils import load_teamgames, logit_cluster, or_ci, z

K_FACTOR = 24.0
LOG: list[str] = []
def log(m=""):
    print(m); LOG.append(str(m))


def add_pre_game_elo(d: pd.DataFrame) -> pd.DataFrame:
    """Attach pre-game Elo and rating_diff (own - opp) to every team-game row."""
    d = d.copy()
    d["team"] = d["teamname"].fillna(d["teamid"]).fillna("UNK")
    # game-level frame: one row per game with blue/red team + blue result
    g = d.pivot_table(index=["gameid", "year", "league", "date"], columns="side",
                      values="result", aggfunc="first")
    gt = d.pivot_table(index=["gameid"], columns="side", values="team", aggfunc="first")
    g = g.reset_index().merge(gt.reset_index(), on="gameid", suffixes=("_res", "_team"))
    g = g.rename(columns={"Blue_res": "blue_result", "Blue_team": "blue_team",
                          "Red_team": "red_team"})
    g["dt"] = pd.to_datetime(g["date"], errors="coerce")
    g = g.sort_values(["year", "league", "dt", "gameid"]).reset_index(drop=True)

    pre_blue, pre_red = np.full(len(g), np.nan), np.full(len(g), np.nan)
    ratings = None
    key = None
    for i, r in enumerate(g.itertuples(index=False)):
        k = (r.year, r.league)
        if k != key:                       # reset ratings each (year, league)
            ratings = defaultdict(lambda: 1500.0); key = k
        eb, er = ratings[r.blue_team], ratings[r.red_team]
        pre_blue[i], pre_red[i] = eb, er
        if pd.notna(r.blue_result):
            exp_b = 1.0 / (1.0 + 10 ** ((er - eb) / 400.0))
            ratings[r.blue_team] = eb + K_FACTOR * (r.blue_result - exp_b)
            ratings[r.red_team]  = er + K_FACTOR * ((1 - r.blue_result) - (1 - exp_b))
    g["pre_blue"], g["pre_red"] = pre_blue, pre_red

    # map rating_diff back to each team-game row
    bmap = g.set_index("gameid")[["pre_blue", "pre_red"]]
    d = d.merge(bmap, on="gameid", how="left")
    d["pre_elo"] = np.where(d.side == "Blue", d.pre_blue, d.pre_red)
    d["opp_elo"] = np.where(d.side == "Blue", d.pre_red, d.pre_blue)
    d["rating_diff"] = d["pre_elo"] - d["opp_elo"]
    return d


def main():
    d = load_teamgames()
    d = add_pre_game_elo(d)
    d["z_rd"] = z(d["rating_diff"])

    # sanity: Elo should predict wins
    val = d.dropna(subset=["z_rd", "result"])
    m_str = logit_cluster("result ~ z_rd", val)
    log("PRE-GAME ELO sanity: result ~ z(rating_diff)")
    log(f"  OR per SD = {np.exp(m_str.params.z_rd):.3f}  McFadden R^2={m_str.prsquared:.4f}"
        f"  (rating_diff SD = {d.rating_diff.std():.0f} Elo)")

    # ---- blue-side OR before vs after controlling strength (per year) ----
    log("\nBLUE-SIDE OR: raw vs strength-controlled (result ~ blue [+ z_rd])")
    log("  (coupled regime 2022-25: side assigned -> strength ~orthogonal, OR stable/up;")
    log("   decoupled 2026: teams CHOOSE side -> some raw edge is strong-teams-pick-blue.)")
    for y in sorted(d.year.unique()):
        s = d[d.year == y].dropna(subset=["result", "blue", "z_rd"])
        b0 = or_ci(logit_cluster("result ~ blue", s), "blue")
        b1 = or_ci(logit_cluster("result ~ blue + z_rd", s), "blue")
        tag = "selection: raw edge partly strong-teams-on-blue" if (b0[0] - b1[0]) > 0.05 \
              else "map effect not a strength artifact"
        log(f"  {y}: blue OR {b0[0]:.3f} (raw) -> {b1[0]:.3f} [CI {b1[1]:.3f},{b1[2]:.3f} "
            f"p={b1[3]:.2g}] ({tag})")

    # ---- 2026: first-pick null, strength-controlled ----
    s26 = d[d.year == 2026].dropna(subset=["result", "blue", "firstPick", "z_rd"])
    fp0 = or_ci(logit_cluster("result ~ firstPick + blue", s26), "firstPick")
    fp1 = or_ci(logit_cluster("result ~ firstPick + blue + z_rd", s26), "firstPick")
    log("\n2026 FIRST-PICK OR: raw vs strength-controlled")
    log(f"  firstPick OR {fp0[0]:.3f} (p={fp0[3]:.2g})  ->  {fp1[0]:.3f} (p={fp1[3]:.2g}) with strength")

    # ---- "how much does draft matter?" McFadden R^2 decomposition (2026) ----
    zg = []
    for role in C.ROLES:
        s26[f"z_{role}"] = z(s26[f"{role}_gap"]); zg.append(f"z_{role}")
    s26d = s26.dropna(subset=zg)
    r_null = logit_cluster("result ~ z_rd", s26d).prsquared
    r_side = logit_cluster("result ~ z_rd + blue", s26d).prsquared
    r_draft = logit_cluster("result ~ z_rd + blue + firstPick + " + " + ".join(zg), s26d).prsquared
    log("\nHOW MUCH DOES DRAFT MATTER?  McFadden pseudo-R^2, nested (2026, n=%d)" % len(s26d))
    log(f"  team strength (Elo) only          : {r_null:.4f}")
    log(f"  + blue side (map)                 : {r_side:.4f}   (+{r_side-r_null:.4f})")
    log(f"  + first-pick + 5-lane counterpick : {r_draft:.4f}   (+{r_draft-r_side:.4f} from ALL draft timing)")
    log("  -> crude team strength explains far more than map side, which in turn")
    log("     dwarfs every draft-timing lever combined (~0 incremental R^2).")

    pd.DataFrame({"model": ["strength", "strength+side", "strength+side+draft"],
                  "mcfadden_r2": [r_null, r_side, r_draft]}).to_csv(
        os.path.join(C.RESULTS_DIR, "team_strength_R2.csv"), index=False)
    with open(os.path.join(C.RESULTS_DIR, "team_strength.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("\nWrote results/team_strength.txt, results/team_strength_R2.csv")


if __name__ == "__main__":
    main()

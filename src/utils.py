"""Small shared helpers: loading, standardization, clustered logit, OR/CI, BH-FDR."""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C


def load_teamgames() -> pd.DataFrame:
    if not os.path.exists(C.DERIVED_TEAMGAMES):
        raise SystemExit("Derived table missing. Run:  python src/build_dataset.py")
    return pd.read_csv(C.DERIVED_TEAMGAMES, low_memory=False)


def z(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return (s - s.mean()) / s.std()


def logit_cluster(formula: str, df: pd.DataFrame, group: str = "gameid"):
    """Logistic regression with cluster-robust SE by ``group``."""
    return smf.logit(formula, df).fit(
        disp=0, cov_type="cluster", cov_kwds={"groups": df[group]})


def ols_cluster(formula: str, df: pd.DataFrame, group: str = "gameid"):
    return smf.ols(formula, df).fit(
        cov_type="cluster", cov_kwds={"groups": df[group]})


def or_ci(res, name: str):
    """(OR, lo95, hi95, p) for a fitted coefficient."""
    b, se = res.params[name], res.bse[name]
    return np.exp(b), np.exp(b - 1.96 * se), np.exp(b + 1.96 * se), res.pvalues[name]


def bh_fdr(pvals):
    """Benjamini-Hochberg FDR-adjusted p-values (monotone)."""
    p = np.asarray(pvals, float)
    n = len(p)
    order = np.argsort(p)
    adj = np.empty(n)
    prev = 1.0
    for rank, idx in enumerate(order[::-1]):          # largest -> smallest
        i = n - rank                                   # BH rank (1-based)
        prev = min(prev, p[idx] * n / i)
        adj[idx] = prev
    return adj

"""
QoE scoring functions used in Section 4 of the paper: KPI normalization
(eqs. 1 and 2) and the coverage score (eq. 5) with its penalties.
"""
import numpy as np
import pandas as pd


# ── Normalization functions (Sect. 3.1) ─────────────────────────────────

def linear_norm_pos(x, L, U):
    """Eq. (1), positive KPI (higher = better)."""
    return np.clip((x - L) / (U - L), 0, 1)


def linear_norm_neg(x, L, U):
    """Negative KPI (lower = better). L is the bad level and U the good level,
    as in the threshold table, so U < L and the same expression as for a
    positive KPI applies."""
    return np.clip((x - L) / (U - L), 0, 1)


def logistic_norm_pos(x, a, b):
    """Logistic normalization, positive KPI (higher = better)."""
    return 1.0 / (1.0 + np.exp(-a * (x - b)))


def logistic_norm_neg(x, a, b):
    """Logistic negative KPI."""
    return 1.0 / (1.0 + np.exp(+a * (x - b)))


# ── Levels and logistic parameters (Table 1 of the paper; SERVICE_SCORES.md for the rest) ──────────────────────────────

KPI_THRESHOLDS = {
    "DL_Mbps":   {"dir": "pos", "L": 1.0,   "U": 20.0,   "a": 0.25, "b": 5.0},
    "UL_Mbps":   {"dir": "pos", "L": 0.5,   "U": 10.0,   "a": 0.40, "b": 3.0},
    "RTT_ms":    {"dir": "neg", "L": 150.0,  "U": 30.0,   "a": 0.04, "b": 75.0},
    "TCP_pct":   {"dir": "neg", "L": 10.0,   "U": 0.5,    "a": 0.30, "b": 3.0},
    "Session_SR":{"dir": "pos", "L": 80.0,   "U": 99.0,   "a": 0.30, "b": 92.0},
    "RSRP_dBm":  {"dir": "pos", "L": -110.0, "U": -80.0,  "a": 0.10, "b": -95.0},
    "RSRQ_dB":   {"dir": "pos", "L": -15.0,  "U": -8.0,   "a": 0.50, "b": -11.5},
    "SINR_dB":   {"dir": "pos", "L": 0.0,    "U": 20.0,   "a": 0.25, "b": 10.0},
    "MOS":       {"dir": "pos", "L": 2.5,    "U": 4.3,    "a": 2.00, "b": 3.4},
    "Attach_SR": {"dir": "pos", "L": 85.0,   "U": 99.0,   "a": 0.40, "b": 94.0},
}


def normalize_kpi(series, kpi_name, method="logistic"):
    """Normalize a KPI series using the paper's thresholds."""
    cfg = KPI_THRESHOLDS[kpi_name]
    if method == "linear":
        if cfg["dir"] == "pos":
            return linear_norm_pos(series, cfg["L"], cfg["U"])
        else:
            return linear_norm_neg(series, cfg["L"], cfg["U"])
    else:  # logistic
        if cfg["dir"] == "pos":
            return logistic_norm_pos(series, cfg["a"], cfg["b"])
        else:
            return logistic_norm_neg(series, cfg["a"], cfg["b"])


# ── Coverage score (eq. 5, Sect. 3.2) ────────────────────────────────

def compute_qoe_cov(df, col_rsrp=None, col_rsrq=None,
                    col_sinr=None, col_dist=None, method="logistic"):
    """
    Eq. (5):
      QoE_COV = 100 × (0.35·Z_RSRP + 0.25·Z_RSRQ + 0.30·Z_SINR + 0.10·Z_DIST)

    If DIST or any KPI column is None/absent, weights are renormalized
    over the available columns so the score always sums to 100.
    """
    # Collect available components: (weight, z_score)
    components = []

    if col_rsrp and col_rsrp in df.columns:
        z = normalize_kpi(df[col_rsrp], "RSRP_dBm", method)
        components.append((0.35, z))

    if col_rsrq and col_rsrq in df.columns:
        z = normalize_kpi(df[col_rsrq], "RSRQ_dB", method)
        components.append((0.25, z))

    if col_sinr and col_sinr in df.columns:
        z = normalize_kpi(df[col_sinr], "SINR_dB", method)
        components.append((0.30, z))

    if col_dist and col_dist in df.columns:
        z = linear_norm_neg(df[col_dist], L=5000, U=0)   # 5 km bad, 0 km good
        components.append((0.10, z))

    if not components:
        raise ValueError(
            "compute_qoe_cov: no valid KPI columns found. "
            "Check col_rsrp/col_rsrq/col_sinr arguments."
        )

    # Renormalize weights to sum to 1.0
    total_w = sum(w for w, _ in components)
    qoe = sum((w / total_w) * z for w, z in components) * 100
    return qoe


# ── QoE score → class mapping ──────────────────────────────────────────────

QOE_BANDS = [
    (90, 100, "Excellent"),
    (70,  90, "Good"),
    (50,  70, "Degraded"),
    (0,   50, "Poor"),
]


def qoe_to_class(score):
    """Map a QoE score [0,100] to the four-level label."""
    for lo, hi, label in QOE_BANDS:
        if lo <= score <= hi:
            return label
    return "Poor"


def scores_to_classes(scores):
    return pd.Series(scores).apply(qoe_to_class)


# ── Coverage penalties (Sect. 3.2) ─────────────────────────────────────

def coverage_penalty(df, col_rsrp="RSRP_dBm", col_rsrq="RSRQ_dB",
                     col_sinr="SINR_dB"):
    p = (15 * (df[col_rsrp] < -110).astype(int)
       + 10 * (df[col_rsrq] < -15).astype(int)
       + 10 * (df[col_sinr] < 0).astype(int))
    return p

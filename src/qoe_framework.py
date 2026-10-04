"""
QoE scoring functions.
Normalization and the coverage score used in Section 4 of the paper, plus
feature helpers for the archived churn notebooks.
"""
import numpy as np
import pandas as pd


# ── Normalization functions (Section 3.1) ─────────────────────────────────

def linear_norm_pos(x, L, U):
    """Eq. lin_pos: positive KPI (higher = better)."""
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


# ── KPI thresholds from Table 1 of the paper ──────────────────────────────

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


# ── Coverage QoE (eq:cov_qoe, Section 3.6) ────────────────────────────────

def compute_qoe_cov(df, col_rsrp=None, col_rsrq=None,
                    col_sinr=None, col_dist=None, method="logistic"):
    """
    Eq. cov_qoe:
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


# ── Coverage penalty (eq:cov_penalty) ─────────────────────────────────────

def coverage_penalty(df, col_rsrp="RSRP_dBm", col_rsrq="RSRQ_dB",
                     col_sinr="SINR_dB"):
    p = (15 * (df[col_rsrp] < -110).astype(int)
       + 10 * (df[col_rsrq] < -15).astype(int)
       + 10 * (df[col_sinr] < 0).astype(int))
    return p


# ── D2 Framework-derived features (Section 7.5) ───────────────────────────

# IBM Telco xlsx uses spaced/titled names; map to standard Kaggle CSV names.
_IBM_TO_STANDARD = {
    'CustomerID':      'customerID',
    'Tenure Months':   'tenure',
    'Senior Citizen':  'SeniorCitizen',
    'Phone Service':   'PhoneService',
    'Multiple Lines':  'MultipleLines',
    'Internet Service':'InternetService',
    'Online Security': 'OnlineSecurity',
    'Online Backup':   'OnlineBackup',
    'Device Protection':'DeviceProtection',
    'Tech Support':    'TechSupport',
    'Streaming TV':    'StreamingTV',
    'Streaming Movies':'StreamingMovies',
    'Paperless Billing':'PaperlessBilling',
    'Payment Method':  'PaymentMethod',
    'Monthly Charges': 'MonthlyCharges',
    'Total Charges':   'TotalCharges',
    'Churn Label':     'Churn',
    'Churn Value':     '_ChurnValue',   # numeric target duplicate — drop later
}
# IBM-only columns that have no analogue in the standard Kaggle CSV
_IBM_EXTRA_DROP = [
    'Count', 'Country', 'State', 'City', 'Zip Code', 'Lat Long',
    'Latitude', 'Longitude', 'Churn Score', 'Churn Reason', 'CLTV',
    '_ChurnValue',
]


def _normalize_ibm_format(df):
    """Rename IBM xlsx columns to standard Kaggle Telco CSV column names."""
    df = df.rename(columns={k: v for k, v in _IBM_TO_STANDARD.items()
                             if k in df.columns})
    extra = [c for c in _IBM_EXTRA_DROP if c in df.columns]
    if extra:
        df = df.drop(columns=extra)
    return df


def engineer_churn_features(df):
    """
    Create framework-derived features from IBM Telco Churn dataset.
    Maps CRM attributes to the paper's risk model components.
    """
    df = df.copy()

    # --- recurrence proxy R̂: customer with unresolved chronic issues ---
    month_to_month = (df["Contract"] == "Month-to-month").astype(int)
    no_support     = (df["TechSupport"] == "No").astype(int)
    new_customer   = (df["tenure"] < 12).astype(int)
    df["recurrence_proxy"] = month_to_month * no_support * new_customer

    # --- service complexity: active optional services (0–6) ---
    optional_services = [
        "OnlineSecurity", "OnlineBackup",
        "DeviceProtection", "TechSupport",
        "StreamingTV", "StreamingMovies"
    ]
    df["service_complexity"] = df[optional_services].apply(
        lambda row: (row == "Yes").sum(), axis=1
    )

    # --- spend anomaly: normalized deviation from cohort average ---
    df["MonthlyCharges_num"] = pd.to_numeric(df["MonthlyCharges"], errors="coerce")
    mu = df["MonthlyCharges_num"].mean()
    sigma = df["MonthlyCharges_num"].std()
    df["spend_anomaly"] = (df["MonthlyCharges_num"] - mu) / (sigma + 1e-8)

    # --- VIP proxy: high-spend + long-tenure ---
    df["vip_proxy"] = (
        (df["MonthlyCharges_num"] > df["MonthlyCharges_num"].quantile(0.75))
        & (df["tenure"] > 24)
    ).astype(int)

    return df


def _read_d2(filepath):
    """Load D2 from CSV or xlsx, normalizing IBM column names."""
    if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)
    return _normalize_ibm_format(df)


def encode_churn_dataset(df):
    """One-hot encode categorical columns, return X, y."""
    # Normalize IBM format if needed (idempotent on standard CSV)
    df = _normalize_ibm_format(df.copy())
    df = engineer_churn_features(df)

    # Target — works for both 'Yes'/'No' and 1/0 encodings
    churn_col = 'Churn' if 'Churn' in df.columns else None
    if churn_col is None:
        raise ValueError("No 'Churn' column found after normalization.")
    df["Churn_bin"] = pd.to_numeric(
        df[churn_col].map({"Yes": 1, "No": 0}).fillna(df[churn_col]),
        errors="coerce"
    ).fillna(0).astype(int)
    y = df["Churn_bin"]

    # Drop ID and target columns
    drop_cols = ["customerID", "Churn", "Churn_bin", "TotalCharges"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Encode binary yes/no columns
    yes_no_cols = [c for c in df.columns
                   if df[c].dtype == object and
                   set(df[c].dropna().unique()).issubset(
                       {"Yes", "No", "No phone service", "No internet service"}
                   )]
    for col in yes_no_cols:
        df[col] = df[col].map(
            {"Yes": 1, "No": 0,
             "No phone service": 0, "No internet service": 0}
        )

    # One-hot for remaining object columns
    cat_cols = [c for c in df.columns if df[c].dtype == object]
    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    # Fix any remaining NaN
    df = df.fillna(df.median(numeric_only=True))

    return df, y


# ── Result formatting helpers ──────────────────────────────────────────────

def print_latex_row(model_name, metrics_dict):
    """Print a LaTeX table row for the results tables."""
    vals = " & ".join(f"{v:.3f}" for v in metrics_dict.values())
    print(f"    {model_name} & {vals} \\\\")


def save_results(results_dict, filepath):
    """Save results dict to CSV."""
    pd.DataFrame(results_dict).to_csv(filepath, index=False)
    print(f"Saved: {filepath}")

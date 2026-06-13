"""
CMMS metric calculators.

Extracted from the legacy v1 scoring_engine so the v2 product no longer depends
on any v1 module. These are the canonical CMMS analytics used by
``data_analysis_module.CMMSDataAnalyzer`` and consumed by
``scoring_engine_v2.ScoringEngineV2._apply_cmms_evidence_caps``.

UNITS POLICY (important — this is what the unit bugs were about):
    * ``reactive_ratio``  -> fraction in [0, 1]
    * ``compliance_rate`` -> fraction in [0, 1]
    * ``graveyard_ratio`` -> fraction in [0, 1]
    * ``data_quality.score`` / ``score`` -> integer 1..5
Convenience ``*_pct`` keys (percentage 0..100) are provided ONLY for display.
Scoring code must read the fraction keys, never the ``_pct`` ones.
"""
from typing import Dict

import pandas as pd
import re


REACTIVE_TYPES = ["emergency", "corrective", "breakdown", "urgent"]


def calculate_reactive_ratio(work_orders_df: pd.DataFrame) -> Dict:
    """Reactive vs. preventive ratio from a work-order export.

    ``reactive_ratio`` is returned as a fraction (0.0–1.0).
    """
    if not isinstance(work_orders_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    total_wos = len(work_orders_df)

    if "work_order_type" in work_orders_df.columns:
        reactive_count = work_orders_df[
            work_orders_df["work_order_type"].astype(str).str.lower().isin(REACTIVE_TYPES)
        ].shape[0]
    elif "priority" in work_orders_df.columns:
        reactive_count = work_orders_df[
            work_orders_df["priority"].astype(str).isin(["1", "Emergency", "Urgent"])
        ].shape[0]
    else:
        raise ValueError(
            "Cannot determine work order type — missing 'work_order_type' or 'priority' column"
        )

    reactive_ratio = (reactive_count / total_wos) if total_wos > 0 else 0.0

    if reactive_ratio > 0.6:
        severity, score = "CRITICAL - Reactive Spiral", 1
    elif reactive_ratio > 0.4:
        severity, score = "HIGH - Reactive Dominant", 2
    elif reactive_ratio > 0.25:
        severity, score = "MEDIUM - Balanced but Reactive-Heavy", 3
    elif reactive_ratio > 0.15:
        severity, score = "GOOD - Preventive Focus", 4
    else:
        severity, score = "EXCELLENT - Proactive Maintenance", 5

    return {
        "metric": "Reactive Ratio",
        "total_work_orders": total_wos,
        "reactive_work_orders": int(reactive_count),
        "preventive_work_orders": int(total_wos - reactive_count),
        "reactive_ratio": round(reactive_ratio, 4),        # fraction (canonical)
        "reactive_ratio_pct": round(reactive_ratio * 100, 1),  # display only
        "severity": severity,
        "score": score,
        "threshold_50_percent": reactive_ratio > 0.5,
    }


def calculate_pm_compliance(pm_data_df: pd.DataFrame) -> Dict:
    """PM on-time completion rate (7-day grace period).

    ``compliance_rate`` (and alias ``pm_compliance_rate``) is a fraction (0.0–1.0).
    """
    if not isinstance(pm_data_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    if "due_date" not in pm_data_df.columns or "completed_date" not in pm_data_df.columns:
        raise ValueError("Missing required columns: 'due_date' and 'completed_date'")

    df = pm_data_df.copy()
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")
    df["completed_date"] = pd.to_datetime(df["completed_date"], errors="coerce")
    df["days_late"] = (df["completed_date"] - df["due_date"]).dt.days

    total_pms = len(df)
    on_time_pms = int(len(df[df["days_late"] <= 7]))
    late_pms = total_pms - on_time_pms

    compliance_rate = (on_time_pms / total_pms) if total_pms > 0 else 0.0

    if compliance_rate >= 0.95:
        score, severity = 5, "EXCELLENT"
    elif compliance_rate >= 0.85:
        score, severity = 4, "GOOD"
    elif compliance_rate >= 0.70:
        score, severity = 3, "ACCEPTABLE"
    elif compliance_rate >= 0.50:
        score, severity = 2, "POOR"
    else:
        score, severity = 1, "CRITICAL - PM Program Breaking Down"

    late = df[df["days_late"] > 0]["days_late"]
    return {
        "metric": "PM Compliance",
        "total_pms": total_pms,
        "on_time_pms": on_time_pms,
        "late_pms": late_pms,
        "compliance_rate": round(compliance_rate, 4),          # fraction (canonical)
        "pm_compliance_rate": round(compliance_rate, 4),       # stable alias
        "compliance_rate_pct": round(compliance_rate * 100, 1),  # display only
        "average_days_late": round(float(late.mean()), 1) if len(late) else 0.0,
        "severity": severity,
        "score": score,
    }


# Generic/useless closure codes that carry no diagnostic value.
_GENERIC_CODES = {"done", "fixed", "complete", "ok", "n/a", "closed", "completed", ""}

_COMPONENT_RE = re.compile(
    r"\b(pump|motor|valve|bearing|seal|belt|gear|shaft|coupling|fan|compressor|"
    r"conveyor|sensor|actuator|plc|hmi|vfd|drive|filter|strainer|tank|pipe|"
    r"electrical|mechanical|hydraulic|pneumatic|unit|machine|equipment)\b"
)
_FAILURE_RE = re.compile(
    r"\b(fail|broke|leak|worn|damaged|crack|vibrat|overheat|short|trip|"
    r"stuck|seized|corrode|erode|misalign|loose|noise|cavitat|blocked|"
    r"clogged|burnt|overload|undervolt|overvolt|ground fault|fault)\w*\b"
)
_ACTION_RE = re.compile(
    r"\b(replac|repair|adjust|tighten|clean|lubricat|align|calibrat|"
    r"install|remov|rebuild|rewound|reseal|refurbish|inspect|test|"
    r"reset|reprogram|recondition|overhaul)\w*\b"
)


def calculate_data_graveyard_index(work_orders_df: pd.DataFrame) -> Dict:
    """Data-quality / actionability index from closure-note semantics.

    ``score`` is 1..5 (the value scoring reads for AI.2). ``graveyard_ratio`` is a
    fraction (0.0–1.0) of work orders with no usable closure data.
    """
    if not isinstance(work_orders_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    if "closure_notes" not in work_orders_df.columns:
        raise ValueError("Missing 'closure_notes' column")

    total_wos = len(work_orders_df)

    def actionability(notes) -> Dict:
        if pd.isna(notes) or not str(notes).strip():
            return {"score": 0, "component": False, "failure": False, "action": False}
        text = str(notes).lower()
        if text.strip() in _GENERIC_CODES:
            return {"score": 0, "component": False, "failure": False, "action": False}
        has_component = bool(_COMPONENT_RE.search(text))
        has_failure = bool(_FAILURE_RE.search(text))
        has_action = bool(_ACTION_RE.search(text))
        return {
            "score": int(has_component) + int(has_failure) + int(has_action),
            "component": has_component,
            "failure": has_failure,
            "action": has_action,
        }

    results = work_orders_df["closure_notes"].apply(actionability)
    scores = [r["score"] for r in results]

    high = sum(1 for s in scores if s == 3)
    medium = sum(1 for s in scores if s == 2)
    low = sum(1 for s in scores if s == 1)
    poor = sum(1 for s in scores if s == 0)

    weighted = (
        (high * 100) + (medium * 66) + (low * 33)
    ) / total_wos if total_wos > 0 else 0.0
    graveyard_ratio = (poor / total_wos) if total_wos > 0 else 0.0

    if weighted >= 80:
        score, severity = 5, "EXCELLENT - High actionability, rich semantic data"
    elif weighted >= 60:
        score, severity = 4, "GOOD - Solid data quality with some gaps"
    elif weighted >= 40:
        score, severity = 3, "ACCEPTABLE - Improvement needed"
    elif weighted >= 20:
        score, severity = 2, "POOR - Significant data quality issues"
    else:
        score, severity = 1, "SEVERE DATA GRAVEYARD - Cannot perform RCA"

    return {
        "metric": "Data Graveyard Index (Semantic)",
        "total_work_orders": total_wos,
        "poor_quality_closures": poor,
        "graveyard_ratio": round(graveyard_ratio, 4),          # fraction (canonical)
        "graveyard_percentage_pct": round(graveyard_ratio * 100, 1),  # display only
        "severity": severity,
        "score": score,
        "actionability_index": round(weighted, 1),  # 0..100 index
        "quality_breakdown": {
            "high_quality_3_entities": high,
            "medium_quality_2_entities": medium,
            "low_quality_1_entity": low,
            "poor_quality_0_entities": poor,
        },
        "semantic_coverage": {
            "with_component": sum(1 for r in results if r["component"]),
            "with_failure_mode": sum(1 for r in results if r["failure"]),
            "with_corrective_action": sum(1 for r in results if r["action"]),
        },
    }

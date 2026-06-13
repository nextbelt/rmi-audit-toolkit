"""Unit tests for cmms_metrics — these lock the percent-vs-fraction fix.

The v2 scoring engine consumes reactive_ratio / compliance_rate as 0-1 fractions.
Before the fix these were returned as percentages, which silently disabled the
reactive-ratio and PM-compliance caps and rendered 4550% in the UI.
"""
import pandas as pd

from cmms_metrics import (
    calculate_reactive_ratio,
    calculate_pm_compliance,
    calculate_data_graveyard_index,
)


def test_reactive_ratio_is_a_fraction_not_percent():
    df = pd.DataFrame(
        {"work_order_type": ["emergency", "corrective", "preventive", "preventive"]}
    )
    m = calculate_reactive_ratio(df)
    assert 0.0 <= m["reactive_ratio"] <= 1.0
    assert m["reactive_ratio"] == 0.5          # 2 of 4 reactive
    assert m["reactive_ratio_pct"] == 50.0     # display-only mirror
    assert m["reactive_work_orders"] == 2
    assert m["preventive_work_orders"] == 2


def test_reactive_ratio_all_preventive_scores_top():
    df = pd.DataFrame({"work_order_type": ["preventive"] * 5})
    m = calculate_reactive_ratio(df)
    assert m["reactive_ratio"] == 0.0
    assert m["score"] == 5


def test_reactive_ratio_high_trips_wm1_threshold():
    # >50% reactive must read as > 0.5 (the engine's WM.1 cap condition)
    df = pd.DataFrame({"work_order_type": ["emergency"] * 7 + ["preventive"] * 3})
    m = calculate_reactive_ratio(df)
    assert m["reactive_ratio"] > 0.5


def test_pm_compliance_fraction_and_stable_alias():
    df = pd.DataFrame(
        {
            "due_date": ["2026-01-01", "2026-01-01"],
            "completed_date": ["2026-01-03", "2026-02-15"],  # 2 days, 45 days
        }
    )
    m = calculate_pm_compliance(df)
    assert 0.0 <= m["compliance_rate"] <= 1.0
    assert m["compliance_rate"] == 0.5
    # The engine reads pm_compliance_rate; it must exist and match.
    assert m["pm_compliance_rate"] == m["compliance_rate"]
    assert m["on_time_pms"] == 1


def test_data_graveyard_returns_score_and_fraction():
    df = pd.DataFrame(
        {
            "closure_notes": [
                "Replaced worn pump bearing after vibration fault",  # component+failure+action
                "done",  # generic → no actionable content
            ]
        }
    )
    m = calculate_data_graveyard_index(df)
    assert 1 <= m["score"] <= 5
    assert 0.0 <= m["graveyard_ratio"] <= 1.0
    assert m["poor_quality_closures"] == 1

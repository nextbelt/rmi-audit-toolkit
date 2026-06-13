"""Scoring-math regression tests for the v2 engine.

Locks the maturity-band-gap fix (a 3.595 site used to fall through every band
and get mislabeled 'Level 1 - Reactive') and the 3-pillar rollup mapping used by
the report.
"""
import pytest

from scoring_engine_v2 import ScoringEngineV2


@pytest.mark.parametrize(
    "score,expected",
    [
        (1.00, "Level 1 - Reactive"),
        (1.99, "Level 1 - Reactive"),
        (2.00, "Level 2 - Emerging"),
        (2.99, "Level 2 - Emerging"),
        (3.00, "Level 3 - Systematic"),
        (3.59, "Level 3 - Systematic"),
        (3.595, "Level 3 - Systematic"),  # the gap bug: previously misread as Reactive
        (3.60, "Level 4 - Proactive"),
        (4.29, "Level 4 - Proactive"),
        (4.30, "Level 5 - Prescriptive"),
        (5.00, "Level 5 - Prescriptive"),
    ],
)
def test_maturity_bands_are_contiguous(score, expected):
    engine = ScoringEngineV2(db=None)  # _get_maturity_level is pure (no DB)
    assert engine._get_maturity_level(score) == expected


def test_maturity_clamps_out_of_range():
    engine = ScoringEngineV2(db=None)
    assert engine._get_maturity_level(0.5) == "Level 1 - Reactive"
    assert engine._get_maturity_level(7.0) == "Level 5 - Prescriptive"


def test_pillar_map_covers_all_five_domains_once():
    from report_generator_v2 import PILLAR_MAP

    covered = [code for codes in PILLAR_MAP.values() for code in codes]
    assert sorted(covered) == ["AI", "LC", "SG", "WC", "WM"]
    assert set(PILLAR_MAP.keys()) == {"People", "Process", "Technology"}

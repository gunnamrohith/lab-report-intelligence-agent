"""
analyzer.py – Classify parsed lab values and compute a health score.

Responsibilities
-----------------
1. Match every ``ExtractedTest`` against the normal‑ranges dictionary.
2. Classify each matched test as **Low**, **Normal**, or **High**.
3. Compute a composite health score (0–100).
4. Generate a plain‑English explanation for each abnormal result.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from normal_ranges import NORMAL_RANGES, ReferenceRange, lookup
from parser import ExtractedTest


# ──────────────────────────────────────────────────────────────────────
# Enums & data classes
# ──────────────────────────────────────────────────────────────────────


class Status(str, Enum):
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"


class Severity(str, Enum):
    """How far a value deviates from the reference boundary."""
    NORMAL = "Normal"
    MILD = "Mild"
    MODERATE = "Moderate"
    CRITICAL = "Critical"


@dataclass
class AnalyzedTest:
    """Result of comparing one extracted test against its reference range."""

    canonical_name: str
    raw_name: str
    value: float
    min_value: float
    max_value: float
    unit: str
    status: Status
    deviation_pct: float  # 0.0 when normal; positive otherwise
    severity: Severity = Severity.NORMAL
    explanation: str = ""


@dataclass
class AnalysisReport:
    """Aggregate analysis of all matched tests."""

    matched: List[AnalyzedTest] = field(default_factory=list)
    unrecognized: List[ExtractedTest] = field(default_factory=list)
    health_score: int = 100  # 0–100


# ──────────────────────────────────────────────────────────────────────
# Classification helpers
# ──────────────────────────────────────────────────────────────────────


def _classify(value: float, ref: ReferenceRange) -> tuple[Status, float]:
    """Return (status, deviation_percentage)."""
    if value < ref.min_value:
        span = ref.min_value if ref.min_value != 0 else 1.0
        deviation = abs(ref.min_value - value) / span * 100
        return Status.LOW, round(deviation, 1)
    if value > ref.max_value:
        span = ref.max_value if ref.max_value != 0 else 1.0
        deviation = abs(value - ref.max_value) / span * 100
        return Status.HIGH, round(deviation, 1)
    return Status.NORMAL, 0.0


def _severity_level(status: Status, deviation_pct: float) -> Severity:
    """Map status + deviation percentage to a severity tier."""
    if status == Status.NORMAL:
        return Severity.NORMAL
    if status == Status.HIGH:
        if deviation_pct <= 10:
            return Severity.MILD
        if deviation_pct <= 30:
            return Severity.MODERATE
        return Severity.CRITICAL
    # Status.LOW
    if deviation_pct <= 10:
        return Severity.MILD
    if deviation_pct <= 25:
        return Severity.MODERATE
    return Severity.CRITICAL


def _explain(test: AnalyzedTest) -> str:
    """Produce a human‑friendly explanation for a single test."""
    name = test.canonical_name.title()
    if test.status == Status.NORMAL:
        return f"{name} is within the normal range ({test.min_value}–{test.max_value} {test.unit})."
    direction = "below" if test.status == Status.LOW else "above"
    boundary = test.min_value if test.status == Status.LOW else test.max_value
    sev = test.severity.value
    return (
        f"{name} is {test.value} {test.unit}, which is {direction} the normal range "
        f"({test.min_value}–{test.max_value} {test.unit}). "
        f"Severity: {sev} (~{test.deviation_pct}% deviation from {boundary} {test.unit})."
    )


# ──────────────────────────────────────────────────────────────────────
# Health‑score algorithm
# ──────────────────────────────────────────────────────────────────────


def _compute_health_score(tests: List[AnalyzedTest]) -> int:
    """
    Compute a composite score from 0 (critical) to 100 (perfect).

    Method
    ------
    * Start at 100.
    * For every abnormal test, subtract a penalty proportional to its
      deviation percentage (capped so one test can't tank the whole score).
    * Floor at 0.
    """
    if not tests:
        return 100  # nothing to assess

    total_tests = len(tests)
    max_penalty_per_test = 100 / total_tests  # distribute evenly

    penalty = 0.0
    for t in tests:
        if t.status != Status.NORMAL:
            # Map deviation → penalty using a soft sigmoid curve
            raw = min(t.deviation_pct, 100.0)  # cap at 100 %
            test_penalty = max_penalty_per_test * (raw / (raw + 20))
            penalty += test_penalty

    score = max(0, round(100 - penalty))
    return score


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────


def analyze(tests: List[ExtractedTest]) -> AnalysisReport:
    """
    Analyze a list of extracted tests against normal reference ranges.

    Parameters
    ----------
    tests : list[ExtractedTest]

    Returns
    -------
    AnalysisReport
    """
    report = AnalysisReport()

    for ext in tests:
        result = lookup(ext.raw_name)
        if result is None:
            report.unrecognized.append(ext)
            continue

        canonical_name, ref = result
        status, deviation = _classify(ext.value, ref)

        sev = _severity_level(status, deviation)
        analyzed = AnalyzedTest(
            canonical_name=canonical_name,
            raw_name=ext.raw_name,
            value=ext.value,
            min_value=ref.min_value,
            max_value=ref.max_value,
            unit=ref.unit,
            status=status,
            deviation_pct=deviation,
            severity=sev,
        )
        analyzed.explanation = _explain(analyzed)
        report.matched.append(analyzed)

    report.health_score = _compute_health_score(report.matched)
    return report

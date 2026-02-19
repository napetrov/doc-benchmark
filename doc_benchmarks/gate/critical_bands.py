"""Critical bands enforcement — fails CI on condition violations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BandViolation:
    """Single critical band violation."""

    condition: str
    threshold: float
    actual: float
    violated: bool


@dataclass
class CriticalBandsResult:
    """Critical bands check result."""

    enabled: bool
    violations: list[BandViolation]

    @property
    def passed(self) -> bool:
        """True if no violations."""
        return not self.has_violations

    @property
    def has_violations(self) -> bool:
        """Any critical band violated."""
        return any(v.violated for v in self.violations)


def check_critical_bands(summary: dict, spec: dict) -> CriticalBandsResult:
    """Check if summary violates any critical bands.
    
    Returns CriticalBandsResult. Caller decides whether to exit.
    """
    bands = spec.get("critical_bands", {}).get("fail_on", [])
    if not bands:
        return CriticalBandsResult(enabled=False, violations=[])

    violations: list[BandViolation] = []

    for band in bands:
        condition = band.get("condition", "")
        threshold = float(band.get("value", 0.0))

        if condition == "score_below":
            actual = float(summary.get("score", 0.0))
            violated = actual < threshold
            violations.append(BandViolation(condition, threshold, actual, violated))
        elif condition == "coverage_below":
            actual = float(summary.get("coverage", 0.0))
            violated = actual < threshold
            violations.append(BandViolation(condition, threshold, actual, violated))
        elif condition == "freshness_below":
            actual = float(summary.get("freshness_lite", 0.0))
            violated = actual < threshold
            violations.append(BandViolation(condition, threshold, actual, violated))
        elif condition == "readability_below":
            actual = float(summary.get("readability", 0.0))
            violated = actual < threshold
            violations.append(BandViolation(condition, threshold, actual, violated))

    return CriticalBandsResult(enabled=True, violations=violations)

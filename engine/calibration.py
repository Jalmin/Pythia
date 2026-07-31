"""Adaptive, self-tuning calibration for the swarm's published probability.

The oracle is over-confident: measured, when the swarm announces ~68% the event
arrives ~12% of the time. This module learns a correction so the *published*
probability tracks what actually happens.

╔══════════════════════════════════════════════════════════════════════════╗
║  NON-CIRCULARITY — the whole point of this module.                        ║
║                                                                            ║
║  The correction curve is LEARNED on `swarm_probability` (the RAW swarm     ║
║  consensus, BEFORE calibration) versus the observed outcome.               ║
║  The correction is APPLIED and its result written to `probability` (the    ║
║  PUBLISHED value).                                                          ║
║                                                                            ║
║  These two never cross: we never learn the correction from `probability`   ║
║  (that would be circular — the translator learning from its own output).   ║
║  `ledger.raw_calibration_curve()` bins on `swarm_probability`;             ║
║  `ledger.scorecard()` stays on `probability` (the human scorecard).        ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations

# ── documented constants ──
MIN_TOTAL = 30      # below this many resolved raw-binned forecasts, the calibrator is a no-op
MIN_BIN = 3         # a raw-probability bin needs at least this many resolved forecasts to count
FULL_TRUST_N = 100  # data volume at which the correction is applied at full strength


def _interp(x: float, points: list[tuple[float, float]]) -> float:
    """Piecewise-linear interpolation of y at x over (x, y) points sorted by x.
    Flat (clamped) extrapolation beyond the first/last point."""
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return points[-1][1]


def _calibrate(p: float, curve: list[dict]) -> float:
    """Translate a RAW swarm consensus `p` into a calibrated, published probability.

    `curve` comes from `ledger.raw_calibration_curve()`: bins of resolved forecasts
    keyed on the raw swarm probability, each {lo, hi, avg_raw, observed, n}.

    - Not enough data (total < MIN_TOTAL) -> return `p` unchanged (identity no-op).
      This is intentional: the calibrator switches itself on once enough resolved
      forecasts exist.
    - Otherwise interpolate the observed frequency at `p` over the (avg_raw ->
      observed) points = `target`, then pull `p` toward `target` by an adaptive
      `strength = min(1.0, total / FULL_TRUST_N)` (more data -> stronger correction).
    - Clamp to [0.01, 0.99], round to 2 decimals.
    - Any exception -> return `p`: a calibration hiccup must NEVER break the swarm's
      deliberation.
    """
    try:
        usable = [b for b in curve if b["n"] >= MIN_BIN]
        total = sum(b["n"] for b in usable)
        if total < MIN_TOTAL:
            return p
        points = sorted((b["avg_raw"], b["observed"]) for b in usable)
        target = _interp(p, points)
        strength = min(1.0, total / FULL_TRUST_N)
        calibrated = p + strength * (target - p)
        calibrated = max(0.01, min(0.99, calibrated))
        return round(calibrated, 2)
    except Exception:  # noqa: BLE001 — calibration must never sink deliberation
        return p

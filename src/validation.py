"""Validation framework: compare satellite-based flags with field-inspection records.

This module only COUNTS agreement; it never fabricates a metric. With few records the numbers are anecdotes, so the
summary always carries n and a `reliable` flag (>= MIN_RECORDS inspections of flagged zones).

Definitions (per inspection record, which stores the zone's satellite class at the time of the satellite image):
  * flagged      - satellite_class in {HIGH, MODERATE}
  * confirmed    - the inspector recorded condition == "needs_attention"
  * confirmation_rate = confirmed flagged / flagged inspected   (a proxy for the precision of the flags)
  * missed_rate       = needs_attention among inspected zones classed HEALTHY (a proxy for missed problems; only
                        meaningful if unflagged zones were also inspected, ideally chosen at random - otherwise biased)
Records are user-entered and NOT verified ground truth. Spatial and temporal leakage must be avoided when these
records are later used to train or tune anything: split by farm/zone and by date, never by random row.
"""
from __future__ import annotations

MIN_RECORDS = 30
FLAGGED = {"HIGH", "MODERATE"}


def summarize(records: list[dict]) -> dict:
    usable = [r for r in records if r.get("condition") in ("needs_attention", "no_problem") and r.get("satellite_class")]
    flagged = [r for r in usable if r["satellite_class"] in FLAGGED]
    unflagged = [r for r in usable if r["satellite_class"] == "HEALTHY"]
    conf = sum(r["condition"] == "needs_attention" for r in flagged)
    miss = sum(r["condition"] == "needs_attention" for r in unflagged)
    return {
        "n_records": len(records), "n_usable": len(usable),
        "n_flagged_inspected": len(flagged), "n_flagged_confirmed": conf,
        "confirmation_rate": conf / len(flagged) if flagged else None,
        "n_unflagged_inspected": len(unflagged), "n_unflagged_problem": miss,
        "missed_rate": miss / len(unflagged) if unflagged else None,
        "reliable": len(flagged) >= MIN_RECORDS,
    }

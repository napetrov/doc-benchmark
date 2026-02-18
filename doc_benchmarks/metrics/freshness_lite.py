from __future__ import annotations

import datetime as dt
from pathlib import Path


def score(path: Path, max_age_days: int = 365) -> float:
    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    now = dt.datetime.now(tz=dt.timezone.utc)
    age_days = (now - mtime).days

    if age_days <= 0:
        return 1.0
    if age_days >= max_age_days:
        return 0.0
    return round(1.0 - (age_days / max_age_days), 4)

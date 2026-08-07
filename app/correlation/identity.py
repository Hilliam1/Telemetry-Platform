"""Stable identity generation for correlation matches."""

from __future__ import annotations

import hashlib

from app.correlation.models import CorrelationMatch


def correlation_key(
    match: CorrelationMatch,
) -> str:
    """Return a stable fingerprint for one correlation result."""

    parts = (
        match.rule_id,
        str(match.rule_version),
        match.source_host,
        match.first_event_time.isoformat(),
        match.last_event_time.isoformat(),
        *sorted(match.matched_finding_ids),
    )

    payload = "|".join(parts)

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()

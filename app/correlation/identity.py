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
        *match.matched_event_keys,
    )

    payload = "|".join(parts)

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()

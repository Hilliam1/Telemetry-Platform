# ADR 0001: Use PostgreSQL for Telemetry Storage

## Status

Accepted

## Context

The platform needs a structured database that can store raw events, normalized records, process events, host metrics, and collector run history.

## Decision

Use PostgreSQL as the initial database backend.

## Consequences

PostgreSQL provides strong SQL support, indexes, JSON storage options, and a clear upgrade path for analytics and API-backed dashboards.


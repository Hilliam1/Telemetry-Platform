# ADR 0004: Use Multiple Tables for Raw and Structured Data

## Status

Accepted

## Context

Raw event logs preserve complete source data, but structured tables make common analysis easier.

## Decision

Store general logs in `log_events` and extracted process creation events in `process_events`.

## Consequences

The database can support both broad event search and focused process analysis.


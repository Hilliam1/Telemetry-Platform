# ADR 0003: Track EventRecordID for Collector State

## Status

Accepted

## Context

Windows event channels contain many records. The collector needs a way to know which events were already processed.

## Decision

Track the latest processed `EventRecordID` per source and channel.

## Consequences

This keeps ingestion simple and avoids reprocessing old events. The state file must be protected from accidental deletion in production.


# Telemetry Platform Architecture Specification

| Field | Value |
|---|---|
| Specification | `docs/01_System_Architecture.md` |
| Version | 0.5 |
| Status | Draft for architecture review |
| Implements | Platform Phase 17 |
| Last Reviewed | August 2026 |
| Purpose | Define the current system architecture, governing engineering principles, and planned evolution of the Telemetry Platform. |

---

## 1. Executive Summary

### 1.1 Purpose

Telemetry Platform is a modular, self-hosted telemetry collection and analysis platform designed to collect, normalize, store, and expose operational and security telemetry from Windows systems through a clean, layered architecture.

The platform is being engineered as the foundation for an intelligent operational-security system. Its long-term objective is to transform low-level infrastructure telemetry into actionable operational intelligence through deterministic analysis, event correlation, retrieval-augmented knowledge, and AI-assisted reasoning.

The current implementation focuses on establishing a stable backend architecture before introducing advanced analytics or user-facing capabilities. Early development prioritizes modularity, maintainability, extensibility, correctness, and testability over rapid feature growth.

### 1.2 Primary Goals

#### Reliable telemetry collection

The platform must collect Windows Event Log data and host-health telemetry without silently skipping events.

Core characteristics include:

- checkpoint-based collection
- transactional persistence
- deterministic event ordering
- resumable operation
- fault isolation
- explicit error reporting

#### Data normalization

Platform-specific telemetry is converted into a consistent internal representation before persistence.

Windows XML is transformed into structured Python dictionaries with normalized provider names, Event IDs, record IDs, severity levels, timestamps, event data, user data, and host identity.

#### Layered architecture

Each component owns one primary responsibility and communicates through a defined interface. This enables independent testing, focused refactoring, future plugin support, reduced coupling, predictable system behavior, and easier contributor onboarding.

#### Foundation for intelligent security

Future versions are expected to add event correlation, detection rules, risk scoring, knowledge retrieval, AI-assisted investigation, guided remediation, and controlled response playbooks. These capabilities will be layered above the deterministic telemetry pipeline rather than replacing it.

### 1.3 Current Scope

At the Phase 17 baseline, the platform includes:

- Windows Event Log collection
- host-health metric collection
- Windows XML parsing and normalization
- persistent checkpoint management
- PostgreSQL storage
- FastAPI query access
- explicit source registration
- polymorphic source handlers
- dependency injection through a collector factory
- deterministic detection models, rules, evaluation, and finding persistence
- deterministic correlation models, rules, evaluation, and persistence support
- deterministic risk models, policy, providers, assessment, and persistence support
- deterministic alert models, policy, generation, and persistence support
- live deterministic intelligence orchestration during Windows ingestion
- stable detection finding deduplication for source events with Event Record IDs
- stable correlation deduplication keys
- read-only versioned intelligence API routes
- unit testing for major components
- technical repository documentation

The platform intentionally does not yet include a production dashboard, notification delivery, AI reasoning layer, or automated response engine. Phase 11 invokes deterministic detection during Windows event ingestion and persists findings. Phase 12, Phase 13, and Phase 14 add isolated in-memory correlation, risk, and alert foundations. Phase 15 makes correlation matches, risk assessments, and alerts persistable. Phase 16 connects those deterministic intelligence layers to live Windows ingestion while preserving source-level transaction ownership. Phase 17 exposes persisted intelligence through read-only `/api/v1` routes.

### 1.4 Long-Term Vision

The Telemetry Platform is intended to evolve into a self-hosted operational intelligence platform for organizations that may not have dedicated security personnel.

Instead of requiring users to interpret raw Event IDs, XML payloads, and system logs, future versions should explain what happened, explain why it matters, identify affected systems, assign risk, recommend safe next steps, provide approved response actions, and maintain a complete audit trail.

AI is treated as an optional reasoning and explanation layer. Deterministic systems remain responsible for collection, parsing, persistence, correlation, authorization, and response guardrails.

### 1.5 Guiding Principles

- Reliability before convenience
- Modularity before feature accumulation
- Explicit configuration instead of hardcoding
- Deterministic processing before AI reasoning
- Composition before deep inheritance
- Transaction safety before throughput optimization
- Security boundaries before external exposure
- Documentation as part of the system
- Extension through registration and interfaces
- Human approval for high-impact response actions

---

## 2. Design Philosophy

### 2.1 Single Responsibility

Each module should own one primary responsibility.

| Module | Primary responsibility |
|---|---|
| `app/ingest.py` | Process entry point |
| `app/collector_factory.py` | Dependency construction |
| `app/collector.py` | Polling and run orchestration |
| `app/sources.py` | Source definitions |
| `app/source_handlers.py` | Source-specific execution |
| `app/alerts/` | Deterministic alert models, policy, generation, and persistence |
| `app/correlation/` | Deterministic correlation models, rules, evaluation, and persistence |
| `app/detection/` | Deterministic detection models, rules, evaluation, and finding persistence |
| `app/risk/` | Deterministic risk policy, providers, score aggregation, and persistence |
| `app/windows_reader.py` | Windows Event Log access |
| `app/parsers/windows_event_parser.py` | XML parsing and normalization |
| `app/health_metrics.py` | Host metric collection |
| `app/intelligence/` | Live deterministic intelligence orchestration |
| `app/intelligence/query_repository.py` | Read-only intelligence queries |
| `app/intelligence/schemas.py` | Intelligence API response contracts |
| `app/routes/intelligence.py` | Versioned read-only intelligence routes |
| `app/repository.py` | Telemetry persistence |
| `app/state.py` | Checkpoint management |
| `app/database.py` | PostgreSQL connection creation |
| `app/config.py` | Environment-based configuration |
| `app/api.py` | REST query interface |

### 2.2 Separation of Concerns

```mermaid
flowchart LR
 A[Telemetry Sources] --> B[Collection]
 B --> C[Normalization]
 C --> D[Persistence]
 D --> E[(PostgreSQL)]
 E --> F[REST API]
 F --> G[Dashboard and Clients]
```

Architectural constraints include:

- parsers do not execute SQL
- repositories do not read Event Logs
- APIs do not advance collector checkpoints
- collectors do not build SQL
- state management does not depend on the API
- readers do not interpret business meaning

### 2.3 Composition over Inheritance

```mermaid
flowchart TD
 A[Collector] --> B[Source Handler Registry]
 B --> C[Windows Event Handler]
 B --> D[Host Metrics Handler]
 C --> E[Windows Reader]
 C --> F[Windows Event Parser]
 C --> G[State Manager]
 C --> H[Telemetry Repository]
 C --> J[Detection Engine]
 J --> K[Detection Repository]
 D --> I[Host Metrics Collector]
 D --> H
```

Inheritance is used only when a common behavioral contract provides clear value, such as the `SourceHandler` interface and future parser or reasoning-provider interfaces.

### 2.4 Dependency Injection

Concrete dependencies are created in `collector_factory.py` and supplied to the `Collector`.

Benefits include isolated testing, implementation replacement, centralized construction, simpler lifecycle management, and reduced hidden coupling.

### 2.5 Explicit Configuration

Runtime configuration is externalized through environment variables, including PostgreSQL settings, checkpoint path, polling interval, batch size, enabled sources, and logging level.

### 2.6 Deterministic Processing

```mermaid
flowchart LR
 A[Read] --> B[Normalize]
 B --> C[Validate]
 C --> D[Persist]
 D --> E[Commit]
 E --> F[Advance Checkpoint When Applicable]
```

AI will operate only after deterministic analysis has produced qualified evidence.

### 2.7 Transaction Ownership

- source handlers own source-level transaction boundaries
- the collector owns collector-run transaction boundaries
- the repository never commits or rolls back
- checkpoint advancement occurs only after a successful commit

### 2.8 Defensive Failure Handling

The system degrades gracefully where possible. One channel failure does not terminate unrelated channels, unavailable `psutil` does not stop event collection, invalid source names produce explicit configuration errors, and failed database transactions do not advance checkpoints.

### 2.9 Testability

Major modules are independently testable through mocks and injected dependencies. Most unit tests do not require PostgreSQL, Sysmon, Windows Event Logs, or FastAPI.

### 2.10 AI as an Augmentation Layer

```mermaid
flowchart TD
 A[Telemetry] --> B[Normalization]
 B --> C[Correlation]
 C --> D[Detection]
 D --> E[Risk Assessment]
 E --> F[Knowledge Retrieval]
 F --> G[AI Reasoning]
 G --> H[Recommendations]
```

The model explains and recommends. Deterministic services own correctness, permissions, and execution.

---

## 3. Current System Architecture

### 3.1 System Overview

```mermaid
flowchart TD
 A[app.ingest Entry Point] --> B[Collector Factory]
 B --> C[Collector Service]
 C --> D[Resolve Enabled Sources]
 D --> E[Source Registry]
 E --> F[Source Handler Registry]

 F --> G[Windows Event Source Handler]
 F --> H[Host Metrics Source Handler]

 G --> I[Windows Event Reader]
 I --> G
 G --> J[Windows Event Parser]
 J --> G
 G --> K[Telemetry Repository]
 G --> R[Detection Engine]
 R --> S[Detection Repository]
 S --> T[Intelligence Service]
 T --> U[Correlation Repository]
 T --> V[Risk Repository]
 T --> W[Alert Repository]

 H --> L[Host Metrics Collector]
 L --> H
 H --> K

 K --> M[(PostgreSQL)]
 S --> M
 U --> M
 V --> M
 W --> M
 M --> N[FastAPI Query Service]
 N --> O[Planned Dashboard and Clients]

 P[Windows Event Logs] --> I
 Q[Local Host] --> L
```

### 3.2 Supported Sources

Current source definitions include Windows System, Application, Security, Sysmon, PowerShell, Windows Defender, Task Scheduler, and local host metrics. The single `powershell` source reads two channels: `Windows PowerShell` and `Microsoft-Windows-PowerShell/Operational`.

Planned sources include Linux, Syslog, Proxmox, Wazuh, Zeek, Suricata, Docker, network devices, and cloud platforms.

### 3.3 Startup Sequence

```mermaid
sequenceDiagram
 actor User
 participant Entry as app.ingest
 participant Factory as Collector Factory
 participant Collector
 participant Handler as Source Handlers
 User->>Entry: py -m app.ingest
 Entry->>Factory: create_collector()
 Factory->>Factory: Load configuration
 Factory->>Factory: Create dependencies
 Factory->>Handler: Construct handlers
 Factory-->>Entry: Return Collector
 Entry->>Collector: run_forever()
```

### 3.4 Polling Cycle

```mermaid
flowchart TD
 A[Start Poll] --> B[Resolve Enabled Sources]
 B --> C[Find Registered Handler]
 C --> D[Ingest Source]
 D --> E[Accumulate Insert Count]
 E --> F{More Sources?}
 F -- Yes --> C
 F -- No --> G[Record Collector Run]
 G --> H[Commit Collector Run]
 H --> I[Sleep]
 I --> A
```

---

## 4. Component Responsibilities

### 4.1 `app/ingest.py`

Thin executable entry point responsible for logging, collector creation, continuous polling, keyboard interruption, and shutdown.

### 4.2 `app/collector_factory.py`

Composition root responsible for settings, hostname, state, reader, parser, metrics, connection, repository, handlers, and collector construction.

### 4.3 `app/collector.py`

Coordinates enabled sources, handler dispatch, run status, polling intervals, collector-run transactions, and connection shutdown.

### 4.4 `app/sources.py`

Defines supported source names, source kinds, Windows channels, validation, and source ordering.

### 4.5 `app/source_handlers.py`

Implements Windows and host-metric workflows, channel isolation, source-level transactions, persistence coordination, and checkpoint updates.

### 4.6 `app/detection/`

Defines deterministic detection models, built-in rules, in-memory rule evaluation, and finding persistence. The detection engine is invoked by the Windows event handler, and persisted findings are exposed through read-only intelligence API routes.

### 4.7 `app/windows_reader.py`

Encapsulates `EvtQuery`, `EvtNext`, `EvtRender`, query construction, batch limits, and native handle cleanup.

### 4.8 `app/parsers/windows_event_parser.py`

Converts Windows XML into normalized event dictionaries.

### 4.9 `app/health_metrics.py`

Collects CPU, memory, disk, boot-time, hostname, and optional-`psutil` status.

### 4.10 `app/repository.py`

Executes collector INSERT operations without committing, rolling back, parsing, or orchestrating.

### 4.11 `app/state.py`

Loads, validates, advances, and atomically saves source/channel checkpoints.

### 4.12 `app/api.py`

Exposes logs, search, statistics, and metrics over HTTP.

---

## 5. Data Flow and Sequence Architecture

### 5.1 Windows Event Flow

```mermaid
sequenceDiagram
 participant Collector
 participant Handler as Windows Handler
 participant State
 participant Reader
 participant Parser
 participant Repo as Telemetry Repository
 participant Engine as Detection Engine
 participant Findings as Detection Repository
 participant DB as PostgreSQL
 Collector->>Handler: ingest(source)
 Handler->>State: get_last_record_id()
 State-->>Handler: checkpoint
 Handler->>Reader: read_channel(channel, checkpoint)
 Reader-->>Handler: rendered XML
 loop Each event
 Handler->>Parser: parse(XML)
 Parser-->>Handler: normalized event
 Handler->>Repo: insert_log_event()
 Handler->>Repo: insert_process_event()
 Handler->>Engine: evaluate(event)
 Engine-->>Handler: zero or more findings
 Handler->>Findings: insert_findings()
 Repo->>DB: stage INSERT statements
 Findings->>DB: stage finding INSERT statements
 end
 Handler->>DB: COMMIT
 Handler->>State: update_record_id()
 Handler->>State: save()
 Handler-->>Collector: inserted count
```

### 5.2 Host Metrics Flow

```mermaid
sequenceDiagram
 participant Collector
 participant Handler as Metrics Handler
 participant Metrics as Host Metrics Collector
 participant Repo as Repository
 participant DB as PostgreSQL
 Collector->>Handler: ingest(health_metrics)
 Handler->>Metrics: collect()
 Metrics-->>Handler: normalized snapshot
 Handler->>Repo: insert_host_metrics()
 Repo->>DB: stage INSERT
 Handler->>DB: COMMIT
 Handler-->>Collector: 1
```

### 5.3 Windows Event Failure Recovery

```mermaid
flowchart TD
 A[Read or Persist Source] --> B{Success?}
 B -- Yes --> C[Commit]
 C --> D[Advance Checkpoint]
 B -- No --> E[Rollback]
 E --> F[Log Failure]
 F --> G[Continue According to Failure Scope]
```

Checkpoint advancement applies to Windows Event Log sources. Host metrics
sources commit their database transaction but do not update collector
checkpoint state.

### 5.4 API Query Flow

```mermaid
sequenceDiagram
 actor Client
 participant API
 participant DB as PostgreSQL
 Client->>API: HTTP request
 API->>API: Parse path and query parameters
 API->>DB: Parameterized SELECT
 DB-->>API: Rows
 API->>API: Serialize response
 API-->>Client: JSON
```

---

## 6. Database and Persistence Architecture

PostgreSQL is the persistent memory of the platform. It was selected for ACID transactions, mature indexing, Python support, JSON/JSONB capabilities, future `pgvector` compatibility, and scaling options.

### 6.1 Current Tables

| Table | Purpose |
|---|---|
| `log_events` | General normalized telemetry |
| `process_events` | Structured Sysmon process creation telemetry |
| `host_metrics` | Periodic host-health snapshots |
| `collector_runs` | Collector operational history |
| `detection_findings` | Durable deterministic detection findings |
| `correlation_matches` | Durable deterministic correlation matches |
| `risk_assessments` | Durable deterministic risk assessments |
| `alerts` | Durable operator-facing alerts |

### 6.2 Logical ER Model

```mermaid
erDiagram
 LOG_EVENTS {
 int id PK
 string source_host
 string source_type
 string provider_name
 int event_id
 int event_record_id
 string severity
 datetime time_created
 string message
 string raw_data
 datetime inserted_at
 }
 PROCESS_EVENTS {
 int id PK
 string source_host
 string process_guid
 int process_id
 string image
 string command_line
 string parent_image
 string parent_command_line
 string user_name
 string sha256
 datetime created_at
 datetime inserted_at
 }
 HOST_METRICS {
 int id PK
 string host_name
 float cpu_percent
 float memory_percent
 float disk_percent
 datetime boot_time
 datetime collected_at
 }
 COLLECTOR_RUNS {
 int id PK
 string source_host
 string status
 int events_inserted
 datetime started_at
 datetime finished_at
 string error_message
 }
 DETECTION_FINDINGS {
 uuid finding_uuid
 string rule_id
 int rule_version
 string title
 string severity
 string source_host
 string source_type
 int event_id
 int event_record_id
 datetime event_time
 datetime evaluated_at
 string evidence
 }
 CORRELATION_MATCHES {
 uuid correlation_uuid
 string correlation_key
 string rule_id
 int rule_version
 string title
 string severity
 string source_host
 datetime first_event_time
 datetime last_event_time
 string matched_finding_ids
 string matched_detection_rule_ids
 string evidence
 }
 RISK_ASSESSMENTS {
 uuid assessment_uuid
 uuid correlation_uuid
 string correlation_rule_id
 int score
 string level
 int base_score
 string contributions
 string source_host
 datetime assessed_at
 string evidence
 }
 ALERTS {
 uuid alert_uuid
 uuid assessment_uuid
 uuid correlation_uuid
 string correlation_rule_id
 string title
 int risk_score
 string risk_level
 string status
 string source_host
 datetime created_at
 string evidence
 }
```

The current schema does not yet define formal foreign keys between these tables. Correlation relies on host identity, timestamps, source type, providers, Event IDs, and record identifiers.

### 6.3 Planned Database Work

- schema migrations
- deduplication constraints
- `TIMESTAMPTZ`
- `JSONB` raw payloads
- retention and archival
- partitioning
- backup verification
- asset inventory
- alerts and incidents
- audit records
- tenant isolation

---

## 7. API Architecture

The API is the boundary between persisted telemetry and consumers.

```mermaid
flowchart LR
 A[(PostgreSQL)] --> B[FastAPI]
 B --> C[Dashboard]
 B --> D[Reports]
 B --> E[Administrative Tools]
 B --> F[Future Internal Services]
```

The current API exposes a root `/` status response plus endpoints for recent logs, provider filtering, Event ID filtering, source filtering, text search, event statistics, metric history, and latest metrics. A dedicated production health/readiness endpoint is planned but is not currently implemented.

Before commercial release, the API requires authentication, RBAC, API versioning, rate limiting, production connection pooling, formal response models, pagination, audit logging, and tenant isolation.

---

## 8. Security Architecture and Trust Boundaries

### 8.1 Principles

- least privilege
- explicit trust
- defense in depth
- fail secure
- auditability
- data minimization

### 8.2 Trust Boundary Overview

```mermaid
flowchart LR
 subgraph Endpoint
 A[Collector Components]
 end
 subgraph Backend
 B[API and Internal Services]
 C[(PostgreSQL)]
 end
 subgraph Client
 D[Dashboard]
 E[Administrative User]
 end
 A --> C
 B --> C
 D --> B
 E --> D
```

### 8.3 Current Controls

- environment-based credentials
- parameterized SQL
- explicit source validation
- Event Log permission handling
- monotonic, atomic state updates
- commit-before-checkpoint sequencing
- repository reviewed for committed secrets

### 8.4 AI Trust Boundary

```mermaid
flowchart LR
 A[(Telemetry Database)] --> B[Evidence Service]
 B --> C[AI Reasoning Provider]
 C --> D[Validated Recommendation]
 D --> E[Policy Engine]
 E --> F[Human Approval or Approved Automation]
```

The reasoning model must not receive unrestricted database or operating-system access.

---

## 9. Deployment Architecture

### 9.1 Development

```mermaid
flowchart TD
 A[Developer Windows Laptop]
 A --> B[Collector]
 A --> C[PostgreSQL]
 A --> D[FastAPI]
 A --> E[Optional Local Model]
```

### 9.2 Homelab

```mermaid
flowchart TD
 A[Proxmox Host]
 A --> B[Collector VM]
 A --> C[PostgreSQL VM]
 A --> D[API and Dashboard VM]
 A --> E[Wazuh and Network Security Services]
```

### 9.3 Small Business

```mermaid
flowchart LR
 A[Windows Endpoints] --> B[Collectors or Agents]
 B --> C[Central Telemetry Server]
 C --> D[(PostgreSQL)]
 C --> E[API]
 C --> F[Dashboard]
 C --> G[Detection Engine]
 C --> H[Optional Local AI]
```

### 9.4 MSP

```mermaid
flowchart TD
 A[MSP Console] --> B[Authenticated Multi-Tenant Platform]
 B --> C[Customer A]
 B --> D[Customer B]
 B --> E[Customer C]
```

Commercial deployment concerns include signed installers, Windows service packaging, migrations, rollback, configuration preservation, licensing, update channels, support diagnostics, backups, and hardware sizing.

---

## 10. Testing and Quality Architecture

### 10.1 Principles

- test small components
- test observable behavior
- test failure paths
- add regression tests for resolved defects
- automate repeatable checks

### 10.2 Test Layers

```mermaid
flowchart TD
 A[Unit Tests] --> B[Integration Tests]
 B --> C[End-to-End Tests]
 C --> D[Manual Product Validation]
```

### 10.3 Planned CI Checks

- Python compilation
- unit tests
- integration tests
- Ruff
- Black
- MyPy
- Bandit
- `pip-audit`
- secret scanning
- Markdown validation
- broken-link checks
- Mermaid validation where supported

---

## 11. Detection, Correlation, Risk, and Alert Architecture

> **Implementation status:** Phase 17 implements deterministic detection evaluation and persistence plus live intelligence orchestration for correlation matches, risk assessments, and alerts inside the Windows source transaction. Persisted intelligence is exposed through read-only `/api/v1` routes. Notification delivery and alert lifecycle mutation are not implemented.


```mermaid
flowchart TD
 A[Normalized Telemetry] --> B[Detection Rules]
 B --> C[Detection Findings]
 C --> D[Detection Persistence]
 D --> E[Correlation]
 E --> F[Correlation Persistence]
 F --> G[Risk Assessment]
 G --> H[Risk Persistence]
 H --> I[Alert Policy]
 I --> J[Alerts]
 J --> K[Alert Persistence]
 K --> L[Future Incidents]
```

Current Phase 17 components include deterministic detection models, built-in PowerShell-focused rules, an in-memory detection engine, a detection repository that persists and reloads findings, an intelligence service that loads recent findings, an in-memory correlation engine, an in-memory risk engine, an in-memory alert engine, repositories that persist correlation matches, risk assessments, and alerts using caller-controlled transactions, and read-only intelligence API routes. Planned components include a detection rule registry, asset context service, user context service, incident service, notification delivery, and suppression framework.

Detection principles:

- deterministic rules before AI
- transparent evidence
- explainable scoring
- reproducible outcomes
- versioned rules
- testable scenarios
- explicit false-positive handling
- explainable risk contributions
- final scoring owned by deterministic policy
- operator-facing alerts created from deterministic policy
- alert lifecycle transitions controlled by future services

---

## 12. Planned AI and Reasoning Architecture

> **Implementation status:** Future-state design. AI reasoning, RAG, and recommendation services are not implemented in the Phase 17 baseline.


```mermaid
flowchart TD
 A[Alert or Incident] --> B[Evidence Selection]
 B --> C[Knowledge Retrieval]
 C --> D[Reasoning Provider]
 D --> E[Structured Explanation]
 E --> F[Recommendation Validation]
 F --> G[Operator]
```

Provider options may include rules-only, a local 3B-4B model, a local 7B-8B model, a dedicated local inference server, an approved frontier API, or hybrid escalation.

The model should never process raw telemetry volume directly.

```mermaid
flowchart LR
 A[Large Telemetry Volume] --> B[SQL Filtering]
 B --> C[Correlation]
 C --> D[Detection]
 D --> E[Small Evidence Package]
 E --> F[Reasoning Model]
```

---

## 13. Commercial Product Architecture

> **Implementation status:** Product direction and release planning. The installer, dashboard, licensing, alerting, and commercial editions described below are planned rather than current capabilities.

### 13.1 Positioning

A self-hosted security and operational intelligence assistant for small organizations without dedicated security staff.

### 13.2 Initial Customer Profile

- 10-100 endpoints
- Windows-heavy environment
- sensitive business data
- no internal SOC
- owner, office manager, generalist IT staff, or MSP operator
- need for plain-language security guidance

### 13.3 Product Editions

| Edition | Intended audience |
|---|---|
| Community | Homelab, learning, evaluation |
| Professional | Small business |
| MSP | Multi-customer managed service |
| Enterprise | Large and regulated organizations |

### 13.4 Required Capabilities Before Sale

- installer
- Windows service
- reliable upgrades
- dashboard
- alerts
- detection content
- plain-language explanations
- backups
- authentication
- audit logging
- support bundle generation
- licensing
- secure defaults
- rollback procedures

---

## 14. Architecture Evolution

| Phase | Architectural outcome |
|---|---|
| Phase 1 | Configuration and database access extracted |
| Phase 2 | State manager extracted |
| Phase 3 | Windows Event reader extracted |
| Phase 4 | Windows Event parser extracted |
| Phase 5 | Host metrics collector extracted |
| Phase 6 | Persistence repository extracted |
| Phase 7 | Explicit source registry introduced |
| Phase 8 | Polymorphic source handlers introduced |
| Phase 9 | Collector service, factory, and thin entry point introduced |
| Phase 10 | Deterministic in-memory detection foundation introduced |
| Phase 11 | Deterministic findings persisted with source event transactions |
| Phase 12 | Deterministic in-memory correlation foundation introduced |
| Phase 13 | Deterministic in-memory risk assessment foundation introduced |
| Phase 14 | Deterministic in-memory alert foundation introduced |
| Phase 15 | Correlation, risk, and alert persistence boundaries introduced |
| Phase 16 | Live deterministic intelligence orchestration introduced |
| Phase 17 | Read-only intelligence API introduced |
| Phase 18+ | Notifications, product hardening, and intelligence layers |

---

## 15. Architectural Decision Record Index

Architecture Decision Records live in `docs/adr/`.

Current ADRs:

| ADR | Decision |
|---|---|
| [`0001-why-postgresql.md`](adr/0001-why-postgresql.md) | Use PostgreSQL for telemetry storage |
| [`0002-why-fastapi.md`](adr/0002-why-fastapi.md) | Use FastAPI for the API layer |
| [`0003-why-eventrecordid.md`](adr/0003-why-eventrecordid.md) | Track `EventRecordID` for collector state |
| [`0004-why-multi-table-design.md`](adr/0004-why-multi-table-design.md) | Use multiple tables for raw and structured telemetry |
| [`0005-why-rest-before-dashboard.md`](adr/0005-why-rest-before-dashboard.md) | Build the REST API before the dashboard |
| [`0006-why-repository-pattern.md`](adr/0006-why-repository-pattern.md) | Keep SQL persistence in a repository layer |
| [`0007-why-source-handler-architecture.md`](adr/0007-why-source-handler-architecture.md) | Use source handlers for source-specific execution |
| [`0008-why-ai-after-correlation.md`](adr/0008-why-ai-after-correlation.md) | Keep AI downstream from deterministic telemetry analysis |

Planned ADRs:

- Why the collector uses dependency injection.
- Why automated response is separated from reasoning.
- Why the product supports rules-only operation.
- Why the architecture begins single-tenant.

---

## 16. Glossary

**Collector** - Service that coordinates configured telemetry sources.

**Collector Factory** - Composition root that creates collector dependencies.

**Source Registry** - Mapping of supported source names and source kinds.

**Source Handler** - Component that executes the workflow for a source category.

**Reader** - Component that retrieves raw telemetry.

**Parser** - Component that converts raw data into a normalized representation.

**Repository** - Persistence component that executes database operations without owning transactions.

**Checkpoint** - Last successfully committed Event Record ID for a source and channel.

**Detection** - Deterministic finding produced from telemetry evidence.

**Correlation** - Association of related events across time, hosts, users, or sources.

**RAG** - Retrieval-Augmented Generation.

**Reasoning Provider** - Replaceable implementation used to explain qualified evidence.

**Response Engine** - Deterministic service that validates and executes approved actions.

**Trust Boundary** - Point where data or control passes between components with different trust levels.

**Tenant** - Isolated customer environment in a multi-customer deployment.

---

## 17. Architecture Review Checklist

Before final publication:

- verify every module name against `main`
- verify every responsibility against current code
- distinguish current and planned architecture
- validate Mermaid diagrams in GitHub
- remove unsupported Mermaid syntax
- verify database fields against SQL scripts
- verify endpoint names against `app/api.py`
- add links to supporting documents
- eliminate duplicated sections
- align terminology across repository documentation
- review from developer, operator, customer, and security perspectives
- add document version and last-reviewed date

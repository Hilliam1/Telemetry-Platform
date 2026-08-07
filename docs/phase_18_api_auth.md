# Phase 18 API Authentication and Authorization

## Goal

Phase 18 introduces the first authorization boundary for product-facing API
routes.

The objective is:

```text
credential
        |
        v
identity
        |
        v
permissions
        |
        v
route authorization
```

## What Changed

New package:

- `app/auth/__init__.py`
- `app/auth/models.py`
- `app/auth/permissions.py`
- `app/auth/service.py`
- `app/auth/dependencies.py`

Updated modules:

- `app/config.py`
- `app/routes/intelligence.py`

New tests:

- `tests/test_auth_models.py`
- `tests/test_permissions.py`
- `tests/test_auth_service.py`
- `tests/test_intelligence_authorization.py`

New documentation:

- `docs/18_Authentication_Authorization.md`

## Roles

Initial roles:

- `viewer`
- `analyst`
- `responder`
- `administrator`
- `service`

Roles describe common identity types, but routes do not directly check roles.

## Permissions

Initial permissions:

- `intelligence:read`
- `alerts:investigate`
- `response:execute`
- `users:manage`
- `system:configure`

Routes require permissions.

For example, the intelligence API requires:

```text
intelligence:read
```

## API Key Authentication

Phase 18 uses one environment-configured API key:

```text
TELEMETRY_API_KEY
```

Requests send it as:

```text
Authorization: Bearer <API key>
```

The key resolves to a service identity with `intelligence:read`.

This proves the credential-to-permission path without adding password accounts,
sessions, refresh tokens, MFA, or identity-provider integration yet.

## Authorization Dependency

Routes depend on:

```python
require_permission(Permission.INTELLIGENCE_READ)
```

They do not contain logic such as:

```python
if user.role == "admin":
```

That keeps route authorization stable when later phases add local accounts,
Entra ID, OAuth/OIDC, MSP identity, service accounts, or database-backed API
keys.

## Protected Surface

Phase 18 protects:

- `/api/v1/detections`
- `/api/v1/correlations`
- `/api/v1/risk-assessments`
- `/api/v1/alerts`
- `/api/v1/alerts/{alert_uuid}`

Legacy development routes remain unchanged temporarily.

## Acceptance Coverage

Tests verify:

- role and permission values are stable
- role-to-permission mapping is correct
- API keys resolve to identities
- missing API key configuration authenticates nobody
- missing `Authorization` header returns `401`
- invalid API key returns `401`
- valid identity without permission returns `403`
- valid identity with `intelligence:read` returns `200`
- existing route validation and response contracts still work with auth enabled

## Out of Scope

Phase 18 does not add:

- local users
- password login
- database credential tables
- API key rotation
- OAuth/OIDC
- Entra ID
- audit logging
- rate limiting
- alert acknowledgement
- notification delivery

## Validation

Run:

```powershell
py -m pytest -v
py -m compileall app tests
py -m ruff check `
  app\auth `
  app\routes\intelligence.py `
  app\config.py `
  tests\test_auth_models.py `
  tests\test_permissions.py `
  tests\test_auth_service.py `
  tests\test_intelligence_authorization.py `
  tests\test_intelligence_routes.py
```

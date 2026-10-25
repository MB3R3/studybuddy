# StudyBuddy 2.0 Roadmap

**Status:** Proposed sequence following Phase 1.0  
**Last updated:** 2026-10-25

> **Document conventions**
> **Verified** describes the repository today. **Proposed** describes planned work. Phase 1.0 is documentation only and does not implement any item below.

Related documents: [Product requirements](../product/requirements.md) · [Architecture overview](../architecture/overview.md) · [Data model](../architecture/data-model.md)

## 1. Starting point (verified)

- Django 4.2 application with server-rendered templates.
- Existing models: `Topic`, `Room`, `Message`.
- Existing features: registration, login, logout, profiles, room creation and management, messaging, topics, activity feed.
- 36 tests passing in `backend/base/tests.py`.
- `manage.py check` clean.
- `makemigrations --check` reports pre-existing `Message.Meta.ordering` drift; no migration exists for it.
- No DRF, React, Channels, Redis, or PostgreSQL installed.
- SQLite database in use.
- No CI pipeline verified.

## 2. Guiding principles

1. **MVP before platform work.** Ship the API and React replacement before adding private rooms, real-time chat, or moderation.
2. **Preserve behavior.** The current templates and tests define expected behavior until the new UI reaches parity.
3. **Small, reversible steps.** Every phase should be independently reviewable and deployable.
4. **No speculative infrastructure.** Add Redis, Channels, or extra services only when a measured requirement exists.
5. **Test at the API boundary.** Permissions, validation, and ownership rules need explicit API tests.
6. **Keep the existing data.** Migrations must be forward-only and rehearsed against a copy.

## 3. Phase sequence

| Phase | Goal | Depends on | Primary outcome |
|---|---|---|---|
| 1.1 | Engineering hygiene and baseline protection | — | CI, reproducible setup, known drift documented |
| 1.2 | Read-only API and test harness | 1.1 | Public reads served as JSON |
| 1.3 | Authentication and write APIs | 1.2 | Session auth, rooms and messages fully writable via API |
| 1.4 | React application shell and read features | 1.2 | React can browse topics, rooms, messages, profiles, activity |
| 1.5 | React authentication and write features | 1.3, 1.4 | React reaches feature parity for MVP |
| 1.6 | Migration and hardening | 1.5 | Templates retired, API/UI hardened, deployment ready |
| 1.7 | PostgreSQL migration and public launch | 1.6 | Production launch on PostgreSQL |
| 2.x | Post-MVP enhancements | 1.7 | Private rooms, real-time, notifications as validated |

Phases 1.4 and 1.5 may overlap with 1.2 and 1.3, but read APIs must exist before the corresponding screens are built.

## 4. Phase 1.1 — Engineering hygiene and baseline protection

**Objective:** Make the existing baseline reproducible and protected before changing architecture.

**Dependencies:** None.

**Deliverables:**

- A documented local setup that works from a clean checkout using the existing virtual environment layout.
- A CI workflow that runs Django system checks and the 36 existing tests.
- A decision and migration plan for the `Message.Meta.ordering` drift (not necessarily applied yet).
- A short note on the test command and Python version in the repository's contributor guidance.
- A baseline test run recorded in CI.

**Verification:**

- CI fails on a deliberately broken test.
- A clean environment can run migrations and tests using documented commands.
- The drift is either resolved by a reviewed migration or explicitly scheduled.

**Out of scope:** New product features, React, DRF, database changes beyond the drift decision.

## 5. Phase 1.2 — Read-only API and API test harness

**Objective:** Expose existing public data through a versioned JSON API without changing behavior.

**Dependencies:** Phase 1.1.

**Deliverables:**

- Django REST Framework added to dependencies.
- `/api/v1/` routing and serializers for users (public fields only), topics, rooms, messages, and activity.
- Read-only list and detail endpoints with pagination.
- Search and topic filtering for rooms, matching current behavior.
- API tests for response shape, pagination, missing resources, and exclusion of private fields.
- Existing HTML views remain functional.

**Verification:**

- API tests pass alongside the existing 36 tests.
- No email addresses, password data, or internal fields appear in public payloads.
- Room and message ordering matches existing user-visible behavior.
- Manual smoke test confirms the templates still work.

**Out of scope:** Authentication endpoints, write operations, React.

## 6. Phase 1.3 — Authentication and write APIs

**Objective:** Implement the MVP write surface with correct permissions.

**Dependencies:** Phase 1.2.

**Deliverables:**

- Session authentication endpoints: CSRF bootstrap, register, login, logout, current user.
- Create, update, and delete room endpoints.
- Create message and delete message endpoints.
- Object-level permissions: host-only room changes, author-only message deletion.
- Participant updates when a user posts, matching current behavior.
- Validation for empty or oversized messages and required room fields.
- API tests for anonymous access, ownership violations, CSRF failures, and validation errors.

**Verification:**

- Guests receive `401` or `403` for writes and can read public resources.
- Non-hosts receive `403` when editing or deleting another user's room.
- Non-authors receive `403` when deleting another user's message.
- Invalid input returns `400` with field-level errors.
- Existing templates continue to work against the same models.

**Out of scope:** React, private rooms, real-time updates, moderation tools.

## 7. Phase 1.4 — React application shell and read features

**Objective:** Build the new frontend shell and read-only screens against the API.

**Dependencies:** Phase 1.2.

**Deliverables:**

- Vite, React, and TypeScript application in `frontend/`.
- Routing for home, topic/room discovery, room detail, profile, and activity.
- Typed API client with centralized error handling.
- Shared layout, navigation, loading, empty, and error states.
- Read-only room, message, profile, topic, and activity screens.
- Frontend tests for critical rendering and API error states.
- Same-origin development proxy from Vite to Django.

**Verification:**

- All MVP read journeys work in the React app.
- API failures display usable error states rather than blank screens.
- No secrets or tokens are stored in browser storage.
- The Django templates remain available as a fallback.

**Out of scope:** Authentication UI, posting, room management, production deployment.

## 8. Phase 1.5 — React authentication and write features

**Objective:** Reach MVP feature parity in the React application.

**Dependencies:** Phase 1.3 and Phase 1.4.

**Deliverables:**

- Registration, login, logout, and session restoration.
- CSRF handling for all unsafe requests.
- Room creation, editing, and deletion for hosts.
- Message posting and author-only deletion.
- Profile viewing and self-service editing.
- Form validation, pending states, and user-facing error messages.
- End-to-end tests for the critical journeys.

**Verification:**

- All six MVP journeys in the requirements document pass.
- Refreshing the page preserves the session.
- Unauthorized actions are blocked in the UI and rejected by the API.
- Ownership controls are hidden or disabled appropriately, with server enforcement still tested.
- No regression in the existing Django test suite.

**Out of scope:** Private rooms, direct messages, notifications, real-time updates.

## 9. Phase 1.6 — Migration and hardening

**Objective:** Make the React application the primary interface and prepare for production.

**Dependencies:** Phase 1.5.

**Deliverables:**

- Parity checklist signed off against the current templates.
- Django templates retired or reduced to a documented fallback.
- Security review: cookies, CSRF, CORS, headers, rate limiting, input limits, and error disclosure.
- Accessibility pass for keyboard navigation, focus, labels, and contrast.
- Performance check for room lists, message lists, and activity.
- Deployment configuration for static assets, SPA fallback, `/api`, and `/admin` routing.
- Backup and restore procedure for the current database.
- Operational runbook for deploy, rollback, and migration.

**Verification:**

- Parity checklist has no unresolved MVP gaps.
- Security checklist is reviewed with no critical findings.
- A staging deployment completes the critical journeys.
- Backup restoration is rehearsed successfully.

**Out of scope:** Public launch on PostgreSQL; that is Phase 1.7.

## 10. Phase 1.7 — PostgreSQL migration and public launch

**Objective:** Move production data to PostgreSQL and launch publicly.

**Dependencies:** Phase 1.6.

**Deliverables:**

- Environment-driven database configuration.
- PostgreSQL provisioned with backups and monitoring.
- Data transfer from SQLite to PostgreSQL, rehearsed on a copy.
- Row counts and spot checks validated after transfer.
- Production environment variables and secret management.
- HTTPS, secure cookies, HSTS, and allowed hosts configured.
- Monitoring, logging, health checks, and an on-call escalation path.
- Launch checklist and rollback plan.

**Verification:**

- Staging runs on PostgreSQL with the full test suite passing.
- Data validation confirms topics, rooms, messages, participants, and users.
- Critical journeys pass on the production-like environment.
- Rollback to the previous deployment is demonstrated.

**Out of scope:** New product features.

## 11. Phase 2.x — Post-MVP candidates

These items are intentionally unordered. Select them only after MVP launch and user feedback.

| Candidate | Prerequisite | Notes |
|---|---|---|
| Private and unlisted rooms | Explicit membership model and migration plan | Largest schema change; requires visibility rules and tests |
| Real-time messaging | Measured need beyond refresh/polling | Requires Channels, Redis, ASGI deployment |
| Notifications | Clear notification policy | In-app first; email only with consent and delivery tooling |
| Moderation tools | Defined moderation policy | Reports, review queues, audit trail, staff workflows |
| File attachments | Storage, limits, virus scanning, moderation | Significant security and cost implications |
| Full-text search | Measured search quality problem | Consider PostgreSQL search before external search services |
| Mobile client | Validated demand | Revisit token or OAuth authentication |
| Profile customisation | Validated demand | Introduce `UserProfile` only when needed |

## 12. Cross-phase definition of done

A phase is complete only when:

- Its deliverables are merged and reviewed.
- Automated tests cover the new behavior and all existing tests pass.
- Documentation reflects the new behavior.
- No secrets, credentials, or database files are committed.
- The change is deployable or clearly marked as not deployable.
- Known limitations and follow-ups are recorded.

## 13. Risks and decision gates

| Risk | Gate or mitigation |
|---|---|
| Building the API and UI simultaneously causes rework | Complete read APIs before corresponding screens; keep resource contracts stable |
| Hidden behavior differences between templates and React | Maintain a parity checklist from Phase 1.4 onward |
| Migration drift compounds | Resolve the `Message` ordering drift in Phase 1.1 or before any new schema change |
| SQLite limits appear during beta | Move PostgreSQL earlier only if measured concurrency or reliability issues require it |
| Real-time scope expands the MVP | Require measured demand and a separate design before Channels work |
| Private-room scope expands the MVP | Require a validated product decision and the membership migration plan |
| Public launch exposes insecure defaults | Complete Phase 1.6 hardening and Phase 1.7 launch checklist |

## 14. Immediate next phase

**Phase 1.1 — Engineering hygiene and baseline protection.**

It is the smallest step that reduces risk for every later phase. It requires no product decisions, no new dependencies, and no schema changes beyond a reviewed decision on the existing migration drift.

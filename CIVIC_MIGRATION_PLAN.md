# JanPulse Civic Migration Plan

## Purpose

Evolve the CampusPulse issue-deduplication and resolution workflow into a multi-jurisdiction civic issue platform for Gram Panchayats, Municipalities, and Municipal Corporations. The current civic UI is a prototype overlay, not a production civic backend.

## Current prototype scope

- Dedicated responsive JanPulse civic workspace and workspace switch.
- Location context inputs for district, local-body type, local-body name, and village/ward.
- Service shortcuts for water, roads/streetlights, sanitation/waste, public health, public facilities, and civic services.
- Issue tracker backed by the existing issue feed and operational summary endpoints.
- Existing reporting form can be entered from the civic workspace. Locality context is added to the free-text report because the current issue schema has no canonical civic jurisdiction model.
- UI and test smoke assertion only; no official government affiliation or official local-body integration is implied.

## Production work required before civic deployment

### 1. Replace free-text location context with canonical jurisdiction data

Add normalized tables (names are illustrative):
- `jurisdictions`: id, type, official_code, name, parent_id, state_code, active.
- `locality_units`: id, jurisdiction_id, type (village, ward, sansad, para/locality), official_code, name, boundary/reference metadata.
- `service_departments`: id, jurisdiction_id, service_category, responsible_team_id, escalation_policy_id.
- `issue_location`: issue_id, locality_unit_id, latitude, longitude, location_description.

Populate from authoritative state/local-body data. Do not ship placeholder values as if they were actual jurisdiction records.

### 2. Add tenancy and authority-scoped access control

Introduce civic roles such as resident, field_worker, panchayat_operator, municipal_operator, engineer, elected_representative, escalation_officer and platform_admin. Enforce authorization in the API; hiding UI tabs is not authorization. Every read, update, assignment, private message and attachment must be scoped to the authenticated user's jurisdiction and grants. Never accept a client-supplied jurisdiction ID as proof of access.

Keep campus and civic data isolated, ideally through a tenant/domain discriminator plus service-layer enforcement and tests. Migrate legacy campus records without assigning them to a civic tenant.

### 3. Model civic workflow and assignment explicitly

Use configurable service categories, responsible-office routing, severity rules, acknowledgement/resolution targets, escalation steps, evidence requirements and appeal/reopen paths. Timers must be described as configurable targets unless formally approved by the authority. Support cases that need escalation to a block, district, utility or other agency outside the first receiving body.

### 4. Preserve auditability and citizen safety

Use immutable audit events for status transitions and assignment changes. Support masked public identity, private communications, rate limits, attachment validation and retention rules. Redact personal data from public feeds. Clearly distinguish reported, acknowledged, verified, resolved, reopened and closed states.

### 5. Make reports location-aware and accessible

Use structured jurisdiction and locality IDs in the complaint APIs; coordinates are optional and need consent. Add Bengali, Hindi and English flows with simple wording and transliteration tolerance. Make it usable on low-end phones and slow connections. Provide clear offline/error behavior and avoid relying on color alone for status.

### 6. Civic metrics must be computed from real civic records

Scope all counts by jurisdiction and date range. Use database-derived open, overdue, escalated, resolved and reopened counts. Do not return hardcoded fallback metrics or campus seed statistics in a civic dashboard. Mark data freshness and the denominator used for percentages.

## Suggested API evolution

- `GET /api/civic/jurisdictions?parent_id=...`
- `GET /api/civic/localities?jurisdiction_id=...`
- `GET /api/civic/dashboard/summary?jurisdiction_id=...`
- `GET /api/civic/issues?jurisdiction_id=...&locality_id=...&status=...`
- `POST /api/civic/issues`
- `PATCH /api/civic/issues/{id}/assignment`
- `PATCH /api/civic/issues/{id}/status`
- `GET /api/civic/issues/{id}/timeline`

Each endpoint must derive the actor and permitted jurisdiction from server-side authentication, not trust client-supplied scope.

## Minimum test gates

- Resident cannot read or mutate another jurisdiction's private records.
- Civic staff can only work on jurisdictions assigned to them.
- Campus roles cannot access civic-only endpoints unless explicitly granted.
- Campus issue feeds and legacy demo tests continue to pass.
- Invalid or unrecognized locality IDs are rejected.
- Private identity and attachments do not leak to public feeds.
- Duplicate detection does not merge reports across incompatible jurisdiction/location scopes.
- Dashboard totals are correct for the selected jurisdiction and date filter.
- Audit events record actor, role, timestamp, and old/new state for every controlled transition.

## Release recommendation

Treat this branch as a frontend prototype. Do not deploy for real resident reports until canonical civic data, backend authorization, jurisdiction-aware storage/querying, privacy controls, assignment workflows and regression tests are implemented.

# Database Schema Template

ORM: Objection.js | Query Builder: Knex | Database: PostgreSQL
Convention: `snake_case` columns in DB ↔ `camelCase` properties in code (Knex snake-case mappers)

Use this file to document your project's complete schema.
The **Core Tables** section applies to every project of this type unchanged.
The **Domain Tables** section is a template — replace with your project's entities.

---

## Schema Conventions

### Required on Every Table

| Column | Type | Notes |
|--------|------|-------|
| `id` | `bigint` auto-increment | Internal PK — never expose to API clients |
| `uuid` | `uuid` | Public-facing identifier — always use this in API responses and URLs |
| `created_at` | `timestamp` | Set on insert via `timestamps()` migration helper |
| `updated_at` | `timestamp` | Auto-updated via PostgreSQL trigger |

### Soft Delete (add only when the product needs it)
| Column | Type | Notes |
|--------|------|-------|
| `deleted_at` | `timestamp` nullable | `NULL` = active record; set = soft-deleted |

### Naming Rules
- All column names: `snake_case`
- Boolean columns: `is_<state>` (e.g., `is_email_verified`, `is_active`)
- Status/type columns: `smallint`; enum values documented in code constants
- Foreign keys: `<table_singular>_id` (e.g., `user_id`, `role_id`); always indexed
- Flexible non-queryable metadata: `jsonb` columns (e.g., `preferences`, `meta`)

---

## Core Tables

These tables are required in every project of this type. Do not modify their structure
without a strong architectural reason.

### `users`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `uuid` | uuid | UNIQUE, NOT NULL | `gen_random_uuid()` default |
| `email` | varchar(255) | UNIQUE, NOT NULL | Primary login identifier |
| `password` | varchar | nullable | bcrypt hashed; null for OAuth-only users |
| `first_name` | varchar(100) | nullable | |
| `last_name` | varchar(100) | nullable | |
| `profile_picture_slug` | varchar | nullable | S3 object key |
| `contact_mobile_number` | varchar(20) | nullable | |
| `user_type` | smallint | NOT NULL, index | Distinguishes user roles (admin, end-user, etc.) |
| `org_type` | smallint | nullable, index | Individual vs. organisation — if applicable |
| `status` | smallint | NOT NULL default 1, index | Active / inactive / suspended |
| `is_email_verified` | boolean | NOT NULL default false | |
| `multi_factor_auth_enabled` | boolean | NOT NULL default false | |
| `last_login_at` | timestamp | nullable | Used to invalidate tokens issued before this |
| `preferences` | jsonb | default '{}' | UI preferences: theme, language, notification settings |
| `meta` | jsonb | nullable | Project-specific user metadata (domain fields that vary by user type) |
| `created_at` | timestamp | NOT NULL | |
| `updated_at` | timestamp | NOT NULL | |

**Indexes:** `user_type`, `org_type`, `status`, `email` (unique)

> **`meta` field guidance:** Store domain-specific, non-queryable user attributes here
> (e.g., registration numbers, employer details, tax identifiers). Fields that need
> filtering or joining should be promoted to dedicated columns.

---

### `roles`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `uuid` | uuid | UNIQUE, NOT NULL | |
| `name` | varchar(100) | UNIQUE, NOT NULL | Machine-readable name (e.g., `admin`, `user`, `manager`) |
| `display_name` | varchar(255) | nullable | Human-readable label |
| `description` | text | nullable | |
| `created_at` | timestamp | | |
| `updated_at` | timestamp | | |

---

### `permissions`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `uuid` | uuid | UNIQUE, NOT NULL | |
| `name` | varchar(255) | UNIQUE, NOT NULL | Scope string: `<domain>/<action>` (e.g., `users/update`, `reports/export`) |
| `description` | text | nullable | |
| `created_at` | timestamp | | |
| `updated_at` | timestamp | | |

---

### `role_user` (join table)

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | bigint | PK |
| `user_id` | bigint | FK → users.id, CASCADE DELETE, index |
| `role_id` | bigint | FK → roles.id, CASCADE DELETE, index |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

---

### `permission_role` (join table)

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | bigint | PK |
| `permission_id` | bigint | FK → permissions.id, CASCADE DELETE |
| `role_id` | bigint | FK → roles.id, CASCADE DELETE |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

---

### `companies` (for multi-tenant / organisation-aware projects)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `uuid` | uuid | UNIQUE, NOT NULL | |
| `name` | varchar(255) | NOT NULL | |
| `status` | smallint | NOT NULL default 1, index | |
| `meta` | jsonb | nullable | Organisation-specific attributes |
| `created_at` | timestamp | | |
| `updated_at` | timestamp | | |

---

### `team_members` (join table — users ↔ companies)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `company_id` | bigint | FK → companies.id, index | |
| `user_id` | bigint | FK → users.id, index | |
| `role` | smallint | NOT NULL | Team-level role: owner / admin / member |
| `created_at` | timestamp | | |
| `updated_at` | timestamp | | |

---

### `settings`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `uuid` | uuid | UNIQUE | |
| `key` | varchar(255) | UNIQUE, NOT NULL | Dot-notation key (e.g., `app.features.signupEnabled`) |
| `value` | jsonb | nullable | |
| `created_at` | timestamp | | |
| `updated_at` | timestamp | | |

---

## Reference / Lookup Tables

Include only when your project requires geographic or lookup data.

### `countries`

| Column | Type | Notes |
|--------|------|-------|
| `id` | bigint | PK |
| `uuid` | uuid | |
| `name` | varchar(100) | |
| `iso_code` | varchar(3) | ISO 3166-1 alpha-2 or alpha-3 |
| `phone_code` | varchar(10) | International dialling prefix |

> **Pattern:** Hierarchical lookups (states → districts → cities) each have their own
> table with a `parent_id` FK back to the level above. Seed data via Knex seed files,
> not migrations.

---

## Domain Tables (Project-Specific)

Document your project's core business entities here.
The examples below illustrate the pattern — replace with your actual domain.

### Pattern: Primary Domain Entity

```
<domain_entities>/
├── <entity>                   — main domain record
├── <entity>_items             — line items / sub-records
├── <entity>_attachments       — file attachments linked to entity
└── <entity>_audit_logs        — audit trail (optional)
```

### Example: Content / Thread Pattern
_(illustrates a parent → child → attachment hierarchy)_

**`threads`** (parent)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `uuid` | uuid | UNIQUE | |
| `user_id` | bigint | FK → users.id, index | Owner |
| `title` | varchar(500) | nullable | |
| `status` | smallint | NOT NULL default 1 | 1=active, 2=archived |
| `meta` | jsonb | nullable | Domain-specific attributes |
| `created_at` | timestamp | | |
| `updated_at` | timestamp | | |

**`thread_entries`** (child records)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `uuid` | uuid | UNIQUE | |
| `thread_id` | bigint | FK → threads.id, index | |
| `user_id` | bigint | FK → users.id, nullable | Null = system-generated |
| `content` | text | NOT NULL | |
| `meta` | jsonb | nullable | Processing metadata, token counts, etc. |
| `created_at` | timestamp | | |
| `updated_at` | timestamp | | |

**`attachments`** (file references — reusable across entities)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | bigint | PK | |
| `uuid` | uuid | UNIQUE | |
| `user_id` | bigint | FK → users.id, index | Uploader |
| `entity_type` | varchar(50) | NOT NULL | Polymorphic reference (e.g., `thread`, `report`) |
| `entity_id` | bigint | NOT NULL, index | ID of the linked entity |
| `original_name` | varchar(500) | NOT NULL | |
| `slug` | varchar(500) | NOT NULL | S3 object key |
| `mime_type` | varchar(100) | NOT NULL | |
| `size` | bigint | NOT NULL | bytes |
| `status` | smallint | NOT NULL default 1 | |
| `created_at` | timestamp | | |
| `updated_at` | timestamp | | |

> Replace the above with your actual domain tables. Keep the same column conventions.

---

## Migration Files Index

Maintain this list as migrations are added. Use it to audit migration completeness.

```
database/migrations/
├── YYYYMMDDHHMMSS_on_update_function.js        # PostgreSQL auto-update trigger (run once)
│
│   # Core — always present
├── YYYYMMDDHHMMSS_create_users.js
├── YYYYMMDDHHMMSS_create_roles.js
├── YYYYMMDDHHMMSS_create_permissions.js
├── YYYYMMDDHHMMSS_create_role_user.js
├── YYYYMMDDHHMMSS_create_permission_role.js
├── YYYYMMDDHHMMSS_create_settings.js
│
│   # Multi-tenant (if applicable)
├── YYYYMMDDHHMMSS_create_companies.js
├── YYYYMMDDHHMMSS_create_team_members.js
│
│   # Reference data (if applicable)
├── YYYYMMDDHHMMSS_create_countries.js
├── YYYYMMDDHHMMSS_create_states.js
│
│   # Domain tables — add your project's tables here
└── YYYYMMDDHHMMSS_create_<your_entity>.js
```

---

## Enums Reference

Document every `smallint` status/type column here so intent is never ambiguous.

### Standard Enums (used across all projects)

**`UserStatus` (users.status)**
| Value | Constant | Description |
|-------|----------|-------------|
| 1 | `UserStatus.ACTIVE` | Account is active |
| 2 | `UserStatus.INACTIVE` | Deactivated by admin or user |
| 3 | `UserStatus.SUSPENDED` | Suspended — login blocked |

**`UserType` (users.user_type)**
| Value | Constant | Description |
|-------|----------|-------------|
| 1 | `UserType.ADMIN` | System administrator |
| 2 | `UserType.USER` | Standard end user |
> Add additional user types as your domain requires (e.g., `MANAGER`, `AGENT`).

**`OrgType` (users.org_type — if applicable)**
| Value | Constant | Description |
|-------|----------|-------------|
| 1 | `OrgType.INDIVIDUAL` | Single person |
| 2 | `OrgType.ORGANISATION` | Business or legal entity |

**`TeamRole` (team_members.role)**
| Value | Constant | Description |
|-------|----------|-------------|
| 1 | `TeamRole.OWNER` | Full control, cannot be removed |
| 2 | `TeamRole.ADMIN` | Manage members and settings |
| 3 | `TeamRole.MEMBER` | Standard access |

### Project-Specific Enums

Document your domain enums here, following the same table format above.

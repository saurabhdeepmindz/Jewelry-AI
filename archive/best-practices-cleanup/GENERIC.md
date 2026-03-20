# <Project Name> Backend — Claude Configuration

## How to use this file

Copy this file to the root of your new project as **CLAUDE.md**.

Fill in every `<placeholder>` with your project's actual values.

Delete all instruction blocks once populated.

---

# Project Identity

**Name:** `<project-name>-backend`  

**Type:** NestJS TypeScript Monorepo (Microservices)  

**Stack:**

- NestJS 11+
- TypeScript 5.3+
- PostgreSQL
- Objection.js / Knex
- Redis
- Node 20 LTS

**Purpose:**

`<One sentence describing what this backend platform does and who it serves>`

Example:

> Backend API platform for [domain], providing user management, core business features, file services, and notifications.

---

# How to Use This Repo

Before writing any code, read in this order:

1. **RULES.md** — Master engineering rules for this project  
2. **ARCHITECTURE.md** — System design, layers, and module map  
3. **docs/DB_SCHEMA.md** — Database schema and migration conventions  
4. **docs/API_SPEC.md** — API design contracts and response formats  

---

# Project Structure at a Glance

Update the tree below to match your actual apps and libraries once scaffolded.


```
<project-name>-backend/
├── apps/                        # Microservice entry points
│   ├── auth-apis/               # Authentication, user management, OAuth
│   ├── <domain>-apis/           # Core business domain API
│   ├── control-panel/           # Admin dashboard API
│   ├── file-services/           # File upload and storage
│   ├── media-services-job/      # Background job processor
│   └── notification/            # Transactional email delivery
│
├── libs/                        # Shared libraries (imported as @libs/<name>)
│   ├── dmz/                     # Core framework: REST server, validators, exceptions, cache
│   ├── database/                # ORM abstractions: BaseModel, DatabaseRepository<T>
│   ├── common/                  # Shared interfaces, enums, utilities
│   ├── users/                   # User models, repositories, UsersLibService
│   ├── roles-and-permissions/   # RBAC guards, decorators, role/permission models
│   ├── <domain>/                # Domain-specific models and repositories
│   ├── mailman/                 # Email sending abstraction
│   ├── file-lib-service/        # File handling utilities
│   └── settings/                # Application settings
│
├── config/                      # NestJS ConfigModule namespaced loaders
│   ├── app.ts                   # Port, NODE_ENV, app name
│   ├── auth.ts                  # JWT secrets, OAuth credentials
│   ├── database.ts              # PostgreSQL connection
│   ├── cache.ts                 # Redis connection
│   ├── storage.ts               # AWS S3 configuration
│   ├── notifications.ts         # Email service configuration
│   └── index.ts                 # Exports all configs
│
├── database/
│   ├── migrations/              # Knex migration files
│   └── utils/                   # Migration helpers (timestamps, triggers)
│
├── resources/
│   └── lang/                    # Localization strings
│
├── claude-best-practices/       # Architecture, rules, API spec, DB schema docs
│   ├── RULES.md                 # Master engineering rules
│   ├── ARCHITECTURE.md          # System architecture reference
│   ├── CLAUDE-GENERIC.md        # This template (keep for future projects)
│   └── docs/
│       ├── API_SPEC.md          # API endpoint documentation
│       ├── DB_SCHEMA.md         # Database schema documentation
│       └── rules/               # Domain-specific rule files
│
└── CLAUDE.md                    # Active Claude 
```

# Configuration (this file, after filling in)

## Microservice Apps

List each app, its port, and its primary responsibility. Remove rows that don't apply; add domain-specific apps as needed.

| App | Port | Responsibility |
|-----|------|----------------|
| auth-apis | 3001 | Authentication, user management, OAuth, sessions |
| <domain>-apis | 3002 | <Core business domain description> |
| control-panel | 3003 | Admin and management dashboard API |
| file-services | 3004 | File upload, validation, S3 storage |
| media-services-job | 3005 | Background media/file processing jobs |
| notification | — | Transactional email delivery (internal service) |

---

## Shared Libraries

List each library, its `@libs/<name>` alias, and its purpose. Remove rows that don't apply; add domain libraries as needed.

| Library | Alias | Purpose |
|---------|-------|---------|
| dmz | @libs/dmz | Core framework (RestServer, validators, cache, exceptions) |
| database | @libs/database | ORM layer (BaseModel, DatabaseRepository<T>) |
| common | @libs/common | Shared interfaces, enums, utility functions |
| users | @libs/users | User models, repositories, UsersLibService |
| roles-and-permissions | @libs/roles-and-permissions | RBAC guards and decorators |
| <domain> | @libs/<domain> | <Domain description> |
| mailman | @libs/mailman | Email abstraction (Nodemailer/SES) |
| file-lib-service | @libs/file-lib-service | File handling utilities |
| settings | @libs/settings | Application settings store |

---

## Core Principles (Quick Reference)

- Think architect first, implement second — always infer the correct layer before writing code  
- Thin controllers, rich services, isolated repositories — strict clean architecture  
- Repository pattern everywhere — no direct ORM calls outside repository classes  
- DTO validation at boundaries — use `@Validate(Dto)` on all controller methods that accept input  
- Event-driven side effects — emit events; use listeners for email, audit logging, and external sync  
- Transformer layer — shape all API responses via Transformer classes; never return raw ORM models  
- No hardcoded secrets — all configuration through `config/*.ts` and `.env`  
- Immutability — always create new objects; never mutate existing ones  

---

## Operating Mode

You are the **principal architect and senior engineer** for this repository.

- Extend existing patterns before introducing new ones  
- Respect file organisation conventions:
  - controllers
  - services
  - repositories
  - models
  - dto
  - transformers

- Keep files focused:
  - Typical: 200–400 lines
  - Maximum: 800 lines

- Run tests after every change; maintain ≥ 80% coverage  

- Check `claude-best-practices/RULES.md` before generating any new module, service, or migration  

- When a domain-specific rule file exists (example: `docs/rules/backend-nestjs.md`), follow it precisely.

---

## Environment Variables

List the required `.env` variables for this project.

Copy to `.env.example` with empty values before committing.

## Environment Variables

### Application

NODE_ENV=development  
PORT=3001  

### Database

DB_HOST=localhost  
DB_PORT=5432  
DB_NAME=<your_project_name>  
DB_USER=postgres  
DB_PASSWORD=  

### Authentication

JWT_SECRET=  
JWT_LIFETIME=1h  

REFRESH_TOKEN_SECRET=  
REFRESH_TOKEN_LIFETIME=7d  

### Cache

REDIS_HOST=localhost  
REDIS_PORT=6379  

### Storage (AWS S3)

AWS_ACCESS_KEY_ID=  
AWS_SECRET_ACCESS_KEY=  
AWS_REGION=<your-aws-region>  
S3_BUCKET=  

### Email

SMTP_HOST=  
SMTP_PORT=587  
SMTP_USER=  
SMTP_PASS=  

### Error Tracking

SENTRY_DSN=  

### OAuth (if used)

GOOGLE_CLIENT_ID=  
GOOGLE_CLIENT_SECRET=  
GOOGLE_CALLBACK_URL=  

### Add project-specific variables below

---

## Quick Commands

Update app names and ports to match your project.

### Start Services

Start single app (watch mode):

    npm run app -- <app-name>

Start all apps (development):

    npm run start:all:dev

Start all apps (QA):

    npm run start:all:qa

Start all apps (production):

    npm run start:all:prod

---

## Database Commands

Run migrations:

    npx knex migrate:latest --knexfile knexfile.js

Rollback last migration:

    npx knex migrate:rollback --knexfile knexfile.js

---

## Testing

Run all tests:

    npm run test

Run tests with coverage:

    npm run test:cov

---

## Code Quality

Lint and format:

    npm run lint && npm run format

---

## Build

Build production code:

    npm run build

---

## Domain-Specific Context

Fill in this section to give Claude the business context needed for architectural decisions.

---

## Business Domain

Describe the core business problem this platform solves in 2–3 sentences.

Example:

Backend platform for <domain> that manages users, workflows, notifications, and file services.

---

## User Roles

| Role | Description | Key Permissions |
|------|-------------|----------------|
| admin | System administrator | Full platform access |
| <role> | <Description> | <Key actions this role can perform> |

---

## Core Domain Entities

| Entity | Description | Key Relations |
|--------|-------------|---------------|
| User | Platform user | Has roles, belongs to company (optional) |
| <Entity> | <Description> | <Relations> |

---

## Key Business Rules

List important domain rules:

- <Business rule 1>
- <Business rule 2>
- <Business rule 3>
- <Business rule 4>

Example:

- Users must belong to at least one role
- Soft delete required for all business entities
- Audit logs required for admin actions
- File uploads must be virus scanned

## Key Business Rules

- <Rule 1> — e.g., "Users must verify their email before accessing paid features"
- <Rule 2> — e.g., "A company can have at most one owner"
- <Rule 3> — e.g., "Archived records are hidden from listings but retained for audit"

---

## External Integrations

List third-party services this project integrates with.

| Service | Purpose | Library / Method |
|---------|---------|------------------|
| AWS S3 | File storage | @aws-sdk/client-s3 |
| AWS SES | Transactional email | @aws-sdk/client-ses |
| Google OAuth | Social login | passport-google-oauth20 |
| Sentry | Error tracking | @sentry/node |
| <Service> | <Purpose> | <Library> |

---

## Project-Specific Conventions

Add any conventions or decisions that are unique to this project and would not be obvious from the generic rules files.

- <Convention 1> — e.g., "All monetary values are stored in cents as integers"
- <Convention 2> — e.g., "Soft-delete is used on <Entity> because of audit requirements"
- <Convention 3> — e.g., "The <domain>-apis app handles both X and Y to avoid an extra service"
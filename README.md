# Inventory Management System (IMS)

A multi-tenant inventory management platform built with Django — product catalog, purchases, sales, returns, stock tracking, and PDF reporting, with every business isolated to its own organization on a single codebase.

**Live demo:** https://inventory.itbdsoft.com/

| Field | Value |
|---|---|
| Organization | `ORG-GICLXR` |
| Username | `demo@lifecare` |
| Password | `demo@123` |

> The demo runs the exact code in this repository — logging in shows the real multi-tenant flow described below, not a static preview.

---

## Table of Contents

- [Overview](#overview)
- [Highlights](#highlights)
- [Technology Stack](#technology-stack)
- [Key Features](#key-features)
- [Engineering Decisions](#engineering-decisions)
- [Architecture](#architecture)
- [Database Design](#database-design)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)
- [Images](#images)
- [License](#license)
- [Author](#author)

---

## Overview

Small and mid-sized businesses that sell physical products need to track what they buy, what they sell, and what's left — across suppliers, customers, and sometimes multiple branches. Spreadsheets break down once more than one person enters data: there's no single source of truth for current stock, and no audit trail of who changed what.

This project solves that with a **multi-tenant Django application**: one deployment, many businesses, each fully isolated. Every business-relevant model — products, purchases, sales, returns, customers, suppliers — is scoped to an `Organization`, and optionally further scoped to a `Branch`. Authentication, inventory operations, and reporting all respect that boundary.

The application is built as traditional Django views and templates (Django ORM, HTML, Bootstrap) — **not** a REST API. A small set of AJAX/JSON endpoints exist for live stock checks during data entry (see [Architecture](#architecture)).

---

## Highlights

> The five things worth knowing before reading further.

- **True multi-tenancy**, not a single shared database with a filter bolted on — usernames, product codes, and barcodes are unique *per organization*, enforced at the database level via `unique_together`, not just checked in Python.
- **Concurrency-safe stock handling** — sales validate and deduct stock inside `transaction.atomic()`, sequential codes use `select_for_update()`, and a session-scoped reservation system prevents two users from overselling the same unit at the same time.
- **Consistent service-layer architecture** across all six apps — every app separates `models.py` / `validators.py` / `services.py` / `views.py`, so business logic never lives inside a template or a 200-line view.
- **Bilingual PDF reporting** (English/Bengali) built without relying on Django's request-scoped i18n system, with the Bengali font embedded directly into the PDF so generation doesn't depend on the server having that font installed.
- **Correlation-ID error tracking** — every 403/404/500 is logged with a short ID shown to the user, retrievable later through a staff-only lookup view, instead of grepping raw server logs.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Web framework | Django 3.2 |
| Database | PostgreSQL (`psycopg2-binary`) |
| Templating | Django Templates |
| Frontend | HTML, CSS, Bootstrap |
| Static files | WhiteNoise |
| PDF generation | WeasyPrint |
| Barcode generation | python-barcode, Pillow |
| Fuzzy/string matching | RapidFuzz, python-Levenshtein |
| Internationalization | Django i18n (English, Bengali), Babel |
| WSGI servers | Gunicorn, Passenger (`passenger_wsgi.py`) |
| Configuration | python-decouple, `.env` |

---

## Key Features

### Multi-Tenancy & Authentication
- Organization-scoped accounts — usernames and emails are unique **within an organization**, not globally, enforced via `unique_together` constraints and a custom auth backend (`TenantUsernameBackend`) that authenticates by `username + organization` together.
- Role-based accounts: `platform_admin`, `admin`, `manager`, `employee`.
- Self-service onboarding — a business submits an `OrganizationRequest`; approval provisions the `Organization`, its first `Branch`, and its first admin `User` in one step.
- Separate login flow for platform-level administrators, isolated from tenant logins.
- Password reset via emailed token link, in-app password change, and per-login audit trail (`LoginHistory`: user, organization, branch, IP, timestamp).
- Per-organization logo and language preference (English / Bengali).

### Product Catalog
- Four-level taxonomy: `Category` → `Brand` → `ProductGroup` → `Product`, each scoped to an organization/branch.
- Auto-generated, per-organization sequential codes (`BR-001`, `PG-002`, `PR-003`).
- Barcode generation (`python-barcode`, Code128) stored against the product and used during stock/sales lookups.
- Per-product low-stock threshold, consumed by the stock module.

### Inventory Operations
- Opening stock entry per product, per organization/branch.
- Purchases and sales with multiple line items, automatically adjusting stock on save.
- Purchase and sale returns, each validated against current stock before being recorded.
- Product rejects (damaged / expired / defective / contaminated / other), optionally linked to the originating purchase.
- Low-stock report view, plus an in-app warning and email notification once stock reaches its threshold.

### Stock Reservation System
- A `StockReservation` model holds a quantity against a user's session for 30 minutes, so two employees filling out sale forms simultaneously can't both oversell the same unit.
- Available stock = real stock minus reservations held by *other* sessions, recalculated on every check.
- Expired reservations clean up automatically; a bulk-availability endpoint supports live polling while a form is open.

### Reporting
- PDF generation (WeasyPrint) for opening stock, purchases, sales, returns, and rejects — filtered by date range, scoped to organization/branch, previewable in-browser before download.
- Bengali-language reports via a hand-built translation dictionary and a base64-embedded font, so rendering doesn't depend on system fonts or network access at request time.
- Per-organization logo embedded in the report header.

### Suppliers, Customers & Admin Tooling
- Organization-scoped `Supplier` and `Customer` records with create/list/detail/update views, plus lookup-by-code-or-mobile endpoints used during purchase/sale entry.
- A custom `TenantScopedAdminMixin` applied across Django admin: tenant users see only their own organization's (and branch's) records, the `organization` field is hidden and auto-assigned, and FK dropdowns are scoped accordingly. Platform superadmins bypass all of this.
- Custom 403/404/500 handlers that log a structured JSON record (path, method, user, IP, user agent, traceback) under a short correlation ID, plus a staff-only `/error-lookup/` view to retrieve that record without touching server logs.

---

## Engineering Decisions

A feature list shows *what* exists. This section covers *why* it's built this way.

**Why a `services.py` per app, instead of logic in views.**
Views resolve `request.user.organization`/`.branch`, hand off to a service function, and render a template. Business rules — stock math, code generation, PDF assembly — live in one place instead of being duplicated across views and templates. A view that creates a sale is a few lines long; the actual sale logic is testable in isolation from HTTP.

**Why stock mutations are wrapped in `transaction.atomic()`.**
A sale writes to the transaction header, its line items, and the stock record together. If any write fails partway through, none of it should persist — otherwise you'd end up with a sale recorded but stock never deducted, or the reverse. Sequential code generation (`PR-001`, `SL-002`, …) additionally uses `select_for_update()` so two concurrent requests can't generate the same code.

**Why tenant scoping is enforced twice — in queries and in the admin.**
Every service function that touches organization-scoped data filters explicitly by `organization` (and `branch` where relevant) rather than relying on a global default manager. The Django admin gets the same treatment through `TenantScopedAdminMixin`, so there's no side door into another tenant's data through `/admin/` just because the ORM-level scoping was bypassed.

**Why stock reservations exist at all.**
Without them, two employees viewing the same product's stock during checkout could both see "5 available" and both try to sell 5, overselling by however much the second sale needed. A 30-minute, session-scoped hold makes "available stock" mean *available to you, right now*, not just the raw database value.

**Why validators are separated from services.**
`validators.py` answers "is this input acceptable" (format, presence, uniqueness) before a service function ever touches the database. Keeping that check ahead of the service call means the service functions can assume valid input and focus purely on the business logic.

---

## Architecture

```
Request
  │
  ▼
URL routing (per-app urls.py, included from ims_project/urls.py)
  │
  ▼
View  — login_required; resolves request.user.organization / .branch
  │
  ├──▶ validators.py   input validation, returns True/False + messages
  ├──▶ services.py     business logic, wrapped in transaction.atomic()
  │                    where multiple writes must succeed or fail together
  ▼
Django ORM ──▶ PostgreSQL
  │
  ▼
Template (Django Templates + Bootstrap)  — or JsonResponse for AJAX stock checks
```

Every app follows the same shape:

| File | Responsibility |
|---|---|
| `models.py` | Data definition, tenant-scoped fields, constraints |
| `validators.py` | Pre-database input validation |
| `services.py` | Business logic, atomic transactions where needed |
| `views.py` | Thin coordination between request, validators, services |
| `urls.py` | Route definitions |
| `admin.py` | Django admin registration (tenant-scoped via mixin) |

The project is configured for deployment behind a Passenger-compatible host (`passenger_wsgi.py` alongside the standard `wsgi.py`/`asgi.py`), with WhiteNoise serving static files and `python-decouple`/`.env` handling environment-based configuration.

---

## Database Design

At the core of the schema is the tenant chain:

```
Organization (UUID primary key)
   └── Branch (optional subdivision; code unique per organization)
         └── User (username / email / phone unique per organization, not globally)
```

Every business-facing model — `Category`, `Brand`, `ProductGroup`, `Product`, `Supplier`, `Customer`, `OpeningStock`, `Purchase`(`Item`), `Sale`(`Item`), `PurchaseReturn`(`Item`), `SaleReturn`(`Item`), `ProductReject`, `StockReservation` — carries an `organization` foreign key, and most carry an optional `branch` foreign key. Uniqueness constraints (a product's barcode, a category's name, a supplier's code) are scoped to `(organization, field)` rather than globally unique, since the same code is allowed to exist independently in two different organizations.

Transaction-style models follow a **header / line-item** pattern: one row for the transaction (`Purchase`, `Sale`, `PurchaseReturn`, `SaleReturn`) and related item rows (`PurchaseItem`, `SaleItem`, …) each with product, quantity, unit price, and subtotal — with a `UniqueConstraint` preventing the same product from appearing twice on one transaction.

Audit fields (`created_at`, `updated_at`, `created_by`, `updated_by`) are present on essentially every business model, giving a consistent trail of who created or last modified each record.

---

## Project Structure

```
ims_project_v1/
├── ims_project/        Settings, root URLs, WSGI/ASGI, custom error handlers
├── authenticate_app/    Organization, Branch, User, LoginHistory, auth views/services
├── product_app/         Category, Brand, ProductGroup, Product, barcode generation
├── stock_app/           Stock transactions, StockReservation, tenant-scoped admin mixin
├── personinfo_app/      Supplier, Customer, user profile views
├── report_app/          PDF/HTML report generation, translations, WeasyPrint integration
├── dashboard_app/       Dashboard entry point, error-lookup diagnostic view
├── templates/           Django templates, grouped by app
├── locale/bn/           Bengali translation files
├── media/               Uploaded org logos, profile images, barcodes, fonts
└── requirements.txt
```

Each app internally repeats the same convention — `models.py`, `validators.py`, `services.py`, `views.py`, `urls.py`, `admin.py` — described in [Architecture](#architecture).

---

## Installation

**Requirements:** Python 3.x, PostgreSQL, the packages in `requirements.txt`.

```bash
# Clone and enter the project
git clone <your-repo-url>
cd ims_project_v1

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file in the project root (see below), then:
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**`.env` variables:**

```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=

EMAIL_HOST=
EMAIL_PORT=
EMAIL_USE_TLS=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

> Never commit a real `.env` file — add it to `.gitignore`.

---

## Known Limitations

- **No automated test suite.** Each app's `tests.py` is the default Django boilerplate; there is no unit or integration test coverage yet.
- **No REST API.** The application is fully server-rendered; the JSON endpoints in `stock_app` support live stock checks in the browser, not general-purpose API access.
- **No full-text search, filtering, or pagination in application list views.** Django admin has `search_fields` configured, but tenant-facing list pages render the full queryset. Lookup-by-code/mobile endpoints exist for suppliers, customers, and barcodes, which is narrower than a general search feature.
- **Django 3.2**, an older LTS release, is the framework version in use.
- **Some validators are intentionally basic** — email format checking, for example, is a simple `@`/`.` substring check rather than a full RFC-compliant validator.

---

## Future Improvements

- Add unit and integration tests for the service layer (stock deduction, code generation, reservation logic) and tenant-isolation guarantees.
- Introduce pagination and basic filtering on list views as data volume grows.
- Upgrade to a current Django LTS release.
- Expose core operations (purchases, sales, stock lookups) through a versioned REST API using Django REST Framework.
- Extend the Bengali localization approach — or move to full Django i18n — for additional languages.

---
## Images
For application images, please refer to the images/ folder, where files are organized at the app level.



---
## License

Copyright 2026 Ismail Koni

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this project except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Author

**MD ISMAIL**

Junior Backend Developer focused on Python, Django, and PostgreSQL.

- GitHub: https://github.com/ismailCrafts
- Portfolio: https://md-ismail.netlify.app/
- LinkedIn: https://www.linkedin.com/in/dev-mdismail/
- Email: ismailbhuyan.dev@gmail.com

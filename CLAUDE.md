# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**HaroHUB** adalah platform e-commerce Gunpla (Gundam Plastic Model Kit) full-stack untuk pasar Indonesia, dibangun sebagai proyek portfolio yang menonjolkan kemampuan **backend engineering** dan **recommendation engine**. Frontend hadir sebagai bukti hidup bahwa backend bekerja end-to-end.

## Commands

```bash
# Setup
pip install -r requirments.txt

# Development server
python manage.py runserver

# Tailwind CSS watcher (jalankan berdampingan dengan runserver)
./tailwindcss -i static/src/input.css -o static/css/output.css --watch

# Database
python manage.py migrate
python manage.py createsuperuser   # email-based, bukan username

# Seed data (urutan penting)
python manage.py seed_catalog      # products, grades, timelines, series
python manage.py seed_shipping     # flat-rate shipping per city
python manage.py seed_events       # synthetic behavior events (demo)
python manage.py compute_recommendations  # compute F-28/F-29/F-30 tables

# Testing
python manage.py test
python manage.py test apps.order.tests.test_state_machine   # satu file
python manage.py test apps.recommendations.tests.test_engine  # tanpa database

# Settings
DJANGO_SETTINGS_MODULE=config.settings.development   # default dev
DJANGO_SETTINGS_MODULE=config.settings.production    # prod
```

Database switching otomatis via `DATABASE_URL` environment variable — tidak perlu edit kode manual.

## Architecture

### Stack

| Layer | Technology |
|---|---|
| Framework | Django + Django REST Framework |
| Frontend | Django Templates + HTMX + Tailwind CSS (standalone binary) |
| Database dev | SQLite |
| Database prod | PostgreSQL (Supabase) via `DATABASE_URL` |
| Background job | `python manage.py compute_recommendations` (dijadwalkan cron harian jam 02:00) |
| Maps | Google Maps Platform |

DRF berperan sebagai **endpoint JSON untuk HTMX** (autocomplete, widget rekomendasi) dan dokumentasi API di `/api/docs/` — bukan primary API layer.

### Project Structure

```
config/              # project package
  settings/
    base.py          # shared config, membaca DATABASE_URL
    development.py   # DEBUG=True, fallback SQLite
    production.py    # PostgreSQL, whitenoise, django-storages

apps/
  core/              # abstract models & mixins — no views/urls/migrations
  common/            # validators, generators, templatetags, context_processors, exceptions
  accounts/          # User(AbstractUser), Address
  catalog/           # Product, ProductImage, Grade, Timeline, Series
  cart/              # Cart, CartItem — no services.py
  order/             # Order (state machine), OrderItem, ShippingRate, Payment + services.py
  recommendations/   # engine/ (pure Python) + services.py (serve) + management commands

templates/
  base.html
  partials/          # global HTMX fragments: _<feature>_<section>.html
  <app>/             # full-page templates per app

static/
  src/input.css      # Tailwind source
  css/output.css     # generated output (gitignored)
  js/app.js
```

### URL Namespaces

| App | Namespace | Example |
|---|---|---|
| `catalog` | `catalog` | `{% url 'catalog:detail' slug %}` |
| `recommendations` | `recommendations` | `{% url 'recommendations:widget_similar' id %}` |
| `cart` | `cart` | `{% url 'cart:index' %}` |
| `order` | `order` | `{% url 'order:checkout' %}` |
| `accounts` | `accounts` | `{% url 'accounts:login' %}` |

### Dependency Direction

```
core / common  ◄── (leaf — imported by all, never imports back)
      ▲
  accounts
      ▲
   catalog
      ▲
cart / order / recommendations
```

FK lintas-app wajib pakai **lazy string** (`'catalog.Product'`). Service call dipanggil **di dalam fungsi view**, bukan di import level atas — mencegah circular import.

### Recommendation Engine (3-Layer CQRS-lite)

```
Capture (write)  →  Compute (batch)  →  Serve (read)
BehaviorEvent       compute_recommendations   ProductSimilarity (F-28)
Wishlist            management command        UserRecommendation (F-29)
                    transaction.atomic        ProductPopularity (F-30)
```

- **`engine/`** — pure Python, zero ORM coupling. Receives `dataclass` (from `types.py`), returns scores. Unit-testable without database.
- **Weights injected from `settings.py`**, never imported inside `engine/`.
- Serve tables are disposable: `CASCADE`, `FloatField`, rebuilt every batch run.
- Cold-start fallback (F-30) lives in `services.py`, not `engine/`.

### Order State Machine

All order status changes **must** go through `Order.transition_to()`. Admin (F-21) calls this method — never sets `status` directly. Valid transitions:

```
PENDING → PAID → PROCESSING → SHIPPED → COMPLETED
PENDING/PAID/PROCESSING → CANCELLED
```

`Payment.status = PAID` is the only trigger for `Order PENDING → PAID`.

### Key Model Decisions

- **`Cart`** does not store price (read live). **`OrderItem`** freezes price/name/image at checkout.
- **`Order.shipping_*`** is a snapshot of the address (Address is mutable and deletable).
- **`BehaviorEvent`** is an append-only log. No UPDATE/DELETE.
- **`BehaviorEvent`** is the unified signal log (VIEW/WISHLIST/PURCHASE). PURCHASE duplicates `OrderItem` — intentional (two purposes, two homes).
- **`weight`** is not stored in `BehaviorEvent` — it is a hyperparameter in `settings.py`, applied at compute time, not capture time.

## Database Portability Rules (SQLite → PostgreSQL)

- **Forbidden:** `ArrayField`, `SearchVector`, anything from `django.contrib.postgres`
- **`JSONField` allowed** but avoid heavy query-by-key
- **`LIKE` search** — case-insensitive in SQLite, case-sensitive in PostgreSQL; test again in prod
- **`db.sqlite3` in `.gitignore`** — do not commit

## Settings Configuration

Recommendation engine hyperparameters live in `settings.py` (not DB) so they can be tuned and recomputed:

```python
RECOMMENDATION_WEIGHTS = {'VIEW': 1, 'WISHLIST': 3, 'PURCHASE': 5}
RECOMMENDATION_DIMENSION_WEIGHTS = {'series': 3, 'timeline': 2, 'grade': 1}
SIMILARITY_WEIGHTS = {'series': 3, 'timeline': 2, 'grade': 1}
SIMILARITY_TOP_K = 30
RECOMMENDATION_TOP_N = 12
```

`RECOMMENDATION_DIMENSION_WEIGHTS` and `SIMILARITY_WEIGHTS` share the same values but are **two separate keys** — different operations, may be tuned independently.

## Domain Knowledge (Required for Product/Recommendation Features)

> Read `docs/01-domain-knowledge.md` before working on any feature involving products, categories, filters, or the recommendation system.

Enum values that must be consistent throughout the codebase:

```python
product.grade        → "EG"|"HG"|"RG"|"MG"|"PG"|"SD"|"MetalBuild"|"FigureRise"
product.timeline_id  → "UC"|"AC"|"CE"|"AD"|"PD"|"AS"|"BF"|"SD"
product.series       → free string (e.g. "Gundam SEED")
```

Hierarchy: `Series → Timeline` (series is a child of timeline). `product.timeline_id` is **not stored directly on Product** — derived via `product.series.timeline`.

## AppConfig

Every app must have `AppConfig.name = 'apps.<name>'` (explicit, because apps live under the `apps/` package).

## Feature Scope

**MVP (21 features)** complete. Deliberately skipped: password reset (F-09), Midtrans real (F-14), RajaOngkir real (F-15), promo codes (F-23). Payment and shipping use **mock simulation**.

See `docs/02-feature-map.md` for the full feature list and `docs/03-mvp-feature-specifications.md` for acceptance criteria.

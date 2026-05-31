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

# Recommendation engine (batch job)
python manage.py compute_recommendations

# Testing
python manage.py test
python manage.py test apps.order.tests.test_state_machine   # satu file
python manage.py test apps.rekomendasi.tests.test_engine    # tanpa database

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
config/          # project package (bukan app)
  settings/
    base.py          # shared config, membaca DATABASE_URL
    development.py   # DEBUG=True, fallback SQLite
    production.py    # PostgreSQL, whitenoise, django-storages

apps/
  core/          # abstract models & mixins — tidak punya views/urls/migrations
  common/        # validators, generators, templatetags, context_processors, exceptions
  accounts/      # User(AbstractUser), Address
  produk/        # Product, ProductImage, Grade, Timeline, Series
  cart/          # Cart, CartItem — paling ramping, tanpa services.py
  order/         # Order (state machine), OrderItem, ShippingRate, Payment + services.py
  rekomendasi/   # engine/ (Python murni) + services.py (serve) + management command

templates/
  base.html
  partials/      # global HTMX fragments: _<fitur>_<bagian>.html (prefix underscore)
  <app>/         # halaman utuh per app

static/
  src/input.css  # sumber kebenaran Tailwind
  css/output.css # hasil generate (gitignored)
  js/app.js
```

### Dependency Direction

```
core / common  ◄── (leaf, diimpor semua, tidak pernah impor balik)
      ▲
  accounts
      ▲
   produk
      ▲
cart / order / rekomendasi
```

FK lintas-app wajib pakai **lazy string** (`'produk.Product'`). Service call dipanggil **di dalam fungsi view**, bukan di import level atas — mencegah circular import.

### Recommendation Engine (3-Layer CQRS-lite)

```
Capture (write)  →  Compute (batch)  →  Serve (read)
BehaviorEvent       compute_recommendations   ProductSimilarity (F-28)
Wishlist            management command        UserRecommendation (F-29)
                    transaction.atomic        ProductPopularity (F-30)
```

- **`engine/`** — Python murni, zero ORM coupling. Menerima `dataclass` (dari `types.py`), mengembalikan skor. Bisa di-unit-test tanpa database.
- **Weights disuntikkan dari `settings.py`**, tidak pernah diimpor dari dalam `engine/`.
- Tabel serve bersifat disposable: `CASCADE`, `FloatField`, dibangun ulang tiap batch run.
- Cold-start fallback (F-30) ada di `services.py`, bukan `engine/`.

### Order State Machine

Semua perubahan status order **wajib** lewat `Order.transition_to()`. Admin (F-21) memanggil method ini, bukan set `status` mentah. Transisi yang sah:

```
PENDING → PAID → PROCESSING → SHIPPED → COMPLETED
PENDING/PAID/PROCESSING → CANCELLED
```

`Payment.status = PAID` adalah satu-satunya pemicu `Order PENDING → PAID`.

### Key Model Decisions

- **`Cart`** tidak menyimpan harga (dibaca live). **`OrderItem`** membekukan harga/nama/foto saat checkout.
- **`Order.shipping_*`** adalah snapshot alamat (Address mutable & bisa dihapus user).
- **`BehaviorEvent`** adalah append-only log. Tidak ada UPDATE/DELETE.
- **`BehaviorEvent`** adalah sumber sinyal terpadu (VIEW/WISHLIST/PURCHASE), termasuk menerima PURCHASE yang juga ada di `OrderItem` — duplikasi ini disengaja.
- **`weight`** tidak disimpan di `BehaviorEvent` — bobot adalah hyperparameter di `settings.py`, diterapkan saat compute, bukan saat capture.

## Database Portability Rules (SQLite → PostgreSQL)

Selama development, jaga portabilitas agar migrasi ke prod mulus:

- **Dilarang:** `ArrayField`, `SearchVector`, semua field dari `django.contrib.postgres`
- **`JSONField` boleh** tapi hindari query-by-key yang berat
- **`LIKE` search** — case-insensitive di SQLite, case-sensitive di PostgreSQL; test ulang di prod
- **`db.sqlite3` di `.gitignore`** — jangan commit

## Settings Configuration

Hyperparameter rekomendasi disimpan di `settings.py` (bukan database) agar bisa di-tune lalu di-recompute:

```python
RECOMMENDATION_WEIGHTS = {'VIEW': 1, 'WISHLIST': 3, 'PURCHASE': 5}
RECOMMENDATION_DIMENSION_WEIGHTS = {'series': 3, 'timeline': 2, 'grade': 1}
SIMILARITY_WEIGHTS = {'series': 3, 'timeline': 2, 'grade': 1}
SIMILARITY_TOP_K = 30
RECOMMENDATION_TOP_N = 12
```

`RECOMMENDATION_DIMENSION_WEIGHTS` dan `SIMILARITY_WEIGHTS` memiliki nilai yang sama tapi **tetap dua key terpisah** — operasi berbeda, layak di-tune independen.

## Domain Knowledge (Wajib Dibaca untuk Fitur Produk/Rekomendasi)

> Lihat `docs/01-domain-knowledge.md` sebelum mengerjakan fitur apapun yang berhubungan dengan produk, kategori, filter, atau sistem rekomendasi.

Nilai enum yang harus konsisten di seluruh codebase:

```python
product.grade        → "EG"|"HG"|"RG"|"MG"|"PG"|"SD"|"MetalBuild"|"FigureRise"
product.timeline_id  → "UC"|"AC"|"CE"|"AD"|"PD"|"AS"|"BF"|"SD"
product.series       → string bebas (contoh: "Gundam SEED")
```

Hierarchy: `Series → Timeline` (series adalah turunan timeline). `product.timeline_id` **tidak disimpan langsung di Product** — diturunkan via `product.series.timeline`.

## AppConfig

Setiap app harus memiliki `AppConfig.name = 'apps.<nama>'` (eksplisit, karena berada di bawah paket `apps/`).

## Feature Scope

**MVP (21 fitur)** harus selesai untuk demo end-to-end. Yang sengaja di-skip: reset password (F-09), Midtrans real (F-14), RajaOngkir real (F-15), kode promo (F-23). Payment dan shipping menggunakan **simulasi mock**.

Lihat `docs/02-feature-map.md` untuk daftar lengkap fitur dan `docs/03-mvp-feature-specifications.md` untuk acceptance criteria per fitur.

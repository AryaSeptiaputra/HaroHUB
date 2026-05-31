# HaroHUB

Platform e-commerce Gunpla (Gundam Plastic Model Kit) full-stack untuk pasar Indonesia. Dibangun sebagai proyek portfolio yang menonjolkan kemampuan **backend engineering**, **data modeling**, dan **recommendation system** — bukan kelengkapan fitur.

---

## Latar Belakang

Gunpla adalah kategori produk dengan hierarki atribut yang kaya: grade (EG, HG, RG, MG, PG), timeline universe (UC, CE, AD, …), dan seri. Hierarki ini membuat Gunpla menjadi domain yang menarik untuk membangun recommendation engine berbasis konten — setiap atribut membawa sinyal preferensi yang bermakna, bahkan tanpa data perilaku historis.

Proyek ini dirancang agar bisa dijelaskan secara teknis dan bisnis dalam interview: arsitektur yang terstruktur, keputusan desain yang disadari, dan trade-off yang didokumentasikan.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 5 + Django REST Framework |
| Frontend | Django Templates + HTMX + Tailwind CSS |
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL — Supabase |
| Background Job | Django Management Command |
| Maps | Google Maps Platform |
| Deploy | Railway / Render / Fly.io |

**Prinsip pemilihan stack:** kedalaman teknis di backend & AI, kesederhanaan di tempat lain. Tailwind dipasang via [standalone CLI](https://tailwindcss.com/blog/standalone-cli) — nol Node.js dependency. HTMX untuk interaktivitas tanpa SPA overhead.

---

## Fitur Utama

### Katalog & Discovery
- Product listing dengan filter multi-dimensi: grade, timeline, seri, rentang harga, ketersediaan
- Search dengan autocomplete real-time (HTMX)
- Image gallery per produk

### Transaksi
- Keranjang belanja (login-required, stok divalidasi saat checkout)
- Checkout dengan snapshot harga & alamat — riwayat pesanan tidak pernah "berbohong"
- Simulasi pembayaran (mock) dengan 4 metode: transfer bank, e-wallet, QRIS, COD
- Kalkulasi ongkir mock per-kota dari `ShippingRate`
- Pin lokasi alamat pengiriman via Google Maps

### Order Management
- State machine pesanan: `PENDING → PAID → PROCESSING → SHIPPED → COMPLETED`
- Admin dashboard untuk update status pesanan (F-21)
- Riwayat & detail pesanan per user

### Recommendation Engine
- **F-28 "Produk Serupa"** — content-based similarity dari overlap atribut (grade, seri, timeline)
- **F-29 "Untuk Kamu"** — personalized via implicit feedback (view, wishlist, purchase)
- **F-30 Cold-start fallback** — popularity-based untuk user baru tanpa histori

### Admin
- Product CRUD + upload & kelola foto (Django Admin)
- Manajemen status pesanan via action yang memanggil state machine

---

## Arsitektur Recommendation Engine

Engine mengikuti pola **CQRS-lite** dengan tiga lapis yang dipisah secara fisik:

```
┌─────────────────────────────────────────────────────────┐
│  CAPTURE (write-path)                                   │
│  BehaviorEvent (VIEW / WISHLIST / PURCHASE) — append-only│
│  Wishlist                                               │
└───────────────────────┬─────────────────────────────────┘
                        │ offline, dijadwalkan cron 02:00
                        ▼
┌─────────────────────────────────────────────────────────┐
│  COMPUTE (batch)                                        │
│  python manage.py compute_recommendations               │
│  → transaction.atomic: DELETE lama + bulk_create baru   │
│  → engine/ modules (Python murni, zero ORM coupling)    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  SERVE (read-path)                                      │
│  ProductSimilarity    → F-28, index (source, -score)    │
│  UserRecommendation   → F-29, index (user, -score)      │
│  ProductPopularity    → F-30, index (-score)            │
│  Serving = SELECT ... ORDER BY score LIMIT N            │
│  Komputasi mahal tidak pernah menyentuh request user    │
└─────────────────────────────────────────────────────────┘
```

**Algoritma F-28 (item similarity):**
```
score = (3 × same_series) + (2 × same_timeline) + (1 × same_grade)
```
Hierarki series → timeline bekerja gratis: sepasang kit se-series mendapat `5`, se-timeline mendapat `2`, hanya se-grade mendapat `1`.

**Algoritma F-29 (personalized):**
```
1. Kumpulkan BehaviorEvent user → bobot {VIEW:1, WISHLIST:3, PURCHASE:5}
2. Bangun preference profile per dimensi (max-normalized)
3. Skor kandidat = Σ(dim_weight × profile_affinity)
4. Simpan top-12 per user, kecualikan yang sudah dibeli
```

Bobot adalah **hyperparameter di `settings.py`** — diinjeksikan ke engine saat compute, tidak disimpan di database. Mengubah bobot lalu rerun `compute_recommendations` menghasilkan skor baru tanpa migrasi.

---

## Database Design Highlights

**22 tabel custom** di atas ~10 tabel bawaan Django:

| Modul | Tabel |
|---|---|
| accounts | `User` (email-login), `Address` |
| produk | `Product`, `ProductImage`, `Grade`, `Timeline`, `Series` |
| cart | `Cart`, `CartItem` |
| order | `Order`, `OrderItem`, `ShippingRate`, `Payment` |
| rekomendasi (write) | `BehaviorEvent`, `Wishlist` |
| rekomendasi (serve) | `ProductSimilarity`, `UserRecommendation`, `ProductPopularity` |

**Keputusan desain yang disengaja:**

- **Reference vs Snapshot** — `CartItem` membaca harga live; `OrderItem` membekukan harga/nama/foto saat checkout. Riwayat pembelian tidak ikut berubah saat admin mengedit produk.
- **Order sebagai state machine** — semua transisi status lewat `Order.transition_to()`. Transisi ilegal (mis. `PENDING → SHIPPED`) diblokir di level aplikasi.
- **`timeline` tidak disimpan di `Product`** — diturunkan via `product.series.timeline`, satu sumber kebenaran.
- **Partial unique index** pada `ProductImage.is_primary` — DB-enforced, bukan hanya logika aplikasi.
- **`on_delete` mencerminkan sifat data** — `CASCADE` untuk data ephemeral (cart, derived), `PROTECT` untuk catatan historis (order, order items).

---

## Struktur Project

```
harohub/
├── config/                  # project package
│   └── settings/
│       ├── base.py          # shared, membaca DATABASE_URL
│       ├── development.py   # DEBUG + SQLite fallback
│       └── production.py    # PostgreSQL + whitenoise + storages
├── apps/
│   ├── core/                # abstract models (TimeStampedModel, dll)
│   ├── common/              # validators, generators, templatetags
│   ├── accounts/            # User, Address
│   ├── produk/              # Product catalog
│   ├── cart/                # Cart & CartItem
│   ├── order/               # Order state machine + services.py
│   └── rekomendasi/
│       ├── engine/          # Python murni: similarity.py, profile.py, popularity.py
│       ├── services.py      # serve-time logic + cold-start
│       └── management/commands/compute_recommendations.py
├── templates/
│   ├── partials/            # HTMX fragments global (_<fitur>_<bagian>.html)
│   └── <app>/
└── static/
    ├── src/input.css        # Tailwind source
    └── js/app.js
```

**Arah dependensi** (satu arah, nol siklus):
```
core / common → accounts → produk → cart / order / rekomendasi
```

---

## Setup & Development

### Prerequisites

- Python 3.12+
- [Tailwind CSS standalone CLI](https://github.com/tailwindlabs/tailwindcss/releases) — letakkan binary di root project sebagai `tailwindcss`

### Instalasi

```bash
git clone https://github.com/AryaSeptiaputra/HaroHUB.git
cd HaroHUB

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirments.txt

cp .example.env .env
# isi nilai di .env (lihat bagian Environment Variables)

python manage.py migrate
python manage.py createsuperuser   # login via email
python manage.py runserver
```

### Tailwind (watcher, berdampingan dengan runserver)

```bash
./tailwindcss -i static/src/input.css -o static/css/output.css --watch
```

### Recommendation Engine

```bash
# Jalankan sekali setelah ada data produk & behavior event
python manage.py compute_recommendations

# Produksi: jadwalkan via cron
0 2 * * * python manage.py compute_recommendations
```

---

## Environment Variables

Salin `.example.env` ke `.env` dan isi nilainya:

```env
SECRET_KEY=

# Database — kosongkan untuk SQLite (development)
DATABASE_URL=

# Google Maps Platform
GOOGLE_MAPS_API_KEY_FRONTEND=   # key frontend, restrict by HTTP referrer di GCP
GOOGLE_MAPS_API_KEY_BACKEND=    # key server-side, restrict by IP di GCP

# Django settings module
DJANGO_SETTINGS_MODULE=config.settings.development
```

**Database switching otomatis:** dev tanpa `DATABASE_URL` → SQLite; production dengan `DATABASE_URL` Supabase → PostgreSQL. Zero code change.

---

## API Documentation

DRF + drf-spectacular mengekspos dokumentasi interaktif di:

```
/api/docs/    → Swagger UI
/api/schema/  → OpenAPI schema
```

---

## Catatan Portfolio

Beberapa keputusan sengaja berbeda dari aplikasi komersial — dan ini disadari penuh:

| Keputusan | Alasan |
|---|---|
| Payment & shipping = mock | Setup production credentials kompleks; mock cukup mendemonstrasikan alur transaksi lengkap |
| Tanpa Celery/Redis | Logic rekomendasi adalah kode Python murni yang ingin ditonjolkan; management command cukup, mudah dijelaskan baris demi baris |
| Tanpa reset password | Membutuhkan email service; tidak menambah skill baru yang belum tercakup fitur lain |
| Synthetic seed data | Aplikasi baru belum punya data behavior nyata; seed data untuk keperluan demo |
| Google Maps hanya untuk UX | Koordinat tidak menggerakkan logika bisnis (ongkir mock per-kota); fungsinya demonstrasi integrasi pihak ketiga |

*"Kalau ini production, saya akan migrasi ke Celery + Redis untuk retry mechanism dan monitoring recommendation job."*

---

## License

MIT

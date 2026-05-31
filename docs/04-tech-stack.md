# Tech Stack — HaroHUB

> Platform e-commerce Gunpla full-stack untuk pasar Indonesia. Dirancang sebagai proyek **portfolio** yang menekankan kemampuan **backend engineering** dan **AI / recommendation engineering** — bukan frontend. Frontend hadir secukupnya sebagai "bukti hidup" bahwa backend bekerja end-to-end.

---

## Ringkasan

| Layer | Development | Production |
|---|---|---|
| Bahasa | Python | Python |
| Framework | Django + Django REST Framework | sama |
| Database | SQLite | PostgreSQL (Supabase) |
| Frontend | Django Templates + HTMX + Tailwind CSS | sama |
| Background job | Django Management Command (dijadwalkan via cron) | sama |
| Maps | Google Maps Platform | sama |

Prinsip yang menyatukan seluruh pilihan di atas: **kedalaman teknis di backend & AI, kesederhanaan di tempat lain.** Setiap kompleksitas yang tidak menambah nilai portfolio secara proporsional dipangkas secara sadar.

---

## 1. Bahasa & Framework — Python + Django + DRF

Django dipilih karena fondasi bawaannya langsung memangkas banyak pekerjaan repetitif:

- **ORM yang matang** — model ditulis sekali, SQL di-generate sesuai database. Inilah yang memungkinkan strategi SQLite → PostgreSQL (lihat bagian 3).
- **Auth system bawaan** — password hashing, session, dan decorator `@login_required` sudah tersedia. F-06 dan F-07 berdiri di atas fondasi ini, bukan ditulis dari nol.
- **Admin panel otomatis** — memberi head start besar untuk F-19 (Produk CRUD), F-20 (kelola foto), dan F-21 (manajemen status pesanan).

### Peran DRF dalam arsitektur full-stack

Karena aplikasi ini full-stack Django (bukan decoupled SPA), peran DRF **bergeser** — bukan sebagai primary API layer, melainkan:

- Endpoint JSON untuk panggilan HTMX yang butuh respons partial — autocomplete pencarian (F-03), widget rekomendasi (F-28 / F-29).
- **Bonus portfolio:** dokumentasi API via `drf-spectacular` yang diekspos di `/api/docs/`. Menunjukkan kemampuan membangun API yang consumable oleh client mana pun — nilai plus di mata interviewer.

---

## 2. Arsitektur Aplikasi — Django Full-Stack

**Pilihan: Django Templates + HTMX + Tailwind** (bukan backend API + frontend React/Next terpisah).

Alasannya selaras dengan tujuan portfolio: sebagai backend & AI engineer, yang perlu dibuktikan adalah **kualitas API design, data modeling, dan recommendation engine** — bukan kemampuan React. Frontend cukup menjadi bukti bahwa backend berfungsi. Satu codebase, lebih sederhana, fokus tetap di tempat yang membedakan.

HTMX dipilih untuk interaktivitas (autocomplete, update keranjang, widget rekomendasi) tanpa perlu membangun SPA — partial HTML/JSON dari server sudah cukup.

---

## 3. Database — SQLite (dev) → PostgreSQL (prod)

**Development** memakai SQLite demi kemudahan setup (tanpa service terpisah, file lokal). **Production** memakai PostgreSQL di **Supabase** (free tier, persistent).

### Kenapa production wajib PostgreSQL, bukan SQLite

- **Ephemeral filesystem** — platform deploy modern (Railway/Render/Fly.io) menghapus filesystem tiap redeploy. File SQLite produksi akan hilang setiap deploy — fatal untuk demo interview.
- **Single-writer lock** — SQLite mengunci seluruh database saat menulis. Saat batch job rekomendasi (lapis Compute) menulis ke tabel precomputed, request lain bisa terblokir. PostgreSQL memakai row-level locking. Ini skenario yang **pasti terjadi** di sistem ini, bukan edge case.
- **Persepsi portfolio** — PostgreSQL adalah standar de facto web app; interviewer technical akan menilai pilihan database.

### Strategi migrasi

Migrasi cukup mengganti `ENGINE` di `settings.py` dari `django.db.backends.sqlite3` ke `django.db.backends.postgresql`, lalu jalankan `migrate`. **Model dan migration files tidak berubah** — selama tidak memakai fitur PostgreSQL-specific.

### Aturan portabilitas (dipatuhi selama development)

Agar migrasi mulus, selama dev:

- **Hindari field PostgreSQL-only** — `ArrayField`, `SearchVector`, dan sejenisnya dari `django.contrib.postgres`.
- **`JSONField`** boleh, tapi hindari query-by-key yang berat (perilaku sedikit berbeda antar backend). Desain ini sengaja tidak heavily query JSON.
- **Case sensitivity** — `LIKE` di SQLite case-insensitive secara default, PostgreSQL tidak. Search (F-03) yang "terasa benar" di SQLite perlu di-test ulang di PostgreSQL.
- **`db.sqlite3` masuk `.gitignore`** — jangan commit database dev ke Git.

> Konsekuensi penting: **partial unique index** (dipakai untuk `ProductImage.is_primary`) didukung baik di SQLite maupun PostgreSQL — konsisten dengan janji migrasi ini.

---

## 4. Frontend Styling — Tailwind CSS

Utility-first CSS untuk styling cepat dan konsisten tanpa menulis CSS kustom berlebih. Dipasangkan dengan Django Templates + HTMX.

---

## 5. Background Job — Django Management Command

Recommendation engine membutuhkan perhitungan periodik (similarity matrix, skor per-user). Perhitungan ini dijalankan **offline** sebagai management command, dijadwalkan via cron:

```bash
python manage.py compute_recommendations
```

```cron
0 2 * * *   python manage.py compute_recommendations   # tiap hari jam 02.00
```

### Kenapa management command, bukan Celery / Django-Q

- **Logic rekomendasi adalah kode Python murni** (numpy/pandas/pure Python) — ini yang ingin ditonjolkan sebagai AI engineer, bukan kemampuan konfigurasi Celery.
- **Mudah dijelaskan baris demi baris** di interview — tidak ada "magic", semuanya eksplisit.
- **Nol dependency tambahan** — tidak butuh Redis (broker) atau worker yang harus selalu running.

Celery + Redis disebut sebagai **improvement yang disadari**: *"Kalau ini production, saya akan migrasi ke Celery + Redis untuk retry mechanism dan monitoring."* Menunjukkan paham trade-off, bukan tidak tahu Celery ada.

> Management command ini adalah **lapis Compute** dalam arsitektur write/compute/serve recommendation engine (detail di `database_design.md`).

---

## 6. Maps — Google Maps Platform

Dipakai untuk fitur pin lokasi alamat pengiriman. Yang masuk ke database hanyalah hasil akhir (koordinat + `place_id` + teks alamat); interaksi peta sepenuhnya di frontend.

### Catatan implementasi & operasional

- **`place_id`** — ID unik & stabil dari Google. Terms of Service Google mengizinkan menyimpannya **permanen**, berbeda dari data Places lain yang dibatasi caching-nya (~30 hari). Karena peta ditampilkan di peta Google sendiri (bukan peta non-Google), batasan display ToS otomatis terhindari.
- **Keamanan API key** — key untuk Maps JavaScript terekspos di frontend (tak terhindarkan). **Wajib di-restrict** di Google Cloud Console: HTTP referrer restriction + API restriction. Geocoding server-side memakai **key terpisah** yang di-restrict by IP.
- **Billing** — sejak Juli 2018, semua penggunaan Google Maps Platform mewajibkan billing account aktif, **bahkan dalam free tier**. Per Maret 2025, model harga berubah dari kredit bulanan $200 menjadi batas penggunaan gratis bulanan per SKU. Untuk traffic portfolio, penggunaan hampir pasti tetap di dalam batas gratis, tetapi kartu kredit untuk verifikasi tetap diperlukan saat setup.

> Catatan jujur untuk framing interview: koordinat yang disimpan **tidak menggerakkan logika bisnis apa pun** di build ini (ongkir memakai mock per-kota, tanpa hitung jarak). Fungsinya murni **UX realism** + **demonstrasi integrasi pihak ketiga**. Di production dengan shipping API nyata, koordinat akan menjadi input kalkulasi ongkir berbasis jarak.

---

## Catatan Konteks Portfolio

Beberapa keputusan sengaja berbeda dari aplikasi komersial nyata, dan ini disadari penuh:

- **Payment & shipping = mock** — menyederhanakan setup sambil tetap mendemonstrasikan alur transaksi lengkap.
- **Fitur high-effort / low-demo di-skip** — reset password, integrasi payment/shipping real, kode promo.
- **Recommendation memakai synthetic seed data** — aplikasi baru belum punya data behavior nyata.
- **Fokus pada kedalaman teknis** di area backend & AI, bukan kelengkapan fitur.# Tech Stack — HaroHUB

> Platform e-commerce Gunpla full-stack untuk pasar Indonesia. Dirancang sebagai proyek **portfolio** yang menekankan kemampuan **backend engineering** dan **AI / recommendation engineering** — bukan frontend. Frontend hadir secukupnya sebagai "bukti hidup" bahwa backend bekerja end-to-end.

---

## Ringkasan

| Layer | Development | Production |
|---|---|---|
| Bahasa | Python | Python |
| Framework | Django + Django REST Framework | sama |
| Database | SQLite | PostgreSQL (Supabase) |
| Frontend | Django Templates + HTMX + Tailwind CSS | sama |
| Background job | Django Management Command (dijadwalkan via cron) | sama |
| Maps | Google Maps Platform | sama |

Prinsip yang menyatukan seluruh pilihan di atas: **kedalaman teknis di backend & AI, kesederhanaan di tempat lain.** Setiap kompleksitas yang tidak menambah nilai portfolio secara proporsional dipangkas secara sadar.

---

## 1. Bahasa & Framework — Python + Django + DRF

Django dipilih karena fondasi bawaannya langsung memangkas banyak pekerjaan repetitif:

- **ORM yang matang** — model ditulis sekali, SQL di-generate sesuai database. Inilah yang memungkinkan strategi SQLite → PostgreSQL (lihat bagian 3).
- **Auth system bawaan** — password hashing, session, dan decorator `@login_required` sudah tersedia. F-06 dan F-07 berdiri di atas fondasi ini, bukan ditulis dari nol.
- **Admin panel otomatis** — memberi head start besar untuk F-19 (Produk CRUD), F-20 (kelola foto), dan F-21 (manajemen status pesanan).

### Peran DRF dalam arsitektur full-stack

Karena aplikasi ini full-stack Django (bukan decoupled SPA), peran DRF **bergeser** — bukan sebagai primary API layer, melainkan:

- Endpoint JSON untuk panggilan HTMX yang butuh respons partial — autocomplete pencarian (F-03), widget rekomendasi (F-28 / F-29).
- **Bonus portfolio:** dokumentasi API via `drf-spectacular` yang diekspos di `/api/docs/`. Menunjukkan kemampuan membangun API yang consumable oleh client mana pun — nilai plus di mata interviewer.

---

## 2. Arsitektur Aplikasi — Django Full-Stack

**Pilihan: Django Templates + HTMX + Tailwind** (bukan backend API + frontend React/Next terpisah).

Alasannya selaras dengan tujuan portfolio: sebagai backend & AI engineer, yang perlu dibuktikan adalah **kualitas API design, data modeling, dan recommendation engine** — bukan kemampuan React. Frontend cukup menjadi bukti bahwa backend berfungsi. Satu codebase, lebih sederhana, fokus tetap di tempat yang membedakan.

HTMX dipilih untuk interaktivitas (autocomplete, update keranjang, widget rekomendasi) tanpa perlu membangun SPA — partial HTML/JSON dari server sudah cukup.

---

## 3. Database — SQLite (dev) → PostgreSQL (prod)

**Development** memakai SQLite demi kemudahan setup (tanpa service terpisah, file lokal). **Production** memakai PostgreSQL di **Supabase** (free tier, persistent).

### Kenapa production wajib PostgreSQL, bukan SQLite

- **Ephemeral filesystem** — platform deploy modern (Railway/Render/Fly.io) menghapus filesystem tiap redeploy. File SQLite produksi akan hilang setiap deploy — fatal untuk demo interview.
- **Single-writer lock** — SQLite mengunci seluruh database saat menulis. Saat batch job rekomendasi (lapis Compute) menulis ke tabel precomputed, request lain bisa terblokir. PostgreSQL memakai row-level locking. Ini skenario yang **pasti terjadi** di sistem ini, bukan edge case.
- **Persepsi portfolio** — PostgreSQL adalah standar de facto web app; interviewer technical akan menilai pilihan database.

### Strategi migrasi

Migrasi cukup mengganti `ENGINE` di `settings.py` dari `django.db.backends.sqlite3` ke `django.db.backends.postgresql`, lalu jalankan `migrate`. **Model dan migration files tidak berubah** — selama tidak memakai fitur PostgreSQL-specific.

### Aturan portabilitas (dipatuhi selama development)

Agar migrasi mulus, selama dev:

- **Hindari field PostgreSQL-only** — `ArrayField`, `SearchVector`, dan sejenisnya dari `django.contrib.postgres`.
- **`JSONField`** boleh, tapi hindari query-by-key yang berat (perilaku sedikit berbeda antar backend). Desain ini sengaja tidak heavily query JSON.
- **Case sensitivity** — `LIKE` di SQLite case-insensitive secara default, PostgreSQL tidak. Search (F-03) yang "terasa benar" di SQLite perlu di-test ulang di PostgreSQL.
- **`db.sqlite3` masuk `.gitignore`** — jangan commit database dev ke Git.

> Konsekuensi penting: **partial unique index** (dipakai untuk `ProductImage.is_primary`) didukung baik di SQLite maupun PostgreSQL — konsisten dengan janji migrasi ini.

---

## 4. Frontend Styling — Tailwind CSS

Utility-first CSS untuk styling cepat dan konsisten tanpa menulis CSS kustom berlebih. Dipasangkan dengan Django Templates + HTMX.

---

## 5. Background Job — Django Management Command

Recommendation engine membutuhkan perhitungan periodik (similarity matrix, skor per-user). Perhitungan ini dijalankan **offline** sebagai management command, dijadwalkan via cron:

```bash
python manage.py compute_recommendations
```

```cron
0 2 * * *   python manage.py compute_recommendations   # tiap hari jam 02.00
```

### Kenapa management command, bukan Celery / Django-Q

- **Logic rekomendasi adalah kode Python murni** (numpy/pandas/pure Python) — ini yang ingin ditonjolkan sebagai AI engineer, bukan kemampuan konfigurasi Celery.
- **Mudah dijelaskan baris demi baris** di interview — tidak ada "magic", semuanya eksplisit.
- **Nol dependency tambahan** — tidak butuh Redis (broker) atau worker yang harus selalu running.

Celery + Redis disebut sebagai **improvement yang disadari**: *"Kalau ini production, saya akan migrasi ke Celery + Redis untuk retry mechanism dan monitoring."* Menunjukkan paham trade-off, bukan tidak tahu Celery ada.

> Management command ini adalah **lapis Compute** dalam arsitektur write/compute/serve recommendation engine (detail di `database_design.md`).

---

## 6. Maps — Google Maps Platform

Dipakai untuk fitur pin lokasi alamat pengiriman. Yang masuk ke database hanyalah hasil akhir (koordinat + `place_id` + teks alamat); interaksi peta sepenuhnya di frontend.

### Catatan implementasi & operasional

- **`place_id`** — ID unik & stabil dari Google. Terms of Service Google mengizinkan menyimpannya **permanen**, berbeda dari data Places lain yang dibatasi caching-nya (~30 hari). Karena peta ditampilkan di peta Google sendiri (bukan peta non-Google), batasan display ToS otomatis terhindari.
- **Keamanan API key** — key untuk Maps JavaScript terekspos di frontend (tak terhindarkan). **Wajib di-restrict** di Google Cloud Console: HTTP referrer restriction + API restriction. Geocoding server-side memakai **key terpisah** yang di-restrict by IP.
- **Billing** — sejak Juli 2018, semua penggunaan Google Maps Platform mewajibkan billing account aktif, **bahkan dalam free tier**. Per Maret 2025, model harga berubah dari kredit bulanan $200 menjadi batas penggunaan gratis bulanan per SKU. Untuk traffic portfolio, penggunaan hampir pasti tetap di dalam batas gratis, tetapi kartu kredit untuk verifikasi tetap diperlukan saat setup.

> Catatan jujur untuk framing interview: koordinat yang disimpan **tidak menggerakkan logika bisnis apa pun** di build ini (ongkir memakai mock per-kota, tanpa hitung jarak). Fungsinya murni **UX realism** + **demonstrasi integrasi pihak ketiga**. Di production dengan shipping API nyata, koordinat akan menjadi input kalkulasi ongkir berbasis jarak.

---

## Catatan Konteks Portfolio

Beberapa keputusan sengaja berbeda dari aplikasi komersial nyata, dan ini disadari penuh:

- **Payment & shipping = mock** — menyederhanakan setup sambil tetap mendemonstrasikan alur transaksi lengkap.
- **Fitur high-effort / low-demo di-skip** — reset password, integrasi payment/shipping real, kode promo.
- **Recommendation memakai synthetic seed data** — aplikasi baru belum punya data behavior nyata.
- **Fokus pada kedalaman teknis** di area backend & AI, bukan kelengkapan fitur.
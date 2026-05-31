# Feature Map - HaroHUB

### 3.1 Tabel Fitur Lengkap

> **Legenda Status:** ✅ Selesai · 🔲 Belum (Phase 2) · — Diskip by design

| ID | Fitur | Kategori | Tier | Effort | Nilai Portfolio | Status |
|---|---|---|---|---|---|---|
| F-01 | Product listing + pagination | Katalog | **MVP** | Low | Tinggi | ✅ |
| F-02 | Filter grade, seri & harga | Katalog | **MVP** | Medium | Tinggi | ✅ |
| F-03 | Search dengan autocomplete | Katalog | **MVP** | Medium | Tinggi | ✅ |
| F-04 | Detail produk + image gallery | Katalog | **MVP** | Low | Tinggi | ✅ |
| F-05 | Review & rating produk | Katalog | Phase 2 | Medium | Sedang | 🔲 |
| F-06 | Register & login (email) | Auth | **MVP** | Low | Tinggi | ✅ |
| F-07 | Middleware route protection | Auth | **MVP** | Low | Tinggi | ✅ |
| F-08 | Login via Google OAuth | Auth | Phase 2 | Medium | Sedang | 🔲 |
| F-09 | Reset password via email | Auth | ~~Skip~~ | Medium | Rendah | — |
| F-10 | Keranjang belanja (add/edit/remove) | Cart | **MVP** | Low | Tinggi | ✅ |
| F-11 | Checkout + form alamat pengiriman | Cart | **MVP** | Low | Tinggi | ✅ |
| F-12 | Simulasi pembayaran (mock UI) | Cart | **MVP** | Low | Sedang | ✅ |
| F-13 | Kalkulasi ongkir (mock / flat rate) | Cart | **MVP** | Low | Sedang | ✅ |
| F-14 | Integrasi Midtrans real | Cart | ~~Skip~~ | High | Rendah | — |
| F-15 | Integrasi RajaOngkir real | Cart | ~~Skip~~ | Medium | Rendah | — |
| F-16 | Riwayat pesanan user | Pesanan | **MVP** | Low | Tinggi | ✅ |
| F-17 | Detail & status pesanan | Pesanan | **MVP** | Low | Sedang | ✅ |
| F-18 | Notifikasi email pesanan | Pesanan | Phase 2 | Medium | Rendah | 🔲 |
| F-19 | Produk CRUD (admin) | Admin | **MVP** | Medium | Tinggi | ✅ |
| F-20 | Upload & kelola foto produk | Admin | **MVP** | Medium | Tinggi | ✅ |
| F-21 | Update & manajemen status pesanan | Admin | **MVP** | Low | Tinggi | ✅ |
| F-22 | Dashboard statistik penjualan | Admin | Phase 2 | Medium | Tinggi | 🔲 |
| F-23 | Kode promo & diskon | Admin | ~~Skip~~ | High | Rendah | — |
| F-24 | Responsive design (mobile-first) | UX | **MVP** | Low | Tinggi | ✅ |
| F-25 | Loading skeleton & error states | UX | **MVP** | Low | Tinggi | ✅ |
| F-26 | SEO meta tags dinamis | UX | Phase 2 | Low | Sedang | 🔲 |
| F-27 | Behavior event tracking | Rekomendasi | **MVP** | Low | Tinggi | ✅ |
| F-28 | "Produk Serupa" — item-based similarity | Rekomendasi | **MVP** | Medium | Tinggi | ✅ |
| F-29 | "Untuk Kamu" — personalized recommendations | Rekomendasi | **MVP** | Medium | Tinggi | ✅ |
| F-30 | Cold start / popularity fallback | Rekomendasi | **MVP** | Low | Sedang | ✅ |
| F-31 | Recommendation metrics & logging | Rekomendasi | Phase 2 | Medium | Tinggi | 🔲 |

---

### 3.2 Ringkasan Scope

| Tier | Total | Selesai | Sisa |
|---|---|---|---|
| **MVP** | **21 fitur** | **21 ✅** | 0 |
| **Phase 2** | **6 fitur** | 0 | 6 🔲 |
| **Skip** | **4 fitur** | — | — |
| **Total** | **31 fitur** | **21** | |

**Semua 21 fitur MVP telah diimplementasikan.**

---

### 3.3 Catatan Implementasi per Fitur

| ID | Catatan Implementasi |
|---|---|
| F-01 | `listing_view` · `Paginator(12)` · URL params untuk page |
| F-02 | Filter multi-dimensi di URL params · grade multi-checkbox · series dependent via HTMX |
| F-03 | `search_autocomplete_view` · HTMX partial · trigger ≥2 karakter · max 5 hasil |
| F-04 | `detail_view` · image switcher via JS · thumbnail gallery |
| F-06 | `register_view` + `login_view` · `USERNAME_FIELD = 'email'` · custom `UserManager` |
| F-07 | `@login_required` di semua view privat · `LOGIN_URL = 'accounts:login'` · `?next=` redirect |
| F-10 | `add_to_cart` + `update_item` + `remove_item` · HTMX OOB badge update · quantity capped at stock |
| F-11 | `checkout_view` · address selector · HTMX shipping preview per kota terpilih |
| F-12 | `payment_view` · mock instruksi per metode (Transfer/E-Wallet/QRIS/COD) · konfirmasi satu klik |
| F-13 | `ShippingRate` flat rate per kota · `seed_shipping` 16 kota · dibekukan ke `Order.shipping_cost` |
| F-16 | `order_list_view` · status badge berwarna · link ke detail |
| F-17 | `order_detail_view` · snapshot alamat + finansial + items · state machine timestamps |
| F-19 | `ProductAdmin` · `prepopulated_fields` slug · `list_editable` status/stock |
| F-20 | `ProductImageInline` · `ImageField(upload_to='products/')` · preview thumbnail di admin |
| F-21 | `OrderAdmin` dengan 4 custom actions · memanggil `transition_to()` — tidak pakai `list_editable` pada status |
| F-24 | Tailwind CSS utility-first · responsive grid `grid-cols-2 sm:grid-cols-3 xl:grid-cols-4` di semua listing |
| F-25 | HTMX lazy-load dengan `animate-pulse` skeleton · empty state di semua list view (cart/order/katalog/profil) |
| F-27 | `record_event()` append-only · dipanggil di: product detail (VIEW), confirm_payment (PURCHASE), wishlist_toggle (WISHLIST) |
| F-28 | `ProductSimilarity` precomputed · `widget_similar` HTMX lazy-load di detail · skor = overlap atribut berbobot |
| F-29 | `UserRecommendation` precomputed · `widget_for_you` HTMX lazy-load di listing · profile = implicit feedback max-norm |
| F-30 | `ProductPopularity` precomputed · auto-fallback di `get_user_recommendations()` jika tidak ada data user |

---

### 3.4 Alasan Skip

| ID | Fitur | Alasan |
|---|---|---|
| F-09 | Reset password | Membutuhkan email service; tidak menambah skill baru yang belum tercakup fitur lain |
| F-14 | Midtrans real | Setup production credentials kompleks; mock sudah cukup mendemonstrasikan alur checkout lengkap |
| F-15 | RajaOngkir real | Sama dengan F-14; kalkulasi mock mendemonstrasikan pola yang sama |
| F-23 | Kode promo & diskon | High effort, tidak menambah nilai portfolio secara proporsional untuk scope yang ada |

---

### 3.5 Skill Portfolio yang Terdemonstrasikan

| Skill Area | Fitur Pendukung | Lokasi Kode |
|---|---|---|
| Auth & session management | F-06, F-07 | `apps/accounts/` |
| Full-stack CRUD + API design | F-16, F-17, F-19, F-21 | `apps/order/`, `apps/produk/admin.py` |
| Client-side state management | F-10 (cart state + HTMX OOB) | `apps/cart/` |
| End-to-end transactional flow | F-11, F-12, F-13 | `apps/order/services.py` |
| File upload & storage | F-19, F-20 | `apps/produk/admin.py`, `ProductImage` |
| Database querying & filtering | F-02, F-03 | `apps/produk/views.py` |
| State machine pattern | F-17, F-21 | `apps/order/models.py` · `ALLOWED_TRANSITIONS` |
| Service layer + atomic transactions | F-11, F-12 | `apps/order/services.py` |
| HTMX progressive enhancement | F-02, F-03, F-10, F-28, F-29 | `templates/partials/` |
| Data pipeline & system design | F-27, F-28, F-29, F-30 | `apps/rekomendasi/` |
| Content-based recommendation | F-28, F-29, F-30 | `apps/rekomendasi/engine/` |
| Implicit feedback profiling | F-27, F-29 | `engine/profile.py` · `compute_recommendations` |

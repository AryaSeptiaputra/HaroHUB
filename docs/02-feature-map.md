# Feature Map - HaroHUB

### 3.1 Tabel Fitur Lengkap

| ID | Fitur | Kategori | Tier | Effort | Nilai Portfolio |
|---|---|---|---|---|---|
| F-01 | Product listing + pagination | Katalog | **MVP** | Low | Tinggi |
| F-02 | Filter grade, seri & harga | Katalog | **MVP** | Medium | Tinggi |
| F-03 | Search dengan autocomplete | Katalog | **MVP** | Medium | Tinggi |
| F-04 | Detail produk + image gallery | Katalog | **MVP** | Low | Tinggi |
| F-05 | Review & rating produk | Katalog | Phase 2 | Medium | Sedang |
| F-06 | Register & login (email) | Auth | **MVP** | Low | Tinggi |
| F-07 | Middleware route protection | Auth | **MVP** | Low | Tinggi |
| F-08 | Login via Google OAuth | Auth | Phase 2 | Medium | Sedang |
| F-09 | Reset password via email | Auth | ~~Skip~~ | Medium | Rendah |
| F-10 | Keranjang belanja (add/edit/remove) | Cart | **MVP** | Low | Tinggi |
| F-11 | Checkout + form alamat pengiriman | Cart | **MVP** | Low | Tinggi |
| F-12 | Simulasi pembayaran (mock UI) | Cart | **MVP** | Low | Sedang |
| F-13 | Kalkulasi ongkir (mock / flat rate) | Cart | **MVP** | Low | Sedang |
| F-14 | Integrasi Midtrans real | Cart | ~~Skip~~ | High | Rendah |
| F-15 | Integrasi RajaOngkir real | Cart | ~~Skip~~ | Medium | Rendah |
| F-16 | Riwayat pesanan user | Pesanan | **MVP** | Low | Tinggi |
| F-17 | Detail & status pesanan | Pesanan | **MVP** | Low | Sedang |
| F-18 | Notifikasi email pesanan | Pesanan | Phase 2 | Medium | Rendah |
| F-19 | Produk CRUD (admin) | Admin | **MVP** | Medium | Tinggi |
| F-20 | Upload & kelola foto produk | Admin | **MVP** | Medium | Tinggi |
| F-21 | Update & manajemen status pesanan | Admin | **MVP** | Low | Tinggi |
| F-22 | Dashboard statistik penjualan | Admin | Phase 2 | Medium | Tinggi |
| F-23 | Kode promo & diskon | Admin | ~~Skip~~ | High | Rendah |
| F-24 | Responsive design (mobile-first) | UX | **MVP** | Low | Tinggi |
| F-25 | Loading skeleton & error states | UX | **MVP** | Low | Tinggi |
| F-26 | SEO meta tags dinamis | UX | Phase 2 | Low | Sedang |
| F-27 | Behavior event tracking | Rekomendasi | **MVP** | Low | Tinggi |
| F-28 | "Produk Serupa" — item-based similarity | Rekomendasi | **MVP** | Medium | Tinggi |
| F-29 | "Untuk Kamu" — personalized recommendations | Rekomendasi | **MVP** | Medium | Tinggi |
| F-30 | Cold start / popularity fallback | Rekomendasi | **MVP** | Low | Sedang |
| F-31 | Recommendation metrics & logging | Rekomendasi | Phase 2 | Medium | Tinggi |

### 3.2 Ringkasan Scope

| Tier | Jumlah | Keterangan |
|---|---|---|
| **MVP** | **21 fitur** | Core yang harus selesai untuk demo end-to-end |
| **Phase 2** | **6 fitur** | Ditambahkan setelah MVP solid |
| **Skip** | **4 fitur** | Sadar tidak dibangun, lihat alasan di bawah |
| **Total** | **31 fitur** | |

### 3.3 Alasan Skip

| ID | Fitur | Alasan |
|---|---|---|
| F-09 | Reset password | Membutuhkan email service; tidak menambah skill baru yang belum tercakup fitur lain |
| F-14 | Midtrans real | Setup production credentials kompleks; mock sudah cukup mendemonstrasikan alur checkout lengkap |
| F-15 | RajaOngkir real | Sama dengan F-14; kalkulasi mock mendemonstrasikan pola yang sama |
| F-23 | Kode promo & diskon | High effort, tidak menambah nilai portfolio secara proporsional untuk scope yang ada |

### 3.4 Skill Portfolio yang Terdemonstrasikan

| Skill Area | Fitur Pendukung |
|---|---|
| Auth & session management | F-06, F-07 |
| Full-stack CRUD + API design | F-16, F-17, F-19, F-21 |
| Client-side state management | F-10 (cart state dengan persistence) |
| End-to-end transactional flow | F-11, F-12, F-13 |
| File upload & CDN integration | F-19, F-20 |
| Database querying & filtering | F-02, F-03 |
| UI/UX & responsive design | F-04, F-24, F-25 |
| Data pipeline & system design | F-27, F-28, F-29, F-30 |
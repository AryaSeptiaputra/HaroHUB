# MVP Feature Specifications - HaroHUB

> Setiap fitur memiliki **User Story** dan **Acceptance Criteria (AC)**. AC berfungsi sebagai checklist verifikasi setelah implementasi.

---

### Katalog

#### F-01 · Product Listing + Pagination

**User Story**
Sebagai pengunjung, saya ingin melihat daftar produk Gunpla yang tersedia dalam grid, agar saya bisa browse dan menemukan produk yang menarik.

**Acceptance Criteria**
- [ ] Grid produk menampilkan 12 item per halaman secara default
- [ ] Setiap card menampilkan: foto utama, nama produk, grade badge, harga, status stok
- [ ] Pagination menggunakan URL params (`?page=2`) agar bisa di-bookmark dan di-share
- [ ] Loading skeleton tampil selama data di-fetch
- [ ] Empty state dengan CTA tampil jika tidak ada produk yang tersedia

---

#### F-02 · Filter Grade, Seri & Harga

**User Story**
Sebagai kolektor, saya ingin memfilter produk berdasarkan grade, timeline, seri, dan rentang harga, agar saya bisa menemukan produk yang sesuai preferensi dengan cepat.

**Acceptance Criteria**
- [ ] Filter grade: multi-select checkbox — EG, HG, RG, MG, PG, SD, Metal Build, Figure-Rise
- [ ] Filter timeline: pilihan UC, AC, CE, AD, PD, AS, BF, SD
- [ ] Filter seri: list yang muncul hanya setelah timeline dipilih (dependent)
- [ ] Filter harga: range slider dengan input angka manual (min / max)
- [ ] Filter ketersediaan: toggle Ready Stock / Pre-order
- [ ] Semua filter aktif tampil sebagai chip / badge yang bisa di-remove satu per satu
- [ ] State filter disimpan di URL params — bukan di local state — agar bisa di-bookmark
- [ ] Tombol "Reset Semua Filter" menghapus semua params aktif sekaligus

---

#### F-03 · Search dengan Autocomplete

**User Story**
Sebagai pembeli, saya ingin mengetik nama model dan mendapat saran produk secara real-time, agar saya bisa menemukan produk spesifik tanpa harus scroll.

**Acceptance Criteria**
- [ ] Dropdown saran muncul setelah input mencapai ≥ 2 karakter
- [ ] Menampilkan maksimal 5 saran, masing-masing dengan: foto thumbnail, nama produk, grade badge
- [ ] Klik saran langsung navigasi ke halaman detail produk tersebut
- [ ] Tekan Enter atau klik ikon search navigasi ke halaman hasil pencarian penuh
- [ ] State "Produk tidak ditemukan" tampil jika tidak ada hasil yang cocok
- [ ] Input menggunakan debounce 300ms untuk mengurangi jumlah API call
- [ ] Navigasi keyboard: tombol ↑ ↓ untuk berpindah antar saran, Esc untuk menutup

---

#### F-04 · Detail Produk + Image Gallery

**User Story**
Sebagai calon pembeli, saya ingin melihat detail lengkap sebuah produk beserta foto dari berbagai sudut, agar saya bisa membuat keputusan pembelian yang tepat.

**Acceptance Criteria**
- [ ] Gallery: satu foto utama besar + strip thumbnail di bawah; klik thumbnail mengganti foto utama
- [ ] Informasi produk: nama, grade, skala, seri, timeline, harga (format Rupiah), status stok, kondisi
- [ ] Tombol "Tambah ke Keranjang" aktif jika stok tersedia; disabled dengan tooltip jika stok habis
- [ ] Tombol "Tambah ke Wishlist" untuk user yang sudah login, bisa di-toggle
- [ ] Breadcrumb navigasi: Beranda › Katalog › [Nama Produk]
- [ ] Section "Produk Serupa" (F-28) tampil di bagian bawah halaman
- [ ] URL menggunakan slug produk, bukan numeric ID

---

### Auth

#### F-06 · Register & Login (Email)

**User Story**
Sebagai pengunjung, saya ingin membuat akun dan login dengan email, agar saya bisa melakukan pembelian, menyimpan wishlist, dan melacak pesanan saya.

**Acceptance Criteria**
- [ ] Form register: nama lengkap, email, password dengan konfirmasi (min. 8 karakter)
- [ ] Validasi format email dan kekuatan password berjalan di sisi client dan server
- [ ] Pesan error yang spesifik per kasus: "Email sudah terdaftar", "Password salah", "Email tidak valid"
- [ ] Setelah login berhasil, user diarahkan kembali ke halaman yang sebelumnya dituju
- [ ] Rate limiting: maksimal 5 percobaan login gagal per 15 menit dari IP yang sama

---

#### F-07 · Middleware Route Protection

**User Story**
Sebagai sistem, saya perlu memastikan halaman dan API tertentu hanya bisa diakses oleh pengguna yang terautentikasi atau memiliki role yang sesuai, agar data dan aksi sensitif terlindungi.

**Acceptance Criteria**
- [ ] Halaman `/checkout`, `/orders/*`, `/profile` redirect ke `/login` jika tidak terautentikasi
- [ ] Redirect ke login menyertakan `callbackUrl` sehingga user kembali ke halaman asal setelah login
- [ ] Halaman `/admin/*` hanya bisa diakses user dengan role `ADMIN`; tampilkan 403 jika bukan admin
- [ ] API routes di `/api/admin/*` mengembalikan status 401 jika tidak login, 403 jika bukan admin
- [ ] Proteksi berjalan sebelum halaman di-render (middleware level)

---

### Cart & Checkout

#### F-10 · Keranjang Belanja

**User Story**
Sebagai pembeli, saya ingin menambahkan produk ke keranjang, mengubah jumlahnya, dan menghapusnya, agar saya bisa mengumpulkan produk sebelum memutuskan membeli.

**Acceptance Criteria**
- [ ] Produk bisa ditambahkan ke cart dari halaman listing (F-01) maupun detail produk (F-04)
- [ ] Cart user yang login tersimpan di database dan persisten lintas device
- [ ] Cart guest tersimpan di localStorage; di-merge ke user cart saat guest tersebut login
- [ ] Quantity bisa diubah via tombol `+` / `−` dan input langsung
- [ ] Item bisa dihapus satu per satu dari cart
- [ ] Badge di navbar menampilkan total item di cart dan update secara real-time
- [ ] Tidak bisa menambahkan item melebihi jumlah stok yang tersedia

---

#### F-11 · Checkout + Form Alamat Pengiriman

**User Story**
Sebagai pembeli, saya ingin mengisi alamat pengiriman dan melihat ringkasan pesanan sebelum konfirmasi, agar saya yakin pesanan sudah benar sebelum membayar.

**Acceptance Criteria**
- [ ] Form alamat: nama penerima, nomor HP, alamat lengkap, kota, provinsi, kode pos
- [ ] User bisa memilih dari alamat tersimpan di profil atau mengisi alamat baru
- [ ] Ada opsi untuk menyimpan alamat baru ke profil
- [ ] Ringkasan pesanan menampilkan: daftar produk, qty, subtotal per item, ongkir, total akhir
- [ ] Pilihan metode pengiriman dengan perkiraan lama pengiriman (data mock)
- [ ] Submit pesanan membuat record di tabel orders, mengurangi stok produk, dan redirect ke halaman pembayaran

---

#### F-12 · Simulasi Pembayaran (Mock)

**User Story**
Sebagai pengguna yang menjalankan demo, saya ingin bisa mensimulasikan proses pembayaran end-to-end tanpa payment gateway nyata, agar seluruh alur transaksi bisa didemonstrasikan secara lengkap.

**Acceptance Criteria**
- [ ] Halaman mock payment menampilkan ringkasan: order ID, daftar produk, dan total yang harus dibayar
- [ ] Tombol "Bayar Sekarang" mensimulasikan proses dengan loading animation selama 2–3 detik
- [ ] Setelah simulasi berhasil: status order berubah ke `PAID`, redirect ke halaman konfirmasi pesanan
- [ ] Tombol "Batalkan Pembayaran" mengubah status order ke `CANCELLED`
- [ ] Banner yang jelas menyatakan ini adalah mode simulasi — tidak ada transaksi keuangan nyata

---

#### F-13 · Kalkulasi Ongkir (Mock)

**User Story**
Sebagai pembeli, saya ingin melihat pilihan ekspedisi beserta estimasi biaya sebelum checkout, agar saya bisa memilih opsi pengiriman yang sesuai.

**Acceptance Criteria**
- [ ] Tiga pilihan ekspedisi dengan harga yang di-hardcode: JNE REG, J&T Express, SiCepat REG
- [ ] Setiap opsi menampilkan: nama ekspedisi, biaya, estimasi hari tiba
- [ ] Total pesanan diperbarui otomatis saat ekspedisi dipilih
- [ ] Catatan kecil bahwa harga ongkir adalah estimasi untuk keperluan demo

---

### Pesanan

#### F-16 · Riwayat Pesanan

**User Story**
Sebagai pembeli, saya ingin melihat semua pesanan yang pernah saya buat beserta statusnya, agar saya bisa memantau dan mereview riwayat pembelian saya.

**Acceptance Criteria**
- [ ] List pesanan diurutkan dari yang paling baru
- [ ] Setiap item menampilkan: order ID singkat, tanggal, total, status badge berwarna, thumbnail produk
- [ ] Badge status menggunakan warna berbeda: Pending (abu), Paid (biru), Processing (kuning), Shipped (ungu), Delivered (hijau), Cancelled (merah)
- [ ] Klik item pesanan navigasi ke halaman detail (F-17)
- [ ] Empty state dengan tombol "Mulai Belanja" tampil untuk user yang belum pernah order

---

#### F-17 · Detail & Status Pesanan

**User Story**
Sebagai pembeli, saya ingin melihat detail lengkap dan timeline status sebuah pesanan, agar saya tahu perkembangan pesanan saya secara akurat.

**Acceptance Criteria**
- [ ] Informasi header: order ID, tanggal dibuat, ekspedisi yang dipilih, metode pembayaran
- [ ] Alamat pengiriman ditampilkan lengkap
- [ ] List item pesanan: foto, nama produk, grade, harga satuan, qty, subtotal per item
- [ ] Ringkasan biaya: subtotal produk, ongkir, total akhir
- [ ] Timeline status visual berupa stepper: Pending → Paid → Processing → Shipped → Delivered
- [ ] Nomor resi ditampilkan dan bisa di-copy jika status sudah `SHIPPED`
- [ ] Tombol "Hubungi Admin" sebagai link ke WhatsApp atau email yang dikonfigurasi

---

### Admin

#### F-19 · Produk CRUD

**User Story**
Sebagai admin, saya ingin bisa menambahkan, mengedit, dan menghapus produk dari katalog, agar inventaris toko selalu akurat dan up-to-date.

**Acceptance Criteria**
- [ ] Form tambah / edit produk mencakup: nama, slug, deskripsi, grade, timeline, series, skala, harga (IDR), stok, kondisi, status produk
- [ ] Slug di-generate otomatis dari nama produk, namun bisa diedit manual
- [ ] Validasi slug unik secara real-time saat diketik
- [ ] Edit produk menampilkan form yang sudah terisi dengan data yang ada (pre-filled)
- [ ] Hapus produk bersifat soft delete — produk tidak dihapus permanen dari database
- [ ] Dialog konfirmasi muncul sebelum aksi hapus dieksekusi
- [ ] Halaman list produk admin dilengkapi search by nama dan filter by status

---

#### F-20 · Upload & Kelola Foto Produk

**User Story**
Sebagai admin, saya ingin mengupload beberapa foto untuk tiap produk dan menentukan foto utamanya, agar tampilan produk di katalog terlihat menarik dan informatif.

**Acceptance Criteria**
- [ ] Multi-file upload dengan batas maksimal 5 foto per produk
- [ ] Preview foto tampil sebelum upload dikonfirmasi
- [ ] Foto di-upload ke Cloudinary; URL hasil upload disimpan di database
- [ ] Admin bisa menandai satu foto sebagai "foto utama" yang ditampilkan di catalog card
- [ ] Admin bisa menghapus foto individual tanpa menghapus foto lainnya
- [ ] Validasi file: format JPEG / PNG / WebP saja, ukuran maksimal 5 MB per file

---

#### F-21 · Manajemen Status Pesanan

**User Story**
Sebagai admin, saya ingin mengubah status pesanan dan memasukkan nomor resi, agar pembeli bisa memantau perkembangan pesanan mereka.

**Acceptance Criteria**
- [ ] Tabel semua pesanan dengan kolom: order ID, nama pembeli, total, status, tanggal dibuat
- [ ] Tabel bisa difilter berdasarkan status dan diurutkan berdasarkan tanggal
- [ ] Status pesanan bisa diperbarui via dropdown dengan validasi transisi yang sah
- [ ] Field input nomor resi muncul ketika status diubah ke `SHIPPED`
- [ ] Setiap perubahan status tersimpan di tabel history (ditampilkan di timeline F-17)
- [ ] Toast notification muncul saat update status berhasil disimpan

**Transisi status yang valid:**
```
PENDING → PAID → PROCESSING → SHIPPED → DELIVERED
   ↓         ↓
CANCELLED  CANCELLED
```

---

### UX & Polish

#### F-24 · Responsive Design (Mobile-First)

**User Story**
Sebagai pengguna yang mengakses dari HP, saya ingin semua halaman berfungsi dengan baik di layar kecil, agar pengalaman belanja saya tetap nyaman.

**Acceptance Criteria**
- [ ] Semua halaman fungsional dan tidak ada elemen yang terpotong di viewport 375px hingga 1440px
- [ ] Navbar berubah menjadi hamburger menu di mobile; full navigation bar di desktop
- [ ] Product grid: 2 kolom di mobile, 3 di tablet, 4 di desktop
- [ ] Panel filter: tampil sebagai bottom sheet di mobile, sidebar di desktop
- [ ] Semua area yang bisa diklik atau di-tap memiliki ukuran minimal 44×44px
- [ ] Tidak ada horizontal scrollbar yang muncul di viewport mobile

---

#### F-25 · Loading Skeleton & Error States

**User Story**
Sebagai pengguna, saya ingin mendapat umpan balik visual yang jelas saat data sedang dimuat atau terjadi kesalahan, agar saya tidak bingung dengan kondisi aplikasi.

**Acceptance Criteria**
- [ ] Skeleton loading tampil untuk: product grid, product detail, order list, search results, recommendation section
- [ ] Error boundary terpasang di setiap halaman utama — menampilkan pesan ramah, bukan raw error
- [ ] Halaman 404 custom untuk produk atau pesanan yang tidak ditemukan
- [ ] Toast / snackbar error tampil untuk aksi yang gagal: gagal tambah ke cart, gagal checkout, gagal load data
- [ ] Empty state dengan ilustrasi dan call-to-action untuk: cart kosong, pencarian tanpa hasil, riwayat pesanan kosong

---

### Sistem Rekomendasi

> **⚠ AI Context Note:** Sistem rekomendasi menggunakan **content-based filtering dengan implicit feedback**. Tiga sinyal behavior dengan bobot berbeda: `view` (bobot 1), `wishlist` (bobot 3), `purchase` (bobot 5). Profil preferensi dibangun dari akumulasi skor per dimensi atribut produk (grade, timeline, series). Komputasi berjalan sebagai batch job periodik — bukan real-time — dan hasilnya disimpan di tabel terpisah untuk performa read yang optimal.

---

#### F-27 · Behavior Event Tracking

**User Story**
Sebagai sistem, saya perlu mencatat setiap interaksi bermakna antara pengguna dan produk, agar recommendation engine memiliki cukup data untuk membangun profil preferensi yang akurat.

**Events yang Dicatat**

| Event Type | Kapan Di-fire | Bobot |
|---|---|---|
| `product_viewed` | User yang login membuka halaman detail produk (F-04) | 1 |
| `product_wishlisted` | User menambahkan atau menghapus produk dari wishlist | 3 |
| `product_purchased` | Status order berubah ke `PAID` di sisi server | 5 |

**Acceptance Criteria**
- [ ] Event `product_viewed` di-fire di server side saat halaman F-04 di-render untuk authenticated user
- [ ] Event `product_wishlisted` di-fire saat user mengklik tombol wishlist di F-04
- [ ] Event `product_purchased` di-fire di server side saat payment mock dikonfirmasi berhasil
- [ ] Setiap event menyimpan: user_id, product_id, event_type, timestamp
- [ ] Logging bersifat asynchronous / fire-and-forget — tidak boleh memblokir UI atau response API
- [ ] Deduplication: event `product_viewed` dari user dan produk yang sama dalam satu jam diabaikan

---

#### F-28 · "Produk Serupa" — Item-Based Similarity

**User Story**
Sebagai pembeli, saya ingin melihat produk-produk yang mirip di halaman detail, agar saya bisa menemukan alternatif atau varian lain tanpa harus kembali ke katalog dan mencari ulang.

**Cara Kerja**

Dua produk dianggap "serupa" berdasarkan shared attributes berikut:

| Kondisi | Poin Similarity |
|---|---|
| Series sama | +50 |
| Timeline sama (jika series berbeda) | +20 |
| Grade sama | +30 |

Catatan: Jika series sudah sama, skor timeline **tidak** ditambahkan untuk menghindari double-counting hierarki parent-child.

Tabel similarity adalah **pre-computed** dan diregenerasi saat ada produk baru atau produk diperbarui.

**Acceptance Criteria**
- [ ] Section "Produk Serupa" menampilkan 4–6 produk di halaman F-04
- [ ] Produk diurutkan berdasarkan similarity score dari tertinggi ke terendah
- [ ] Produk yang sedang dilihat tidak muncul di daftar
- [ ] Produk dengan stok 0 atau status `DISCONTINUED` tidak ditampilkan
- [ ] Jika hasil kurang dari 4, fallback ke produk lain dalam timeline yang sama
- [ ] Tabel similarity diperbarui setiap kali admin menambah atau mengedit produk (F-19)

---

#### F-29 · "Untuk Kamu" — Personalized Recommendations

**User Story**
Sebagai pembeli dengan riwayat interaksi, saya ingin melihat rekomendasi produk yang dipersonalisasi di homepage, agar saya bisa menemukan produk baru yang relevan tanpa harus aktif mencari.

**Cara Kerja**

**Step 1 — Bangun profil preferensi user** dari tabel `user_events`:
```
Untuk setiap event:
  recency_factor = 1.0  jika event < 30 hari lalu
                   0.5  jika event 31–90 hari lalu
                   0.2  jika event > 90 hari lalu

  skor[grade][product.grade]             += bobot_event × recency_factor
  skor[timeline][product.timeline_id]    += bobot_event × recency_factor
  skor[series][product.series]           += bobot_event × recency_factor
```

**Step 2 — Hitung skor relevansi tiap kandidat produk:**
```
relevance_score =
  (skor[series][product.series]            × 0.50) +
  (skor[timeline][product.timeline_id]     × 0.30) +
  (skor[grade][product.grade]              × 0.20)
```

**Step 3 — Filter dan ranking:**
- Exclude produk yang sudah pernah dibeli user
- Exclude produk stok 0 atau status `DISCONTINUED`
- Diversifikasi hasil: maksimal 60% dari satu series yang sama
- Ambil top-12 produk dengan skor tertinggi

**Acceptance Criteria**
- [ ] Section "Untuk Kamu" tampil di homepage hanya untuk user login yang memiliki ≥ 3 events
- [ ] Menampilkan 8–12 produk dalam horizontal scroll card
- [ ] Produk yang sudah pernah dibeli user tidak muncul dalam rekomendasi
- [ ] Rekomendasi diperbarui minimal setiap 24 jam melalui batch job
- [ ] Jika user memiliki < 3 events, tampilkan F-30 (cold start fallback) sebagai gantinya

---

#### F-30 · Cold Start / Popularity Fallback

**User Story**
Sebagai pengunjung baru atau user dengan interaksi yang masih sedikit, saya ingin tetap melihat konten produk yang relevan dan menarik di homepage, agar pengalaman pertama saya di toko ini tetap berguna.

**Cara Kerja**

Hitung popularity score untuk tiap produk berdasarkan total weighted events dalam 7 hari terakhir:
```
popularity_score = SUM(bobot_event) untuk semua events dalam 7 hari terakhir
```

**Acceptance Criteria**
- [ ] Ditampilkan untuk: user tidak login, atau user dengan < 3 events di tabel user_events
- [ ] Label yang ditampilkan adalah "Trending Minggu Ini" — bukan "Untuk Kamu"
- [ ] Produk trending dikelompokkan per grade: "HG Populer", "MG Populer", dst.
- [ ] Setiap kelompok grade menampilkan 4–6 produk dengan popularity score tertinggi
- [ ] Data trending diperbarui setiap 24 jam bersamaan dengan batch job F-29
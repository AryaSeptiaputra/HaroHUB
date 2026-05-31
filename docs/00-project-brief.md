# Project Brief - HaroHUB

### Ringkasan

GunplaStore adalah platform e-commerce full-stack untuk penjualan Gunpla (Gundam Plastic Model Kit) yang ditargetkan untuk pasar Indonesia. Dibangun sebagai proyek portfolio yang mendemonstrasikan kemampuan full-stack development, system design thinking melalui recommendation engine berbasis perilaku pengguna, dan penerapan modern web technologies dalam satu produk yang kohesif.

### Goals

**Portfolio Goals**
- Mendemonstrasikan kemampuan full-stack dalam satu proyek yang dapat di-demo secara end-to-end
- Menunjukkan pemahaman system design melalui recommendation engine berbasis implicit feedback
- Menunjukkan code quality, arsitektur yang terstruktur, dan engineering judgment
- Menghasilkan proyek yang bisa dijelaskan secara teknis dan bisnis dalam interview

**Product Goals**
- Pengalaman belanja Gunpla yang intuitif untuk pembeli di Indonesia
- Sistem rekomendasi yang mempelajari preferensi pengguna dari perilaku nyata
- Admin dashboard yang functional untuk manajemen katalog dan fulfillment pesanan

### Target Pengguna

| Persona | Deskripsi | Kebutuhan Utama |
|---|---|---|
| **Pembeli Pemula** | Baru mengenal Gunpla, belum familiar dengan perbedaan grade dan seri | Panduan memilih, rekomendasi yang relevan, informasi produk yang jelas |
| **Kolektor Aktif** | Sudah punya preferensi grade dan seri tertentu, tahu apa yang dicari | Filter yang powerful, rekomendasi personal, stok real-time |
| **Admin Toko** | Mengelola katalog, inventaris, dan fulfillment pesanan | Dashboard yang efisien, manajemen produk dan foto yang mudah |

### Konteks Portfolio

Proyek ini **bukan** untuk produksi nyata. Beberapa keputusan sengaja dibuat berbeda dari aplikasi komersial:

- Payment gateway dan shipping API menggunakan **simulasi (mock)** untuk menyederhanakan setup sambil tetap mendemonstrasikan alur transaksi lengkap
- Fitur dengan kompleksitas tinggi namun nilai demo rendah (promo codes, reset password, real payment integration) di-skip secara sadar
- Sistem rekomendasi menggunakan **synthetic seed data** untuk keperluan demo karena aplikasi baru tidak punya data behavior nyata
- Fokus pada **kedalaman teknis** di area tertentu, bukan kelengkapan fitur
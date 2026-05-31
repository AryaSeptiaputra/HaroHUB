# Domain Knowledge - HaroHUB

> **⚠ AI Context Note:** Bagian ini wajib disertakan sebagai konteks saat meminta AI mengerjakan fitur apapun yang berhubungan dengan produk, kategori, filter, atau sistem rekomendasi.

### 2.1 Grade — Tingkatan Produk Gunpla

Grade adalah sistem klasifikasi resmi dari Bandai yang menentukan skala, tingkat detail, dan kompleksitas perakitan sebuah kit.

| Grade | Skala | Deskripsi | Target Pembeli |
|---|---|---|---|
| **Entry Grade (EG)** | Varies | Snap-fit tanpa lem, tidak perlu cat, harga paling terjangkau | Pemula mutlak |
| **High Grade (HG)** | 1/144 | Entry level paling populer, detail cukup, overan semua kalangan | Semua level |
| **Real Grade (RG)** | 1/144 | Detail tinggi dengan internal frame di skala 1/144, butuh ketelitian | Intermediate |
| **Master Grade (MG)** | 1/100 | Detail sangat lengkap dengan inner frame penuh, sendi yang kompleks | Intermediate–Advanced |
| **Perfect Grade (PG)** | 1/60 | Kelas premium tertinggi, konstruksi paling kompleks dan terbesar | Advanced / Collector |
| **Super Deformed (SD)** | Non-scale | Chibi / imut, proporsi tidak realistis, cocok untuk hadiah | Casual / Gift |
| **Metal Build** | Non-scale | Die-cast premium, kolektibel pajangan, bukan kit rakit biasa | High-end Collector |
| **Figure-Rise Standard** | Non-scale | Figure karakter anime (bukan mecha), snap-fit | Fans karakter |

### 2.2 Timeline — Universe Gundam

Timeline adalah "semesta" tempat sebuah seri Gundam berlangsung. Satu timeline bisa memiliki banyak seri. Ini adalah atribut penting untuk sistem rekomendasi karena pengguna yang menyukai satu seri biasanya tertarik dengan seri lain dalam timeline yang sama.

| Timeline ID | Nama Lengkap | Seri yang Termasuk |
|---|---|---|
| `UC` | Universal Century | Mobile Suit Gundam 0079, Zeta Gundam, Gundam ZZ, Char's Counterattack, F91, Victory, Unicorn, Hathaway's Flash |
| `AC` | After Colony | Gundam Wing, Endless Waltz |
| `CE` | Cosmic Era | Gundam SEED, Gundam SEED Destiny, Gundam SEED Freedom |
| `AD` | Anno Domini | Gundam 00, 00 The Movie |
| `PD` | Post Disaster | Iron-Blooded Orphans |
| `AS` | Ad Stella | The Witch from Mercury |
| `BF` | Build Fighters | Build Fighters, Build Divers, Build Divers Re:Rise |
| `SD` | SD World | SD Gundam World Heroes, Sangoku Soketsuden |

**Hierarki:** Series adalah turunan dari Timeline.
Contoh: Series *"Gundam SEED"* adalah bagian dari Timeline *"CE" (Cosmic Era)*.
Contoh: Series *"Iron-Blooded Orphans"* adalah bagian dari Timeline *"PD" (Post Disaster)*.

### 2.3 Atribut Produk untuk Sistem Rekomendasi

Tiga atribut berikut adalah fondasi dari recommendation engine. Nilai-nilai ini harus konsisten di seluruh codebase:

```
product.grade        → "EG" | "HG" | "RG" | "MG" | "PG" | "SD" | "MetalBuild" | "FigureRise"
product.timeline_id  → "UC" | "AC" | "CE" | "AD" | "PD" | "AS" | "BF" | "SD"
product.series       → string bebas, contoh: "Gundam SEED" | "Gundam 00" | "Iron-Blooded Orphans"
```

### 2.4 Status & Kondisi Produk

```
Status produk:
  ACTIVE        → Tersedia untuk dibeli, stok ada
  PRE_ORDER     → Bisa dipesan, belum tersedia / belum rilis
  DISCONTINUED  → Tidak diproduksi lagi, tidak ditampilkan di rekomendasi

Kondisi produk:
  SEALED        → Produk baru, segel pabrik utuh
  PRE_OWNED     → Produk bekas, kondisi dijelaskan di deskripsi
```

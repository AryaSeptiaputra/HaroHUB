# Rancangan Database — HaroHUB

> Rancangan model data untuk platform e-commerce Gunpla. Disusun sebagai **5 modul Django** di atas ~10 tabel bawaan Django (auth, session, admin, content type, migrations) yang ter-generate otomatis sejak `migrate` pertama.
>
> Catatan database: **SQLite untuk development, PostgreSQL (Supabase) untuk production.** Semua keputusan di bawah menjaga portabilitas antar-keduanya (lihat `tech_stack.md` bagian 3).

---

## Daftar Isi

1. [Prinsip Desain Lintas-Tabel](#prinsip-desain-lintas-tabel)
2. [Modul `accounts`](#modul-accounts)
3. [Modul `produk`](#modul-produk)
4. [Modul `cart`](#modul-cart)
5. [Modul `order`](#modul-order)
6. [Modul `rekomendasi`](#modul-rekomendasi)
7. [Inventaris Tabel](#inventaris-tabel)
8. [Konfigurasi](#konfigurasi)

---

## Prinsip Desain Lintas-Tabel

Lima benang merah ini konsisten di seluruh skema. Memahaminya membuat tiap keputusan per-tabel terasa koheren, bukan ad hoc.

### 1. Reference vs Snapshot

Data yang merujuk entitas lain dibagi menjadi dua sifat:

- **Reference** — tautan hidup (FK), selalu mencerminkan keadaan terkini.
- **Snapshot** — nilai yang **dibekukan** pada satu momen, kebal terhadap perubahan sumbernya di kemudian hari.

| Entitas | Sifat | Implementasi |
|---|---|---|
| `Address.place_id` | Reference | fetch ulang dari Google kapan saja |
| `CartItem` | Reference (live) | harga dibaca live dari `product.price` |
| `OrderItem` | Reference **+** Snapshot | FK ke product **dan** field harga/nama/foto yang beku |
| `Order` (alamat) | Snapshot | kolom `shipping_*` yang dibekukan |
| `Order.shipping_cost` | Snapshot | dibaca dari `ShippingRate`, lalu beku |

Kunci pemahaman: **snapshot melindungi dari mutasi field yang mutable, bukan sekadar dari penghapusan.** Harga produk bisa diubah admin; tanpa snapshot, riwayat pesanan akan "berbohong" tentang apa yang sebenarnya dibayar pelanggan.

### 2. `on_delete` mencerminkan sifat data

- **CASCADE** — untuk data yang *dimiliki* parent (hapus parent → anak ikut) atau data *ephemeral/disposable* (cart, derived data).
- **PROTECT** — untuk *catatan historis* yang tak tergantikan (order, payment) — entitas yang dirujuk tidak boleh bisa dihapus selama referensinya hidup. Inilah dasar kebijakan **soft-delete** (produk ditandai `DISCONTINUED`, bukan dihapus).

### 3. Lean vs Audit-Trail

Di beberapa titik ada pilihan antara model ramping vs model yang menyimpan jejak lengkap. Proyek ini **konsisten memilih lean**:

- `Payment` = OneToOne (mutasi status), bukan FK 1:banyak (riwayat percobaan).
- `Order` memakai kolom timestamp (`shipped_at`, dst), bukan tabel history per-transisi.

Trade-off yang diterima: kehilangan jejak detail, demi kesederhanaan yang sepadan untuk scope mock.

### 4. Partial Unique Index

Pola "maksimal satu baris yang memenuhi kondisi tertentu" ditegakkan di level DB via `UniqueConstraint` + `condition`. Dipakai pada `ProductImage.is_primary`. Didukung di SQLite **dan** PostgreSQL.

### 5. Write / Compute / Serve (CQRS-lite)

Recommendation engine memisahkan tiga lapis secara **fisik**:

| Lapis | Tugas | Dioptimalkan untuk |
|---|---|---|
| **Capture** (write) | merekam sinyal mentah | append murah |
| **Compute** (batch) | mengolah sinyal → skor | jalan offline, boleh lambat |
| **Serve** (read) | balikkan rekomendasi instan | SELECT cepat (index berat) |

Komputasi mahal **tidak pernah menyentuh request user** — sudah dikerjakan sebelumnya oleh management command (lapis Compute), hasilnya tinggal dibaca.

### Tipe data: uang vs skor

- **`DecimalField`** untuk uang (`price`, `total`) dan koordinat — presisi adalah *fakta*, tak boleh kena floating-point drift.
- **`FloatField`** untuk skor rekomendasi — *artefak komputasi* yang hanya dipakai untuk ranking (`ORDER BY`), tak pernah dijumlahkan secara finansial, dan dihitung ulang tiap batch run.

---

## Modul `accounts`

### `User`

Custom user model berbasis `AbstractUser` dengan **login via email** (`USERNAME_FIELD = 'email'`). Menggantikan `auth_user` bawaan — Django membuat tabel `accounts_user` berisi semua field bawaan + field tambahan.

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []                       # email & password otomatis required

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
```

**Keputusan kunci:**

- **Tidak ada tabel `Profile` terpisah.** Pola Profile adalah workaround untuk keterbatasan `auth_user` yang justru dihilangkan oleh `AbstractUser`. Atribut skalar user (nama, telepon) tinggal langsung sebagai kolom di sini.
- **Aturan tabel baru:** atribut **satu nilai per user** → kolom di `User`; atribut **banyak nilai per user** → tabel terpisah ber-FK (lihat `Address`).
- Pemisahan role Customer vs Admin memakai `is_staff` + `auth_group` bawaan — **tidak perlu tabel `roles` sendiri.**

> Data untuk recommendation engine **tidak** dibaca dari User — preferensi diturunkan dari *perilaku* (`BehaviorEvent`, `OrderItem`), bukan disimpan sebagai atribut profil.

### `Address`

Satu user bisa punya banyak alamat (one-to-many) → tabel terpisah. Mendukung pin lokasi via Google Maps Platform.

```python
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')

    # Kontak pengiriman
    recipient_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    # Alamat tekstual — pre-filled dari Google, tetap EDITABLE
    full_address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)

    # Dari Google Maps Platform
    place_id = models.CharField(max_length=255, blank=True)   # referensi stabil, boleh disimpan permanen
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    # Instruksi kurir — sangat relevan di konteks Indonesia
    notes = models.CharField(max_length=255, blank=True)

    is_default = models.BooleanField(default=False)
```

**Keputusan kunci:**

- **`DecimalField` untuk koordinat** (bukan `FloatField`) — presisi predictable, tanpa float drift. `decimal_places=6` ≈ presisi 0.11 m. `max_digits` longitude (10) > latitude (9) karena rentang ±180 vs ±90.
- **Koordinat `null=True`** — user boleh menyimpan alamat tanpa nge-pin di peta; jangan paksa form gagal.
- **`full_address` tetap editable**, bukan read-only dari Google — alamat Indonesia (RT/RW, nomor rumah, patokan) sering lebih presisi daripada reverse geocode Google.
- **Tidak menyimpan `formatted_address` terpisah** — dengan `place_id` tersimpan, versi Google bisa di-fetch ulang; menyimpannya lagi hanya redundansi.
- `city` & `postal_code` bisa auto-fill dari Google `address_components`, tetap editable.

---

## Modul `produk`

Tiga atribut domain (grade, series, timeline) **bukan** disatukan dalam satu tabel `categories` ber-kolom `type`. Alasannya: ketiganya **single-valued** (FK, bukan M2M), dan **series punya hierarki ke timeline** yang tidak punya rumah di tabel flat. Karena itu pula tabel junction `product_categories` **tidak dibutuhkan**.

### `Timeline`, `Series`, `Grade` (reference tables)

```python
class Timeline(models.Model):
    slug = models.SlugField(max_length=20, unique=True)        # 'uc', 'ce'
    name = models.CharField(max_length=100)                    # 'Universal Century'
    description = models.TextField(blank=True)


class Series(models.Model):
    slug = models.SlugField(max_length=80, unique=True)        # 'gundam-seed'
    name = models.CharField(max_length=120)                    # 'Gundam SEED'
    timeline = models.ForeignKey(Timeline, on_delete=models.PROTECT, related_name='series')  # HIERARKI


class Grade(models.Model):
    slug = models.SlugField(max_length=20, unique=True)        # 'hg', 'mg'
    name = models.CharField(max_length=100)                    # 'High Grade'
    scale = models.CharField(max_length=20, blank=True)        # '1/144'
    description = models.TextField(blank=True)
```

### `Product`

```python
class ProductStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    PRE_ORDER = 'PRE_ORDER', 'Pre-order'
    DISCONTINUED = 'DISCONTINUED', 'Discontinued'


class ProductCondition(models.TextChoices):
    SEALED = 'SEALED', 'Sealed'
    PRE_OWNED = 'PRE_OWNED', 'Pre-owned'


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name='products')
    series = models.ForeignKey(Series, on_delete=models.PROTECT, related_name='products')

    status = models.CharField(max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
    condition = models.CharField(max_length=20, choices=ProductCondition.choices, default=ProductCondition.SEALED)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Keputusan kunci:**

- **`timeline` tidak disimpan langsung di Product** — diturunkan via `product.series.timeline`. Satu sumber kebenaran; mustahil ada produk dengan series CE tapi timeline UC yang bertentangan.
- **Reference table vs enum:** `grade`/`series`/`timeline` → tabel (punya metadata + slug + hierarki); `status`/`condition` → `TextChoices` (set kecil, fixed, tanpa metadata — tabel terpisah akan over-engineering).
- **`on_delete=PROTECT`** pada grade/series — soft-delete, grade yang masih dipakai produk tak bisa dihancurkan.
- **`price` = `DecimalField`** — uang tak boleh kena float drift.

### `ProductImage`

Satu produk banyak foto (one-to-many) → tabel terpisah. F-04 butuh image gallery.

```python
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=models.Q(is_primary=True),
                name='unique_primary_image_per_product',
            )
        ]
```

**Keputusan kunci:**

- **`is_primary` vs `display_order` menjawab dua pertanyaan berbeda.** `is_primary` = foto thumbnail (satu wajah produk, dipakai di listing/search/cart/rekomendasi). `display_order` = urutan foto di galeri detail (F-04). Keduanya independen — galeri bisa dibuka box art sementara thumbnail memakai foto build dramatis.
- **Partial unique index** menjamin maksimal satu `is_primary=True` per produk di level DB. (Menjamin *minimal* satu primary diurus di logika aplikasi.)
- `on_delete=CASCADE` — hapus produk, foto ikut.

---

## Modul `cart`

Modul paling sederhana. **Login-required** (bukan guest cart) → tanpa `session_id` / logika merge. Catatan: F-11/F-12/F-13 (checkout/payment/ongkir) **bukan** bagian modul ini — mereka adalah *proses checkout* yang menghasilkan Order.

### `Cart` & `CartItem`

```python
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())   # dihitung on-the-fly, TIDAK disimpan


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='+')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product'], name='unique_product_per_cart')
        ]

    @property
    def subtotal(self):
        return self.quantity * self.product.price   # harga dibaca LIVE dari produk
```

**Keputusan kunci:**

- **Cart TIDAK menyimpan harga** — kebalikan dari `OrderItem`. Cart adalah pandangan hidup; harga selalu dibaca live dari `product.price`. Harga baru membeku **tepat saat checkout** (konversi cart → order).
- **`UniqueConstraint(cart, product)`** — satu produk = satu baris. Add produk yang sudah ada → naikkan `quantity` (UPDATE), bukan baris baru (INSERT).
- **`on_delete=CASCADE` pada product** — kebalikan dari `OrderItem` (PROTECT). Cart ephemeral, tak ada nilai historis untuk dilindungi.
- **`related_name='+'`** — tak ada reverse accessor dari Product (data cart = noise, dibuang).
- **Stok & ketersediaan BUKAN urusan skema cart** — divalidasi di momen checkout (produk bisa jadi `DISCONTINUED` / habis selama duduk di keranjang).

---

## Modul `order`

Modul terkaya. `Order` bukan sekadar wadah data — dia adalah **state machine**.

### Enums

```python
class OrderStatus(models.TextChoices):
    PENDING    = 'PENDING', 'Menunggu Pembayaran'
    PAID       = 'PAID', 'Dibayar'
    PROCESSING = 'PROCESSING', 'Diproses'
    SHIPPED    = 'SHIPPED', 'Dikirim'
    COMPLETED  = 'COMPLETED', 'Selesai'
    CANCELLED  = 'CANCELLED', 'Dibatalkan'


class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = 'BANK_TRANSFER', 'Transfer Bank'
    E_WALLET      = 'E_WALLET', 'E-Wallet'
    QRIS          = 'QRIS', 'QRIS'
    COD           = 'COD', 'Bayar di Tempat'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Menunggu Pembayaran'
    PAID    = 'PAID', 'Lunas'
    FAILED  = 'FAILED', 'Gagal'
    EXPIRED = 'EXPIRED', 'Kedaluwarsa'
```

### State machine: transisi yang sah

| Dari | Boleh transisi ke | Catatan |
|---|---|---|
| `PENDING` | `PAID`, `CANCELLED` | belum ada uang — cancel paling bersih |
| `PAID` | `PROCESSING`, `CANCELLED` | cancel di sini = konsep refund (di luar scope) |
| `PROCESSING` | `SHIPPED`, `CANCELLED` | **batas akhir cancel** |
| `SHIPPED` | `COMPLETED` | tak bisa cancel — sudah di jalan, jadinya retur |
| `COMPLETED` | — | terminal |
| `CANCELLED` | — | terminal |

> **Batas cancel di `SHIPPED` adalah keputusan desain.** "Cancel" dan "retur" adalah dua alur berbeda; retur di luar scope. **Refund tidak dimodelkan** (tidak ada di feature map, `Payment` tanpa state `REFUNDED`) — cancel cukup menandai order + alasan.

### `Order`

```python
from django.utils import timezone
from django.core.exceptions import ValidationError

ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING:    {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID:       {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED:    {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED:  set(),
    OrderStatus.CANCELLED:  set(),
}


class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    # SNAPSHOT alamat (dibekukan saat checkout)
    shipping_recipient_name = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=20)
    shipping_full_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    shipping_notes = models.CharField(max_length=255, blank=True)

    # SNAPSHOT finansial (dibekukan saat checkout)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # nilai dari ShippingRate
    total = models.DecimalField(max_digits=12, decimal_places=2)

    # Snapshot waktu transisi (paid_at ada di Payment, bukan di sini)
    shipped_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def can_transition_to(self, new_status):
        return new_status in ALLOWED_TRANSITIONS[self.status]

    def transition_to(self, new_status, reason=''):
        if not self.can_transition_to(new_status):
            raise ValidationError(f"Transisi {self.status} → {new_status} tidak diizinkan")
        self.status = new_status
        now = timezone.now()
        if new_status == OrderStatus.SHIPPED:
            self.shipped_at = now
        elif new_status == OrderStatus.COMPLETED:
            self.completed_at = now
        elif new_status == OrderStatus.CANCELLED:
            self.cancelled_at = now
            self.cancellation_reason = reason
        self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)                 # simpan dulu → dapat self.id
        if not self.order_number:
            self.order_number = f"HH-{self.created_at:%Y%m%d}-{self.id:04d}"
            super().save(update_fields=['order_number'])
```

**Keputusan kunci:**

- **Validasi transisi di level aplikasi, bukan constraint DB** — state-machine logic tak bisa ditegakkan constraint DB biasa tanpa trigger (yang merusak portabilitas). Semua perubahan status wajib lewat `transition_to()`; transisi ilegal melempar `ValidationError`. Admin (F-21) memanggil method ini, bukan set `status` mentah.
- **Snapshot alamat** (`shipping_*`) — `Address` mutable & bisa dihapus user; record harus mengabadikan alamat saat transaksi. Kolom eksplisit (bukan `JSONField`) demi konsistensi relasional + ramah template. Koordinat **tidak** di-snapshot (tak melayani fungsi di sisi order).
- **`subtotal` & `total` disimpan** — bukan anti-drift (sudah deterministik dari item beku), melainkan sebagai **catatan finansial eksplisit** ("berapa yang ditagih"), satu sumber kebenaran tak bergantung logika perhitungan.
- **`user = PROTECT`** — order adalah catatan finansial; karena user dijamin ada, email/nama user tak perlu di-snapshot.
- **`order_number` human-readable** (`HH-20260530-0042`) via **two-phase save** — format butuh `id` yang baru ada setelah INSERT. Memakai `id` (bukan hitungan harian) untuk menghindari race condition. Trade-off: nomor tidak reset harian & membocorkan perkiraan total order (non-isu untuk portfolio).
- **`paid_at` ada di `Payment`**, bukan di sini — hindari duplikasi sumber kebenaran.

### `OrderItem`

```python
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')      # parent → CASCADE
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')  # reference → PROTECT

    # Snapshot: dibekukan saat order dibuat
    product_name = models.CharField(max_length=200)
    product_image = models.CharField(max_length=255, blank=True)
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity   # dari field BEKU, bukan product.price
```

**Keputusan kunci:**

- **Reference + Snapshot bersamaan.** FK ke product menjawab *"produk ini SEKARANG seperti apa?"* (tombol beli lagi, link, analitik); field beku menjawab *"produk ini DULU seperti apa saat dibeli?"* (integritas riwayat).
- **Snapshot karena MUTASI, bukan penghapusan.** Bahkan jika produk tak pernah dihapus, `price`/`name`/`image` mutable — admin bisa mengubahnya. Tanpa snapshot, riwayat berubah.
- **Asimetri `on_delete`:** `order` = CASCADE (item milik order), `product` = PROTECT (kebalikan dari `CartItem` yang CASCADE). Produk tak boleh dihapus selama ada di pesanan → soft-delete via `DISCONTINUED`.
- **`related_name='order_items'`** (diberi nama, beda dari cart yang `'+'`) — data pembelian adalah **sinyal** yang dibaca recommendation engine (purchase) & popularity fallback. Cart reverse = noise dibuang; order reverse = signal disimpan.

> Yang **tidak** di-snapshot: `grade`/`series`/`slug` — nama produk sudah memuat grade ("HG..."), dan riwayat hanya butuh nama+foto+harga+qty. Detail lain masih bisa via FK.

### `ShippingRate`

Sumber tarif ongkir mock per-kota. Nilai dibaca saat checkout, lalu dibekukan ke `Order.shipping_cost`.

```python
class ShippingRate(models.Model):
    city = models.CharField(max_length=100, unique=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_days = models.CharField(max_length=20, blank=True)   # "2-3" → ditampilkan di UI
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['city']
```

**Keputusan kunci:**

- **Ini "tabel ongkir"-nya** — bukan tabel shipment per-order (biaya + alamat sudah di-snapshot ke `Order`). Tabel shipment baru perlu kalau memodelkan kurir/resi/tracking, yang di luar scope F-13.
- **Pencocokan kota rapuh** — `ShippingRate.city` terkontrol, `Address.city` teks bebas. Solusi: saat checkout, kota untuk lookup ongkir **dipilih dari dropdown** yang di-populate dari `ShippingRate` (nilai dijamin match). Wajib tangani kasus "kota tak ditemukan" (blokir checkout atau tarif default).
- Ongkir nyata bergantung berat kit; mock per-kota sengaja menyederhanakan.

### `Payment`

Relasi **OneToOne** (satu order, satu record pembayaran) dengan state machine sendiri.

```python
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)   # cermin order.total saat bayar
    transaction_ref = models.CharField(max_length=64, blank=True)   # ref mock, mis. "MOCK-7F3A9C"
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Keputusan kunci:**

- **Tabel terpisah karena status pembayaran adalah sumbu berbeda dari status pesanan** — Payment punya lifecycle sendiri (`PENDING → PAID`, atau `PENDING → FAILED → PENDING → PAID`, atau `PENDING → EXPIRED`).
- **OneToOne (bukan FK 1:banyak)** — pilihan lean. **Retry tetap didukung** via mutasi status `FAILED → PENDING` pada baris yang sama. Trade-off yang diterima: `method`/`transaction_ref` ter-overwrite saat retry (jejak percobaan gagal tidak tersimpan).
- **`on_delete=CASCADE`** — payment dimiliki order.
- **`amount` cermin `order.total`** — record transaksi konvensionalnya self-contained.

### Wiring: dua state machine, satu titik temu

`Payment.status = PAID` adalah **satu-satunya pemicu** yang menggerakkan `Order.status` dari `PENDING` → `PAID`. Order tidak pernah memindahkan dirinya sendiri — ia bereaksi pada hasil Payment.

```python
# pembayaran mock dikonfirmasi:
payment.status = PaymentStatus.PAID
payment.paid_at = timezone.now()
payment.save()
order.transition_to(OrderStatus.PAID)

# pembayaran kedaluwarsa:
payment.status = PaymentStatus.EXPIRED
payment.save()
order.transition_to(OrderStatus.CANCELLED, reason='Pembayaran kedaluwarsa')
```

> **Efek samping cancel (logika aplikasi, bukan skema):** stok dikurangi saat checkout, maka transisi ke `CANCELLED` harus **mengembalikan stok**. Dijalankan di dalam/sekitar `transition_to`.

---

## Modul `rekomendasi`

Jantung portfolio. Arsitektur tiga lapis (Capture → Compute → Serve). Teknik: **content-based filtering** dengan **implicit feedback** — dua output, dua mesin:

- **F-28 "Produk Serupa"** (produk↔produk) — murni content-based dari atribut. **Nol perilaku, nol cold-start.**
- **F-29 "Untuk Kamu"** (user→produk) — implicit feedback membangun profil preferensi atas atribut. Butuh perilaku → cold start ditangani F-30.

> Ini **bukan** collaborative filtering — tidak pernah menghitung "orang yang beli X juga beli Y". Atribut yang menggerakkan pencocokan; perilaku hanya membangun profil di F-29. Menghindari new-item cold-start, cocok dengan synthetic seed data, dan **explainable**.

### Lapis Capture (write-path)

```python
class EventType(models.TextChoices):
    VIEW     = 'VIEW', 'View'
    WISHLIST = 'WISHLIST', 'Wishlist'
    PURCHASE = 'PURCHASE', 'Purchase'


class BehaviorEvent(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behavior_events')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='behavior_events')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    # CATATAN: TIDAK ada kolom `weight`

    class Meta:
        indexes = [
            models.Index(fields=['user']),                  # agregasi per-user (F-29)
            models.Index(fields=['product', 'event_type']), # popularitas per produk (F-30)
        ]


class Wishlist(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_wishlist_item')
        ]
```

**Keputusan kunci:**

- **`weight` TIDAK disimpan — kontras dengan snapshot harga.** Bobot adalah **hyperparameter algoritma** yang ingin di-tune; mengubah purchase 5→6 harus me-recompute semua dengan bobot baru, bukan menghormati bobot lama. Bobot tinggal di **config**, diterapkan saat compute. Event merekam *apa yang terjadi* (type); algoritma yang memberi *nilai*.
- **`BehaviorEvent` append-only** — ledger immutable, tak ada UPDATE/DELETE (kecuali pruning event lama).
- **Index ramping** — write dioptimalkan untuk append murah; kecepatan serving datang dari tabel precomputed, bukan tabel ini. Batch job boleh full-scan (offline).
- **`Wishlist` kembaran `CartItem`** — tabel current state: unique `(user, product)`, CASCADE pada product. Wishlist = fitur tampil/hapus; sinyal wishlist untuk engine mengalir lewat `BehaviorEvent` (event log terpadu).
- **`user` wajib** — view hanya terekam untuk user login (tracking anonim butuh `session_id`, disederhanakan secara sadar).

#### Sumber sinyal (event log terpadu)

Engine membaca **satu tabel** (`BehaviorEvent` memuat VIEW/WISHLIST/PURCHASE). Sinyal PURCHASE memang juga ada di `OrderItem` — duplikasi ini **bukan bug, melainkan pola yang diakui**: `OrderItem` = kebenaran transaksional, event PURCHASE = sinyal ML. Dua tujuan, dua rumah. Konsekuensinya batch job jadi sepele dan engine decoupled dari skema Order/Wishlist.

### Lapis Serve (read-path)

**Sifat bersama ketiga tabel precomputed di bawah:**

1. **`FloatField`** untuk skor (hanya untuk ranking, bukan finansial).
2. **`on_delete=CASCADE`** di semua FK — derived data, disposable/rebuildable.
3. **Hanya top-N/top-K** — bukan semua pasangan/skor.
4. **Index `(kunci, -score)` berat** — INILAH sumber kecepatan serving.
5. **Dibangun ulang tiap batch run** — recompute dari nol, bukan update incremental → idempoten.

#### `ProductSimilarity` (F-28)

```python
class ProductSimilarity(models.Model):
    source_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similar_to')
    target_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='+')
    score          = models.FloatField()
    computed_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['source_product', 'target_product'], name='unique_similarity_pair')
        ]
        indexes = [
            models.Index(fields=['source_product', '-score']),
        ]
```

**Skor** = overlap atribut berbobot:

```
score = (3 jika series sama) + (2 jika timeline sama) + (1 jika grade sama)
```

Hierarki series→timeline bekerja gratis: pasangan se-series dapat `3+2=5` (pasti naik ke puncak); beda-series-se-timeline dapat `2`; grade ortogonal dapat `1`.

**Keputusan kunci:**

- **Disimpan directional (source→target)**, bukan kanonik — meski skor simetris, serving "diberi X, balikkan tetangga teratas" jadi `WHERE source_product=X ORDER BY -score` yang trivial hanya jika directional. *Skor* simetris, tapi *daftar top-N* tak harus simetris — penyimpanan directional menangkap ini dengan tepat.
- **Hanya skor positif, top-K per source** (mis. 30). 500 produk ≈ 15.000 baris.
- **Filter `DISCONTINUED` di compute time** — batch job tidak menulis baris bertarget produk discontinued. Re-check status saat serve sebagai jaring pengaman.

#### `UserRecommendation` (F-29)

```python
class UserRecommendation(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='+')
    score       = models.FloatField()
    reason      = models.CharField(max_length=120, blank=True)   # explainability
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_user_recommendation')
        ]
        indexes = [
            models.Index(fields=['user', '-score']),
        ]
```

**Cara skor lahir** (satu-satunya tempat implicit feedback masuk):

```
1. Kumpulkan BehaviorEvent user → terapkan bobot {VIEW:1, WISHLIST:3, PURCHASE:5}
2. Agregasi jadi PROFIL PREFERENSI atas atribut
   → mis. {timeline: {CE: 0.6, UC: 0.3}, grade: {MG: 0.7, RG: 0.3}}
3. Skor tiap produk kandidat = kecocokan atributnya dengan profil
4. Simpan top-N per user
```

**Keputusan kunci:**

- **`reason`** mewujudkan janji "explainable recommendations" (`"Karena kamu menyukai Cosmic Era"`). Batch job tahu atribut mana paling menyumbang skor, lalu menuliskannya. Opsional, tapi pembeda.
- **Kecualikan produk yang sudah dibeli di compute time** — tidak menyodorkan SKU identik yang sudah dimiliki. (Versi MG dari kit HG yang sudah dibeli tetap muncul — yang dikecualikan hanya produk identik, bukan se-series.)
- **Cold start diserahkan ke F-30** — user tanpa event dilewati batch job; serve mendeteksi & jatuh ke popularitas.
- Struktur **berima dengan `ProductSimilarity`** (beda kunci saja).

#### `ProductPopularity` (F-30, cold-start fallback)

```python
class ProductPopularity(models.Model):
    product     = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='popularity')
    score       = models.FloatField()
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['-score'])]
```

**Keputusan kunci:**

- **Tabel precomputed (bukan query agregat per-request)** — menjaga kemurnian "lapis serve nol komputasi per-request". Popularitas global → tabel mungil (OneToOne, satu baris per produk). Fallback = `ORDER BY -score LIMIT N`. *(Query agregat juga defensible karena popularitas murah & global; tabel dipilih demi konsistensi arsitektur.)*
- **Skor** = jumlah event berbobot per produk lintas semua user, `DISCONTINUED` dikecualikan. (Sofistikasi opsional: recency decay.)

#### `RecommendationLog` (F-31, Phase 2 — metrics)

```python
class RecommendationSource(models.TextChoices):
    SIMILAR      = 'SIMILAR', 'Produk Serupa'       # F-28
    PERSONALIZED = 'PERSONALIZED', 'Untuk Kamu'     # F-29
    POPULAR      = 'POPULAR', 'Populer'             # F-30


class RecommendationLog(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='recommendation_logs')
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='+')
    source      = models.CharField(max_length=20, choices=RecommendationSource.choices)
    was_clicked = models.BooleanField(default=False)
    shown_at    = models.DateTimeField(auto_now_add=True)
    clicked_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['source', 'was_clicked'])]   # CTR per source
```

**Keputusan kunci:**

- **Nilai inti di field `source`** — mengukur **CTR per jenis rekomendasi** ("F-29 mengungguli F-30 sebesar X%"). Cerita analitik matang: tidak cuma membuat rekomendasi, tapi mengukur mana yang bekerja.
- Satu baris per impression, di-update `was_clicked=True` saat diklik. Phase 2 — dirancang, bukan jalur kritis MVP.

### Lapis Compute (management command)

Bukan tabel — **mesin yang memproduksi keempat tabel Serve** di atas.

```python
# python manage.py compute_recommendations
@transaction.atomic
def handle(self):
    weights = settings.RECOMMENDATION_WEIGHTS   # {VIEW:1, WISHLIST:3, PURCHASE:5}
    products = (Product.objects
                .exclude(status=ProductStatus.DISCONTINUED)
                .select_related('grade', 'series__timeline'))

    # F-28: overlap atribut antar-pasangan → top-K per source → bulk_create
    # F-29: agregasi event berbobot per user → profil → skor kandidat → exclude purchased → top-N → bulk_create
    # F-30: jumlah event berbobot per produk → bulk_create
```

**Properti operasional:**

- **Atomic rewrite** — DELETE-lama + INSERT-baru dibungkus `transaction.atomic`; pembaca selalu melihat data lama **atau** baru, tak pernah tabel kosong di tengah proses.
- **`bulk_create`** — ribuan baris dalam segelintir query, bukan baris-per-baris.
- **Idempoten** — recompute-dari-nol; jalankan dua kali → hasil sama. Inilah dasar sifat disposable/CASCADE/Float di lapis Serve.

> **Klimaks CQRS-lite:** tiga sumber sinyal (`BehaviorEvent` + `OrderItem` + atribut produk) → satu command offline → empat tabel siap-saji. Request user tak pernah menyentuh perhitungan ini.

---

## Inventaris Tabel

**22 tabel rancangan** (+ ~10 tabel bawaan Django):

| Modul | Tabel |
|---|---|
| **accounts** | `User`, `Address` |
| **produk** | `Product`, `ProductImage`, `Grade`, `Timeline`, `Series` |
| **cart** | `Cart`, `CartItem` |
| **order** | `Order`, `OrderItem`, `ShippingRate`, `Payment` |
| **rekomendasi** (write) | `BehaviorEvent`, `Wishlist` |
| **rekomendasi** (serve) | `ProductSimilarity`, `UserRecommendation`, `ProductPopularity` |
| **rekomendasi** (Phase 2) | `RecommendationLog` |

---

## Konfigurasi

Hyperparameter algoritma — disimpan di `settings.py`, **bukan** di database, agar bisa di-tune ulang lalu di-recompute.

```python
# Bobot implicit feedback (F-29, F-30)
RECOMMENDATION_WEIGHTS = {
    'VIEW': 1,
    'WISHLIST': 3,
    'PURCHASE': 5,        # hyperparameter; rentang desain 5–6
}

# Bobot overlap atribut untuk similarity (F-28)
SIMILARITY_WEIGHTS = {
    'series': 3,
    'timeline': 2,
    'grade': 1,
}

# Cap penyimpanan & penyajian
SIMILARITY_TOP_K = 30    # disimpan per source product (K ≥ N)
RECOMMENDATION_TOP_N = 12 # disajikan per user
```

---
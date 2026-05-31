# Rancangan Struktur Project Root — HaroHUB

> Rancangan struktur direktori untuk platform e-commerce Gunpla full-stack. Disusun agar **pohon direktori mencerminkan arsitektur konseptual** yang sudah diputuskan — pemisahan 5 modul domain dan tiga lapis Capture/Compute/Serve di engine rekomendasi harus bisa "dibaca" langsung dari struktur folder.
>
> Dokumen ini menutup rancangan **struktur**. *Alur kerja* tiap service (mis. `checkout()`) dibahas terpisah; di sini hanya posisi file dan tanggung jawabnya yang ditetapkan.

---

## Daftar Isi

1. [Prinsip Desain Struktur](#prinsip-desain-struktur)
2. [Pohon Root Lengkap](#pohon-root-lengkap)
3. [Lapis `config/`](#lapis-config)
4. [Lapis `apps/` — Arah Dependensi](#lapis-apps--arah-dependensi)
5. [Bedah Per-App](#bedah-per-app)
6. [Batas `core` vs `common`](#batas-core-vs-common)
7. [Struktur Internal `rekomendasi/engine/`](#struktur-internal-rekomendasiengine)
8. [Struktur Internal `order/services.py`](#struktur-internal-orderservicespy)
9. [Templates & Static (Tailwind Standalone)](#templates--static-tailwind-standalone)
10. [Catatan Operasional Produksi](#catatan-operasional-produksi)
11. [Konvensi Global](#konvensi-global)
12. [Keputusan yang Masih Terbuka](#keputusan-yang-masih-terbuka)

---

## Prinsip Desain Struktur

Empat prinsip ini menyatukan seluruh keputusan di bawah:

1. **Struktur mencerminkan arsitektur.** Interviewer yang membuka repo harus bisa membaca desain dari pohon direktori — pemisahan modul domain dan tiga lapis recommendation engine terlihat di filesystem, bukan tersembunyi di dalam kode.
2. **File hanya ada kalau app memikulnya.** Bukan menyalin template app Django mentah ke setiap modul. App tanpa view tak punya `urls.py`; app tanpa tabel tak punya `migrations/` berisi apa pun.
3. **Pisahkan infrastruktur dari domain.** `config/` (project package) terpisah dari `apps/` (aplikasi domain). Batas "ini plumbing, ini bisnis" eksplisit.
4. **Algoritma murni terpisah dari plumbing Django.** Logika rekomendasi hidup sebagai Python murni yang nol-coupling ke ORM/request — bisa di-unit-test tanpa database dan dijelaskan baris demi baris.

---

## Pohon Root Lengkap

```
harohub/
├── manage.py
├── tailwindcss                 # binary standalone Tailwind (gitignored)
├── tailwind.config
├── .env.example
├── .gitignore                  # db.sqlite3, media/, staticfiles/, .env, tailwindcss, output.css*
├── README.md
├── pyproject.toml              # atau requirements/{base,dev,prod}.txt
│
├── config/                     # PROJECT PACKAGE (bukan app)
│   ├── settings/
│   │   ├── base.py             # shared; baca DATABASE_URL
│   │   ├── development.py      # DEBUG, fallback SQLite
│   │   └── production.py       # Postgres, whitenoise, django-storages
│   ├── urls.py                 # root URLconf + include app + /api/ + /api/docs/
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── core/                   # abstract models & mixins (ORM-layer)
│   ├── common/                 # validators, generators, template tags (non-model)
│   ├── accounts/               # User, Address
│   ├── produk/                 # Product, ProductImage, Grade, Timeline, Series
│   ├── cart/                   # Cart, CartItem
│   ├── order/                  # Order, OrderItem, ShippingRate, Payment + services.py
│   └── rekomendasi/            # engine/ (compute murni) + services.py (serve)
│
├── templates/
│   ├── base.html
│   ├── partials/               # GLOBAL — fragment HTMX lintas-halaman
│   └── <app>/                  # template namespaced per app
│
├── static/
│   ├── src/input.css           # SUMBER KEBENARAN Tailwind
│   ├── css/output.css          # hasil generate
│   └── js/app.js               # htmx + sedikit JS
├── staticfiles/                # target collectstatic (gitignored)
└── media/                      # upload dev (gitignored)
```

---

## Lapis `config/`

**Project package, bukan app.** Memisahkan `config/` dari `apps/` membuat batas infrastruktur vs domain eksplisit, dan lebih rapi daripada menumpuk semua di root saat app berjumlah 8.

**Settings split, bukan satu `settings.py`.**

| File | Tanggung jawab |
|---|---|
| `base.py` | Semua konfigurasi shared; `AUTH_USER_MODEL`, `INSTALLED_APPS`, `TEMPLATES`, hyperparameter rekomendasi; **membaca `DATABASE_URL`** |
| `development.py` | `DEBUG=True`; bila `DATABASE_URL` kosong → fallback ke SQLite |
| `production.py` | Postgres (Supabase) otomatis dari `DATABASE_URL`; whitenoise untuk static; `django-storages` untuk media |

**Keputusan kunci:**

- **Migrasi DB lewat environment variable, bukan edit manual.** `base.py` membaca `DATABASE_URL` via `dj-database-url`/`django-environ`. Dev tanpa env → SQLite; prod Supabase mengisi env → Postgres. Swap menjadi **zero code change** — bukti portabilitas yang lebih kuat daripada "ganti `ENGINE` manual saat deploy".
- **`AppConfig.name = 'apps.<nama>'`** di tiap app — eksplisit, karena app berada di bawah paket `apps/`.

---

## Lapis `apps/` — Arah Dependensi

Satu invariant yang menjaga struktur tetap koheren: **dependensi mengalir satu arah, nol siklus.**

```
core / common  ◄── (leaf: boleh diimpor siapa saja, tidak pernah mengimpor balik)
       ▲
   accounts     (paling dasar — semua ber-FK ke User)
       ▲
    produk
       ▲
 cart / order / rekomendasi   (lapis aplikasi — membaca accounts & produk)
```

- **`core` & `common` adalah leaf** — semua app boleh impor dari keduanya; keduanya tak pernah impor balik dari domain app.
- **Satu-satunya titik berpotensi memutar: `produk` ↔ `rekomendasi`** (produk memanggil `record_event`, engine membaca atribut Product). Dijinakkan dengan **FK string lazy** (`'produk.Product'`) + **service call di dalam fungsi view**, bukan di import level atas. Siklus tak pernah terjadi saat runtime.

---

## Bedah Per-App

### `core` — ORM-layer, paling tipis

```
apps/core/
├── apps.py
├── models.py        # TimeStampedModel (abstract), mixin lain
└── tests/test_models.py
```

Yang penting bukan apa yang ada, tapi apa yang **tidak**: tak ada `views.py`, `urls.py`, `admin.py`, dan **`migrations/` kosong selamanya** (abstract model tak membuat tabel). App "perpustakaan" — diimpor, tak pernah dijalankan. Tetap didaftarkan di `INSTALLED_APPS`.

### `common` — non-model utilities

```
apps/common/
├── apps.py
├── validators.py            # validasi reusable (mis. format nomor HP Indonesia)
├── generators.py            # mock transaction_ref "MOCK-7F3A9C" (F-12)
├── context_processors.py    # cart_count untuk badge navbar
├── exceptions.py            # exception domain (mis. CheckoutError)
├── templatetags/harohub_extras.py   # filter rupiah, dll
└── tests/
```

**Dua jebakan:** (1) app ini **wajib** di `INSTALLED_APPS` meski tanpa model — template tag hanya ditemukan dari app terdaftar. (2) `context_processors.py` didaftarkan terpisah di `TEMPLATES['OPTIONS']['context_processors']`, bukan via registrasi app.

### `accounts`

```
apps/accounts/
├── models.py        # User(AbstractUser), Address
├── managers.py      # UserManager kustom — TIDAK opsional
├── forms.py         # RegistrationForm, LoginForm, AddressForm
├── admin.py         # custom UserAdmin
├── views.py         # F-06 register/login, F-07 proteksi route
├── urls.py
├── migrations/
└── tests/
```

**Keputusan kunci:**

- **`managers.py` wajib.** Begitu `USERNAME_FIELD = 'email'`, `UserManager` bawaan rusak (`createsuperuser` error). Manager kustom meng-override `create_user`/`create_superuser` berbasis email.
- **`AUTH_USER_MODEL = 'accounts.User'` di-set SEBELUM `migrate` pertama.** Accounts praktis app pertama yang diselesaikan modelnya.
- **F-07** = `LoginRequiredMixin`/`@login_required` per-view (katalog publik, cart/order privat), bukan middleware tulisan-tangan.

### `produk` — paling "lebar"

```
apps/produk/
├── models.py        # Product, ProductImage, Grade, Timeline, Series + Status/Condition
├── managers.py      # Product.objects.active() — dipakai di mana-mana
├── admin.py         # ProductAdmin + ProductImageInline (F-19, F-20)
├── forms.py         # filter form (F-02)
├── views.py         # F-01 listing, F-02 filter, F-04 detail
├── api.py           # OPSIONAL — tergantung keputusan autocomplete
├── serializers.py   # OPSIONAL — idem
├── urls.py
├── migrations/
└── tests/
```

**Keputusan kunci:**

- **`Product.objects.active()`** (exclude `DISCONTINUED`) ditulis sekali sebagai manager method — definisi "aktif" konsisten di listing, search, detail, dan engine rekomendasi.
- **`api.py`/`serializers.py` bersifat opsional**, tergantung keputusan autocomplete F-03 (lihat [Keputusan Terbuka](#keputusan-yang-masih-terbuka)).

### `cart` — paling ramping

```
apps/cart/
├── models.py        # Cart, CartItem
├── views.py         # F-10 add/edit/remove — HTMX-heavy
├── urls.py
├── migrations/
└── tests/
```

Yang **hilang dan disengaja:** tanpa `services.py` (operasi single-model), tanpa `forms.py` (input cuma product_id + quantity), praktis tanpa `admin.py`. Checkout (cart→order) **bukan** milik app ini — itu `order/services.py`.

### `order` — paling kaya

```
apps/order/
├── models.py        # Order (state machine), OrderItem, ShippingRate, Payment + enum
├── services.py      # checkout() — orkestrasi lintas-model
├── admin.py         # F-21: aksi status memanggil transition_to(), BUKAN set mentah
├── views.py         # F-16 riwayat, F-17 detail
├── urls.py
├── migrations/
└── tests/
    ├── test_state_machine.py
    └── test_checkout.py
```

**Keputusan kunci — pembagian kerja yang tegas:**

- **Single-model logic tetap di model** (`Order.transition_to()`, `CartItem.subtotal`) — fat model.
- **Cross-model orchestration masuk `services.py`** (`checkout()` menyentuh OrderItem, Order, ShippingRate, Product, Payment sekaligus). Dibungkus `transaction.atomic`. **(Struktur lengkap → bagian "Struktur Internal `order/services.py`".)**
- **`admin.py` (F-21) wajib memanggil `transition_to()`**, bukan `list_editable` pada `status` — kalau tidak, admin bisa melanggar state machine sendiri (mis. `PENDING → SHIPPED`).

### `rekomendasi` — jantung portfolio

```
apps/rekomendasi/
├── models.py        # BehaviorEvent, Wishlist + 3 tabel serve + RecommendationLog
├── engine/          # LAPIS COMPUTE — Python murni, nol Django
│   ├── types.py
│   ├── similarity.py
│   ├── profile.py
│   └── popularity.py
├── services.py      # LAPIS SERVE — baca precomputed + cold-start + record_event()
├── management/commands/compute_recommendations.py   # adapter ORM → engine → bulk_create
├── views.py         # widget HTMX (F-28/F-29)
├── urls.py
├── migrations/
└── tests/
    ├── test_engine.py     # uji algoritma TANPA database
    └── test_services.py   # uji fallback cold-start
```

**Keputusan kunci:**

- **`engine/` adalah package, bukan file** — tiga output (F-28/29/30) = tiga modul algoritma terpisah, masing-masing nol-coupling ke ORM.
- **Cold-start fallback (F-30) ada di `services.py`, bukan `engine/`** — keputusan "user tanpa rekomendasi → jatuh ke popularitas" adalah logika *serve-time*, bukan *compute-time*.
- **Capture event via service call eksplisit** (`record_event`), bukan signals — sejalan prinsip "no magic, semuanya eksplisit".

---

## Batas `core` vs `common`

Dua folder utilitas tanpa aturan tegas berubah jadi laci sampah. Aturannya satu kalimat, bisa diuji:

> **`core`** = apapun yang ikut ke sistem ORM/migrasi (abstract model, mixin, custom manager/field). Uji: *"kalau `makemigrations`, apakah ini muncul?"* → ya → `core`.
>
> **`common`** = framework glue stateless + helper murni yang tak pernah mendefinisikan tabel. Uji: *"kalau database dihapus, apakah kode ini masih masuk akal?"* → ya → `common`.

**Contoh konkret:**

| Item | Rumah | Alasan |
|---|---|---|
| `TimeStampedModel` | `core` | abstract model, muncul saat diwariskan |
| Generator `MOCK-7F3A9C` | `common` | fungsi murni tanpa DB |
| `order_number` (`HH-...`) | **`Order.save()`** | butuh `self.id`, terikat lifecycle model |
| `OrderStatus`, `EventType` | **`models.py` app masing-masing** | muncul di migrasi via `choices`, milik domain |
| Filter rupiah | `common/templatetags` | helper presentasi |

> **Jangan tarik `TextChoices` ke `common`.** Tampak seperti "konstanta bersama", tapi muncul di migrasi dan milik domain app-nya.
>
> **Catatan validator:** validator yang dipasang ke *field model* path importnya ter-hardcode di migrasi — jangan rename/pindah filenya setelah dipakai. Validator level-form bebas dari ini.

---

## Struktur Internal `rekomendasi/engine/`

Pemisahan algoritma murni dari plumbing Django. Engine menerima **data polos** (dataclass), bukan objek Django, dan mengembalikan skor.

### Kosakata data bersama (`types.py`)

```python
@dataclass(frozen=True)
class ProductAttrs:
    id: int
    grade_id: int
    series_id: int
    timeline_id: int

@dataclass(frozen=True)
class Event:
    product_id: int
    event_type: str          # 'VIEW' | 'WISHLIST' | 'PURCHASE'

@dataclass
class PreferenceProfile:
    timeline: dict[int, float]   # max-norm
    grade:    dict[int, float]
    series:   dict[int, float]

@dataclass
class ScoredProduct:
    product_id: int
    score: float
    reason: str              # explainability
```

### Tanda tangan fungsi

```python
# similarity.py — F-28
def pair_score(a: ProductAttrs, b: ProductAttrs, weights: dict[str, int]) -> float
def compute_similarities(
    products: list[ProductAttrs], weights: dict[str, int], top_k: int,
) -> dict[int, list[tuple[int, float]]]    # source_id → [(target_id, score), ...]

# profile.py — F-29
def build_profile(
    events: list[Event], attrs_index: dict[int, ProductAttrs], weights: dict[str, int],
) -> PreferenceProfile
def score_products(
    profile: PreferenceProfile, candidates: list[ProductAttrs],
    dim_weights: dict[str, float], top_n: int, exclude_ids: set[int],
) -> list[ScoredProduct]

# popularity.py — F-30
def compute_popularity(events: list[Event], weights: dict[str, int]) -> dict[int, float]
```

### Dua keputusan algoritma yang terkunci

**Skor F-28** = overlap atribut berbobot, plafon `3+2+1 = 6`:
```
score = (3 jika series sama) + (2 jika timeline sama) + (1 jika grade sama)
```

**Skor F-29** = bobot dimensi × afinitas profil:
```
score = W_series × profil.series[s] + W_timeline × profil.timeline[t] + W_grade × profil.grade[g]
```

- **Profil pakai max-norm** (bagi nilai tertinggi per dimensi, favorit = 1.0) — bukan sum-norm. Mencegah kardinalitas tinggi (banyak series) menelan bobot dimensi. Plafon jadi `6`, simetris dengan F-28.
- **Dua keluarga bobot terpisah:** bobot **event** `{VIEW:1, WISHLIST:3, PURCHASE:5}` (di `build_profile`) vs bobot **dimensi** `{series:3, timeline:2, grade:1}` (di `score_products`). Dua tahap, dua urusan.
- **`reason`** lahir dari dimensi penyumbang skor terbesar; ties dipecah series > timeline > grade.

### Peran command (adapter tipis)

```python
@transaction.atomic
def handle(self, *args, **options):
    # _fetch_* (ORM) → engine murni → _write_* (ORM, DELETE-lama + bulk_create)
```

Engine tak pernah lihat database. `weights` selalu **disuntikkan** dari `settings.py`, tak pernah diimpor dari dalam engine — perwujudan kode dari "weight adalah hyperparameter".

### Tambahan `settings.py`

```python
RECOMMENDATION_WEIGHTS            = {'VIEW': 1, 'WISHLIST': 3, 'PURCHASE': 5}   # event
RECOMMENDATION_DIMENSION_WEIGHTS  = {'series': 3, 'timeline': 2, 'grade': 1}    # dimensi (F-29)
SIMILARITY_WEIGHTS                = {'series': 3, 'timeline': 2, 'grade': 1}    # F-28
SIMILARITY_TOP_K                  = 30
RECOMMENDATION_TOP_N              = 12
```

> `RECOMMENDATION_DIMENSION_WEIGHTS` dan `SIMILARITY_WEIGHTS` kebetulan sama nilainya, tetap **dua key terpisah** — operasi berbeda (user↔produk vs produk↔produk), layak di-tune independen.

---

## Struktur Internal `order/services.py`

Modul ini memikul orkestrasi lintas-model paling rumit di sistem. Prinsipnya sudah ditetapkan: **single-model logic tetap di model, cross-model orchestration masuk service.** Bagian ini mengunci *permukaan*-nya — fungsi apa, tanda tangannya, tanggung jawabnya, dan batas model↔service. *Alur kerja* langkah-demi-langkah di dalam tiap fungsi dibahas di sesi terpisah.

### Permukaan publik (function signatures)

```python
def checkout(cart: Cart, address: Address, payment_method: str) -> Order
def confirm_payment(payment: Payment, transaction_ref: str = '') -> None
def expire_payment(payment: Payment) -> None
def cancel_order(order: Order, reason: str) -> None
```

| Fungsi | Tanggung jawab (cross-model) | Model yang disentuh |
|---|---|---|
| `checkout` | Konversi cart → order: bekukan harga & alamat, lookup ongkir, decrement stok, buat Payment | Cart, CartItem, Order, OrderItem, ShippingRate, Product, Payment |
| `confirm_payment` | Titik temu dua state machine: Payment→`PAID` memicu Order `PENDING`→`PAID`; emit sinyal PURCHASE | Payment, Order, BehaviorEvent |
| `expire_payment` | Payment→`EXPIRED` memicu pembatalan; delegasi ke `cancel_order` | Payment, (→ `cancel_order`) |
| `cancel_order` | Order→`CANCELLED` + **kembalikan stok** | Order, Product |

> `confirm_payment` dan `expire_payment` sengaja dibuat **simetris** — keduanya handler *hasil pembayaran* (sukses vs kedaluwarsa), masing-masing menggerakkan satu state machine sesuai keputusan wiring di `05-database-design.md` ("Payment.status = PAID adalah satu-satunya pemicu Order PENDING→PAID").

### Batas model ↔ service

Garis yang menentukan sebuah operasi tinggal di model atau di service: **menyentuh satu model → model; menyentuh lebih dari satu → service.**

| Operasi | Rumah | Alasan |
|---|---|---|
| Perubahan status + timestamp transisi | `Order.transition_to()` | single-model |
| Validasi transisi sah/ilegal | `Order.can_transition_to()` | single-model |
| Generasi `order_number` | `Order.save()` | butuh `self.id` |
| `subtotal` / `total` per item | properti model (`OrderItem.subtotal`) | single-model |
| Decrement / restore stok | **service** | lintas Order ↔ Product |
| Snapshot harga/nama/foto ke `OrderItem` | **service** | lintas Cart/Product → Order |
| Snapshot alamat ke `Order.shipping_*` | **service** | lintas Address → Order |
| Wiring Payment → Order | **service** (`confirm`/`expire`) | lintas Payment ↔ Order |

### Keputusan penempatan: efek stok pada cancel

`05-database-design.md` menyebut restore stok dijalankan "di dalam/sekitar `transition_to`". Keputusan struktur di sini: **`transition_to()` tetap murni single-model** (hanya ubah status + timestamp), sedangkan **efek stok lintas-model tinggal di `cancel_order`** yang membungkus `transition_to`.

Alasannya: `transition_to` dipakai semua transisi (termasuk `SHIPPED`, `COMPLETED` yang tak menyentuh stok). Menanam logika Product di dalamnya merusak kemurnian single-model dan membuatnya tak bisa diuji tanpa Product. Jadi pola finalnya — **service memanggil method model, lalu menambah efek lintas-model di sekelilingnya**:

```
cancel_order():  order.transition_to(CANCELLED, reason)   # model: status only
                 + kembalikan stok ke Product             # service: cross-model
                 (semua dalam transaction.atomic)
```

### Seam lintas-app & dependency

Tiga titik sambung keluar dari modul ini, semua mengikuti disiplin **lazy FK + service call di dalam fungsi** (bukan import level atas):

- **`common.generators`** → `transaction_ref` mock (`"MOCK-7F3A9C"`) saat membuat `Payment`.
- **`common.exceptions.CheckoutError`** → dilempar saat stok habis, kota tak ada di `ShippingRate`, atau cart kosong.
- **`rekomendasi.services.record_event(user, product, PURCHASE)`** → dipanggil saat pembelian commit, mengisi event log terpadu `BehaviorEvent`. Inilah seam yang berpotensi memutar (`order` → `rekomendasi`), dijinakkan dengan pemanggilan di dalam fungsi. *(Kapan tepatnya PURCHASE di-emit — saat checkout atau saat `confirm_payment` — termasuk alur kerja, dibahas terpisah.)*

### Atomicity

Keempat fungsi membungkus tulisan lintas-model dalam `transaction.atomic`. Checkout parsial (stok terlanjur terkurang tetapi Order gagal dibuat) tak boleh terjadi — semua-atau-tidak.

> *Urutan operasi* di dalam `checkout()` (validasi ketersediaan → snapshot → decrement → buat Payment → dst), penanganan race condition stok, dan timing emit PURCHASE = **sesi alur kerja terpisah.** Yang final di sini hanya permukaan dan batas tanggung jawabnya.

---

## Templates & Static (Tailwind Standalone)

**Tailwind via binary standalone CLI** — nol dependency Node, nol `package.json`. Sejalan prinsip "kesederhanaan di luar backend/AI".

```
static/
├── src/input.css       # SUMBER KEBENARAN (direktif & layer Tailwind)
├── css/output.css      # HASIL GENERATE
└── js/app.js
```

Workflow dev (berdampingan dengan `runserver`):
```bash
./tailwindcss -i static/src/input.css -o static/css/output.css --watch
```

**Templates:** `templates/partials/` **global** untuk semua fragment HTMX. Konvensi penamaan `_<fitur>_<bagian>.html` (mis. `_rekomendasi_widget.html`, `_cart_badge.html`) untuk mencegah tabrakan; prefix underscore menandai "fragment, bukan halaman utuh". Template halaman utuh di `templates/<app>/`.

---

## Catatan Operasional Produksi

Tiga hal yang gampang terlewat di deploy (Railway/Render/Fly.io):

1. **Media files punya masalah ephemeral yang sama dengan SQLite.** Foto produk (F-20) di `media/` ikut terhapus tiap redeploy. Argumen "wajib Postgres di prod" otomatis berlaku ke storage: `ProductImage.image` harus pakai object storage (Supabase Storage / S3 / Cloudinary) via `django-storages` di `production.py`. (Sejalan skill "File upload & CDN integration".)
2. **Static pakai whitenoise** — tanpa nginx terpisah, ini cara standar menyajikan `output.css` + asset di prod.
3. **`output.css` di-build saat deploy** (pilihan condong): build step `curl` binary Linux → `--minify` → `collectstatic`. Sumber kebenaran tetap `input.css`. Menunjukkan paham pipeline asset end-to-end. *(Alternatif: commit `output.css`, prod nol-binary — defensible bila "demo tak boleh gagal deploy" jadi prioritas.)*

---

## Konvensi Global

| Konvensi | Aturan |
|---|---|
| **Testing** | `tests.py` → `tests/` package di tiap app (`test_models.py`, `test_services.py`, dst) sejak awal |
| **AppConfig** | `name = 'apps.<nama>'` eksplisit |
| **FK lintas-app** | string lazy (`'produk.Product'`) untuk hindari circular import |
| **Service call** | dipanggil di dalam fungsi view, bukan import level atas |
| **Partial HTMX** | `templates/partials/_<fitur>_<bagian>.html` |
| **Arah impor** | core/common = leaf; accounts → produk → (cart/order/rekomendasi); nol siklus |

---

## Keputusan yang Masih Terbuka

Dua keputusan tidak menghalangi mulai ngoding, tapi enak diberesi sebelum menyentuh app terkait:

1. **Autocomplete F-03 — HTML partial vs DRF JSON.** Menentukan hidup-matinya `produk/api.py` & `serializers.py`.
   - *Saran:* HTML partial untuk autocomplete (natural untuk HTMX, nol overhead serializer); simpan DRF untuk endpoint yang sengaja dipamerkan di `/api/docs/` sebagai bukti API design.
2. **Konfirmasi final F-29** — max-norm + dua key bobot terpisah sudah disepakati di dokumen ini; tinggal dikunci saat implementasi.

> *Alur kerja* tiap service (`checkout()`, `record_event()`, cold-start serve) dibahas di sesi terpisah. Struktur — posisi file dan tanggung jawabnya — sudah final di dokumen ini.

---
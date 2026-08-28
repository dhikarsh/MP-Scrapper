# Radar Pasar — Dashboard Produk Terlaris Mingguan

Dashboard internal untuk memantau produk terlaris **per kategori asli**
Shopee dan Tokopedia (kini bagian TikTok Shop), sebagai bahan riset tim
marketing sebelum meng-upload produk ke **Akulaku**. Satu halaman web
statis (HTML + JSON) — buka di browser, tanpa install apa pun.

Saat ini `data/products.json` berisi **data contoh (dummy)** dengan
struktur kategori yang sudah memakai kategori asli Shopee (`productCatId`)
dan Tokopedia (`tokopedia.com/p/<slug>`) yang kamu simpan.

---

## 1. Dimana menemukan App ID, Secret, dan host GraphQL (Shopee)

**Jalur resmi standar:**
1. Buka **affiliate.shopee.co.id** → login dengan akun afiliasimu.
2. Di homepage/dashboard afiliasi, cari menu **"Open API"**.
3. Di situ ada **App ID** (angka) dan **Secret/App Secret** (string panjang) — tinggal disalin.
4. Host GraphQL juga biasanya tercantum di halaman yang sama (formatnya
   `open-api.affiliate.shopee.<tld-negara>/graphql`, mis. `.vn`, `.com.my`,
   `.com.br` di negara lain — **untuk Indonesia, salin persis apa yang
   tertulis di dashboard-mu**, jangan menebak dari pola negara lain).

**Kalau menu "Open API" tidak kelihatan** (seperti pada screenshot
dashboard yang kamu kirim — itu memang tampilan resmi Shopee Affiliate
Portal, hanya menunya bisa beda posisi tergantung tipe akun):
- Cek ikon **"..." (titik tiga)** di pojok kanan atas, biasanya berisi menu tambahan.
- Cek dropdown nama akun (di contohmu tertulis **"dashlabs"**) → sering ada submenu Account Settings/API.
- Kalau tetap tidak ada, kemungkinan akses Open API belum aktif untuk akunmu — klik **Help Center** (tombol di pojok kanan atas) dan minta tim Shopee mengaktifkan akses Open API untuk akun afiliasimu. Tidak semua akun affiliate otomatis dapat akses API, terutama akun baru atau akun di bawah jaringan/agency tertentu.
- App ID & Secret bersifat rahasia — jangan pernah taruh langsung di kode yang di-push ke GitHub publik. Simpan sebagai **GitHub Secret** (lihat bagian 2 di bawah).

---

## 2. Setup & jalankan

1. Simpan 3 nilai berikut sebagai **GitHub Secret** (Settings → Secrets and variables → Actions → New repository secret):
   - `SHOPEE_APP_ID`
   - `SHOPEE_SECRET`
   - `SHOPEE_GRAPHQL_HOST`
2. (Opsional) sesuaikan daftar `SHOPEE_CATEGORIES` di `scripts/kumpulkan_data.py` kalau kategori Shopee-mu berubah — formatnya `(slug, nama, catid)`, `catid` diambil dari angka setelah `-cat.` di URL kategori Shopee.
3. Test lokal dulu:
   ```bash
   pip install -r scripts/requirements.txt
   SHOPEE_APP_ID=xxx SHOPEE_SECRET=yyy SHOPEE_GRAPHQL_HOST=zzz python scripts/kumpulkan_data.py
   ```
   Ini akan menimpa **blok Shopee saja** di `data/products.json` dengan produk terlaris asli per kategori (diurutkan berdasarkan `sales` lewat parameter `productCatId` + `sortType: 2`).
4. `.github/workflows/update-data.yml` menjalankan langkah yang sama otomatis tiap Senin pagi dan commit hasilnya.

---

## 3. Tokopedia → sekarang diarahkan ke TikTok Shop

Sejak **30 September 2025**, Open API Tokopedia untuk pasar Indonesia
resmi dihentikan. Integrasi seller Tokopedia sekarang lewat
**TikTok Shop Partner Center** (Tokopedia & TikTok Shop satu grup di
bawah GoTo/ByteDance). Kalau kamu ingin mendaftar API resmi untuk sisi
Tokopedia, di sinilah tempatnya:

- Daftar developer/partner di **partner.tiktokshop.com** (pilih tipe akun **"Tokopedia & Shop"** untuk pasar Indonesia).
- Yang tersedia: **Affiliate Seller API**, **Affiliate Creator API**, **Affiliate Partner API**, dan Seller API biasa (produk, order, dsb).

**Penting untuk diketahui:** sama seperti Shopee Seller API, semua API
resmi TikTok Shop di atas hanya memberi data **toko/kolaborasi milik
akunmu sendiri** — bukan data "produk terlaris lintas semua toko per
kategori" seperti yang didapat dari Shopee Affiliate API. Tidak ada API
resmi publik untuk itu di TikTok Shop/Tokopedia saat ini.

Karena itu, untuk blok `tokopedia` di `data/products.json`, tiga opsi:
1. **Input manual tim** — buka `tokopedia.com/p/<kategori>` seperti pengguna biasa, catat produk terlaris, edit `data/products.json` langsung di GitHub.
2. **Scraper pelengkap** (lihat bagian 3b di bawah) — otomatis, tapi rapuh dan perlu perawatan berkala.
3. **Vendor data pihak ketiga** (bukan API resmi ByteDance, tapi legal & berbayar) seperti Kalodata atau FindNiche.

### 3b. Opsi lain selain Shopee Affiliate API, + scraper Tokopedia sebagai pelengkap

**Alternatif Shopee Affiliate API:**

| Opsi | Cakupan | Catatan |
|---|---|---|
| Shopee Open Platform (Seller API) | Toko sendiri saja | Tidak cocok untuk riset kompetitor |
| Vendor data pihak ketiga (ShopAPIS, Compass, Jubelio Insight, Ginee Insight, iPrice Insights) | Shopee + Tokopedia, kadang + TikTok Shop | Berbayar, sudah rapi per kategori |
| Kalodata / FindNiche | Fokus TikTok Shop (mencakup Tokopedia) | Berbayar |
| Jaringan afiliasi lain (Involve Asia, AccessTrade ID, Admitad) | Data performa produk lintas platform | Daftar sebagai publisher |
| "Unofficial API" di RapidAPI/Apify | Macam-macam | Ini scraping juga, cuma dikerjakan pihak ketiga |

**Scraper Tokopedia (`scripts/scrape_tokopedia.py`)** — dibuat sebagai
**pelengkap sementara**, bukan pengganti sumber resmi. Beberapa hal
penting sebelum dipakai:

- **robots.txt Tokopedia** secara teknis tidak melarang crawling halaman
  kategori/pencarian, tapi **Syarat & Ketentuan Tokopedia kemungkinan
  tetap melarang scraping otomatis** sebagai klausul kontrak terpisah
  dari robots.txt. Risiko ini tetap ada di luar robots.txt.
- Tokopedia situs React/Next.js (konten dimuat lewat JavaScript), jadi
  scraper ini pakai **Playwright** (headless browser sungguhan), bukan
  `requests` biasa yang cuma akan dapat HTML kosong.
- Scraper **tidak** melakukan bypass CAPTCHA, login, atau penyamaran
  anti-deteksi apa pun — kalau Tokopedia menampilkan captcha/blokir,
  skrip berhenti, dan itu memang proteksi mereka bekerja seperti
  seharusnya.
- **Class CSS Tokopedia ter-hash dan sering berubah** setiap mereka
  deploy ulang. Selector di skrip adalah titik awal yang wajar, bukan
  jaminan — kalau hasil kosong, cek manual lewat DevTools browser
  (klik kanan kartu produk → Inspect) dan update `SELECTORS` di skrip.
- Setup:
  ```bash
  pip install playwright
  playwright install chromium
  python scripts/scrape_tokopedia.py
  ```
  Hanya menimpa blok `tokopedia` di `data/products.json` — blok `shopee` tidak disentuh.
- Sebelum menjalankan: buka `tokopedia.com/search?q=<kata kunci>` di
  browser, urutkan manual dengan filter **"Terjual Terbanyak"**, lalu
  salin parameter dari URL hasilnya ke `SORT_PARAM` di skrip (jangan
  menebak kode parameternya).
- Jalankan dengan wajar: skala kecil, tidak terus-menerus/paralel, ada
  jeda antar-kategori (sudah diberi delay di skrip) — supaya tidak
  membebani server Tokopedia atau memicu blokir IP kantor.

---

## 4. Metode pembayaran — dihapus

Field metode pembayaran sudah **dihapus seluruhnya** dari model data dan
tampilan. Tidak ada API resmi (Shopee maupun TikTok Shop/Tokopedia) yang
mengekspos data ini per produk, jadi menampilkannya hanya akan berupa
angka karangan yang menyesatkan buat tim marketing.

---

## 5. Analisis rentang harga (untuk strategi pricing)

Tiap kategori sekarang punya panel **"Analisis Rentang Harga"** di sisi
kanan kartu produk: total unit terjual minggu ini dikelompokkan per
rentang harga (`<20rb`, `20-50rb`, `50-100rb`, dst — lihat `BUCKET_EDGES`
di `index.html` kalau mau ubah batasnya). Panel ini otomatis menandai
**"sweet spot"** — rentang harga dengan total penjualan tertinggi di
kategori itu — supaya tim bisa langsung lihat di kisaran harga berapa
produk paling laku sebelum menentukan banderol di Akulaku.

Ini dihitung otomatis dari `harga` + `terjual_minggu_ini` setiap produk
di `data/products.json`, tidak perlu data tambahan.

---

## 6. Deploy ke GitHub Pages

1. Upload semua isi folder ini ke repo GitHub.
2. Settings → Pages → Deploy from a branch → `main` → `/ (root)` → Save.
3. Dapat URL publik `https://<username>.github.io/<repo>/` untuk dibagikan ke tim.
4. Update `data/products.json` (manual atau lewat workflow) → Pages otomatis redeploy.

---

---

## 7. Alternatif: RapidAPI / Apify (scraper Shopee pihak ketiga)

Kalau Shopee Affiliate Open API belum bisa kamu akses, `scripts/shopee_third_party.py`
bisa dipakai sebagai **pelengkap/cadangan sementara** lewat layanan scraper
pihak ketiga (RapidAPI atau Apify). Beberapa hal penting sebelum dipakai:

- **Ini bukan API resmi Shopee.** Layanan ini scraper pihak ketiga yang
  dijual sebagai produk — beberapa developer scraper serupa secara terbuka
  menulis bahwa layanan mereka dibangun khusus untuk menembus anti-bot
  Shopee. Risiko ToS Shopee tidak hilang, cuma pekerjaan teknisnya
  dipindah ke pihak ketiga.
- **Bisa berhenti berfungsi tanpa peringatan** kalau Shopee mengubah
  proteksinya — di luar kendalimu maupun kendali penyedia layanan.
- **Berbayar** di luar kuota trial gratis (RapidAPI/Apify keduanya model bayar-per-pemakaian).
- **Skema respons WAJIB dicek manual** — setiap layanan scraper pihak
  ketiga punya nama field sendiri-sendiri (`name` vs `title`, `sold` vs
  `historical_sold`, dst). Skrip ini punya fungsi `rapidapi_to_produk()` /
  `apify_to_produk()` yang perlu kamu sesuaikan setelah melihat respons
  asli dari playground/console masing-masing layanan — jangan jalankan
  langsung tanpa cek dulu.

**Cara pakai:**
```bash
pip install requests
# Untuk RapidAPI:
export SHOPEE_THIRD_PARTY_SOURCE=rapidapi
export RAPIDAPI_KEY=xxx
export RAPIDAPI_HOST=xxx   # dari tab "Code Snippets" di halaman playground-mu
export RAPIDAPI_ENDPOINT=/search   # sesuaikan dengan endpoint yang kamu pakai
python scripts/shopee_third_party.py

# Untuk Apify:
export SHOPEE_THIRD_PARTY_SOURCE=apify
export APIFY_TOKEN=xxx
export APIFY_ACTOR_ID=fmKWN5uByUCIy2Sam
python scripts/shopee_third_party.py
```

Sebelum menjalankan penuh, disarankan tes satu kategori dulu (edit
`KEYWORDS` jadi satu entri), `print(raw)` di dalam fungsi normalisasi
untuk lihat bentuk respons sesungguhnya, baru sesuaikan pemetaan field-nya.

Perlakukan ini sebagai **cadangan**, bukan pengganti Affiliate API kalau
akunmu sudah aktif — Affiliate API tetap jalur paling resmi dan stabil
untuk jangka panjang.

---

## Struktur folder

```
.
├── index.html                     # Dashboard (platform tabs: Shopee / Tokopedia)
├── data/
│   └── products.json              # { minggu, terakhir_diperbarui, platforms: [...] }
├── scripts/
│   ├── kumpulkan_data.py          # Isi otomatis blok Shopee via Affiliate Open API
│   └── requirements.txt
└── .github/workflows/
    └── update-data.yml
```

### Format `data/products.json`

```json
{
  "minggu": "18 - 24 Agustus 2026",
  "terakhir_diperbarui": "2026-08-27T09:00:00+07:00",
  "platforms": [
    {
      "id": "shopee",
      "nama": "Shopee",
      "kategori": [
        {
          "id": "electronics",
          "nama": "Electronics",
          "shopee_cat_id": 11044258,
          "url": "https://shopee.co.id/Electronics-cat.11044258",
          "produk": [
            { "rank": 1, "nama": "...", "toko": "...", "harga": 149000, "terjual_minggu_ini": 4820, "rating": 4.9 }
          ]
        }
      ]
    },
    {
      "id": "tokopedia",
      "nama": "Tokopedia (kini bagian TikTok Shop)",
      "kategori": [
        {
          "id": "elektronik",
          "nama": "Elektronik",
          "url": "https://www.tokopedia.com/p/elektronik",
          "produk": [ ... ]
        }
      ]
    }
  ]
}
```

Field `toko`, `harga`, `terjual_minggu_ini`, `rating` cukup — tidak ada
lagi field metode pembayaran.

---

## Menjalankan preview lokal

```bash
cd radar-pasar
python3 -m http.server 8000
# buka http://localhost:8000
```
(`fetch()` butuh server statis, tidak bisa dobel-klik file langsung. Ini
hanya untuk preview — versi yang dipakai tim tetap URL GitHub Pages.)

---

## Disclaimer

Alat ini adalah alat bantu riset internal, **bukan produk resmi** dari
Shopee, Tokopedia/TikTok Shop, atau Akulaku. Pastikan sumber data yang
dipakai mematuhi Syarat & Ketentuan platform terkait, dan periksa kembali
data sebelum dijadikan dasar keputusan bisnis.

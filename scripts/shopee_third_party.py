"""
Integrasi sumber data Shopee ALTERNATIF -- lewat layanan scraper pihak
ketiga (RapidAPI / Apify), BUKAN Shopee Affiliate Open API.

BACA DULU
=========
Kedua layanan ini BUKAN API resmi Shopee. Mereka scraper pihak ketiga
yang dijual sebagai layanan berbayar -- artinya:
- Risiko ToS Shopee tidak hilang, cuma pekerjaan "menembus" anti-bot-nya
  dikerjakan pihak ketiga, bukan kamu.
- Bisa berhenti berfungsi kapan saja kalau Shopee mengubah proteksinya
  (di luar kendalimu maupun kendali penyedia layanan).
- Berbayar per-request/run di luar kuota trial gratis.
- Field respons BISA BEDA dari yang diasumsikan di bawah -- kedua
  layanan ini tidak seragam, jadi WAJIB kamu sesuaikan MAP_FIELDS
  setelah melihat respons asli dari playground/console masing-masing
  (lihat instruksi di bagian bawah file).

Pakai skrip ini sebagai PELENGKAP/CADANGAN kalau Shopee Affiliate Open
API (scripts/kumpulkan_data.py) tidak bisa kamu akses -- bukan pengganti
permanen kalau Affiliate API-mu sudah aktif, karena itu tetap opsi yang
paling resmi & stabil.

Cara pakai
==========
1. Pilih salah satu (atau dua-duanya) dengan set SOURCE = "rapidapi" atau "apify".
2. Isi API key/token lewat environment variable (lihat KONFIGURASI).
3. WAJIB: jalankan sekali secara manual dulu, print(raw) hasil mentahnya,
   lalu sesuaikan fungsi normalisasi (rapidapi_to_produk / apify_to_produk)
   dengan nama field yang SESUNGGUHNYA muncul -- jangan asumsikan field
   di bawah ini sudah benar tanpa dicek, karena setiap layanan scraper
   pihak ketiga punya skema respons sendiri-sendiri.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()  # baca file .env di root project kalau ada -- lihat scripts/README_ENV.md
except ImportError:
    pass  # python-dotenv opsional; kalau tidak diinstall, tetap bisa pakai `export` manual

OUTPUT_PATH = "data/products.json"
WIB = timezone(timedelta(hours=7))

# ---------------------------------------------------------------------------
# KONFIGURASI
# ---------------------------------------------------------------------------
SOURCE = os.environ.get("SHOPEE_THIRD_PARTY_SOURCE", "rapidapi")  # "rapidapi" | "apify"

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
# Ganti sesuai host API yang kamu pakai di RapidAPI (lihat tab "Code Snippets"
# di halaman playground-mu untuk nilai X-RapidAPI-Host yang benar).
RAPIDAPI_HOST = os.environ.get("RAPIDAPI_HOST", "shopee-product-scraper2.p.rapidapi.com")
# Endpoint & parameter dikonfirmasi dari tab "Code Snippets" di playground:
# GET https://shopee-product-scraper2.p.rapidapi.com/shopee?country=ID&priceSlicing=false&maxItems=30&keywords=...
RAPIDAPI_ENDPOINT = os.environ.get("RAPIDAPI_ENDPOINT", "/shopee")

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
APIFY_ACTOR_ID = os.environ.get("APIFY_ACTOR_ID", "fmKWN5uByUCIy2Sam")

# Kategori/kata kunci yang mau diambil -- sesuaikan dengan kategori dashboard-mu.
KEYWORDS = [
    ("elektronik", "Electronics", "power bank"),
    ("fashion-pria", "Men Clothes", "kaos pria"),
    ("fashion-wanita", "Women Clothes", "atasan wanita"),
    ("kecantikan", "Beauty Care", "sunscreen"),
    ("rumah-tangga", "Home & Living", "rak organizer"),
    ("hp-aksesoris", "Mobile Accessories", "case hp"),
]

PRODUK_PER_KATEGORI = 10


# ---------------------------------------------------------------------------
# RAPIDAPI
# ---------------------------------------------------------------------------
def rapidapi_search(keyword: str, limit: int = 10) -> dict:
    url = f"https://{RAPIDAPI_HOST}{RAPIDAPI_ENDPOINT}"
    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    # Parameter dikonfirmasi dari playground: country, priceSlicing, maxItems, keywords.
    params = {
        "country": "ID",
        "priceSlicing": "false",
        "maxItems": limit,
        "keywords": keyword,
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def rapidapi_to_produk(raw: dict) -> list[dict]:
    """
    SESUAIKAN INI setelah kamu lihat bentuk respons asli.
    Contoh di bawah MENGASUMSIKAN struktur umum {"data": {"items": [...]}} --
    ganti path-nya kalau struktur asli berbeda (print(raw) dulu untuk cek).
    """
    items = raw.get("data", {}).get("items", []) or raw.get("items", []) or []
    out = []
    for it in items:
        out.append({
            "nama": it.get("name") or it.get("title", ""),
            "toko": it.get("shop_name") or it.get("shopName", "-"),
            "harga": int(it.get("price") or it.get("price_min") or 0),
            "terjual_minggu_ini": int(it.get("sold") or it.get("historical_sold") or 0),
            "rating": float(it.get("rating") or it.get("item_rating", {}).get("rating_star", 0) or 0),
        })
    return out


# ---------------------------------------------------------------------------
# APIFY
# ---------------------------------------------------------------------------
def apify_run_sync(keyword: str) -> list[dict]:
    """Menjalankan actor secara sinkron dan mengambil hasil dataset-nya
    lewat endpoint run-sync-get-dataset-items -- cek tab "API" di
    console.apify.com untuk actor-mu kalau nama input field beda."""
    url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/run-sync-get-dataset-items"
    params = {"token": APIFY_TOKEN}
    # Nama field input ("search"/"searchKeywords"/"query") tergantung actor-nya --
    # cek tab "Input" di console Apify untuk skema yang benar.
    body = {"search": keyword, "maxItems": PRODUK_PER_KATEGORI}
    resp = requests.post(url, params=params, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()  # list of dataset items


def apify_to_produk(raw_items: list[dict]) -> list[dict]:
    """SESUAIKAN INI setelah lihat bentuk item asli dari dataset Apify-mu."""
    out = []
    for it in raw_items:
        out.append({
            "nama": it.get("name") or it.get("title", ""),
            "toko": it.get("shopName") or it.get("shop", {}).get("name", "-"),
            "harga": int(it.get("price") or 0),
            "terjual_minggu_ini": int(it.get("sold") or it.get("historicalSold") or 0),
            "rating": float(it.get("rating") or it.get("itemRating") or 0),
        })
    return out


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def ambil_kategori_third_party() -> list[dict]:
    kategori_out = []
    for slug, nama, keyword in KEYWORDS:
        print(f"Mengambil: {nama} ({keyword}) via {SOURCE}")
        if SOURCE == "rapidapi":
            if not RAPIDAPI_KEY:
                raise RuntimeError("RAPIDAPI_KEY belum diisi.")
            raw = rapidapi_search(keyword, limit=PRODUK_PER_KATEGORI)
            produk = rapidapi_to_produk(raw)
        elif SOURCE == "apify":
            if not APIFY_TOKEN:
                raise RuntimeError("APIFY_TOKEN belum diisi.")
            raw = apify_run_sync(keyword)
            produk = apify_to_produk(raw)
        else:
            raise ValueError(f"SOURCE tidak dikenal: {SOURCE}")

        produk = sorted(produk, key=lambda p: p["terjual_minggu_ini"], reverse=True)[:PRODUK_PER_KATEGORI]
        for i, p in enumerate(produk, start=1):
            p["rank"] = i
        kategori_out.append({"id": slug, "nama": nama, "produk": produk})
        time.sleep(1.5)
    return kategori_out


def main():
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        current = json.load(f)

    shopee_kategori = ambil_kategori_third_party()

    for pf in current["platforms"]:
        if pf["id"] == "shopee":
            pf["kategori"] = shopee_kategori

    now = datetime.now(WIB)
    current["terakhir_diperbarui"] = now.isoformat()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    print(f"Blok Shopee diperbarui via {SOURCE} ({len(shopee_kategori)} kategori).")


if __name__ == "__main__":
    # Mode debug: `python scripts/shopee_third_party.py debug "power bank"`
    # Cetak respons MENTAH satu kali (tanpa menyentuh products.json) supaya
    # kamu bisa cek struktur field aslinya sebelum menyesuaikan
    # rapidapi_to_produk() / apify_to_produk() di atas.
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        kw = sys.argv[2] if len(sys.argv) > 2 else "power bank"
        print(f"--- Mengambil contoh respons mentah untuk '{kw}' via {SOURCE} ---")
        if SOURCE == "rapidapi":
            raw = rapidapi_search(kw)
        else:
            raw = apify_run_sync(kw)
        print(json.dumps(raw, ensure_ascii=False, indent=2)[:4000])
        print("\n--- (dipotong 4000 karakter kalau lebih panjang) ---")
        print("Salin bagian ini (SEMBUNYIKAN dulu data pribadi/token kalau ada) "
              "untuk disesuaikan pemetaan field-nya.")
    else:
        main()

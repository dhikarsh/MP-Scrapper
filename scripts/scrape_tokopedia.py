"""
Scraper Tokopedia (PELENGKAP, bukan pengganti) -- pakai Playwright.

BACA DULU
=========
- Ini scraping halaman publik Tokopedia (seperti browser biasa membuka
  halaman pencarian/kategori), TANPA login, TANPA bypass CAPTCHA, dan
  TANPA mencoba menyamar sebagai bukan-bot. Kalau Tokopedia menampilkan
  captcha/blokir, skrip ini akan berhenti dan gagal -- itu memang tanda
  proteksi mereka bekerja sesuai rancangannya, bukan sesuatu yang skrip
  ini coba akali.
- robots.txt Tokopedia secara teknis tidak melarang crawling halaman
  kategori/pencarian, TAPI Syarat & Ketentuan Tokopedia kemungkinan tetap
  melarang scraping otomatis sebagai klausul kontrak. Risiko itu ada di
  luar kendali skrip ini -- pakai untuk riset internal skala kecil, bukan
  dijalankan terus-menerus/skala besar.
- Tokopedia adalah situs React/Next.js -- kontennya dirender lewat
  JavaScript, karena itu skrip ini pakai Playwright (headless browser
  sungguhan), bukan requests+BeautifulSoup biasa.
- CSS selector Tokopedia ter-hash dan SERING BERUBAH setiap mereka
  deploy ulang frontend. Selector di bawah adalah titik awal yang wajar,
  BUKAN jaminan akan selalu jalan. Kalau hasilnya kosong, buka halaman
  pencarian Tokopedia manual di browser, klik kanan salah satu kartu
  produk -> Inspect, lalu update SELECTORS di bawah sesuai yang kamu
  lihat saat itu.
- Jalankan dengan jeda antar-kategori yang wajar (sudah diberi delay di
  bawah) -- jangan dipercepat/diparalelkan, supaya tidak membebani server
  Tokopedia atau memicu blokir IP kantor.

Instalasi
=========
    pip install playwright
    playwright install chromium

Cara pakai
==========
    python scripts/scrape_tokopedia.py
Hasil ditulis ke data/products.json, HANYA blok platforms[id=tokopedia].
Blok "shopee" tidak disentuh sama sekali.
"""

import json
import time
import re
from datetime import datetime, timezone, timedelta

from playwright.sync_api import sync_playwright

OUTPUT_PATH = "data/products.json"
WIB = timezone(timedelta(hours=7))

# Kategori Tokopedia yang mau dipantau. "keyword" dipakai untuk halaman
# pencarian (lebih stabil daripada halaman /p/<slug> yang kadang berubah
# struktur). Sesuaikan bebas.
TOKOPEDIA_CATEGORIES = [
    ("elektronik", "Elektronik", "elektronik"),
    ("fashion-pria", "Fashion Pria", "kaos pria"),
    ("fashion-wanita", "Fashion Wanita", "atasan wanita"),
    ("kecantikan", "Kecantikan", "skincare"),
    ("rumah-tangga", "Rumah Tangga", "peralatan dapur"),
    ("handphone-tablet", "Handphone & Tablet", "case hp"),
]

PRODUK_PER_KATEGORI = 10

# PENTING: kode urutan "Terjual Terbanyak" (parameter ob=... / orderBy=...)
# TIDAK ditebak di sini karena berisiko salah. Cara amannya:
#   1. Buka tokopedia.com/search?q=<keyword> di browser.
#   2. Klik filter urutkan -> "Terjual Terbanyak".
#   3. Copy parameter dari URL hasilnya (mis. "&ob=5") dan tempel di
#      SORT_PARAM di bawah.
SORT_PARAM = ""  # contoh: "&ob=5"  -- ISI SETELAH KAMU VERIFIKASI SENDIRI

# Titik awal selector -- KEMUNGKINAN BESAR PERLU DIPERBARUI, lihat catatan
# di atas. Beberapa fallback disediakan supaya lebih tahan perubahan kecil.
SELECTORS = {
    "card": '[data-testid="divProductWrapper"], div[class*="product-card"], a[href*="tokopedia.com"][class*="pcv"]',
    "nama": '[data-testid="linkProductName"], span[class*="prd_link-product-name"], span[class*="product-name"]',
    "harga": '[data-testid="linkProductPrice"], div[class*="prd_link-product-price"], div[class*="product-price"]',
    "toko": '[data-testid="linkShopName"], span[class*="prd_link-shop-name"], span[class*="shop-name"]',
    "terjual": '[data-testid="labelProductSold"], span[class*="prd_label-integrity"], span[class*="product-sold"]',
    "rating": '[data-testid="icnStarRating"], span[class*="prd_rating"]',
}


def parse_harga(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text or "")
    return int(digits) if digits else 0


def parse_terjual(text: str) -> int:
    if not text:
        return 0
    text = text.lower().replace("terjual", "").strip()
    mult = 1
    if "rb" in text or "k" in text:
        mult = 1000
        text = text.replace("rb", "").replace("k", "")
    if "+" in text:
        text = text.replace("+", "")
    digits = re.sub(r"[^\d.]", "", text)
    try:
        return int(float(digits) * mult) if digits else 0
    except ValueError:
        return 0


def scrape_kategori(page, keyword: str, limit: int) -> list[dict]:
    url = f"https://www.tokopedia.com/search?q={keyword.replace(' ', '+')}{SORT_PARAM}"
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2500)  # beri waktu render + lazy-load

    cards = page.query_selector_all(SELECTORS["card"])
    if not cards:
        print(f"  [!] Tidak ada kartu produk ditemukan untuk '{keyword}'. "
              f"Selector kemungkinan sudah usang -- cek DevTools & update SELECTORS.")
        return []

    hasil = []
    for card in cards[:limit]:
        def teks(sel):
            el = card.query_selector(sel)
            return el.inner_text().strip() if el else ""

        nama = teks(SELECTORS["nama"])
        if not nama:
            continue
        hasil.append({
            "nama": nama,
            "toko": teks(SELECTORS["toko"]) or "-",
            "harga": parse_harga(teks(SELECTORS["harga"])),
            "terjual_minggu_ini": parse_terjual(teks(SELECTORS["terjual"])),
            "rating": 0.0,  # rating sering berupa gambar bintang, bukan teks -- isi manual bila perlu
        })
    return hasil


def ambil_kategori_tokopedia() -> list[dict]:
    kategori_out = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
        for slug, nama, keyword in TOKOPEDIA_CATEGORIES:
            print(f"Mengambil kategori: {nama} ({keyword})")
            produk = scrape_kategori(page, keyword, PRODUK_PER_KATEGORI)
            produk = sorted(produk, key=lambda x: x["terjual_minggu_ini"], reverse=True)
            for i, pr in enumerate(produk, start=1):
                pr["rank"] = i
            kategori_out.append({
                "id": slug, "nama": nama,
                "url": f"https://www.tokopedia.com/search?q={keyword.replace(' ', '+')}",
                "produk": produk,
            })
            time.sleep(3)  # jeda antar-kategori -- jangan dipercepat
        browser.close()
    return kategori_out


def main():
    with open(OUTPUT_PATH, encoding="utf-8") as f:
        current = json.load(f)

    tokopedia_kategori = ambil_kategori_tokopedia()

    updated = False
    for pf in current["platforms"]:
        if pf["id"] == "tokopedia":
            pf["kategori"] = tokopedia_kategori
            updated = True
    if not updated:
        current["platforms"].append({
            "id": "tokopedia", "nama": "Tokopedia (kini bagian TikTok Shop)",
            "kategori": tokopedia_kategori,
        })

    now = datetime.now(WIB)
    current["terakhir_diperbarui"] = now.isoformat()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    print(f"Blok Tokopedia di {OUTPUT_PATH} diperbarui ({len(tokopedia_kategori)} kategori).")


if __name__ == "__main__":
    main()

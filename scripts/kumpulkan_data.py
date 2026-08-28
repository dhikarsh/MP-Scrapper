"""
Pengumpulan data produk terlaris mingguan -- versi API resmi, per kategori asli.

RINGKASAN
=========
- SHOPEE: pakai Shopee Affiliate Open API (GraphQL), query `productOfferV2`
  dengan parameter `productCatId` (category id ASLI dari URL kategori Shopee-mu)
  dan `sortType: 2` (urut berdasarkan penjualan). Ini mengambil produk terlaris
  langsung per kategori resmi Shopee -- bukan tebak-tebakan lewat kata kunci.
- TOKOPEDIA: sejak integrasi seller Tokopedia (pasar ID) dipindah ke TikTok
  Shop Partner Center (per 30 Sept 2025), TIDAK ada API resmi market-wide
  untuk "produk terlaris lintas semua toko" di Tokopedia/TikTok Shop --
  sama seperti Shopee Seller API, API itu hanya untuk toko sendiri. Karena
  itu skrip ini TIDAK menyentuh blok "tokopedia" di products.json -- bagian
  itu tetap diisi/diupdate manual oleh tim langsung di file JSON (lihat
  README.md bagian "Tokopedia / TikTok Shop").
- METODE PEMBAYARAN dihapus dari model data -- tidak ada API resmi manapun
  (Shopee maupun TikTok Shop/Tokopedia) yang mengekspos data ini per produk.

Cara pakai
==========
1. Isi SHOPEE_APP_ID, SHOPEE_SECRET, SHOPEE_GRAPHQL_HOST lewat environment
   variable (lihat README.md untuk cara dapatkan & GitHub Secrets).
2. Sesuaikan/tambah entri di SHOPEE_CATEGORIES kalau kategori kamu berubah
   (catid diambil dari URL: https://shopee.co.id/<slug>-cat.<CATID>).
3. Jalankan: python scripts/kumpulkan_data.py
   -> Hanya blok platforms[id=shopee].kategori di data/products.json yang
      ditimpa dengan hasil API; blok "tokopedia" dibiarkan apa adanya.
"""

import hashlib
import json
import os
import time
from datetime import datetime, timezone, timedelta

import requests

SHOPEE_APP_ID = os.environ.get("SHOPEE_APP_ID", "")
SHOPEE_SECRET = os.environ.get("SHOPEE_SECRET", "")
# WAJIB diverifikasi di dashboard Open API akunmu -- lihat README.md.
SHOPEE_GRAPHQL_HOST = os.environ.get("SHOPEE_GRAPHQL_HOST", "open-api.affiliate.shopee.co.id")

OUTPUT_PATH = "data/products.json"
WIB = timezone(timedelta(hours=7))

# Diambil langsung dari daftar URL kategori Shopee yang kamu simpan.
# Tambah/hapus/ubah bebas -- catid selalu angka setelah "-cat." di URL.
SHOPEE_CATEGORIES = [
    ("electronics", "Electronics", 11044258),
    ("computer-accessories", "Computer Accessories", 11044364),
    ("mobile-accessories", "Mobile Accessories", 11044458),
    ("men-clothes", "Men Clothes", 11042849),
    ("men-shoes", "Men Shoes", 11042985),
    ("men-bags", "Men Bags", 11043011),
    ("fashion-accessories", "Fashion Accessories", 11042921),
    ("watches", "Watches", 11042900),
    ("health", "Health", 11043279),
    ("hobby-collection", "Hobby & Collection", 11043572),
    ("food-beverages", "Food & Beverages", 11043451),
    ("beauty-care", "Beauty Care", 11043145),
    ("home-living", "Home & Living", 11043778),
    ("women-clothes", "Women Clothes", 11042745),
    ("muslim-fashion", "Muslim Fashion", 11042684),
    ("baby-kids-fashion", "Baby & Kids Fashion", 11043031),
    ("mom-baby", "Mom & Baby", 11043350),
    ("women-shoes", "Women Shoes", 11042604),
    ("women-bags", "Women Bags", 11042642),
    ("automotive", "Automotive", 11043660),
    ("sports-outdoor", "Sports & Outdoor", 11043958),
    ("souvenir-party-supplies", "Souvenir & Party Supplies", 11116633),
    ("vouchers", "Vouchers", 11044631),
    ("stationery-books", "Stationery & Books", 11044123),
    ("photography", "Photography", 11044588),
    ("deals-nearby", "Deals Nearby", 11105951),
]

PRODUK_PER_KATEGORI = 10


def shopee_signature(payload: str, timestamp: int) -> str:
    factor = f"{SHOPEE_APP_ID}{timestamp}{payload}{SHOPEE_SECRET}"
    return hashlib.sha256(factor.encode()).hexdigest()


def shopee_product_offer_by_category(cat_id: int, limit: int = 10) -> list[dict]:
    """Ambil produk terlaris (sortType 2 = Sales) untuk satu productCatId."""
    query = """
    query Fetch($catId: Int, $page: Int, $limit: Int) {
      productOfferV2(productCatId: $catId, sortType: 2, page: $page, limit: $limit) {
        nodes {
          itemId
          productName
          shopName
          priceMin
          priceMax
          sales
          ratingStar
          offerLink
        }
      }
    }
    """
    body = json.dumps({"query": query, "variables": {"catId": cat_id, "page": 1, "limit": limit}})
    ts = int(time.time())
    sig = shopee_signature(body, ts)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={SHOPEE_APP_ID},Timestamp={ts},Signature={sig}",
    }
    url = f"https://{SHOPEE_GRAPHQL_HOST}/graphql"
    resp = requests.post(url, data=body, headers=headers, timeout=20)
    resp.raise_for_status()
    result = resp.json()
    if "errors" in result:
        raise RuntimeError(f"Shopee API error untuk productCatId {cat_id}: {result['errors']}")
    return result["data"]["productOfferV2"]["nodes"]


def bentuk_produk(node: dict, rank: int) -> dict:
    return {
        "rank": rank,
        "nama": node["productName"],
        "toko": node.get("shopName", "-"),
        "harga": int(node.get("priceMin") or 0),
        "terjual_minggu_ini": int(node.get("sales") or 0),
        "rating": float(node.get("ratingStar") or 0),
    }


def ambil_kategori_shopee() -> list[dict]:
    if not SHOPEE_APP_ID or not SHOPEE_SECRET:
        raise RuntimeError(
            "SHOPEE_APP_ID / SHOPEE_SECRET belum diisi. Set sebagai "
            "environment variable atau GitHub Actions secret -- lihat README.md."
        )
    kategori_out = []
    for slug, nama, catid in SHOPEE_CATEGORIES:
        nodes = shopee_product_offer_by_category(catid, limit=PRODUK_PER_KATEGORI)
        produk = sorted(
            [bentuk_produk(n, 0) for n in nodes],
            key=lambda p: p["terjual_minggu_ini"], reverse=True,
        )
        for i, p in enumerate(produk, start=1):
            p["rank"] = i
        kategori_out.append({
            "id": slug, "nama": nama, "shopee_cat_id": catid,
            "url": f"https://shopee.co.id/{nama.replace(' ', '-').replace('&','')}-cat.{catid}",
            "produk": produk,
        })
        time.sleep(0.3)  # jaga-jaga terhadap rate limit
    return kategori_out


def main():
    if not os.path.exists(OUTPUT_PATH):
        raise SystemExit(f"{OUTPUT_PATH} belum ada. Jalankan dari root project.")

    with open(OUTPUT_PATH, encoding="utf-8") as f:
        current = json.load(f)

    shopee_kategori = ambil_kategori_shopee()

    updated = False
    for pf in current["platforms"]:
        if pf["id"] == "shopee":
            pf["kategori"] = shopee_kategori
            updated = True
    if not updated:
        current["platforms"].insert(0, {"id": "shopee", "nama": "Shopee", "kategori": shopee_kategori})

    now = datetime.now(WIB)
    current["terakhir_diperbarui"] = now.isoformat()
    current["minggu"] = f"Minggu berjalan (diperbarui {now.strftime('%d %b %Y')})"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    print(f"Blok Shopee di {OUTPUT_PATH} berhasil diperbarui ({len(shopee_kategori)} kategori).")


if __name__ == "__main__":
    main()

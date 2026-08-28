import os
import json
import requests
import time
from datetime import datetime

TOKEN = os.getenv("APIFY_TOKEN")
if not TOKEN:
    raise Exception("APIFY_TOKEN tidak ditemukan di environment!")

ACTOR_ID = "xtracto/shopee-scraper"
MAX_PRODUCTS = 10  # Ambil 10 produk teratas per kategori

# Daftar 26 kategori
CATEGORIES = [
    {"id": "electronics", "url": "https://shopee.co.id/Electronics-cat.11044258", "nama": "Elektronik"},
    {"id": "computer", "url": "https://shopee.co.id/Computer-Accessories-cat.11044364", "nama": "Aksesoris Komputer"},
    {"id": "mobile", "url": "https://shopee.co.id/Mobile-Accessories-cat.11044458", "nama": "Aksesoris HP"},
    {"id": "men-clothes", "url": "https://shopee.co.id/Men-Clothes-cat.11042849", "nama": "Pakaian Pria"},
    {"id": "men-shoes", "url": "https://shopee.co.id/Men-Shoes-cat.11042985", "nama": "Sepatu Pria"},
    {"id": "men-bags", "url": "https://shopee.co.id/Men-Bags-cat.11043011", "nama": "Tas Pria"},
    {"id": "fashion-acc", "url": "https://shopee.co.id/Fashion-Accessories-cat.11042921", "nama": "Aksesoris Fashion"},
    {"id": "watches", "url": "https://shopee.co.id/Watches-cat.11042900", "nama": "Jam Tangan"},
    {"id": "health", "url": "https://shopee.co.id/Health-cat.11043279", "nama": "Kesehatan"},
    {"id": "hobby", "url": "https://shopee.co.id/Hobby-Collection-cat.11043572", "nama": "Hobi & Koleksi"},
    {"id": "food", "url": "https://shopee.co.id/Food-Beverages-cat.11043451", "nama": "Makanan & Minuman"},
    {"id": "beauty", "url": "https://shopee.co.id/Beauty-Care-cat.11043145", "nama": "Perawatan Kecantikan"},
    {"id": "home", "url": "https://shopee.co.id/Home-Living-cat.11043778", "nama": "Rumah Tangga"},
    {"id": "women-clothes", "url": "https://shopee.co.id/Women-Clothes-cat.11042745", "nama": "Pakaian Wanita"},
    {"id": "muslim", "url": "https://shopee.co.id/Muslim-Fashion-cat.11042684", "nama": "Fashion Muslim"},
    {"id": "baby-kids", "url": "https://shopee.co.id/Baby-Kids-Fashion-cat.11043031", "nama": "Fashion Bayi & Anak"},
    {"id": "mom-baby", "url": "https://shopee.co.id/Mom-Baby-cat.11043350", "nama": "Ibu & Bayi"},
    {"id": "women-shoes", "url": "https://shopee.co.id/Women-Shoes-cat.11042604", "nama": "Sepatu Wanita"},
    {"id": "women-bags", "url": "https://shopee.co.id/Women-Bags-cat.11042642", "nama": "Tas Wanita"},
    {"id": "automotive", "url": "https://shopee.co.id/Automotive-cat.11043660", "nama": "Otomotif"},
    {"id": "sports", "url": "https://shopee.co.id/Sports-Outdoor-cat.11043958", "nama": "Olahraga & Outdoor"},
    {"id": "souvenir", "url": "https://shopee.co.id/Souvenir-Party-Supplies-cat.11116633", "nama": "Souvenir & Pesta"},
    {"id": "vouchers", "url": "https://shopee.co.id/Vouchers-cat.11044631", "nama": "Voucher"},
    {"id": "stationery", "url": "https://shopee.co.id/Stationery-Books-cat.11044123", "nama": "Alat Tulis & Buku"},
    {"id": "photography", "url": "https://shopee.co.id/Photography-cat.11044588", "nama": "Fotografi"},
    {"id": "deals", "url": "https://shopee.co.id/Deals-Nearby-cat.11105951", "nama": "Deals Nearby"}
]

def scrape_category(cat_url, max_items=10):
    """Panggil Apify Actor untuk 1 kategori"""
    path = cat_url.replace("https://shopee.co.id", "")
    payload = {
        "mode": "category",
        "category": path,
        "country": "id",
        "maxProducts": max_items,
        "sort": "sales",
        "fetchDetail": True,
        "delay": 1
    }
    
    # Jalankan Actor
    run_res = requests.post(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={TOKEN}",
        json=payload
    )
    run_res.raise_for_status()
    run_id = run_res.json()["data"]["id"]
    
    # Tunggu selesai
    while True:
        status_res = requests.get(
            f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}?token={TOKEN}"
        )
        status_res.raise_for_status()
        status = status_res.json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "ABORTED"]:
            raise Exception(f"Actor gagal: {status}")
        time.sleep(5)
    
    # Ambil hasil
    dataset_res = requests.get(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}/dataset/items?token={TOKEN}&format=json&limit={max_items}"
    )
    dataset_res.raise_for_status()
    return dataset_res.json()

def main():
    print(f"🔄 Memulai scraping {len(CATEGORIES)} kategori...")
    results = []
    
    for i, cat in enumerate(CATEGORIES):
        print(f"  [{i+1}/{len(CATEGORIES)}] Mengambil {cat['nama']}...")
        try:
            produk = scrape_category(cat["url"], MAX_PRODUCTS)
            results.append({
                "id": cat["id"],
                "nama": cat["nama"],
                "produk": [
                    {
                        "nama": p.get("name", "Tidak ada nama"),
                        "toko": p.get("shop_name", "Tidak ada toko"),
                        "harga": p.get("price", 0),
                        "terjual_minggu_ini": p.get("sold_count", 0),
                        "rating": p.get("rating", 0),
                        "url": p.get("url", "#"),
                        "image": p.get("image_url", "")
                    }
                    for p in produk
                ]
            })
        except Exception as e:
            print(f"  ❌ Gagal: {e}")
            results.append({"id": cat["id"], "nama": cat["nama"], "produk": []})
    
    # Simpan ke JSON
    final_data = {
        "minggu": f"Minggu ke-{datetime.now().strftime('%W')} ({datetime.now().strftime('%d %B %Y')})",
        "terakhir_diperbarui": datetime.now().isoformat(),
        "platforms": [
            {"id": "shopee", "nama": "Shopee", "kategori": results}
        ]
    }
    
    # Buat folder data jika belum ada
    os.makedirs("data", exist_ok=True)
    
    with open("data/products.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Selesai! Total {len(results)} kategori diproses.")
    print(f"📁 Data disimpan di data/products.json")

if __name__ == "__main__":
    main()
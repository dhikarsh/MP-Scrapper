# Cara aman menyimpan token/API key

**Jangan pernah** tempel token langsung di file `.py`, di chat AI mana pun,
di screenshot, atau di Slack/WhatsApp. Sekali kelihatan orang lain (atau
tersimpan di riwayat chat), anggap sudah bocor — rotate/cabut segera.

## Setup lokal (sekali saja)

1. Buat file bernama `.env` di root project (sejajar dengan folder `scripts/`):

   ```
   SHOPEE_THIRD_PARTY_SOURCE=rapidapi
   RAPIDAPI_KEY=isi_token_baru_di_sini
   RAPIDAPI_HOST=shopee-product-scraper2.p.rapidapi.com
   RAPIDAPI_ENDPOINT=/search
   APIFY_TOKEN=isi_token_baru_di_sini
   APIFY_ACTOR_ID=fmKWN5uByUCIy2Sam
   ```

2. Tambahkan baris ini ke file `.gitignore` di root project (buat kalau
   belum ada), supaya `.env` **tidak pernah** ikut ter-upload ke GitHub:

   ```
   .env
   ```

3. Install dependensi tambahan sekali saja:

   ```bash
   pip install python-dotenv
   ```

Setelah itu jalankan skrip seperti biasa — `.env` otomatis terbaca lewat
`load_dotenv()` yang sudah ditambahkan di `scripts/shopee_third_party.py`.
Tidak perlu lagi `export` manual satu-satu di terminal tiap kali buka sesi baru.

## Untuk GitHub Actions (otomatisasi mingguan)

Token **tidak** ditaruh di `.env` untuk ini — pakai **GitHub Secrets**
(Settings → Secrets and variables → Actions), seperti sudah diatur di
`.github/workflows/update-data.yml`.

## Kalau token pernah tidak sengaja terekspos (tertempel di chat, ke-commit ke Git, dll)

Anggap token itu bocor, meskipun kelihatannya "cuma untuk sesaat":
- **RapidAPI**: rapidapi.com → My Apps / Security → revoke key lama → generate baru.
- **Apify**: console.apify.com/settings/integrations → rotate token (token lama tetap jalan 24 jam supaya sempat diganti di semua tempat).

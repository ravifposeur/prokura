# Prokura

Monorepo lokal Prokura dengan satu sumber data:

- `prokura-api` - Express API untuk customer web dan admin.
- `prokura-web` - Next.js customer web.
- `prokura-admin` - Streamlit admin yang membaca API.
- `docker-compose.yml` - PostgreSQL lokal untuk data Prokura.

Remote Git root saat ini terhubung ke `https://github.com/ravifposeur/prokura.git`.

## Port Lokal

| Service | URL |
| --- | --- |
| Customer web | http://127.0.0.1:3000 |
| Admin web | http://127.0.0.1:8501 |
| API | http://127.0.0.1:5000 |
| PostgreSQL Docker | localhost:5439 |

Database default:

- database: `prokuradb`
- user: `prokura`
- password: `prokura`

## Menjalankan

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Start API:

```powershell
cd prokura-api
$env:PGHOST="127.0.0.1"
$env:PGPORT="5439"
$env:PGUSER="prokura"
$env:PGPASSWORD="prokura"
$env:PGDATABASE="prokuradb"
npm run dev
```

Start customer web:

```powershell
cd prokura-web
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:5000"
npx next dev -p 3000
```

Start admin:

```powershell
cd prokura-admin
$env:PROKURA_API_BASE_URL="http://127.0.0.1:5000"
python -m streamlit run app3.py --server.port 8501 --server.address 127.0.0.1
```

## Validasi Cepat

```bash
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/api/admin/summary
curl http://127.0.0.1:5000/api/products
```

Expected summary seed awal:

```json
{"companies":3,"products":5,"orders":3,"pending_orders":1}
```

## Catatan Data

Data saat ini cukup untuk prototype integrasi API tunggal, tetapi belum final sebagai data produksi. Yang masih perlu diminta:

- Dari Ravief: dump PostgreSQL atau file SQL yang sebelumnya disebut README lama (`2.horeca_sql.sql`, `3.horeca_product_images.sql`).
- Dari Tama: dump/admin data final dan konfirmasi field yang dibutuhkan admin.

File admin MySQL lama disimpan di `prokura-admin/app_mysql_legacy.py` sebagai referensi migrasi fitur.

## Status Migrasi Admin Legacy

`prokura-admin/app3.py` adalah versi aktif berbasis API/PostgreSQL. Modul yang sudah dimigrasikan dari legacy:

- Dashboard Utama: KPI, pesanan terbaru, stok kritis, grafik revenue, grafik status PO.
- Manajemen Stok Gudang: katalog/ringkasan, tambah produk, import CSV, update produk, hapus produk bila belum dipakai PO.
- Manajemen Klien B2B: daftar klien, tambah klien, daftar dan tambah pengguna.
- Manajemen Pesanan PO: daftar PO, detail item, buat PO baru, update status.
- Laporan & Analitik: filter tanggal, KPI revenue, revenue bulanan, revenue segmen, top produk, top klien, export CSV.
- Portal Pembelian User: login email, registrasi perusahaan/user, katalog produk, keranjang, checkout, riwayat PO, detail PO.
- Light theme dan CSS portal/kartu produk/cart/badge/header/sidebar mengikuti styling legacy Streamlit.

Yang belum 1:1 penuh:

- Verifikasi pixel-perfect berbasis screenshot belum bisa dilakukan dari Codex karena browser in-app gagal start di sandbox Windows. Validasi runtime Streamlit dan API sudah lewat.

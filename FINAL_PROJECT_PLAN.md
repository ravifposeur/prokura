# Perencanaan Proyek 2 Final Project - Prokura

## Instruksi Dosen

Proyek 2 adalah mengimplementasikan sebuah sistem e-commerce yang mengintegrasikan beberapa sistem.

Ketentuan utama:

1. Integrasi antar sistem/perusahaan harus menggunakan microservice.
2. Setiap sistem perusahaan wajib memiliki fitur UI/UX, misalnya:
   - Penambahan barang baru.
   - Penambahan stok.
   - Pembelian barang oleh customer.
   - Pencarian barang.
   - Rekapitulasi penjualan.
3. Setiap anggota tim harus mengimplementasikan dua fitur.
4. Saat presentasi demo, setiap anggota wajib menampilkan minimal satu fitur yang dibuat, meliputi:
   - SQL query.
   - Kode program.
   - Perubahan pada database.

## Anggota Tim

| Nama | NIM |
| --- | --- |
| Ravif Gayuh Wicaksono | 24/540583/PA/22953 |
| Aloysius Pijar Hutama Indrianto | 24/534591/PA/22675 |
| Indratanaya Budiman | 24/534784/PA/22683 |
| Gilbert Nathaniel | 24/533877/PA/22623 |
| Pison Golda Mountera | 24/543770/PA/23107 |

## Konsep Sistem

Prokura digunakan sebagai sistem e-commerce B2B untuk rantai pasok HoReCa. Sistem dibagi menjadi beberapa microservice agar integrasi antar modul/perusahaan tidak dilakukan langsung ke database, tetapi melalui API.

Rancangan microservice:

| Microservice | Tanggung Jawab | Contoh Endpoint |
| --- | --- | --- |
| Catalog Service | Data produk, kategori, pencarian produk | `GET /api/products`, `POST /api/products` |
| Inventory Service | Stok gudang, penambahan stok, riwayat stok | `PATCH /api/products/:id/stock`, `GET /api/inventory/movements` |
| Customer Service | Perusahaan B2B dan user customer | `GET /api/companies`, `POST /api/users` |
| Order Service | Cart checkout, purchase order, status PO | `POST /api/orders`, `PATCH /api/orders/:id/status` |
| Reporting Service | Rekap penjualan, top produk, top customer | `GET /api/reports/sales` |

Implementasi awal masih dapat berada dalam repo yang sama, tetapi batas integrasi harus dibuat melalui endpoint API. UI admin dan UI customer tidak boleh query database langsung.

## Pembagian Fitur

Setiap anggota mendapat dua fitur. Pembagian dibuat agar beban seimbang: setiap anggota memegang satu fitur transaksi/perubahan data dan satu fitur tampilan/rekap/pencarian.

| Anggota | Fitur 1 | Fitur 2 | Microservice Utama |
| --- | --- | --- | --- |
| Ravif Gayuh Wicaksono | Penambahan barang baru | Pencarian dan filter barang | Catalog Service |
| Aloysius Pijar Hutama Indrianto | Penambahan stok barang | Riwayat pergerakan stok | Inventory Service |
| Indratanaya Budiman | Pembelian barang oleh customer | Riwayat pembelian customer | Order Service |
| Gilbert Nathaniel | Manajemen customer/perusahaan | Manajemen user perusahaan | Customer Service |
| Pison Golda Mountera | Rekapitulasi penjualan | Analitik top produk dan top customer | Reporting Service |

## Detail Fitur Per Anggota

### 1. Ravif Gayuh Wicaksono - Catalog Service

#### Fitur 1: Penambahan Barang Baru

Deskripsi:
Admin dapat menambahkan produk baru melalui UI admin dengan data SKU, nama produk, kategori, satuan, harga dasar, dan stok awal.

UI/UX:
- Form tambah produk di admin.
- Validasi SKU unik.
- Pesan sukses/gagal.
- Produk baru langsung muncul di katalog.

SQL query demo:

```sql
INSERT INTO products (sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang)
VALUES ('SKU-DEMO-001', 'Demo Product', 'Bahan Pokok', 'Kg', 25000, 50)
RETURNING product_id, sku, nama_produk, stok_gudang;
```

Kode program yang ditunjukkan:
- Endpoint `POST /api/products`.
- Form tambah produk di `prokura-admin/app3.py`.

Perubahan database:
- Baris baru masuk ke tabel `products`.

#### Fitur 2: Pencarian dan Filter Barang

Deskripsi:
Customer/admin dapat mencari produk berdasarkan nama/SKU dan memfilter berdasarkan kategori/stok.

UI/UX:
- Search input.
- Filter kategori.
- Checkbox stok tersedia.
- Tabel/kartu produk terfilter.

SQL query demo:

```sql
SELECT product_id, sku, nama_produk, kategori, harga_dasar, stok_gudang
FROM products
WHERE LOWER(nama_produk) LIKE LOWER('%muffin%')
   OR LOWER(sku) LIKE LOWER('%muffin%')
ORDER BY nama_produk;
```

Kode program yang ditunjukkan:
- Endpoint `GET /api/products`.
- Filter UI katalog di admin/customer web.

Perubahan database:
- Tidak selalu mengubah database, tetapi demo dapat digabungkan dengan Fitur 1: produk baru yang baru ditambahkan langsung dapat dicari.

### 2. Aloysius Pijar Hutama Indrianto - Inventory Service

#### Fitur 1: Penambahan Stok Barang

Deskripsi:
Admin gudang dapat menambah stok produk tanpa mengubah data produk lain.

UI/UX:
- Pilih produk.
- Input jumlah stok masuk.
- Input catatan.
- Stok produk bertambah.

SQL query demo:

```sql
UPDATE products
SET stok_gudang = stok_gudang + 25
WHERE product_id = 1
RETURNING product_id, nama_produk, stok_gudang;
```

Kode program yang ditunjukkan:
- Endpoint rencana `PATCH /api/products/:product_id/stock`.
- Form penambahan stok di modul Inventory admin.

Perubahan database:
- Kolom `products.stok_gudang` bertambah.

#### Fitur 2: Riwayat Pergerakan Stok

Deskripsi:
Setiap perubahan stok dicatat agar dapat diaudit, baik stok masuk maupun stok keluar akibat checkout.

UI/UX:
- Tabel riwayat stok.
- Filter produk dan tipe pergerakan.
- Informasi tanggal, jumlah, dan catatan.

SQL query demo:

```sql
CREATE TABLE inventory_movements (
    movement_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    movement_type VARCHAR(30) NOT NULL,
    quantity INT NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO inventory_movements (product_id, movement_type, quantity, note)
VALUES (1, 'STOCK_IN', 25, 'Restock demo presentasi');
```

Kode program yang ditunjukkan:
- Endpoint rencana `GET /api/inventory/movements`.
- Insert movement saat stok ditambah.

Perubahan database:
- Tabel baru `inventory_movements`.
- Baris baru setiap stok berubah.

### 3. Indratanaya Budiman - Order Service

#### Fitur 1: Pembelian Barang oleh Customer

Deskripsi:
Customer memilih produk, memasukkan ke cart, lalu checkout menjadi purchase order.

UI/UX:
- Kartu produk.
- Keranjang belanja.
- Total belanja.
- Tombol checkout.
- Notifikasi PO berhasil dibuat.

SQL query demo:

```sql
INSERT INTO purchaseorders (company_id, dibuat_oleh, metode_pembayaran, total_tagihan)
VALUES (1, 1, 'Tempo_30_Hari', 250000)
RETURNING po_id;

INSERT INTO orderdetails (po_id, product_id, kuantitas, harga_final)
VALUES (currval('purchaseorders_po_id_seq'), 1, 5, 50000);

UPDATE products
SET stok_gudang = stok_gudang - 5
WHERE product_id = 1;
```

Kode program yang ditunjukkan:
- Endpoint `POST /api/orders`.
- UI checkout di portal pembelian.

Perubahan database:
- Baris baru di `purchaseorders`.
- Baris baru di `orderdetails`.
- Stok di `products` berkurang.

#### Fitur 2: Riwayat Pembelian Customer

Deskripsi:
Customer dapat melihat daftar PO perusahaan dan detail item setiap PO.

UI/UX:
- Tabel riwayat PO.
- Detail PO dalam expander/modal.
- Status PO dan total tagihan.

SQL query demo:

```sql
SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
       po.tanggal_dipesan, u.nama_lengkap AS pembuat
FROM purchaseorders po
JOIN users u ON po.dibuat_oleh = u.user_id
WHERE po.company_id = 1
ORDER BY po.tanggal_dipesan DESC;
```

Kode program yang ditunjukkan:
- Endpoint `GET /api/companies/:company_id/orders`.
- UI Riwayat Pesanan Saya.

Perubahan database:
- Data riwayat berubah setelah checkout pada Fitur 1.

### 4. Gilbert Nathaniel - Customer Service

#### Fitur 1: Manajemen Customer/Perusahaan

Deskripsi:
Admin dapat menambahkan perusahaan/customer B2B baru.

UI/UX:
- Form tambah perusahaan.
- Input nama perusahaan, NPWP, segmen industri, limit kredit.
- Tabel daftar perusahaan.

SQL query demo:

```sql
INSERT INTO companies (nama_perusahaan, npwp, kategori_industri, limit_kredit)
VALUES ('PT Demo Customer', '12.345.678.9-000.111', 'Hotel', 10000000)
RETURNING company_id, nama_perusahaan, limit_kredit;
```

Kode program yang ditunjukkan:
- Endpoint `POST /api/companies`.
- Form tambah klien di admin.

Perubahan database:
- Baris baru di tabel `companies`.

#### Fitur 2: Manajemen User Perusahaan

Deskripsi:
Admin dapat menambahkan user untuk perusahaan tertentu dengan peran Chef, Procurement, atau Finance Manager.

UI/UX:
- Pilih perusahaan.
- Tabel user perusahaan.
- Form tambah user.

SQL query demo:

```sql
INSERT INTO users (company_id, nama_lengkap, email, peran)
VALUES (1, 'User Demo', 'user.demo@prokura.test', 'Procurement')
RETURNING user_id, company_id, nama_lengkap, email, peran;
```

Kode program yang ditunjukkan:
- Endpoint `POST /api/users`.
- Tab Manajemen Pengguna di admin.

Perubahan database:
- Baris baru di tabel `users`.

### 5. Pison Golda Mountera - Reporting Service

#### Fitur 1: Rekapitulasi Penjualan

Deskripsi:
Admin dapat melihat rekap penjualan berdasarkan rentang tanggal.

UI/UX:
- Date range picker.
- KPI total PO, total revenue, rata-rata nilai PO, klien aktif.
- Tabel transaksi.
- Export CSV.

SQL query demo:

```sql
SELECT COUNT(*) AS total_po,
       COALESCE(SUM(total_tagihan), 0) AS total_revenue,
       COALESCE(AVG(total_tagihan), 0) AS avg_po,
       COUNT(DISTINCT company_id) AS klien_aktif
FROM purchaseorders
WHERE DATE(tanggal_dipesan) BETWEEN '2026-01-01' AND '2026-12-31'
  AND status_po != 'Cancelled';
```

Kode program yang ditunjukkan:
- Endpoint `GET /api/reports/sales`.
- Modul Laporan & Analitik di admin.

Perubahan database:
- Tidak mengubah data langsung, tetapi hasil rekap berubah setelah ada order baru dari fitur pembelian.

#### Fitur 2: Analitik Top Produk dan Top Customer

Deskripsi:
Admin dapat melihat produk terlaris dan customer dengan revenue tertinggi.

UI/UX:
- Grafik top 10 produk.
- Grafik top 10 klien.
- Filter tanggal mengikuti rekap penjualan.

SQL query demo:

```sql
SELECT p.nama_produk AS produk,
       SUM(od.kuantitas) AS total_qty,
       SUM(od.kuantitas * od.harga_final) AS revenue
FROM orderdetails od
JOIN products p ON od.product_id = p.product_id
JOIN purchaseorders po ON od.po_id = po.po_id
WHERE po.status_po != 'Cancelled'
GROUP BY p.product_id
ORDER BY total_qty DESC
LIMIT 10;
```

Kode program yang ditunjukkan:
- Query bagian `top_products` dan `top_clients` pada Reporting Service.
- Grafik Plotly di admin.

Perubahan database:
- Hasil analitik berubah setelah order baru dibuat.

## Checklist Demo Presentasi

Setiap anggota saat demo minimal menampilkan:

1. UI fitur yang dibuat.
2. Endpoint/kode program yang menangani fitur.
3. SQL query terkait.
4. Kondisi database sebelum dan sesudah fitur dijalankan.
5. Bukti integrasi microservice: UI memanggil API, API mengubah/membaca PostgreSQL.

Contoh format demo singkat:

1. Tampilkan data awal dengan SQL `SELECT`.
2. Jalankan fitur dari UI.
3. Tampilkan kode endpoint.
4. Tampilkan SQL query yang dijalankan/diwakili endpoint.
5. Tampilkan data akhir dengan SQL `SELECT`.

## Status Implementasi End-to-End

Status ini mencatat realisasi fitur di kode Prokura setelah rencana dieksekusi.

| Anggota | Fitur | Endpoint/API | UI | Status |
| --- | --- | --- | --- | --- |
| Ravif | Penambahan barang baru | `POST /api/products` | Admin `Manajemen Stok Gudang -> Tambah Produk Baru` | Selesai |
| Ravif | Pencarian dan filter barang | `GET /api/products?q=...&category=...` | Admin dan customer web katalog produk | Selesai |
| Aloysius | Penambahan stok barang | `PATCH /api/products/:product_id/stock` | Admin `Manajemen Stok Gudang -> Penambahan Stok` | Selesai |
| Aloysius | Riwayat pergerakan stok | `GET /api/inventory/movements` | Admin `Manajemen Stok Gudang -> Riwayat Pergerakan Stok` | Selesai |
| Indratanaya | Pembelian barang oleh customer | `POST /api/orders` | Portal Pembelian dan customer web checkout | Selesai |
| Indratanaya | Riwayat pembelian customer | `GET /api/companies/:company_id/orders`, `GET /api/orders/:po_id` | Portal Pembelian `Riwayat Pesanan Saya` | Selesai |
| Gilbert | Manajemen customer/perusahaan | `POST /api/companies`, `GET /api/companies` | Admin `Manajemen Klien B2B -> Tambah Klien Baru` | Selesai |
| Gilbert | Manajemen user perusahaan | `POST /api/users`, `GET /api/users` | Admin `Manajemen Klien B2B -> Manajemen Pengguna` | Selesai |
| Pison | Rekapitulasi penjualan | `GET /api/reports/sales` | Admin `Laporan & Analitik` | Selesai |
| Pison | Analitik top produk dan top customer | `GET /api/reports/sales` bagian `top_products` dan `top_clients` | Grafik laporan admin | Selesai |

## Bukti Smoke Test

Smoke test otomatis tersedia di:

```powershell
.\scripts\final_project_smoke.ps1
```

Smoke test tersebut menjalankan semua fitur utama:

1. Membuat produk baru.
2. Mencari produk baru melalui API katalog.
3. Menambah stok produk.
4. Mengecek riwayat pergerakan stok.
5. Membuat perusahaan customer.
6. Membuat user perusahaan.
7. Membuat purchase order.
8. Mengecek riwayat pembelian customer.
9. Mengecek rekap penjualan dan top analytics.
10. Mengecek kondisi akhir produk dan movement stok.

Hasil smoke test terakhir:

```text
Catalog Service: product created, search result count 1
Inventory Service: stock increased to 15, movement count 2 before checkout
Customer Service: company and user created
Order Service: PO created, customer order history count 1
Reporting Service: report summary returned, top products and top clients returned
Final stock state: 13 after checkout quantity 2
Final movements: INITIAL_STOCK, STOCK_IN, STOCK_OUT
```

# Ravif Gayuh Wicaksono

NIM: 24/540583/PA/22953

## Peran

Owner Catalog Service. Fokus pada data produk, penambahan SKU baru, katalog, pencarian, dan filter produk.

## Tanggung Jawab Fitur

1. Penambahan barang baru.
2. Pencarian dan filter barang.

## Lokasi Kode Program

- Route katalog: `prokura-api/src/services/catalog/routes.js`
  - `GET /api/products`: line 11.
  - `POST /api/products`: line 21.
- SQL repository katalog: `prokura-api/src/services/catalog/repository.js`
  - Query list/search produk: line 22.
  - Insert produk baru: line 37.
- Domain validation: `prokura-api/src/services/catalog/domain.js`.
- UI admin tambah produk: `prokura-admin/app3.py`, menu `Manajemen Stok Gudang`, mulai line 399 dan form line 463.
- UI customer search/filter: `prokura-web/app/page.tsx`, fetch produk line 58 dan search input line 264.

## SQL Query Demo

Tambah produk:

```sql
INSERT INTO products (sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang)
VALUES ('SKU-DEMO-001', 'Demo Product', 'Bahan Pokok', 'Kg', 25000, 50)
RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang;
```

Pencarian produk:

```sql
SELECT p.product_id, p.sku, p.nama_produk, p.kategori, p.satuan,
       p.harga_dasar, p.stok_gudang
FROM products p
WHERE p.nama_produk ILIKE '%demo%'
   OR p.sku ILIKE '%demo%'
ORDER BY p.nama_produk ASC;
```

## Penjelasan Sistem

UI admin dan customer tidak membaca database langsung. UI memanggil API gateway `http://127.0.0.1:5000/api/products`. Catalog route memvalidasi payload, menormalisasi SKU, lalu repository menjalankan SQL ke PostgreSQL. Saat produk dibuat dengan stok awal, sistem juga mencatat `INITIAL_STOCK` ke Inventory Service melalui `recordInventoryMovement`.

## Alur Demo

1. Tampilkan data awal dengan `SELECT` produk berdasarkan SKU demo.
2. Buka admin, menu `Manajemen Stok Gudang`, tab `Tambah Produk Baru`.
3. Isi SKU, nama, kategori, satuan, harga, dan stok awal.
4. Submit form dan tunjukkan response sukses.
5. Buka katalog/search, cari SKU atau nama produk baru.
6. Tampilkan database akhir: produk baru muncul dan stok awal tercatat.

## Bukti Validasi

- Unit test Catalog: `prokura-api/tests/unit/catalog-domain.test.js`.
- Repository test Catalog: `prokura-api/tests/unit/repository.test.js`.
- Integration test lintas service: `prokura-api/tests/integration/api-final-project.test.js`.
- Smoke test final project membuat produk dan mencari produk baru.

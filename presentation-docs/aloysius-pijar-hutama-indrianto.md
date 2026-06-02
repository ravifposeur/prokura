# Aloysius Pijar Hutama Indrianto

NIM: 24/534591/PA/22675

## Peran

Owner Inventory Service. Fokus pada perubahan stok gudang dan audit trail pergerakan stok.

## Tanggung Jawab Fitur

1. Penambahan stok barang.
2. Riwayat pergerakan stok.

## Lokasi Kode Program

- Route inventory: `prokura-api/src/services/inventory/routes.js`
  - `PATCH /api/products/:product_id/stock`: line 4.
  - `GET /api/inventory/movements`: line 51.
- SQL insert movement: `prokura-api/src/services/inventory/repository.js`, line 22.
- Domain validation quantity: `prokura-api/src/services/inventory/domain.js`.
- UI admin stok: `prokura-admin/app3.py`
  - Menu `Manajemen Stok Gudang`: line 399.
  - Form `Penambahan Stok Barang`: line 587.
  - Tabel `Riwayat Pergerakan Stok`: line 624.

## SQL Query Demo

Penambahan stok:

```sql
UPDATE products
SET stok_gudang = stok_gudang + 25
WHERE product_id = 1
RETURNING product_id, sku, nama_produk, stok_gudang;
```

Catatan movement:

```sql
INSERT INTO inventory_movements
  (product_id, movement_type, quantity, note, reference_type, reference_id)
VALUES
  (1, 'STOCK_IN', 25, 'Restock demo presentasi', 'PRODUCT', 1);
```

Riwayat movement:

```sql
SELECT m.movement_id, m.product_id, p.sku, p.nama_produk,
       m.movement_type, m.quantity, m.note,
       m.reference_type, m.reference_id, m.created_at
FROM inventory_movements m
JOIN products p ON m.product_id = p.product_id
WHERE m.product_id = 1
ORDER BY m.created_at DESC, m.movement_id DESC;
```

## Penjelasan Sistem

Inventory Service memisahkan update stok dari perubahan metadata produk. Endpoint `PATCH /api/products/:product_id/stock` hanya menerima quantity positif dan catatan. Dalam satu transaksi database, stok bertambah dan baris `STOCK_IN` masuk ke tabel `inventory_movements`, sehingga perubahan bisa diaudit.

## Alur Demo

1. Pilih satu produk dan tampilkan stok awal.
2. Buka admin, menu `Manajemen Stok Gudang`, tab `Penambahan Stok`.
3. Input quantity dan catatan restock.
4. Submit, lalu tunjukkan stok produk bertambah.
5. Buka tab `Riwayat Pergerakan Stok`.
6. Tampilkan row `STOCK_IN` terbaru dan cocokkan dengan SQL.

## Bukti Validasi

- Unit test Inventory: `prokura-api/tests/unit/inventory-domain.test.js`.
- Integration test mengecek restock dan movement.
- Smoke test final project membuktikan stok naik dari 10 ke 15 dan movement berisi `INITIAL_STOCK`, `STOCK_IN`, lalu `STOCK_OUT`.

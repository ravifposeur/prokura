# Indratanaya Budiman

NIM: 24/534784/PA/22683

## Peran

Owner Order Service. Fokus pada checkout customer, purchase order, perubahan stok keluar, status PO, dan riwayat pembelian.

## Tanggung Jawab Fitur

1. Pembelian barang oleh customer.
2. Riwayat pembelian customer.

## Lokasi Kode Program

- Route order: `prokura-api/src/services/order/routes.js`
  - `GET /api/companies/:company_id/orders`: line 26.
  - `GET /api/orders/:po_id`: line 36.
  - `POST /api/orders`: line 46.
  - `PATCH /api/orders/:po_id/status`: line 104.
- SQL repository order: `prokura-api/src/services/order/repository.js`
  - List riwayat customer: line 17.
  - Insert purchase order: line 55.
  - Insert detail order: line 67.
  - Kurangi stok: line 77.
- UI customer web: `prokura-web/app/page.tsx`
  - Checkout POST order: line 129.
  - Detail PO: line 152.
  - Tombol `Ajukan Approval`: line 444.
  - Riwayat PO finance: line 460.
- UI portal pembelian admin: `prokura-admin/app3.py`, mulai line 990, checkout tabs line 1123, riwayat line 1329.

## SQL Query Demo

Checkout purchase order:

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

Riwayat pembelian customer:

```sql
SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
       po.tanggal_dipesan, u.nama_lengkap AS pembuat
FROM purchaseorders po
JOIN users u ON po.dibuat_oleh = u.user_id
WHERE po.company_id = 1
ORDER BY po.tanggal_dipesan DESC;
```

## Penjelasan Sistem

Order Service menerima payload checkout dari UI customer. Service memvalidasi payload, mengunci stok produk dengan `FOR UPDATE`, membuat purchase order, membuat detail order, mengurangi stok, dan mencatat `STOCK_OUT` ke inventory movement. Semua dilakukan dalam transaksi database sehingga kalau stok tidak cukup, order dibatalkan dan stok tidak berubah.

## Alur Demo

1. Buka customer web, pilih role `Chef`.
2. Cari produk dan masukkan ke cart.
3. Klik `Ajukan Approval`.
4. Tunjukkan PO baru pada riwayat customer/finance.
5. Buka detail PO dan tampilkan item order.
6. Tampilkan database akhir: row baru di `purchaseorders`, row baru di `orderdetails`, stok berkurang, dan movement `STOCK_OUT` tercatat.

## Bukti Validasi

- Unit test Order: `prokura-api/tests/unit/order-domain.test.js`.
- Integration test checkout lintas service.
- Integration test reject order mengembalikan stok.
- Integration test approval order tidak membuat stock return.
- Smoke test final project membuat PO dan mengecek riwayat pembelian customer.

# Pison Golda Mountera

NIM: 24/543770/PA/23107

## Peran

Owner Reporting Service. Fokus pada rekap penjualan, KPI transaksi, top produk, top customer, dan ringkasan admin.

## Tanggung Jawab Fitur

1. Rekapitulasi penjualan.
2. Analitik top produk dan top customer.

## Lokasi Kode Program

- Route reporting: `prokura-api/src/services/reporting/routes.js`
  - `GET /api/admin/summary`: line 5.
  - `GET /api/reports/sales`: line 14.
- SQL repository reporting: `prokura-api/src/services/reporting/repository.js`
  - Summary sales: line 17.
  - Top products: line 56.
  - Top clients: line 73.
  - Transactions report: line 91.
- Domain date range: `prokura-api/src/services/reporting/domain.js`.
- UI admin laporan: `prokura-admin/app3.py`
  - Menu `Laporan & Analitik`: line 912.
  - Fetch report `/api/reports/sales`: line 924.

## SQL Query Demo

Rekapitulasi penjualan:

```sql
SELECT COUNT(*) AS total_po,
       COALESCE(SUM(total_tagihan), 0) AS total_revenue,
       COALESCE(AVG(total_tagihan), 0) AS avg_po,
       COUNT(DISTINCT company_id) AS klien_aktif
FROM purchaseorders
WHERE DATE(tanggal_dipesan) BETWEEN '2026-01-01' AND '2026-12-31'
  AND status_po != 'Cancelled';
```

Top produk:

```sql
SELECT p.nama_produk AS produk, p.kategori,
       SUM(od.kuantitas) AS total_qty,
       SUM(od.kuantitas * od.harga_final) AS revenue
FROM orderdetails od
JOIN products p ON od.product_id = p.product_id
JOIN purchaseorders po ON od.po_id = po.po_id
WHERE DATE(po.tanggal_dipesan) BETWEEN '2026-01-01' AND '2026-12-31'
  AND po.status_po != 'Cancelled'
GROUP BY p.product_id
ORDER BY total_qty DESC
LIMIT 10;
```

Top customer:

```sql
SELECT c.nama_perusahaan AS klien, c.kategori_industri AS segmen,
       COUNT(po.po_id) AS jumlah_po,
       SUM(po.total_tagihan) AS revenue
FROM purchaseorders po
JOIN companies c ON po.company_id = c.company_id
WHERE DATE(po.tanggal_dipesan) BETWEEN '2026-01-01' AND '2026-12-31'
  AND po.status_po != 'Cancelled'
GROUP BY c.company_id
ORDER BY revenue DESC
LIMIT 10;
```

## Penjelasan Sistem

Reporting Service tidak mengubah database secara langsung. Service membaca transaksi dari `purchaseorders`, `orderdetails`, `products`, dan `companies`, lalu mengembalikan summary, tren bulanan, segment revenue, top products, top clients, dan transaksi. Hasil laporan berubah otomatis setelah fitur checkout membuat PO baru.

## Alur Demo

1. Buka admin, menu `Laporan & Analitik`.
2. Pilih rentang tanggal, misalnya tahun 2026.
3. Tunjukkan KPI total PO, total revenue, average PO, dan klien aktif.
4. Tunjukkan grafik/tabel top produk dan top customer.
5. Jalankan checkout demo baru dari Order Service.
6. Refresh laporan dan tunjukkan angka/top analytics berubah.

## Bukti Validasi

- Unit test Reporting: `prokura-api/tests/unit/reporting-domain.test.js`.
- Repository test Reporting: `prokura-api/tests/unit/repository.test.js`.
- Integration test mengecek reporting sales.
- Smoke test final project mengecek summary, top products, dan top clients.

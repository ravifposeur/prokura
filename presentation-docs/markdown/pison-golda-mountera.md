# Pison Golda Mountera

NIM: 24/543770/PA/23107

## Peran

Owner Reporting Service. Pison bertanggung jawab pada rekap penjualan, KPI transaksi, top produk, top customer, dan ringkasan admin.

## Bukti Microservice

Reporting Service berada di `prokura-api/src/services/reporting` dan dapat dijalankan sebagai service tersendiri melalui `service-host`.

Lokasi kode: `prokura-api/src/service-host.js`

```js
const serviceRegistry = {
  catalog: registerCatalogRoutes,
  customer: registerCustomerRoutes,
  inventory: registerInventoryRoutes,
  order: registerOrderRoutes,
  reporting: registerReportingRoutes,
};
```

Penjelasan: entry `reporting: registerReportingRoutes` membuktikan Reporting Service punya boundary sendiri. Pada Docker Compose microservices, service ini berjalan di port `5105`.

## Tanggung Jawab Fitur

1. Rekapitulasi penjualan.
2. Analitik top produk dan top customer.

## Lokasi Kode Program dan Penjelasan

### Route laporan

Lokasi kode: `prokura-api/src/services/reporting/routes.js`

- `GET /api/admin/summary`: line 5.
- `GET /api/reports/sales`: line 14.

```js
app.get("/api/admin/summary", async (_req, res) => {
  try {
    const summary = await getAdminSummary(pool);
    res.json({ success: true, data: summary });
  } catch (error) {
    sendError(res, error, "Gagal mengambil ringkasan admin");
  }
});
```

Penjelasan: endpoint ini memberi ringkasan cepat untuk dashboard admin, seperti jumlah perusahaan, produk, order, dan order pending.

```js
app.get("/api/reports/sales", async (req, res) => {
  try {
    const { start, end } = normalizeDateRange(req.query);
    const report = await getSalesReport(pool, { start, end });

    res.json({
      success: true,
      data: report,
    });
  } catch (error) {
    sendError(res, error, "Gagal mengambil laporan penjualan");
  }
});
```

Penjelasan: endpoint laporan menerima rentang tanggal, menormalisasi tanggal, lalu mengambil data sales report dari repository. Response berisi summary, tren bulanan, segment revenue, top products, top clients, dan transaksi.

### SQL repository reporting

Lokasi kode: `prokura-api/src/services/reporting/repository.js`

- Summary sales: line 17.
- Top products: line 56.
- Top clients: line 73.
- Transactions report: line 91.

```js
const summary = await pool.query(
  `
    SELECT COUNT(*)::int AS total_po,
           COALESCE(SUM(total_tagihan), 0)::float AS total_revenue,
           COALESCE(AVG(total_tagihan), 0)::float AS avg_po,
           COUNT(DISTINCT company_id)::int AS klien_aktif
    FROM purchaseorders
    WHERE DATE(tanggal_dipesan) BETWEEN $1 AND $2
      AND status_po != 'Cancelled'
  `,
  params,
);
```

Penjelasan: query ini menghitung KPI utama laporan: total PO, total revenue, rata-rata nilai PO, dan jumlah klien aktif. Order dengan status `Cancelled` tidak dihitung sebagai penjualan.

```js
const monthly = await pool.query(
  `
    SELECT TO_CHAR(tanggal_dipesan, 'YYYY-MM') AS bulan,
           SUM(total_tagihan)::float AS revenue,
           COUNT(*)::int AS jumlah_po
    FROM purchaseorders
    WHERE DATE(tanggal_dipesan) BETWEEN $1 AND $2
      AND status_po != 'Cancelled'
    GROUP BY TO_CHAR(tanggal_dipesan, 'YYYY-MM')
    ORDER BY bulan ASC
  `,
  params,
);
```

Penjelasan: query ini mengelompokkan revenue dan jumlah PO per bulan. Data ini dipakai untuk grafik tren penjualan.

```js
const topProducts = await pool.query(
  `
    SELECT p.nama_produk AS produk, p.kategori,
           SUM(od.kuantitas)::int AS total_qty,
           SUM(od.kuantitas * od.harga_final)::float AS revenue
    FROM orderdetails od
    JOIN products p ON od.product_id = p.product_id
    JOIN purchaseorders po ON od.po_id = po.po_id
    WHERE DATE(po.tanggal_dipesan) BETWEEN $1 AND $2
      AND po.status_po != 'Cancelled'
    GROUP BY p.product_id
    ORDER BY total_qty DESC
    LIMIT 10
  `,
  params,
);
```

Penjelasan: query ini mencari produk terlaris berdasarkan total kuantitas. Join ke `products` memberi nama produk dan kategori, sedangkan join ke `purchaseorders` memastikan filter tanggal dan status diterapkan.

```js
const topClients = await pool.query(
  `
    SELECT c.nama_perusahaan AS klien, c.kategori_industri AS segmen,
           COUNT(po.po_id)::int AS jumlah_po,
           SUM(po.total_tagihan)::float AS revenue
    FROM purchaseorders po
    JOIN companies c ON po.company_id = c.company_id
    WHERE DATE(po.tanggal_dipesan) BETWEEN $1 AND $2
      AND po.status_po != 'Cancelled'
    GROUP BY c.company_id
    ORDER BY revenue DESC
    LIMIT 10
  `,
  params,
);
```

Penjelasan: query ini mencari customer dengan revenue tertinggi. Hasilnya dipakai untuk grafik atau tabel top customer.

### UI admin laporan

Lokasi kode: `prokura-admin/app3.py`

- Menu `Laporan & Analitik`: line 912.
- Fetch report `/api/reports/sales`: line 924.

Penjelasan: UI admin memilih rentang tanggal dan memanggil endpoint Reporting Service. UI tidak menghitung langsung dari database.

## SQL Query Demo dan Penjelasan

### Query 1: rekapitulasi penjualan

```sql
SELECT COUNT(*) AS total_po,
       COALESCE(SUM(total_tagihan), 0) AS total_revenue,
       COALESCE(AVG(total_tagihan), 0) AS avg_po,
       COUNT(DISTINCT company_id) AS klien_aktif
FROM purchaseorders
WHERE DATE(tanggal_dipesan) BETWEEN '2026-01-01' AND '2026-12-31'
  AND status_po != 'Cancelled';
```

Penjelasan: query ini menghitung KPI sales dalam rentang tahun 2026. `COALESCE` membuat nilai agregat menjadi 0 jika belum ada order pada rentang tersebut.

### Query 2: analitik top produk

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

Penjelasan: query ini menghitung produk terlaris dari detail order. `SUM(od.kuantitas)` menentukan ranking, sedangkan `SUM(od.kuantitas * od.harga_final)` menghitung revenue produk.

### Query 3: analitik top customer

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

Penjelasan: query ini menghitung customer dengan revenue tertinggi. Data ini penting untuk melihat pelanggan B2B paling bernilai.

## Alur Demo

### A. Rekapitulasi penjualan

1. Buka admin `Laporan & Analitik`.
2. Pilih rentang tanggal, misalnya 2026-01-01 sampai 2026-12-31.
3. Tunjukkan KPI total PO, total revenue, average PO, dan klien aktif.
4. Tunjukkan route `GET /api/reports/sales`.
5. Jalankan SQL rekapitulasi penjualan untuk membuktikan angka berasal dari database.

### B. Analitik top produk dan top customer

1. Masih di menu laporan, lihat bagian top produk.
2. Tunjukkan produk dengan total quantity tertinggi.
3. Lihat bagian top customer.
4. Tunjukkan customer dengan revenue tertinggi.
5. Jalankan SQL top produk dan top customer untuk membuktikan hasil UI sama dengan agregasi database.

## Bukti Validasi

- Unit test Reporting: `prokura-api/tests/unit/reporting-domain.test.js`.
- Repository test Reporting: `prokura-api/tests/unit/repository.test.js`.
- Integration test mengecek reporting sales.
- Smoke test final project mengecek summary, top products, dan top clients.

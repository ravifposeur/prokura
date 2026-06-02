# Indratanaya Budiman

NIM: 24/534784/PA/22683

## Peran

Owner Order Service. Indratanaya bertanggung jawab pada checkout customer, purchase order, perubahan stok keluar, status PO, dan riwayat pembelian.

## Bukti Microservice

Order Service berada di `prokura-api/src/services/order` dan dapat dijalankan sebagai service tersendiri melalui `service-host`.

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

Penjelasan: entry `order: registerOrderRoutes` menunjukkan Order Service punya boundary terpisah. Pada deployment microservices, Order Service berjalan di port `5104`, sementara UI tetap memanggil API lewat HTTP.

## Tanggung Jawab Fitur

1. Pembelian barang oleh customer.
2. Riwayat pembelian customer.

## Lokasi Kode Program dan Penjelasan

### Route checkout order

Lokasi kode: `prokura-api/src/services/order/routes.js`

- `POST /api/orders`: line 46.

```js
app.post("/api/orders", async (req, res) => {
  const { company_id, dibuat_oleh, metode_pembayaran, total_tagihan, items } =
    req.body;

  try {
    validateOrderPayload(req.body);
  } catch (error) {
    return res.status(400).json({ success: false, message: error.message });
  }

  const orderTotal = total_tagihan == null ? calculateOrderTotal(items) : Number(total_tagihan);
  const client = await pool.connect();
```

Penjelasan: endpoint checkout menerima payload order dari UI, memvalidasi isi payload, lalu menghitung total order jika total belum dikirim. Validasi dilakukan sebelum transaksi database dimulai.

```js
await client.query("BEGIN");

for (const item of items) {
  const stock = await lockProductStock(client, item.product_id);
  if (!stock || Number(stock.stok_gudang) < Number(item.kuantitas)) {
    throw new Error(`Stok produk ${item.product_id} tidak cukup`);
  }
}
```

Penjelasan: stok tiap produk dikunci dengan `FOR UPDATE` melalui repository. Ini mencegah dua checkout bersamaan mengambil stok yang sama.

```js
const newPoId = await createPurchaseOrder(client, {
  company_id,
  dibuat_oleh,
  metode_pembayaran,
  total_tagihan: orderTotal,
});

for (const item of items) {
  await createOrderDetail(client, newPoId, item);
  await decrementProductStock(client, item);

  await recordInventoryMovement(client, {
    productId: item.product_id,
    movementType: "STOCK_OUT",
    quantity: -Number(item.kuantitas),
    note: `Checkout PO #${newPoId}`,
    referenceType: "ORDER",
    referenceId: newPoId,
  });
}
```

Penjelasan: setelah PO dibuat, sistem membuat detail order, mengurangi stok, dan mencatat `STOCK_OUT`. Semua langkah berada dalam satu transaksi agar order dan stok tetap konsisten.

### Route riwayat dan detail pembelian

Lokasi kode: `prokura-api/src/services/order/routes.js`

- `GET /api/companies/:company_id/orders`: line 26.
- `GET /api/orders/:po_id`: line 36.

```js
app.get("/api/companies/:company_id/orders", async (req, res) => {
  try {
    const { company_id } = req.params;
    const orders = await listCompanyOrders(pool, company_id);
    res.json({ success: true, data: orders });
  } catch (error) {
    sendError(res, error, "Gagal mengambil riwayat PO");
  }
});
```

Penjelasan: endpoint ini mengambil daftar PO milik satu perusahaan. Customer dapat melihat riwayat pembelian tanpa mengakses tabel langsung.

```js
app.get("/api/orders/:po_id", async (req, res) => {
  try {
    const { po_id } = req.params;
    const details = await listOrderDetails(pool, po_id);
    res.json({ success: true, data: details });
  } catch (error) {
    sendError(res, error, "Gagal mengambil detail PO");
  }
});
```

Penjelasan: endpoint ini mengambil item detail dari satu PO sehingga demo bisa menunjukkan barang, kuantitas, harga final, dan subtotal.

### SQL repository order

Lokasi kode: `prokura-api/src/services/order/repository.js`

- List riwayat customer: line 17.
- Insert purchase order: line 55.
- Insert detail order: line 67.
- Kurangi stok: line 77.

```js
const { rows } = await pool.query(
  `
    SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
           po.tanggal_dipesan, u.nama_lengkap AS pembuat
    FROM purchaseorders po
    JOIN users u ON po.dibuat_oleh = u.user_id
    WHERE po.company_id = $1
    ORDER BY po.tanggal_dipesan DESC
  `,
  [companyId],
);
```

Penjelasan: query ini membaca riwayat PO untuk satu perusahaan. Join ke `users` menampilkan nama pembuat PO.

```js
const { rows } = await client.query(
  `
    INSERT INTO purchaseorders (company_id, dibuat_oleh, metode_pembayaran, total_tagihan)
    VALUES ($1, $2, $3, $4)
    RETURNING po_id
  `,
  [order.company_id, order.dibuat_oleh, order.metode_pembayaran, order.total_tagihan],
);
```

Penjelasan: query ini membuat header PO dan mengembalikan `po_id`. Nilai `po_id` dipakai untuk menyimpan detail item.

```js
await client.query(
  `
    INSERT INTO orderdetails (po_id, product_id, kuantitas, harga_final)
    VALUES ($1, $2, $3, $4)
  `,
  [poId, item.product_id, item.kuantitas, item.harga_final],
);
```

Penjelasan: query ini menyimpan item order. Setiap item berisi produk, kuantitas, dan harga final saat checkout.

```js
await client.query(
  `
    UPDATE products
    SET stok_gudang = stok_gudang - $1
    WHERE product_id = $2
  `,
  [item.kuantitas, item.product_id],
);
```

Penjelasan: query ini mengurangi stok gudang sesuai kuantitas yang dibeli. Karena sudah ada lock stok sebelumnya, pengurangan stok aman terhadap checkout bersamaan.

### UI customer web

Lokasi kode: `prokura-web/app/page.tsx`

- Checkout POST order: line 129.
- Detail PO: line 152.
- Tombol `Ajukan Approval`: line 444.
- Riwayat PO finance: line 460.

```tsx
const res = await fetch(`${API_BASE_URL}/api/orders`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
```

Penjelasan: customer web mengirim checkout ke Order Service melalui API gateway. Payload berisi company, user pembuat, metode pembayaran, total tagihan, dan item cart.

```tsx
const res = await fetch(`${API_BASE_URL}/api/orders/${po.po_id}`);
```

Penjelasan: saat user melihat detail PO, UI mengambil detail order dari endpoint order, bukan dari database langsung.

## SQL Query Demo dan Penjelasan

### Query 1: buat purchase order

```sql
INSERT INTO purchaseorders (company_id, dibuat_oleh, metode_pembayaran, total_tagihan)
VALUES (1, 1, 'Tempo_30_Hari', 250000)
RETURNING po_id;
```

Penjelasan: query ini membuat header PO. `company_id` menunjukkan perusahaan pembeli, `dibuat_oleh` menunjukkan user, dan `total_tagihan` menyimpan nilai transaksi.

### Query 2: tambah detail order

```sql
INSERT INTO orderdetails (po_id, product_id, kuantitas, harga_final)
VALUES (currval('purchaseorders_po_id_seq'), 1, 5, 50000);
```

Penjelasan: query ini memasukkan item PO untuk produk tertentu. `currval` memakai `po_id` terbaru dari insert purchase order pada sesi yang sama.

### Query 3: kurangi stok

```sql
UPDATE products
SET stok_gudang = stok_gudang - 5
WHERE product_id = 1;
```

Penjelasan: query ini menurunkan stok produk sesuai kuantitas checkout. Perubahan stok menjadi bukti database berubah akibat pembelian.

### Query 4: lihat riwayat pembelian customer

```sql
SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
       po.tanggal_dipesan, u.nama_lengkap AS pembuat
FROM purchaseorders po
JOIN users u ON po.dibuat_oleh = u.user_id
WHERE po.company_id = 1
ORDER BY po.tanggal_dipesan DESC;
```

Penjelasan: query ini menampilkan riwayat PO milik satu perusahaan, termasuk status, metode pembayaran, total, tanggal, dan pembuat.

## Alur Demo

### A. Pembelian barang oleh customer

1. Buka customer web dan pilih role `Chef`.
2. Cari produk lalu masukkan ke cart.
3. Tunjukkan total tagihan pada cart.
4. Klik `Ajukan Approval`.
5. Tunjukkan response sukses berisi nomor PO.
6. Jalankan SQL untuk membuktikan row baru di `purchaseorders`, `orderdetails`, stok produk berkurang, dan movement `STOCK_OUT` tercatat.

### B. Riwayat pembelian customer

1. Buka riwayat/antrean PO pada customer web atau portal pembelian.
2. Pilih PO yang baru dibuat.
3. Buka detail PO.
4. Tunjukkan item, kuantitas, harga final, subtotal, dan status PO.
5. Jalankan SQL riwayat pembelian untuk membuktikan data sama dengan UI.

## Bukti Validasi

- Unit test Order: `prokura-api/tests/unit/order-domain.test.js`.
- Integration test checkout lintas service.
- Integration test reject order mengembalikan stok.
- Integration test approval order tidak membuat stock return.
- Smoke test final project membuat PO dan mengecek riwayat pembelian customer.

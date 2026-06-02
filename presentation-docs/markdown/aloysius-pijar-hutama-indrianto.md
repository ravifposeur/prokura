# Aloysius Pijar Hutama Indrianto

NIM: 24/534591/PA/22675

## Peran

Owner Inventory Service. Aloysius bertanggung jawab pada perubahan stok gudang dan audit trail pergerakan stok.

## Bukti Microservice

Inventory Service sudah dipisahkan pada `prokura-api/src/services/inventory`. Service ini dapat berjalan sendiri melalui registry di `prokura-api/src/service-host.js`.

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

Penjelasan: entry `inventory: registerInventoryRoutes` menunjukkan route inventory dipasang sebagai service tersendiri. Pada Docker Compose microservices, service ini diekspos pada port `5102` dengan health endpoint `/health`.

## Tanggung Jawab Fitur

1. Penambahan stok barang.
2. Riwayat pergerakan stok.

## Lokasi Kode Program dan Penjelasan

### Route penambahan stok

Lokasi kode: `prokura-api/src/services/inventory/routes.js`

- `PATCH /api/products/:product_id/stock`: line 4.

```js
app.patch("/api/products/:product_id/stock", async (req, res) => {
  const client = await pool.connect();
  try {
    const { product_id } = req.params;
    const { quantity, note } = req.body;
    let amount;

    try {
      amount = parsePositiveInteger(quantity, "Quantity stok masuk");
    } catch (error) {
      return res.status(400).json({ success: false, message: error.message });
    }
```

Penjelasan: endpoint menerima `product_id`, `quantity`, dan catatan. `parsePositiveInteger` memastikan jumlah stok masuk valid dan positif sebelum database diubah.

```js
await client.query("BEGIN");
const { rows } = await client.query(
  `
    UPDATE products
    SET stok_gudang = stok_gudang + $1
    WHERE product_id = $2
    RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang
  `,
  [amount, product_id],
);
```

Penjelasan: stok produk bertambah secara atomik dengan parameter `$1` untuk jumlah dan `$2` untuk produk. `RETURNING` mengembalikan stok terbaru ke UI.

```js
await recordInventoryMovement(client, {
  productId: Number(product_id),
  movementType: "STOCK_IN",
  quantity: amount,
  note: note || "Penambahan stok manual",
  referenceType: "PRODUCT",
  referenceId: Number(product_id),
});

await client.query("COMMIT");
res.json({ success: true, data: rows[0] });
```

Penjelasan: setelah stok naik, sistem membuat movement `STOCK_IN`. Update stok dan insert movement berada dalam transaksi yang sama agar data stok dan audit trail konsisten.

### Route riwayat pergerakan stok

Lokasi kode: `prokura-api/src/services/inventory/routes.js`

- `GET /api/inventory/movements`: line 51.

```js
if (req.query.product_id) {
  params.push(req.query.product_id);
  conditions.push(`m.product_id = $${params.length}`);
}

if (req.query.movement_type) {
  params.push(req.query.movement_type);
  conditions.push(`m.movement_type = $${params.length}`);
}
```

Penjelasan: endpoint riwayat dapat difilter berdasarkan produk dan tipe movement. Filter ini berguna saat demo untuk menunjukkan riwayat hanya dari produk yang sedang diuji.

```js
const { rows } = await pool.query(
  `
    SELECT m.movement_id, m.product_id, p.sku, p.nama_produk,
           m.movement_type, m.quantity, m.note,
           m.reference_type, m.reference_id, m.created_at
    FROM inventory_movements m
    JOIN products p ON m.product_id = p.product_id
    ${where}
    ORDER BY m.created_at DESC, m.movement_id DESC
  `,
  params,
);
```

Penjelasan: query mengambil movement dan data produk terkait. Urutan descending membuat movement terbaru muncul paling atas.

### SQL insert movement

Lokasi kode: `prokura-api/src/services/inventory/repository.js`

- Insert movement: line 22.

```js
await client.query(
  `
    INSERT INTO inventory_movements
      (product_id, movement_type, quantity, note, reference_type, reference_id)
    VALUES ($1, $2, $3, $4, $5, $6)
  `,
  [
    movement.productId,
    movement.movementType,
    movement.quantity,
    movement.note,
    movement.referenceType,
    movement.referenceId,
  ],
);
```

Penjelasan: repository ini menjadi satu tempat pencatatan movement untuk stok awal, stok masuk, stok keluar, dan stok return. Karena dipakai oleh Catalog dan Order juga, audit inventory tetap konsisten lintas service.

### UI admin stok

Lokasi kode: `prokura-admin/app3.py`

- Menu `Manajemen Stok Gudang`: line 399.
- Form `Penambahan Stok Barang`: line 587.
- Tabel `Riwayat Pergerakan Stok`: line 624.

Penjelasan: UI admin memanggil API inventory untuk menambah stok dan membaca riwayat. Admin tidak menjalankan SQL langsung dari Streamlit.

## SQL Query Demo dan Penjelasan

### Query 1: tambah stok

```sql
UPDATE products
SET stok_gudang = stok_gudang + 25
WHERE product_id = 1
RETURNING product_id, sku, nama_produk, stok_gudang;
```

Penjelasan: query ini menambah stok produk dengan `product_id = 1` sebanyak 25. `RETURNING` menunjukkan stok akhir setelah update.

### Query 2: catat movement

```sql
INSERT INTO inventory_movements
  (product_id, movement_type, quantity, note, reference_type, reference_id)
VALUES
  (1, 'STOCK_IN', 25, 'Restock demo presentasi', 'PRODUCT', 1);
```

Penjelasan: query ini mencatat perubahan stok sebagai movement `STOCK_IN`. Data ini menjadi bukti audit bahwa stok bertambah karena restock manual.

### Query 3: lihat riwayat movement

```sql
SELECT m.movement_id, m.product_id, p.sku, p.nama_produk,
       m.movement_type, m.quantity, m.note,
       m.reference_type, m.reference_id, m.created_at
FROM inventory_movements m
JOIN products p ON m.product_id = p.product_id
WHERE m.product_id = 1
ORDER BY m.created_at DESC, m.movement_id DESC;
```

Penjelasan: query ini menampilkan riwayat stok untuk satu produk. Join ke `products` membuat riwayat lebih mudah dibaca karena menampilkan SKU dan nama produk.

## Alur Demo

### A. Penambahan stok barang

1. Tampilkan stok awal produk dengan SQL `SELECT`.
2. Buka admin `Manajemen Stok Gudang`.
3. Masuk ke tab `Penambahan Stok`.
4. Pilih produk, isi quantity, dan isi catatan restock.
5. Submit form.
6. Tampilkan stok terbaru dari UI atau SQL.

### B. Riwayat pergerakan stok

1. Buka tab `Riwayat Pergerakan Stok`.
2. Filter berdasarkan produk atau tipe `STOCK_IN`.
3. Tunjukkan movement terbaru berisi quantity dan catatan demo.
4. Jalankan SQL riwayat movement untuk membuktikan data masuk ke tabel `inventory_movements`.

## Bukti Validasi

- Unit test Inventory: `prokura-api/tests/unit/inventory-domain.test.js`.
- Integration test mengecek restock dan movement.
- Smoke test final project membuktikan stok naik dan movement tercatat.

# Ravif Gayuh Wicaksono

NIM: 24/540583/PA/22953

## Peran

Owner Catalog Service. Ravif bertanggung jawab pada data produk, penambahan SKU baru, katalog, pencarian, dan filter produk.

## Bukti Microservice

Catalog Service sudah dipisahkan sebagai service boundary di `prokura-api/src/services/catalog`. API gateway di `prokura-api/server.js` memasang route Catalog, sedangkan `prokura-api/src/service-host.js` dapat menjalankan service tunggal bernama `catalog`.

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

Penjelasan: registry ini membuktikan tiap domain punya route module sendiri. Saat `SERVICE_NAME=catalog` atau command `node src/service-host.js catalog` dijalankan, host hanya memasang route Catalog Service. Ini sesuai keinginan dosen karena integrasi sistem dilakukan lewat endpoint API, bukan query database langsung dari UI.

## Tanggung Jawab Fitur

1. Penambahan barang baru.
2. Pencarian dan filter barang.

## Lokasi Kode Program dan Penjelasan

### Route tambah dan cari produk

Lokasi kode: `prokura-api/src/services/catalog/routes.js`

- `GET /api/products`: line 11.
- `POST /api/products`: line 21.

```js
app.get("/api/products", async (req, res) => {
  try {
    const filters = buildProductSearchFilters(req.query);
    const products = await listProducts(pool, filters);
    res.json({ success: true, data: products });
  } catch (error) {
    sendError(res, error, "Gagal mengambil katalog produk");
  }
});
```

Penjelasan: endpoint ini menerima query string dari UI, menormalisasi filter melalui domain helper, lalu memanggil repository `listProducts`. Hasilnya dikembalikan sebagai JSON agar admin dan customer web dapat menampilkan katalog tanpa akses database langsung.

```js
app.post("/api/products", async (req, res) => {
  const client = await pool.connect();
  try {
    const { sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang } = req.body;
    if (!nama_produk || !satuan || !harga_dasar) {
      return res.status(400).json({ success: false, message: "Data produk tidak lengkap" });
    }

    let normalizedSku;
    try {
      normalizedSku = normalizeSku(sku);
    } catch (error) {
      return res.status(400).json({ success: false, message: error.message });
    }
```

Penjelasan: endpoint tambah produk memvalidasi data wajib dan menormalisasi SKU sebelum insert. Validasi ini mencegah data katalog tidak lengkap masuk ke database.

```js
    await client.query("BEGIN");
    const product = await createProduct(client, {
      sku: normalizedSku,
      nama_produk,
      kategori,
      satuan,
      harga_dasar,
      stok_gudang,
    });

    if (Number(stok_gudang || 0) > 0) {
      await recordInventoryMovement(client, {
        productId: product.product_id,
        movementType: "INITIAL_STOCK",
        quantity: Number(stok_gudang || 0),
        note: "Stok awal saat produk dibuat",
        referenceType: "PRODUCT",
        referenceId: product.product_id,
      });
    }

    await client.query("COMMIT");
    res.status(201).json({ success: true, data: product });
```

Penjelasan: insert produk dan pencatatan stok awal berjalan dalam transaksi yang sama. Kalau produk baru punya stok awal, Catalog Service memanggil pencatatan movement `INITIAL_STOCK` sehingga Inventory Service tetap punya audit trail.

### SQL repository katalog

Lokasi kode: `prokura-api/src/services/catalog/repository.js`

- Query list/search produk: line 22.
- Insert produk baru: line 37.

```js
if (filters.q) {
  params.push(`%${filters.q}%`);
  conditions.push(`(p.nama_produk ILIKE $${params.length} OR p.sku ILIKE $${params.length})`);
}

if (filters.category) {
  params.push(filters.category);
  conditions.push(`p.kategori = $${params.length}`);
}
```

Penjelasan: bagian ini membangun filter pencarian berdasarkan nama/SKU dan kategori dengan parameter query PostgreSQL. Parameter dipisahkan dari string SQL untuk mengurangi risiko SQL injection.

```js
const { rows } = await pool.query(
  `
    SELECT p.product_id, p.sku, p.nama_produk, p.kategori, p.satuan,
           p.harga_dasar, p.stok_gudang, i.image_url
    FROM products p
    LEFT JOIN productimages i ON p.product_id = i.product_id AND i.is_primary = TRUE
    ${where}
    ORDER BY p.nama_produk ASC
  `,
  params,
);
```

Penjelasan: query ini mengambil produk beserta gambar utama jika ada, menerapkan filter yang sudah dibuat, lalu mengurutkan produk berdasarkan nama.

```js
const { rows } = await client.query(
  `
    INSERT INTO products (sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang)
    VALUES ($1, $2, $3, $4, $5, $6)
    RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang
  `,
  [
    product.sku,
    product.nama_produk,
    product.kategori || null,
    product.satuan,
    product.harga_dasar,
    product.stok_gudang || 0,
  ],
);
```

Penjelasan: query insert ini membuat produk baru dan langsung mengembalikan data produk yang baru dibuat. Return value dipakai API untuk menampilkan feedback sukses ke UI.

### UI admin dan customer

Lokasi kode:

- `prokura-admin/app3.py`, menu `Manajemen Stok Gudang`, line 399 dan form `Tambah Produk Baru` line 463.
- `prokura-web/app/page.tsx`, fetch produk line 58 dan search input line 264.

```tsx
fetch(`${API_BASE_URL}/api/products`).then((r) => r.json()),
```

Penjelasan: customer web mengambil katalog melalui API gateway, bukan database langsung.

```tsx
<input
  value={searchTerm}
  onChange={(event) => setSearchTerm(event.target.value)}
  placeholder="Cari produk atau SKU..."
```

Penjelasan: input ini menjadi kontrol pencarian di customer web. Nilai `searchTerm` dipakai untuk memfilter produk berdasarkan nama atau SKU di sisi UI setelah data katalog diterima dari API.

## SQL Query Demo dan Penjelasan

### Query 1: tambah produk

```sql
INSERT INTO products (sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang)
VALUES ('SKU-DEMO-001', 'Demo Product', 'Bahan Pokok', 'Kg', 25000, 50)
RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang;
```

Penjelasan: query ini menambahkan satu produk baru ke tabel `products`. Bagian `RETURNING` dipakai untuk membuktikan row benar-benar masuk dan untuk melihat `product_id` yang dibuat PostgreSQL.

### Query 2: cari produk

```sql
SELECT p.product_id, p.sku, p.nama_produk, p.kategori, p.satuan,
       p.harga_dasar, p.stok_gudang
FROM products p
WHERE p.nama_produk ILIKE '%demo%'
   OR p.sku ILIKE '%demo%'
ORDER BY p.nama_produk ASC;
```

Penjelasan: query ini mencari produk dengan keyword `demo` pada nama produk atau SKU. `ILIKE` membuat pencarian tidak sensitif huruf besar/kecil. Hasilnya menunjukkan produk yang baru ditambahkan bisa ditemukan dari katalog.

## Alur Demo

### A. Penambahan barang baru

1. Jalankan SQL `SELECT` berdasarkan SKU demo untuk menunjukkan produk belum ada atau mencatat kondisi awal.
2. Buka admin `Manajemen Stok Gudang`.
3. Masuk ke tab `Tambah Produk Baru`.
4. Isi SKU, nama produk, kategori, satuan, harga dasar, dan stok awal.
5. Submit form.
6. Tunjukkan response sukses dan data produk baru.
7. Jalankan SQL `SELECT` ulang untuk menunjukkan row baru di `products`.

### B. Pencarian dan filter barang

1. Buka katalog produk di admin atau customer web.
2. Ketik nama/SKU produk demo pada search input.
3. Pilih kategori jika ingin menunjukkan filter kategori.
4. Tunjukkan hanya produk yang cocok yang tampil.
5. Hubungkan tampilan UI dengan endpoint `GET /api/products` dan query `ILIKE` pada repository.

## Bukti Validasi

- Unit test Catalog: `prokura-api/tests/unit/catalog-domain.test.js`.
- Repository test Catalog: `prokura-api/tests/unit/repository.test.js`.
- Integration test lintas service: `prokura-api/tests/integration/api-final-project.test.js`.
- Smoke test final project membuat produk dan mencari produk baru.

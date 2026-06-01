# Catalog Service

Tanggung jawab:

- Menambah produk baru.
- Mengubah dan menghapus produk.
- Mencari produk berdasarkan nama, SKU, kategori, dan ketersediaan stok.

Endpoint saat ini masih diregistrasikan di `server.js`:

- `GET /api/products`
- `POST /api/products`
- `PATCH /api/products/:product_id`
- `DELETE /api/products/:product_id`

Target refactor: pindahkan route dan query produk ke `routes.js` dan `repository.js` di folder ini.

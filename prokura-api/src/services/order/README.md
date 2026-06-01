# Order Service

Tanggung jawab:

- Menerima checkout customer.
- Membuat purchase order dan order details.
- Mengurangi stok saat checkout.
- Mengubah status order dan mengembalikan stok saat order ditolak.

Endpoint saat ini masih diregistrasikan di `server.js`:

- `GET /api/orders`
- `GET /api/orders/:po_id`
- `GET /api/companies/:company_id/orders`
- `POST /api/orders`
- `PATCH /api/orders/:po_id/status`

Target refactor: pindahkan route dan transaction script order ke folder ini, lalu konsumsi Inventory Service untuk movement stok.

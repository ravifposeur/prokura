# Inventory Service

Inventory Service bertanggung jawab atas stok gudang dan audit trail pergerakan stok.

Endpoint aktif:

- `PATCH /api/products/:product_id/stock`
- `GET /api/inventory/movements`

Database:

- `products.stok_gudang`
- `inventory_movements`

Perubahan stok yang harus dicatat:

- `INITIAL_STOCK`
- `STOCK_IN`
- `STOCK_OUT`
- `STOCK_RETURN`

const { buildProductSearchFilters, normalizeSku } = require("./domain");
const {
  countOrderDetailsByProduct,
  createProduct,
  deleteProduct,
  listProducts,
  updateProduct,
} = require("./repository");

function registerCatalogRoutes(app, { pool, sendError, recordInventoryMovement }) {
  app.get("/api/products", async (req, res) => {
    try {
      const filters = buildProductSearchFilters(req.query);
      const products = await listProducts(pool, filters);
      res.json({ success: true, data: products });
    } catch (error) {
      sendError(res, error, "Gagal mengambil katalog produk");
    }
  });

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
    } catch (error) {
      await client.query("ROLLBACK");
      sendError(res, error, "Gagal menambah produk");
    } finally {
      client.release();
    }
  });

  app.patch("/api/products/:product_id", async (req, res) => {
    try {
      const { product_id } = req.params;
      const product = await updateProduct(pool, product_id, req.body);

      if (!product) {
        return res.status(404).json({ success: false, message: "Produk tidak ditemukan" });
      }
      res.json({ success: true, data: product });
    } catch (error) {
      sendError(res, error, "Gagal memperbarui produk");
    }
  });

  app.delete("/api/products/:product_id", async (req, res) => {
    try {
      const { product_id } = req.params;
      const usedCount = await countOrderDetailsByProduct(pool, product_id);
      if (usedCount > 0) {
        return res.status(409).json({ success: false, message: "Produk sudah dipakai di PO dan tidak bisa dihapus" });
      }

      const deletedRows = await deleteProduct(pool, product_id);
      if (deletedRows === 0) {
        return res.status(404).json({ success: false, message: "Produk tidak ditemukan" });
      }
      res.json({ success: true, data: { product_id: Number(product_id) } });
    } catch (error) {
      sendError(res, error, "Gagal menghapus produk");
    }
  });
}

module.exports = {
  registerCatalogRoutes,
};

const { buildProductSearchFilters, normalizeSku } = require("./domain");

function registerCatalogRoutes(app, { pool, sendError, recordInventoryMovement }) {
  app.get("/api/products", async (req, res) => {
    try {
      const filters = buildProductSearchFilters(req.query);
      const params = [];
      const conditions = [];

      if (!filters.includeEmpty) {
        conditions.push("p.stok_gudang > 0");
      }

      if (filters.q) {
        params.push(`%${filters.q}%`);
        conditions.push(`(p.nama_produk ILIKE $${params.length} OR p.sku ILIKE $${params.length})`);
      }

      if (filters.category) {
        params.push(filters.category);
        conditions.push(`p.kategori = $${params.length}`);
      }

      const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
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
      res.json({ success: true, data: rows });
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
      const { rows } = await client.query(
        `
          INSERT INTO products (sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang)
          VALUES ($1, $2, $3, $4, $5, $6)
          RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang
        `,
        [normalizedSku, nama_produk, kategori || null, satuan, harga_dasar, stok_gudang || 0],
      );

      if (Number(stok_gudang || 0) > 0) {
        await recordInventoryMovement(client, {
          productId: rows[0].product_id,
          movementType: "INITIAL_STOCK",
          quantity: Number(stok_gudang || 0),
          note: "Stok awal saat produk dibuat",
          referenceType: "PRODUCT",
          referenceId: rows[0].product_id,
        });
      }

      await client.query("COMMIT");
      res.status(201).json({ success: true, data: rows[0] });
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
      const { nama_produk, kategori, satuan, harga_dasar, stok_gudang } = req.body;
      const { rows } = await pool.query(
        `
          UPDATE products
          SET nama_produk = $1, kategori = $2, satuan = $3, harga_dasar = $4, stok_gudang = $5
          WHERE product_id = $6
          RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang
        `,
        [nama_produk, kategori || null, satuan, harga_dasar, stok_gudang, product_id],
      );

      if (rows.length === 0) {
        return res.status(404).json({ success: false, message: "Produk tidak ditemukan" });
      }
      res.json({ success: true, data: rows[0] });
    } catch (error) {
      sendError(res, error, "Gagal memperbarui produk");
    }
  });

  app.delete("/api/products/:product_id", async (req, res) => {
    try {
      const { product_id } = req.params;
      const used = await pool.query("SELECT COUNT(*)::int AS count FROM orderdetails WHERE product_id = $1", [product_id]);
      if (used.rows[0].count > 0) {
        return res.status(409).json({ success: false, message: "Produk sudah dipakai di PO dan tidak bisa dihapus" });
      }

      const result = await pool.query("DELETE FROM products WHERE product_id = $1", [product_id]);
      if (result.rowCount === 0) {
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

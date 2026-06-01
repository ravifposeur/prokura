const { parsePositiveInteger } = require("./domain");

function registerInventoryRoutes(app, { pool, sendError, recordInventoryMovement }) {
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

      if (rows.length === 0) {
        throw new Error("Produk tidak ditemukan");
      }

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
    } catch (error) {
      await client.query("ROLLBACK");
      sendError(res, error, "Gagal menambah stok");
    } finally {
      client.release();
    }
  });

  app.get("/api/inventory/movements", async (req, res) => {
    try {
      const conditions = [];
      const params = [];

      if (req.query.product_id) {
        params.push(req.query.product_id);
        conditions.push(`m.product_id = $${params.length}`);
      }

      if (req.query.movement_type) {
        params.push(req.query.movement_type);
        conditions.push(`m.movement_type = $${params.length}`);
      }

      const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
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

      res.json({ success: true, data: rows });
    } catch (error) {
      sendError(res, error, "Gagal mengambil riwayat stok");
    }
  });
}

module.exports = {
  registerInventoryRoutes,
};

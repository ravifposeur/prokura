const { calculateOrderTotal, validateOrderPayload } = require("./domain");

function registerOrderRoutes(app, { pool, sendError, recordInventoryMovement }) {
  app.get("/api/orders", async (_req, res) => {
    try {
      const { rows } = await pool.query(`
        SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
               po.tanggal_dipesan, c.nama_perusahaan AS company,
               u.nama_lengkap AS pembuat
        FROM purchaseorders po
        JOIN companies c ON po.company_id = c.company_id
        JOIN users u ON po.dibuat_oleh = u.user_id
        ORDER BY po.tanggal_dipesan DESC
      `);
      res.json({ success: true, data: rows });
    } catch (error) {
      sendError(res, error, "Gagal mengambil daftar PO");
    }
  });

  app.get("/api/companies/:company_id/orders", async (req, res) => {
    try {
      const { company_id } = req.params;
      const { rows } = await pool.query(
        `
          SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
                 po.tanggal_dipesan, u.nama_lengkap AS pembuat
          FROM purchaseorders po
          JOIN users u ON po.dibuat_oleh = u.user_id
          WHERE po.company_id = $1
          ORDER BY po.tanggal_dipesan DESC
        `,
        [company_id],
      );
      res.json({ success: true, data: rows });
    } catch (error) {
      sendError(res, error, "Gagal mengambil riwayat PO");
    }
  });

  app.get("/api/orders/:po_id", async (req, res) => {
    try {
      const { po_id } = req.params;
      const { rows } = await pool.query(
        `
          SELECT p.sku, p.nama_produk, p.satuan, od.kuantitas, od.harga_final,
                 (od.kuantitas * od.harga_final) AS subtotal
          FROM orderdetails od
          JOIN products p ON od.product_id = p.product_id
          WHERE od.po_id = $1
          ORDER BY od.detail_id ASC
        `,
        [po_id],
      );
      res.json({ success: true, data: rows });
    } catch (error) {
      sendError(res, error, "Gagal mengambil detail PO");
    }
  });

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
    try {
      await client.query("BEGIN");

      for (const item of items) {
        const stock = await client.query(
          "SELECT stok_gudang FROM products WHERE product_id = $1 FOR UPDATE",
          [item.product_id],
        );
        if (stock.rows.length === 0 || Number(stock.rows[0].stok_gudang) < Number(item.kuantitas)) {
          throw new Error(`Stok produk ${item.product_id} tidak cukup`);
        }
      }

      const poResult = await client.query(
        `
          INSERT INTO purchaseorders (company_id, dibuat_oleh, metode_pembayaran, total_tagihan)
          VALUES ($1, $2, $3, $4)
          RETURNING po_id
        `,
        [company_id, dibuat_oleh, metode_pembayaran, orderTotal],
      );

      const newPoId = poResult.rows[0].po_id;

      for (const item of items) {
        await client.query(
          `
            INSERT INTO orderdetails (po_id, product_id, kuantitas, harga_final)
            VALUES ($1, $2, $3, $4)
          `,
          [newPoId, item.product_id, item.kuantitas, item.harga_final],
        );

        await client.query(
          `
            UPDATE products
            SET stok_gudang = stok_gudang - $1
            WHERE product_id = $2
          `,
          [item.kuantitas, item.product_id],
        );

        await recordInventoryMovement(client, {
          productId: item.product_id,
          movementType: "STOCK_OUT",
          quantity: -Number(item.kuantitas),
          note: `Checkout PO #${newPoId}`,
          referenceType: "ORDER",
          referenceId: newPoId,
        });
      }

      await client.query("COMMIT");
      res.json({
        success: true,
        message: "PO berhasil diajukan untuk approval",
        po_id: newPoId,
        data: { po_id: newPoId },
      });
    } catch (error) {
      await client.query("ROLLBACK");
      res.status(500).json({ success: false, message: error.message || "Gagal memproses transaksi PO" });
    } finally {
      client.release();
    }
  });

  app.patch("/api/orders/:po_id/status", async (req, res) => {
    const { po_id } = req.params;
    const { status_po } = req.body;
    const allowedStatuses = ["Pending_Approval", "Approved", "Rejected", "Processing", "Delivered", "Cancelled"];

    if (!allowedStatuses.includes(status_po)) {
      return res.status(400).json({ success: false, message: "Status PO tidak valid" });
    }

    const client = await pool.connect();
    try {
      await client.query("BEGIN");

      const current = await client.query(
        "SELECT status_po FROM purchaseorders WHERE po_id = $1 FOR UPDATE",
        [po_id],
      );

      if (current.rows.length === 0) {
        throw new Error("PO tidak ditemukan");
      }

      const oldStatus = current.rows[0].status_po;
      const result = await client.query(
        `
          UPDATE purchaseorders
          SET status_po = $1
          WHERE po_id = $2
          RETURNING po_id, status_po
        `,
        [status_po, po_id],
      );

      if (status_po === "Rejected" && oldStatus !== "Rejected") {
        const { rows: items } = await client.query(
          "SELECT product_id, kuantitas FROM orderdetails WHERE po_id = $1",
          [po_id],
        );

        for (const item of items) {
          await client.query(
            "UPDATE products SET stok_gudang = stok_gudang + $1 WHERE product_id = $2",
            [item.kuantitas, item.product_id],
          );

          await recordInventoryMovement(client, {
            productId: item.product_id,
            movementType: "STOCK_RETURN",
            quantity: Number(item.kuantitas),
            note: `Pengembalian stok karena PO #${po_id} ditolak`,
            referenceType: "ORDER",
            referenceId: Number(po_id),
          });
        }
      }

      await client.query("COMMIT");
      res.json({ success: true, data: result.rows[0] });
    } catch (error) {
      await client.query("ROLLBACK");
      sendError(res, error, "Gagal memproses status PO");
    } finally {
      client.release();
    }
  });
}

module.exports = {
  registerOrderRoutes,
};

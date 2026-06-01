const { calculateOrderTotal, validateOrderPayload } = require("./domain");
const {
  createOrderDetail,
  createPurchaseOrder,
  decrementProductStock,
  getOrderStatusForUpdate,
  incrementProductStock,
  listCompanyOrders,
  listOrderDetails,
  listOrders,
  listOrderStockItems,
  lockProductStock,
  updateOrderStatus,
} = require("./repository");

function registerOrderRoutes(app, { pool, sendError, recordInventoryMovement }) {
  app.get("/api/orders", async (_req, res) => {
    try {
      const orders = await listOrders(pool);
      res.json({ success: true, data: orders });
    } catch (error) {
      sendError(res, error, "Gagal mengambil daftar PO");
    }
  });

  app.get("/api/companies/:company_id/orders", async (req, res) => {
    try {
      const { company_id } = req.params;
      const orders = await listCompanyOrders(pool, company_id);
      res.json({ success: true, data: orders });
    } catch (error) {
      sendError(res, error, "Gagal mengambil riwayat PO");
    }
  });

  app.get("/api/orders/:po_id", async (req, res) => {
    try {
      const { po_id } = req.params;
      const details = await listOrderDetails(pool, po_id);
      res.json({ success: true, data: details });
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
        const stock = await lockProductStock(client, item.product_id);
        if (!stock || Number(stock.stok_gudang) < Number(item.kuantitas)) {
          throw new Error(`Stok produk ${item.product_id} tidak cukup`);
        }
      }

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

      const current = await getOrderStatusForUpdate(client, po_id);

      if (!current) {
        throw new Error("PO tidak ditemukan");
      }

      const oldStatus = current.status_po;
      const result = await updateOrderStatus(client, po_id, status_po);

      if (status_po === "Rejected" && oldStatus !== "Rejected") {
        const items = await listOrderStockItems(client, po_id);

        for (const item of items) {
          await incrementProductStock(client, item);

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
    res.json({ success: true, data: result });
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

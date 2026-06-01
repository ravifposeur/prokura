const { normalizeDateRange } = require("./domain");

function registerReportingRoutes(app, { pool, sendError }) {
  app.get("/api/admin/summary", async (_req, res) => {
    try {
      const { rows } = await pool.query(`
        SELECT
          (SELECT COUNT(*)::int FROM companies) AS companies,
          (SELECT COUNT(*)::int FROM products) AS products,
          (SELECT COUNT(*)::int FROM purchaseorders) AS orders,
          (SELECT COUNT(*)::int FROM purchaseorders WHERE status_po = 'Pending_Approval') AS pending_orders
      `);
      res.json({ success: true, data: rows[0] });
    } catch (error) {
      sendError(res, error, "Gagal mengambil ringkasan admin");
    }
  });

  app.get("/api/reports/sales", async (req, res) => {
    try {
      const { start, end } = normalizeDateRange(req.query);
      const params = [start, end];

      const summary = await pool.query(
        `
          SELECT COUNT(*)::int AS total_po,
                 COALESCE(SUM(total_tagihan), 0)::float AS total_revenue,
                 COALESCE(AVG(total_tagihan), 0)::float AS avg_po,
                 COUNT(DISTINCT company_id)::int AS klien_aktif
          FROM purchaseorders
          WHERE DATE(tanggal_dipesan) BETWEEN $1 AND $2
            AND status_po != 'Cancelled'
        `,
        params,
      );

      const monthly = await pool.query(
        `
          SELECT TO_CHAR(tanggal_dipesan, 'YYYY-MM') AS bulan,
                 SUM(total_tagihan)::float AS revenue,
                 COUNT(*)::int AS jumlah_po
          FROM purchaseorders
          WHERE DATE(tanggal_dipesan) BETWEEN $1 AND $2
            AND status_po != 'Cancelled'
          GROUP BY TO_CHAR(tanggal_dipesan, 'YYYY-MM')
          ORDER BY bulan ASC
        `,
        params,
      );

      const segments = await pool.query(
        `
          SELECT c.kategori_industri AS segmen,
                 SUM(po.total_tagihan)::float AS revenue
          FROM purchaseorders po
          JOIN companies c ON po.company_id = c.company_id
          WHERE DATE(po.tanggal_dipesan) BETWEEN $1 AND $2
            AND po.status_po != 'Cancelled'
          GROUP BY c.kategori_industri
          ORDER BY revenue DESC
        `,
        params,
      );

      const topProducts = await pool.query(
        `
          SELECT p.nama_produk AS produk, p.kategori,
                 SUM(od.kuantitas)::int AS total_qty,
                 SUM(od.kuantitas * od.harga_final)::float AS revenue
          FROM orderdetails od
          JOIN products p ON od.product_id = p.product_id
          JOIN purchaseorders po ON od.po_id = po.po_id
          WHERE DATE(po.tanggal_dipesan) BETWEEN $1 AND $2
            AND po.status_po != 'Cancelled'
          GROUP BY p.product_id
          ORDER BY total_qty DESC
          LIMIT 10
        `,
        params,
      );

      const topClients = await pool.query(
        `
          SELECT c.nama_perusahaan AS klien, c.kategori_industri AS segmen,
                 COUNT(po.po_id)::int AS jumlah_po,
                 SUM(po.total_tagihan)::float AS revenue
          FROM purchaseorders po
          JOIN companies c ON po.company_id = c.company_id
          WHERE DATE(po.tanggal_dipesan) BETWEEN $1 AND $2
            AND po.status_po != 'Cancelled'
          GROUP BY c.company_id
          ORDER BY revenue DESC
          LIMIT 10
        `,
        params,
      );

      const transactions = await pool.query(
        `
          SELECT po.po_id, DATE(po.tanggal_dipesan) AS tanggal,
                 c.nama_perusahaan AS klien, c.kategori_industri AS segmen,
                 po.metode_pembayaran AS pembayaran, po.status_po AS status,
                 po.total_tagihan
          FROM purchaseorders po
          JOIN companies c ON po.company_id = c.company_id
          WHERE DATE(po.tanggal_dipesan) BETWEEN $1 AND $2
          ORDER BY po.tanggal_dipesan DESC
        `,
        params,
      );

      res.json({
        success: true,
        data: {
          summary: summary.rows[0],
          monthly: monthly.rows,
          segments: segments.rows,
          top_products: topProducts.rows,
          top_clients: topClients.rows,
          transactions: transactions.rows,
        },
      });
    } catch (error) {
      sendError(res, error, "Gagal mengambil laporan penjualan");
    }
  });
}

module.exports = {
  registerReportingRoutes,
};

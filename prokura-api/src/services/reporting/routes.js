const { normalizeDateRange } = require("./domain");
const { getAdminSummary, getSalesReport } = require("./repository");

function registerReportingRoutes(app, { pool, sendError }) {
  app.get("/api/admin/summary", async (_req, res) => {
    try {
      const summary = await getAdminSummary(pool);
      res.json({ success: true, data: summary });
    } catch (error) {
      sendError(res, error, "Gagal mengambil ringkasan admin");
    }
  });

  app.get("/api/reports/sales", async (req, res) => {
    try {
      const { start, end } = normalizeDateRange(req.query);
      const report = await getSalesReport(pool, { start, end });

      res.json({
        success: true,
        data: report,
      });
    } catch (error) {
      sendError(res, error, "Gagal mengambil laporan penjualan");
    }
  });
}

module.exports = {
  registerReportingRoutes,
};

const express = require("express");
const cors = require("cors");
const { createPool, ensureSchema } = require("./src/shared/db");
const { sendError } = require("./src/shared/http");
const { registerCatalogRoutes } = require("./src/services/catalog/routes");
const { registerCustomerRoutes } = require("./src/services/customer/routes");
const { registerInventoryRoutes } = require("./src/services/inventory/routes");
const { recordInventoryMovement } = require("./src/services/inventory/repository");
const { registerOrderRoutes } = require("./src/services/order/routes");
const { registerReportingRoutes } = require("./src/services/reporting/routes");

const app = express();
app.use(cors());
app.use(express.json());

const pool = createPool();

pool
  .connect()
  .then((client) => {
    client.release();
    return ensureSchema(pool);
  })
  .then(() => {
    console.log("Connected to PostgreSQL");
  })
  .catch((err) => console.error("Database connection failed:", err.stack));

app.get("/api/health", async (_req, res) => {
  try {
    const { rows } = await pool.query("SELECT NOW() AS now");
    res.json({ success: true, data: { database: "ok", now: rows[0].now } });
  } catch (error) {
    sendError(res, error, "Database tidak siap");
  }
});

const routeDependencies = { pool, sendError, recordInventoryMovement };
registerReportingRoutes(app, routeDependencies);
registerCustomerRoutes(app, routeDependencies);
registerCatalogRoutes(app, routeDependencies);
registerInventoryRoutes(app, routeDependencies);
registerOrderRoutes(app, routeDependencies);

const PORT = Number(process.env.PORT || 5000);
app.listen(PORT, () => {
  console.log(`Prokura API running at http://localhost:${PORT}`);
});

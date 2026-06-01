const express = require("express");
const cors = require("cors");
const { createPool, ensureSchema } = require("./shared/db");
const { sendError } = require("./shared/http");
const { registerCatalogRoutes } = require("./services/catalog/routes");
const { registerCustomerRoutes } = require("./services/customer/routes");
const { registerInventoryRoutes } = require("./services/inventory/routes");
const { recordInventoryMovement } = require("./services/inventory/repository");
const { registerOrderRoutes } = require("./services/order/routes");
const { registerReportingRoutes } = require("./services/reporting/routes");

const serviceName = process.argv[2] || process.env.SERVICE_NAME;
const serviceRegistry = {
  catalog: registerCatalogRoutes,
  customer: registerCustomerRoutes,
  inventory: registerInventoryRoutes,
  order: registerOrderRoutes,
  reporting: registerReportingRoutes,
};

if (!serviceRegistry[serviceName]) {
  const names = Object.keys(serviceRegistry).join(", ");
  console.error(`SERVICE_NAME tidak valid. Gunakan salah satu: ${names}`);
  process.exit(1);
}

const app = express();
const pool = createPool();

app.use(cors());
app.use(express.json());

app.get("/health", async (_req, res) => {
  try {
    const { rows } = await pool.query("SELECT NOW() AS now");
    res.json({
      success: true,
      data: {
        service: serviceName,
        database: "ok",
        now: rows[0].now,
      },
    });
  } catch (error) {
    sendError(res, error, `${serviceName} service tidak siap`);
  }
});

app.get(`/api/services/${serviceName}/health`, async (_req, res) => {
  res.json({ success: true, data: { service: serviceName, status: "ok" } });
});

const routeDependencies = { pool, sendError, recordInventoryMovement };
serviceRegistry[serviceName](app, routeDependencies);

pool
  .connect()
  .then((client) => {
    client.release();
    return ensureSchema(pool);
  })
  .then(() => {
    const port = Number(process.env.PORT || 5100);
    app.listen(port, () => {
      console.log(`Prokura ${serviceName} service running at http://localhost:${port}`);
    });
  })
  .catch((error) => {
    console.error(`${serviceName} service database connection failed:`, error.stack);
    process.exit(1);
  });

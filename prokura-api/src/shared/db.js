const { Pool } = require("pg");

function createPool() {
  return new Pool({
    user: process.env.PGUSER || "prokura",
    host: process.env.PGHOST || "localhost",
    database: process.env.PGDATABASE || "prokuradb",
    password: process.env.PGPASSWORD || "prokura",
    port: Number(process.env.PGPORT || 5432),
  });
}

async function ensureSchema(pool) {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS inventory_movements (
      movement_id SERIAL PRIMARY KEY,
      product_id INT REFERENCES products(product_id),
      movement_type VARCHAR(30) NOT NULL,
      quantity INT NOT NULL,
      note TEXT,
      reference_type VARCHAR(30),
      reference_id INT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);
}

module.exports = {
  createPool,
  ensureSchema,
};

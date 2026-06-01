const express = require("express");
const cors = require("cors");
const { Pool } = require("pg");

const app = express();
app.use(cors());
app.use(express.json());

const pool = new Pool({
  user: process.env.PGUSER || "prokura",
  host: process.env.PGHOST || "localhost",
  database: process.env.PGDATABASE || "prokuradb",
  password: process.env.PGPASSWORD || "prokura",
  port: Number(process.env.PGPORT || 5432),
});

function sendError(res, error, message = "Terjadi kesalahan server") {
  console.error(message, error);
  res.status(500).json({ success: false, message });
}

pool
  .connect()
  .then((client) => {
    client.release();
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

app.get("/api/companies", async (_req, res) => {
  try {
    const { rows } = await pool.query(`
      SELECT company_id, nama_perusahaan, npwp, kategori_industri, limit_kredit, created_at
      FROM companies
      ORDER BY nama_perusahaan ASC
    `);
    res.json({ success: true, data: rows });
  } catch (error) {
    sendError(res, error, "Gagal mengambil data perusahaan");
  }
});

app.post("/api/companies", async (req, res) => {
  try {
    const { nama_perusahaan, npwp, kategori_industri, limit_kredit } = req.body;
    if (!nama_perusahaan || !kategori_industri) {
      return res.status(400).json({ success: false, message: "Nama perusahaan dan industri wajib diisi" });
    }

    const { rows } = await pool.query(
      `
        INSERT INTO companies (nama_perusahaan, npwp, kategori_industri, limit_kredit)
        VALUES ($1, $2, $3, $4)
        RETURNING company_id, nama_perusahaan, npwp, kategori_industri, limit_kredit, created_at
      `,
      [nama_perusahaan, npwp || null, kategori_industri, limit_kredit || 0],
    );
    res.status(201).json({ success: true, data: rows[0] });
  } catch (error) {
    sendError(res, error, "Gagal menambah perusahaan");
  }
});

app.get("/api/users", async (req, res) => {
  try {
    const companyId = req.query.company_id;
    const params = [];
    let where = "";
    if (companyId) {
      params.push(companyId);
      where = "WHERE u.company_id = $1";
    }

    const { rows } = await pool.query(
      `
        SELECT u.user_id, u.company_id, c.nama_perusahaan AS company,
               u.nama_lengkap, u.email, u.peran
        FROM users u
        JOIN companies c ON u.company_id = c.company_id
        ${where}
        ORDER BY c.nama_perusahaan ASC, u.nama_lengkap ASC
      `,
      params,
    );
    res.json({ success: true, data: rows });
  } catch (error) {
    sendError(res, error, "Gagal mengambil pengguna");
  }
});

app.post("/api/users", async (req, res) => {
  try {
    const { company_id, nama_lengkap, email, peran } = req.body;
    if (!company_id || !nama_lengkap || !email || !peran) {
      return res.status(400).json({ success: false, message: "Data pengguna tidak lengkap" });
    }

    const { rows } = await pool.query(
      `
        INSERT INTO users (company_id, nama_lengkap, email, peran)
        VALUES ($1, $2, $3, $4)
        RETURNING user_id, company_id, nama_lengkap, email, peran
      `,
      [company_id, nama_lengkap, email, peran],
    );
    res.status(201).json({ success: true, data: rows[0] });
  } catch (error) {
    sendError(res, error, "Gagal menambah pengguna");
  }
});

app.get("/api/products", async (req, res) => {
  try {
    const includeEmpty = req.query.include_empty === "true";
    const { rows } = await pool.query(`
      SELECT p.product_id, p.sku, p.nama_produk, p.kategori, p.satuan,
             p.harga_dasar, p.stok_gudang, i.image_url
      FROM products p
      LEFT JOIN productimages i ON p.product_id = i.product_id AND i.is_primary = TRUE
      ${includeEmpty ? "" : "WHERE p.stok_gudang > 0"}
      ORDER BY p.nama_produk ASC
    `);
    res.json({ success: true, data: rows });
  } catch (error) {
    sendError(res, error, "Gagal mengambil katalog produk");
  }
});

app.post("/api/products", async (req, res) => {
  try {
    const { sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang } = req.body;
    if (!sku || !nama_produk || !satuan || !harga_dasar) {
      return res.status(400).json({ success: false, message: "Data produk tidak lengkap" });
    }

    const { rows } = await pool.query(
      `
        INSERT INTO products (sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang
      `,
      [sku.toUpperCase(), nama_produk, kategori || null, satuan, harga_dasar, stok_gudang || 0],
    );
    res.status(201).json({ success: true, data: rows[0] });
  } catch (error) {
    sendError(res, error, "Gagal menambah produk");
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

app.get("/api/companies/:company_id/credit", async (req, res) => {
  try {
    const { company_id } = req.params;
    const { rows } = await pool.query(
      `
        SELECT company_id, nama_perusahaan, limit_kredit
        FROM companies
        WHERE company_id = $1
      `,
      [company_id],
    );

    if (rows.length === 0) {
      return res
        .status(404)
        .json({ success: false, message: "Perusahaan tidak ditemukan" });
    }

    res.json({ success: true, data: rows[0] });
  } catch (error) {
    sendError(res, error, "Gagal mengambil data kredit");
  }
});

app.get("/api/reports/sales", async (req, res) => {
  try {
    const start = req.query.start || "1900-01-01";
    const end = req.query.end || "2999-12-31";
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

  if (!company_id || !dibuat_oleh || !metode_pembayaran || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ success: false, message: "Payload order tidak lengkap" });
  }

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
      [company_id, dibuat_oleh, metode_pembayaran, total_tagihan],
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
    }

    await client.query("COMMIT");
    res.json({
      success: true,
      message: "PO berhasil diajukan untuk approval",
      po_id: newPoId,
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

const PORT = Number(process.env.PORT || 5000);
app.listen(PORT, () => {
  console.log(`Prokura API running at http://localhost:${PORT}`);
});

const express = require("express");
const cors = require("cors");
const { Pool } = require("pg");

const app = express();
app.use(cors());
app.use(express.json());

// Konfigurasi koneksi lokal
const pool = new Pool({
  user: "prokura",
  host: "localhost",
  database: "prokuradb",
  password: "prokura",
  port: 5432,
});

pool
  .connect()
  .then(() =>
    console.log(
      "✅ Terkoneksi ke PostgreSQL Lokal (prokuraDB) - Kedaulatan Data Aktif",
    ),
  )
  .catch((err) => console.error("❌ Gagal koneksi database:", err.stack));

// ==========================================
// 1. KATALOG PRODUK
// ==========================================
app.get("/api/products", async (req, res) => {
  try {
    const query = `
            SELECT p.product_id, p.sku, p.nama_produk, p.kategori, p.satuan,
                   p.harga_dasar, p.stok_gudang, i.image_url
            FROM Products p
            LEFT JOIN productimages i ON p.product_id = i.product_id AND i.is_primary = TRUE
            WHERE p.stok_gudang > 0
            ORDER BY p.nama_produk ASC;
        `;
    const { rows } = await pool.query(query);
    res.json({ success: true, data: rows });
  } catch (error) {
    console.error("Log Error DB:", error); // Tambahkan baris ini sebagai instrumen monitoring
    res
      .status(500)
      .json({ success: false, message: "Terjadi kesalahan server" });
  }
});

// ==========================================
// 2. CEK LIMIT KREDIT PERUSAHAAN
// Fungsi: Mengecek profil perusahaan dan sisa limit kredit sebelum PO dibuat [cite: 445, 448, 449, 450]
// ==========================================
app.get("/api/companies/:company_id/credit", async (req, res) => {
  try {
    const { company_id } = req.params;
    const query = `
            SELECT nama_perusahaan, limit_kredit
            FROM Companies
            WHERE company_id = $1;
        `;
    const { rows } = await pool.query(query, [company_id]);

    if (rows.length === 0)
      return res
        .status(404)
        .json({ success: false, message: "Perusahaan tidak ditemukan" });
    res.json({ success: true, data: rows[0] });
  } catch (error) {
    res
      .status(500)
      .json({ success: false, message: "Gagal mengambil data kredit" });
  }
});

// ==========================================
// 3. PEMBUATAN PESANAN (TRANSACTION)
// ==========================================
app.post("/api/orders", async (req, res) => {
  const { company_id, dibuat_oleh, metode_pembayaran, total_tagihan, items } =
    req.body;
  const client = await pool.connect();

  try {
    await client.query("BEGIN");

    const poQuery = `
            INSERT INTO PurchaseOrders (company_id, dibuat_oleh, metode_pembayaran, total_tagihan)
            VALUES ($1, $2, $3, $4) RETURNING po_id;
        `;
    const poResult = await client.query(poQuery, [
      company_id,
      dibuat_oleh,
      metode_pembayaran,
      total_tagihan,
    ]);
    const newPoId = poResult.rows[0].po_id;

    for (let item of items) {
      const { product_id, kuantitas, harga_final } = item;

      await client.query(
        `
                INSERT INTO OrderDetails (po_id, product_id, kuantitas, harga_final)
                VALUES ($1, $2, $3, $4);
            `,
        [newPoId, product_id, kuantitas, harga_final],
      );

      await client.query(
        `
                UPDATE Products SET stok_gudang = stok_gudang - $1
                WHERE product_id = $2;
            `,
        [kuantitas, product_id],
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
    res
      .status(500)
      .json({ success: false, message: "Gagal memproses transaksi PO" });
  } finally {
    client.release();
  }
});

// ==========================================
// 4. RIWAYAT PESANAN (DAFTAR PO PERUSAHAAN)
// Fungsi: Menampilkan riwayat PO dari satu perusahaan beserta nama staf pembuatnya [cite: 412, 413, 416, 417, 418, 419, 420]
// ==========================================
app.get("/api/companies/:company_id/orders", async (req, res) => {
  try {
    const { company_id } = req.params;
    const query = `
            SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
                   po.tanggal_dipesan, u.nama_lengkap AS pembuat
            FROM PurchaseOrders po
            JOIN Users u ON po.dibuat_oleh = u.user_id
            WHERE po.company_id = $1
            ORDER BY po.tanggal_dipesan DESC;
        `;
    const { rows } = await pool.query(query, [company_id]);
    res.json({ success: true, data: rows });
  } catch (error) {
    res
      .status(500)
      .json({ success: false, message: "Gagal mengambil riwayat PO" });
  }
});

// ==========================================
// 5. DETAIL PESANAN (ISI PO)
// Fungsi: Menampilkan detail barang yang ada di dalam sebuah pesanan [cite: 423, 424, 427, 428, 429, 430]
// ==========================================
app.get("/api/orders/:po_id", async (req, res) => {
  try {
    const { po_id } = req.params;
    const query = `
            SELECT p.sku, p.nama_produk, p.satuan, od.kuantitas, od.harga_final,
                   (od.kuantitas * od.harga_final) AS subtotal
            FROM OrderDetails od
            JOIN Products p ON od.product_id = p.product_id
            WHERE od.po_id = $1;
        `;
    const { rows } = await pool.query(query, [po_id]);
    res.json({ success: true, data: rows });
  } catch (error) {
    res
      .status(500)
      .json({ success: false, message: "Gagal mengambil detail barang PO" });
  }
});

// ==========================================
// 6. PERSETUJUAN (APPROVAL PO & ROLLBACK STOK)
// Fungsi: Mengubah status PO. Jika ditolak, stok dikembalikan [cite: 433, 434, 437, 438, 439, 440, 441]
// ==========================================
app.patch("/api/orders/:po_id/status", async (req, res) => {
  const { po_id } = req.params;
  const { status_po } = req.body; // Menerima 'Approved' atau 'Rejected'

  const client = await pool.connect();
  try {
    await client.query("BEGIN"); // Mulai transaksi pengamanan data

    // Update status PO
    const updateQuery = `
            UPDATE PurchaseOrders
            SET status_po = $1
            WHERE po_id = $2
            RETURNING po_id, status_po;
        `;
    const result = await client.query(updateQuery, [status_po, po_id]);

    if (result.rows.length === 0) {
      throw new Error("PO tidak ditemukan");
    }

    // Logika objektif: Jika PO ditolak (Rejected), kembalikan stok fisik gudang [cite: 441]
    if (status_po === "Rejected") {
      const detailQuery = `SELECT product_id, kuantitas FROM OrderDetails WHERE po_id = $1`;
      const { rows: items } = await client.query(detailQuery, [po_id]);

      for (let item of items) {
        await client.query(
          `
                    UPDATE Products
                    SET stok_gudang = stok_gudang + $1
                    WHERE product_id = $2
                `,
          [item.kuantitas, item.product_id],
        );
      }
    }

    await client.query("COMMIT");
    res.json({
      success: true,
      message: `PO berhasil diperbarui menjadi ${status_po}`,
      data: result.rows[0],
    });
  } catch (error) {
    await client.query("ROLLBACK");
    console.error("Approval Error:", error);
    res
      .status(500)
      .json({ success: false, message: "Gagal memproses persetujuan PO" });
  } finally {
    client.release();
  }
});

const PORT = 5000;
app.listen(PORT, () =>
  console.log(
    `🚀 Backend Horeca B2B berjalan penuh di http://localhost:${PORT}`,
  ),
);

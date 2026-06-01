const { normalizeCompanyName, validateEmail } = require("./domain");

function registerCustomerRoutes(app, { pool, sendError }) {
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
      if (!kategori_industri) {
        return res.status(400).json({ success: false, message: "Nama perusahaan dan industri wajib diisi" });
      }

      let companyName;
      try {
        companyName = normalizeCompanyName(nama_perusahaan);
      } catch (error) {
        return res.status(400).json({ success: false, message: error.message });
      }

      const { rows } = await pool.query(
        `
          INSERT INTO companies (nama_perusahaan, npwp, kategori_industri, limit_kredit)
          VALUES ($1, $2, $3, $4)
          RETURNING company_id, nama_perusahaan, npwp, kategori_industri, limit_kredit, created_at
        `,
        [companyName, npwp || null, kategori_industri, limit_kredit || 0],
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

      let normalizedEmail;
      try {
        normalizedEmail = validateEmail(email);
      } catch (error) {
        return res.status(400).json({ success: false, message: error.message });
      }

      const { rows } = await pool.query(
        `
          INSERT INTO users (company_id, nama_lengkap, email, peran)
          VALUES ($1, $2, $3, $4)
          RETURNING user_id, company_id, nama_lengkap, email, peran
        `,
        [company_id, nama_lengkap, normalizedEmail, peran],
      );
      res.status(201).json({ success: true, data: rows[0] });
    } catch (error) {
      sendError(res, error, "Gagal menambah pengguna");
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
}

module.exports = {
  registerCustomerRoutes,
};

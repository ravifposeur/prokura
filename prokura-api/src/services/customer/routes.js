const { normalizeCompanyName, validateEmail } = require("./domain");
const {
  createCompany,
  createUser,
  getCompanyCredit,
  listCompanies,
  listUsers,
} = require("./repository");

function registerCustomerRoutes(app, { pool, sendError }) {
  app.get("/api/companies", async (_req, res) => {
    try {
      const companies = await listCompanies(pool);
      res.json({ success: true, data: companies });
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

      const company = await createCompany(pool, {
        nama_perusahaan: companyName,
        npwp,
        kategori_industri,
        limit_kredit,
      });
      res.status(201).json({ success: true, data: company });
    } catch (error) {
      sendError(res, error, "Gagal menambah perusahaan");
    }
  });

  app.get("/api/users", async (req, res) => {
    try {
      const users = await listUsers(pool, req.query.company_id);
      res.json({ success: true, data: users });
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

      const user = await createUser(pool, {
        company_id,
        nama_lengkap,
        email: normalizedEmail,
        peran,
      });
      res.status(201).json({ success: true, data: user });
    } catch (error) {
      sendError(res, error, "Gagal menambah pengguna");
    }
  });

  app.get("/api/companies/:company_id/credit", async (req, res) => {
    try {
      const { company_id } = req.params;
      const credit = await getCompanyCredit(pool, company_id);

      if (!credit) {
        return res
          .status(404)
          .json({ success: false, message: "Perusahaan tidak ditemukan" });
      }

      res.json({ success: true, data: credit });
    } catch (error) {
      sendError(res, error, "Gagal mengambil data kredit");
    }
  });
}

module.exports = {
  registerCustomerRoutes,
};

async function listCompanies(pool) {
  const { rows } = await pool.query(`
    SELECT company_id, nama_perusahaan, npwp, kategori_industri, limit_kredit, created_at
    FROM companies
    ORDER BY nama_perusahaan ASC
  `);
  return rows;
}

async function createCompany(pool, company) {
  const { rows } = await pool.query(
    `
      INSERT INTO companies (nama_perusahaan, npwp, kategori_industri, limit_kredit)
      VALUES ($1, $2, $3, $4)
      RETURNING company_id, nama_perusahaan, npwp, kategori_industri, limit_kredit, created_at
    `,
    [
      company.nama_perusahaan,
      company.npwp || null,
      company.kategori_industri,
      company.limit_kredit || 0,
    ],
  );
  return rows[0];
}

async function listUsers(pool, companyId) {
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
  return rows;
}

async function createUser(pool, user) {
  const { rows } = await pool.query(
    `
      INSERT INTO users (company_id, nama_lengkap, email, peran)
      VALUES ($1, $2, $3, $4)
      RETURNING user_id, company_id, nama_lengkap, email, peran
    `,
    [user.company_id, user.nama_lengkap, user.email, user.peran],
  );
  return rows[0];
}

async function getCompanyCredit(pool, companyId) {
  const { rows } = await pool.query(
    `
      SELECT company_id, nama_perusahaan, limit_kredit
      FROM companies
      WHERE company_id = $1
    `,
    [companyId],
  );
  return rows[0] || null;
}

module.exports = {
  createCompany,
  createUser,
  getCompanyCredit,
  listCompanies,
  listUsers,
};

# Gilbert Nathaniel

NIM: 24/533877/PA/22623

## Peran

Owner Customer Service. Gilbert bertanggung jawab pada data perusahaan B2B, limit kredit, dan user perusahaan.

## Bukti Microservice

Customer Service berada di `prokura-api/src/services/customer` dan dipasang sebagai service tersendiri melalui `registerCustomerRoutes`.

Lokasi kode: `prokura-api/src/service-host.js`

```js
const serviceRegistry = {
  catalog: registerCatalogRoutes,
  customer: registerCustomerRoutes,
  inventory: registerInventoryRoutes,
  order: registerOrderRoutes,
  reporting: registerReportingRoutes,
};
```

Penjelasan: entry `customer: registerCustomerRoutes` membuktikan Customer Service punya boundary sendiri dan dapat dijalankan sebagai proses service di port `5103`.

## Tanggung Jawab Fitur

1. Manajemen customer/perusahaan.
2. Manajemen user perusahaan.

## Lokasi Kode Program dan Penjelasan

### Route perusahaan

Lokasi kode: `prokura-api/src/services/customer/routes.js`

- `GET /api/companies`: line 11.
- `POST /api/companies`: line 20.

```js
app.get("/api/companies", async (_req, res) => {
  try {
    const companies = await listCompanies(pool);
    res.json({ success: true, data: companies });
  } catch (error) {
    sendError(res, error, "Gagal mengambil data perusahaan");
  }
});
```

Penjelasan: endpoint ini mengembalikan daftar perusahaan untuk UI admin. Data berasal dari repository, bukan dari query langsung di UI.

```js
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
```

Penjelasan: endpoint tambah perusahaan memvalidasi industri dan menormalisasi nama perusahaan. Validasi ini menjaga data master customer tetap rapi.

### Route user perusahaan

Lokasi kode: `prokura-api/src/services/customer/routes.js`

- `GET /api/users`: line 46.
- `POST /api/users`: line 55.

```js
app.get("/api/users", async (req, res) => {
  try {
    const users = await listUsers(pool, req.query.company_id);
    res.json({ success: true, data: users });
  } catch (error) {
    sendError(res, error, "Gagal mengambil pengguna");
  }
});
```

Penjelasan: endpoint ini bisa mengambil semua user atau user berdasarkan `company_id`. Fitur ini dipakai pada tab manajemen pengguna.

```js
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
```

Penjelasan: endpoint tambah user memastikan company, nama, email, dan peran terisi. Email divalidasi sebelum disimpan.

### SQL repository customer

Lokasi kode: `prokura-api/src/services/customer/repository.js`

- Insert company: line 13.
- Insert user: line 52.

```js
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
```

Penjelasan: query ini menyimpan perusahaan baru dan mengembalikan data lengkap termasuk `company_id` dan `created_at` untuk ditampilkan di UI.

```js
const { rows } = await pool.query(
  `
    INSERT INTO users (company_id, nama_lengkap, email, peran)
    VALUES ($1, $2, $3, $4)
    RETURNING user_id, company_id, nama_lengkap, email, peran
  `,
  [user.company_id, user.nama_lengkap, user.email, user.peran],
);
```

Penjelasan: query ini membuat user yang terhubung ke perusahaan melalui `company_id`. Return value dipakai sebagai bukti user berhasil dibuat.

### UI admin customer

Lokasi kode: `prokura-admin/app3.py`

- Menu `Manajemen Klien B2B`: line 683.
- Tabs daftar/tambah/user: line 685.
- API create company dipanggil sekitar line 732.
- API create user dipanggil sekitar line 769.

Penjelasan: admin menambah perusahaan dan user lewat form Streamlit yang memanggil endpoint Customer Service.

## SQL Query Demo dan Penjelasan

### Query 1: tambah perusahaan

```sql
INSERT INTO companies (nama_perusahaan, npwp, kategori_industri, limit_kredit)
VALUES ('PT Demo Customer', '12.345.678.9-000.111', 'Hotel', 10000000)
RETURNING company_id, nama_perusahaan, npwp, kategori_industri, limit_kredit, created_at;
```

Penjelasan: query ini membuat perusahaan B2B baru dengan limit kredit. `RETURNING` membuktikan perusahaan tersimpan dan menghasilkan `company_id`.

### Query 2: tambah user perusahaan

```sql
INSERT INTO users (company_id, nama_lengkap, email, peran)
VALUES (1, 'User Demo', 'user.demo@prokura.test', 'Procurement')
RETURNING user_id, company_id, nama_lengkap, email, peran;
```

Penjelasan: query ini menambahkan user untuk perusahaan tertentu. `company_id` menjadi foreign key yang menghubungkan user dengan customer B2B.

### Query 3: lihat user per perusahaan

```sql
SELECT u.user_id, u.company_id, c.nama_perusahaan AS company,
       u.nama_lengkap, u.email, u.peran
FROM users u
JOIN companies c ON u.company_id = c.company_id
WHERE u.company_id = 1
ORDER BY c.nama_perusahaan ASC, u.nama_lengkap ASC;
```

Penjelasan: query ini menampilkan user beserta nama perusahaan. Join membantu membuktikan user yang dibuat benar-benar terhubung ke perusahaan yang dipilih.

## Alur Demo

### A. Manajemen customer/perusahaan

1. Buka admin `Manajemen Klien B2B`.
2. Tampilkan daftar perusahaan sebelum penambahan.
3. Masuk tab `Tambah Klien Baru`.
4. Isi nama perusahaan, NPWP, industri, dan limit kredit.
5. Submit form.
6. Tunjukkan row perusahaan baru di UI dan database.

### B. Manajemen user perusahaan

1. Masuk tab `Manajemen Pengguna`.
2. Pilih perusahaan yang baru dibuat.
3. Isi nama user, email, dan peran.
4. Submit form.
5. Tunjukkan user muncul pada tabel perusahaan.
6. Jalankan SQL join user-company untuk membuktikan relasi database.

## Bukti Validasi

- Unit test Customer: `prokura-api/tests/unit/customer-domain.test.js`.
- Repository test Customer: `prokura-api/tests/unit/repository.test.js`.
- Integration test membuat company dan user.
- Smoke test final project membuat company dan user demo.

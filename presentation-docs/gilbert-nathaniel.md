# Gilbert Nathaniel

NIM: 24/533877/PA/22623

## Peran

Owner Customer Service. Fokus pada data perusahaan B2B, limit kredit, dan user perusahaan.

## Tanggung Jawab Fitur

1. Manajemen customer/perusahaan.
2. Manajemen user perusahaan.

## Lokasi Kode Program

- Route customer: `prokura-api/src/services/customer/routes.js`
  - `GET /api/companies`: line 11.
  - `POST /api/companies`: line 20.
  - `GET /api/users`: line 46.
  - `POST /api/users`: line 55.
  - `GET /api/companies/:company_id/credit`: line 81.
- SQL repository customer: `prokura-api/src/services/customer/repository.js`
  - Insert company: line 13.
  - Insert user: line 52.
- Domain validation: `prokura-api/src/services/customer/domain.js`.
- UI admin: `prokura-admin/app3.py`
  - Menu `Manajemen Klien B2B`: line 683.
  - Tabs daftar/tambah/user: line 685.
  - API create company dipanggil sekitar line 732.
  - API create user dipanggil sekitar line 769.

## SQL Query Demo

Tambah perusahaan:

```sql
INSERT INTO companies (nama_perusahaan, npwp, kategori_industri, limit_kredit)
VALUES ('PT Demo Customer', '12.345.678.9-000.111', 'Hotel', 10000000)
RETURNING company_id, nama_perusahaan, npwp, kategori_industri, limit_kredit, created_at;
```

Tambah user perusahaan:

```sql
INSERT INTO users (company_id, nama_lengkap, email, peran)
VALUES (1, 'User Demo', 'user.demo@prokura.test', 'Procurement')
RETURNING user_id, company_id, nama_lengkap, email, peran;
```

Daftar user per perusahaan:

```sql
SELECT u.user_id, u.company_id, c.nama_perusahaan AS company,
       u.nama_lengkap, u.email, u.peran
FROM users u
JOIN companies c ON u.company_id = c.company_id
WHERE u.company_id = 1
ORDER BY c.nama_perusahaan ASC, u.nama_lengkap ASC;
```

## Penjelasan Sistem

Customer Service menjadi sumber data perusahaan dan user B2B. Admin membuat perusahaan terlebih dahulu, lalu membuat user yang terhubung ke `company_id`. UI customer juga memakai endpoint credit untuk membaca limit kredit perusahaan saat checkout.

## Alur Demo

1. Buka admin, menu `Manajemen Klien B2B`.
2. Tampilkan daftar perusahaan sebelum penambahan.
3. Buka tab `Tambah Klien Baru`, isi nama perusahaan, NPWP, industri, dan limit kredit.
4. Submit dan tunjukkan company baru muncul.
5. Buka tab `Manajemen Pengguna`, pilih perusahaan baru.
6. Tambahkan user perusahaan dan tampilkan user pada tabel.
7. Tunjukkan database akhir di tabel `companies` dan `users`.

## Bukti Validasi

- Unit test Customer: `prokura-api/tests/unit/customer-domain.test.js`.
- Repository test Customer: `prokura-api/tests/unit/repository.test.js`.
- Integration test membuat company dan user.
- Smoke test final project membuat company dan user demo.

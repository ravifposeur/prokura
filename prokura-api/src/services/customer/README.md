# Customer Service

Tanggung jawab:

- Mengelola data perusahaan customer.
- Mengelola user procurement milik perusahaan.
- Menyediakan data kredit customer.

Endpoint saat ini masih diregistrasikan di `server.js`:

- `GET /api/companies`
- `POST /api/companies`
- `GET /api/users`
- `POST /api/users`
- `GET /api/companies/:company_id/credit`

Target refactor: pindahkan route dan query customer ke `routes.js` dan `repository.js` di folder ini.

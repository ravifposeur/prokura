# Reporting Service

Tanggung jawab:

- Rekapitulasi penjualan.
- Ringkasan dashboard admin.
- Agregasi produk terlaris, client terbesar, segmentasi industri, dan tren bulanan.

Endpoint saat ini masih diregistrasikan di `server.js`:

- `GET /api/reports/sales`
- `GET /api/admin/summary`

Target refactor: pindahkan query agregasi ke `repository.js` dan format response laporan ke service module ini.

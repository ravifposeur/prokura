# Kelompok Prokura

Sistem final project: Prokura, e-commerce B2B untuk rantai pasok HoReCa.

1. Ravif Gayuh Wicaksono (24/540583/PA/22953)
- Sebagai owner Catalog Service.
- Implementasi fitur penambahan barang baru.
- Implementasi fitur pencarian dan filter barang.

2. Aloysius Pijar Hutama Indrianto (24/534591/PA/22675)
- Sebagai owner Inventory Service.
- Implementasi fitur penambahan stok barang.
- Implementasi fitur riwayat pergerakan stok.

3. Indratanaya Budiman (24/534784/PA/22683)
- Sebagai owner Order Service.
- Implementasi fitur pembelian barang oleh customer.
- Implementasi fitur riwayat pembelian customer.

4. Gilbert Nathaniel (24/533877/PA/22623)
- Sebagai owner Customer Service.
- Implementasi fitur manajemen customer/perusahaan.
- Implementasi fitur manajemen user perusahaan.

5. Pison Golda Mountera (24/543770/PA/23107)
- Sebagai owner Reporting Service.
- Implementasi fitur rekapitulasi penjualan.
- Implementasi fitur analitik top produk dan top customer.

## Catatan Demo Kelompok

- UI admin: `prokura-admin/app3.py`.
- UI customer: `prokura-web/app/page.tsx`.
- API gateway: `prokura-api/server.js`.
- Service boundary: `prokura-api/src/services/*`.
- Database: PostgreSQL via Docker Compose.
- Bukti validasi utama: `npm test`, `npm run build`, dan `scripts/final_project_smoke.ps1`.

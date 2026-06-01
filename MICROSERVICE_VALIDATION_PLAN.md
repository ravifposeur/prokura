# Rencana Validasi Microservice dan Testing - Prokura

Dokumen ini menjadi rencana kerja sekaligus progress checklist untuk memastikan Prokura memenuhi arahan final project:

- Integrasi antar sistem/perusahaan menggunakan microservice.
- Setiap sistem punya UI/UX.
- Setiap anggota memiliki dua fitur.
- Demo menampilkan SQL query, kode program, dan perubahan database.
- Ada validasi unit test dan integration test.

## Audit Kondisi Saat Ini

Status saat dokumen dibuat:

- UI admin dan customer web sudah tidak query database langsung.
- Semua UI membaca/menulis data melalui `prokura-api`.
- PostgreSQL berjalan via Docker.
- Fitur per anggota sudah tersedia secara fungsional.
- API masih berada dalam satu proses Express besar di `prokura-api/server.js`.

Kesimpulan audit:

- Sistem sudah memakai API boundary, tetapi belum microservice sempurna secara struktur source code dan deployability.
- Agar lebih defensible saat presentasi, API perlu dipisah menjadi service boundary yang jelas: Catalog, Inventory, Customer, Order, Reporting.
- Tahap awal dapat tetap satu proses Express untuk demo lokal, tetapi struktur folder, route module, domain logic, dan test harus menunjukkan service boundary yang tegas.
- Tahap akhir ideal adalah setiap service dapat dijalankan sebagai proses/container terpisah atau minimal route module terpisah dengan kontrak API jelas.

## Target Struktur Microservice

Target bertahap:

```text
prokura-api/
  server.js
  src/
    shared/
      db.js
      http.js
    services/
      catalog/
        routes.js
        repository.js
        domain.js
        README.md
      inventory/
        routes.js
        repository.js
        domain.js
        README.md
      customer/
        routes.js
        repository.js
        domain.js
        README.md
      order/
        routes.js
        repository.js
        domain.js
        README.md
      reporting/
        routes.js
        repository.js
        domain.js
        README.md
    tests/
      unit/
      integration/
```

Catatan:

- `server.js` boleh menjadi API gateway/host Express.
- Setiap folder service harus punya tanggung jawab jelas.
- Integrasi antar UI dan backend tetap melalui HTTP API.
- Akses database tetap melalui repository/service layer, bukan dari UI.

## Daftar Service dan Kontrak

| Service | Endpoint | Status Saat Ini | Target |
| --- | --- | --- | --- |
| Catalog Service | `GET /api/products`, `POST /api/products`, `PATCH /api/products/:id`, `DELETE /api/products/:id` | Ada di `server.js` | Pindah ke `src/services/catalog` |
| Inventory Service | `PATCH /api/products/:id/stock`, `GET /api/inventory/movements` | Ada di `server.js` | Pindah ke `src/services/inventory` |
| Customer Service | `GET /api/companies`, `POST /api/companies`, `GET /api/users`, `POST /api/users` | Ada di `server.js` | Pindah ke `src/services/customer` |
| Order Service | `POST /api/orders`, `GET /api/orders`, `GET /api/orders/:id`, `PATCH /api/orders/:id/status` | Ada di `server.js` | Pindah ke `src/services/order` |
| Reporting Service | `GET /api/reports/sales`, `GET /api/admin/summary` | Ada di `server.js` | Pindah ke `src/services/reporting` |

## Rencana Unit Test

Unit test harus menguji logic yang tidak perlu database.

Checklist:

- [x] Membuat npm script `test`, `test:unit`, dan `test:integration`.
- [x] Membuat folder test awal.
- [x] Unit test Inventory Service untuk validasi jumlah stok masuk.
- [x] Unit test Catalog Service untuk normalisasi SKU dan filter search.
- [x] Unit test Customer Service untuk validasi email/user.
- [x] Unit test Order Service untuk validasi payload checkout dan kalkulasi total.
- [x] Unit test Reporting Service untuk helper agregasi/format data.

## Rencana Integration Test

Integration test menguji API + PostgreSQL Docker secara end-to-end.

Checklist:

- [x] Integration test membuat produk baru dan mencarinya.
- [x] Integration test menambah stok dan mengecek movement.
- [x] Integration test membuat company dan user.
- [x] Integration test membuat order dan mengecek riwayat customer.
- [x] Integration test mengecek reporting sales.
- [ ] Integration test approval/reject order dan return stock.
- [ ] Integration test delete product yang sudah dipakai PO harus gagal.
- [ ] Integration test admin summary setelah transaksi.

## Rencana UI/UX Validation

Checklist:

- [x] Admin Streamlit smoke test via `streamlit.testing`.
- [x] Next.js customer web build test.
- [ ] Playwright/browser screenshot admin Dashboard.
- [ ] Playwright/browser screenshot admin Inventory Service.
- [ ] Playwright/browser screenshot customer checkout.
- [ ] Visual checklist manual jika browser automation tetap gagal di sandbox.

## Rencana Refactor Source ke Service Boundary

Tahap 1 - Fondasi:

- [x] Membuat dokumen rencana ini.
- [x] Menambahkan folder awal `src/services/inventory`.
- [x] Memindahkan sebagian domain logic Inventory ke service module.
- [x] Menambahkan folder awal `src/services/catalog`.
- [x] Menambahkan folder awal `src/services/customer`.
- [x] Menambahkan folder awal `src/services/order`.
- [x] Menambahkan folder awal `src/services/reporting`.
- [x] Menambahkan folder awal `src/shared`.
- [x] Memindahkan sebagian domain logic Catalog, Customer, Order, dan Reporting ke service module.
- [x] Menambahkan unit test Inventory.
- [x] Menambahkan unit test Catalog, Customer, Order, dan Reporting.
- [x] Menambahkan integration test API lintas service.

Tahap 2 - Modularisasi API:

- [ ] Pindahkan route Catalog ke `src/services/catalog/routes.js`.
- [ ] Pindahkan route Inventory ke `src/services/inventory/routes.js`.
- [ ] Pindahkan route Customer ke `src/services/customer/routes.js`.
- [ ] Pindahkan route Order ke `src/services/order/routes.js`.
- [ ] Pindahkan route Reporting ke `src/services/reporting/routes.js`.
- [ ] `server.js` hanya memasang middleware dan register routes.

Tahap 3 - Deployability:

- [ ] Tambah `docker-compose.microservices.yml`.
- [ ] Pisahkan process service bila waktu cukup.
- [ ] Tambah health endpoint per service.
- [ ] Tambah dokumentasi port internal setiap service.

## Cara Menjalankan Test

Unit test:

```bash
cd prokura-api
npm run test:unit
```

Integration test, dengan API dan PostgreSQL sudah hidup:

```bash
cd prokura-api
npm run test:integration
```

Smoke test final project:

```powershell
.\scripts\final_project_smoke.ps1
```

## Progress Log

### 2026-06-02

- [x] Audit awal: sistem belum sepenuhnya microservice deployable, tetapi sudah API-based.
- [x] Dokumen rencana microservice dan testing dibuat.
- [x] Fondasi test API ditambahkan.
- [x] Inventory domain module awal dibuat.
- [x] Unit test Inventory dijalankan.
- [x] Integration test lintas service dijalankan.
- [x] `package.json` API diperbarui dengan script `test`, `test:unit`, dan `test:integration`.
- [x] Domain module awal dibuat untuk Catalog, Customer, Order, dan Reporting.
- [x] `server.js` mulai memakai domain module untuk validasi SKU, email, stok, payload order, dan rentang tanggal laporan.
- [x] API lokal direstart agar memakai kode terbaru.
- [x] `node --check server.js` lolos.
- [x] `npm run test:unit` lolos dengan 15 test.
- [x] `npm run test:integration` lolos dengan 1 test end-to-end API + PostgreSQL.
- [x] `npm test` lolos dengan total 16 test.
- [x] `scripts/final_project_smoke.ps1` lolos untuk Catalog, Inventory, Customer, Order, Reporting, dan final database state.

Catatan sisa:

- Route dan repository belum dipisah penuh dari `server.js`; sistem sudah memiliki service domain boundary, tetapi belum microservice deployable 1 proses/container per service.
- Integration test tambahan untuk reject order/return stock, proteksi delete product, dan admin summary masih perlu dikerjakan pada tahap berikutnya.

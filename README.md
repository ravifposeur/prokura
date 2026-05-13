# Prokura B2B — Core Infrastructure

Prokura adalah sistem *e-commerce* dan manajemen rantai pasok B2B berskala *enterprise*. Sistem ini dirancang secara otonom menggunakan arsitektur *decoupled* (pemisahan Frontend dan Backend) yang berjalan sepenuhnya di infrastruktur lokal. Pendekatan ini memastikan kedaulatan data mutlak tanpa ketergantungan pada layanan *cloud* komersial.

## 🛠 Prasyarat Sistem

Pastikan mesin lokal Anda telah terinstal:

1. **Node.js** (v18.x atau lebih baru)
2. **PostgreSQL** (v14 atau lebih baru)
3. **Git**

---

## 📦 Tahap 1: Inisialisasi Basis Data Lokal

Aplikasi ini tidak menggunakan *cloud database*. Anda harus membangun basis data secara lokal.

**1.** Buka antarmuka PostgreSQL Anda (melalui `psql` di Terminal/CMD atau pgAdmin).

**2.** Buat basis data dan *user* baru:

```sql
CREATE USER prokura WITH PASSWORD 'prokura';
CREATE DATABASE "prokuradb" OWNER prokura;
```

**3.** Keluar dari terminal SQL, lalu impor skema dan data *mockup* melalui terminal OS Anda (arahkan terminal ke folder tempat file `.sql` berada):

```bash
psql -h localhost -U postgres -d prokuraDB -f 2.horeca_sql.sql
psql -h localhost -U postgres -d prokuraDB -f 3.horeca_product_images.sql
```

> **Catatan untuk pengguna Linux:** Jika mengalami error autentikasi *peer*, gunakan perintah:
> ```bash
> sudo -u postgres psql -d prokuraDB -f <nama_file.sql>
> ```

**4.** Berikan hak akses baca/tulis kepada *user* aplikasi dan perbaiki sinkronisasi urutan tabel:

```bash
psql -h localhost -U postgres -d prokuraDB -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prokura;"
psql -h localhost -U postgres -d prokuraDB -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prokura;"
psql -h localhost -U postgres -d prokuraDB -c "UPDATE products SET stok_gudang = 1000;"
psql -h localhost -U postgres -d prokuraDB -c "SELECT setval('purchaseorders_po_id_seq', (SELECT MAX(po_id) FROM purchaseorders)); SELECT setval('orderdetails_detail_id_seq', (SELECT MAX(detail_id) FROM orderdetails));"
```

---

## ⚙️ Tahap 2: Menjalankan Backend API

Backend bertugas sebagai jembatan logika transaksi (menggunakan Node.js + Express).

**1.** Buka terminal baru dan masuk ke direktori backend:

```bash
cd prokura-backend
```

**2.** Instal semua dependensi:

```bash
npm install
```

**3.** Jalankan server lokal:

```bash
node server.js
```

Backend akan berjalan di `http://localhost:5000`. Terminal harus menampilkan pesan `✅ Terkoneksi ke PostgreSQL Lokal`.

---

## 🖥️ Tahap 3: Menjalankan Frontend (Unified Dashboard)

Frontend dibangun menggunakan Next.js dan Tailwind CSS, merangkum fungsi Pengadaan (Chef), Keuangan (Finance), dan Gudang (Procurement) dalam satu antarmuka.

**1.** Buka terminal baru (biarkan terminal backend tetap berjalan) dan masuk ke direktori frontend:

```bash
cd prokura-frontend
```

**2.** Instal dependensi UI:

```bash
npm install
```

**3.** **PENTING — Manajemen Aset Fisik:** Sistem ini menggunakan penyimpanan gambar lokal. Buat hierarki folder berikut di dalam proyek frontend Anda:

```
public/images/products/
```

Letakkan file gambar `.jpg` ke dalam folder tersebut dengan nama yang sama persis dengan SKU di katalog (contoh: `SKU-IRY-4278_1.jpg`).

**4.** Jalankan aplikasi web:

```bash
npm run dev
```

---

## 🚀 Akses Sistem

Buka peramban Anda dan akses: **http://localhost:3000**

Gunakan **Role Switcher** di bagian atas dashboard untuk mensimulasikan alur rantai pasok secara penuh:

- **Terminal Pengadaan (Chef):** Memasukkan barang ke keranjang dan mengajukan PO.
- **Otoritas Anggaran (Finance):** Menginspeksi riwayat PO dan melakukan validasi (Tolak/Sahkan).
- **Gudang & Logistik (Procurement):** Memantau ketersediaan stok gudang dan mencetak manifest pengiriman untuk PO yang telah disahkan.

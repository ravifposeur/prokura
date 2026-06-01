use wise;
show TABLES;
-- 1. Tabel Klien B2B (Perusahaan)
CREATE TABLE Companies (
    company_id SERIAL PRIMARY KEY,
    nama_perusahaan VARCHAR(150) NOT NULL,
    npwp VARCHAR(50) UNIQUE,
    kategori_industri VARCHAR(50) CHECK (kategori_industri IN ('Hotel', 'Restaurant', 'Cafe', 'Catering')),
    limit_kredit DECIMAL(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Pengguna (Staff dari Perusahaan)
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    company_id INT REFERENCES Companies(company_id) ON DELETE CASCADE,
    nama_lengkap VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    peran VARCHAR(50) CHECK (peran IN ('Chef', 'Procurement', 'Finance_Manager'))
);

-- 3. Tabel Katalog Produk Grosir
CREATE TABLE Products (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    nama_produk VARCHAR(150) NOT NULL,
    kategori VARCHAR(50),
    satuan VARCHAR(20) NOT NULL,
    harga_dasar DECIMAL(12, 2) NOT NULL,
    stok_gudang INT DEFAULT 0
);

-- 4. Tabel Pesanan (Purchase Order / PO)
CREATE TABLE PurchaseOrders (
    po_id SERIAL PRIMARY KEY,
    company_id INT REFERENCES Companies(company_id),
    dibuat_oleh INT REFERENCES Users(user_id),
    status_po VARCHAR(50) DEFAULT 'Pending_Approval',
    metode_pembayaran VARCHAR(50) CHECK (metode_pembayaran IN ('Cash', 'Tempo_30_Hari')),
    total_tagihan DECIMAL(15, 2) NOT NULL,
    tanggal_dipesan TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabel Detail Item Pesanan
CREATE TABLE OrderDetails (
    detail_id SERIAL PRIMARY KEY,
    po_id INT REFERENCES PurchaseOrders(po_id) ON DELETE CASCADE,
    product_id INT REFERENCES Products(product_id),
    kuantitas INT NOT NULL,
    harga_final DECIMAL(12, 2) NOT NULL 
);

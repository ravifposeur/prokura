DROP TABLE IF EXISTS orderdetails;
DROP TABLE IF EXISTS purchaseorders;
DROP TABLE IF EXISTS inventory_movements;
DROP TABLE IF EXISTS productimages;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    nama_perusahaan VARCHAR(150) NOT NULL,
    npwp VARCHAR(50) UNIQUE,
    kategori_industri VARCHAR(50) NOT NULL,
    limit_kredit DECIMAL(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(company_id) ON DELETE CASCADE,
    nama_lengkap VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    peran VARCHAR(50) NOT NULL
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    nama_produk VARCHAR(150) NOT NULL,
    kategori VARCHAR(50),
    satuan VARCHAR(20) NOT NULL,
    harga_dasar DECIMAL(12, 2) NOT NULL,
    stok_gudang INT DEFAULT 0
);

CREATE TABLE productimages (
    image_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id) ON DELETE CASCADE,
    image_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE
);

CREATE TABLE inventory_movements (
    movement_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    movement_type VARCHAR(30) NOT NULL,
    quantity INT NOT NULL,
    note TEXT,
    reference_type VARCHAR(30),
    reference_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE purchaseorders (
    po_id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(company_id),
    dibuat_oleh INT REFERENCES users(user_id),
    status_po VARCHAR(50) DEFAULT 'Pending_Approval',
    metode_pembayaran VARCHAR(50) NOT NULL,
    total_tagihan DECIMAL(15, 2) NOT NULL,
    tanggal_dipesan TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orderdetails (
    detail_id SERIAL PRIMARY KEY,
    po_id INT REFERENCES purchaseorders(po_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id),
    kuantitas INT NOT NULL,
    harga_final DECIMAL(12, 2) NOT NULL
);

INSERT INTO companies (company_id, nama_perusahaan, npwp, kategori_industri, limit_kredit, created_at) VALUES
(1, 'Browsetype Hotel Group', '51.581.975.2-795.786', 'Hotel', 33355694.75, '2026-02-25 06:13:59'),
(2, 'Skimia Cafe', '50.688.900.9-894.883', 'Cafe', 27525961.26, '2026-02-25 06:13:59'),
(3, 'Eire Restaurant', '59.310.726.2-086.800', 'Restaurant', 28494593.77, '2026-02-25 06:13:59');

INSERT INTO users (user_id, company_id, nama_lengkap, email, peran) VALUES
(1, 1, 'Sheri Weldrick', 'sweldricka@goodreads.com', 'Chef'),
(2, 1, 'Rudiger Pixton', 'rpixtond@topsy.com', 'Finance_Manager'),
(3, 1, 'Gerrard Gogarty', 'ggogarty7@cornell.edu', 'Procurement'),
(4, 2, 'Ulrica Beeson', 'ubeesong@tumblr.com', 'Procurement'),
(5, 3, 'Wilie Bruhn', 'wbruhnb@ameblo.jp', 'Chef');

INSERT INTO products (product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang) VALUES
(1, 'SKU-IRY-4278', 'Snack Container Set', 'Kemasan', 'box', 102345.08, 120),
(5, 'SKU-JYZ-6187', 'Beef Taco Skillet', 'Daging', 'kg', 125150.53, 1000),
(6, 'SKU-IDT-5014', 'Chocolate Raspberry Tart', 'Bakery', 'box', 62646.05, 1000),
(13, 'SKU-MSF-9427', 'Children''s Educational Workbook', 'Sayuran', 'box', 138834.64, 1000),
(16, 'SKU-FXN-7383', 'Blueberry Muffin Mix', 'Minuman', 'pcs', 40700.88, 1000);

INSERT INTO productimages (product_id, image_url, is_primary) VALUES
(5, '/images/products/SKU-JYZ-6187_1.jpg', true),
(6, '/images/products/SKU-IDT-5014_1.jpg', true),
(13, '/images/products/SKU-MSF-9427_1.jpg', true),
(16, '/images/products/SKU-FXN-7383_1.jpg', true);

INSERT INTO inventory_movements (product_id, movement_type, quantity, note, reference_type, reference_id) VALUES
(1, 'INITIAL_STOCK', 120, 'Stok awal seed database', 'PRODUCT', 1),
(5, 'INITIAL_STOCK', 1000, 'Stok awal seed database', 'PRODUCT', 5),
(6, 'INITIAL_STOCK', 1000, 'Stok awal seed database', 'PRODUCT', 6),
(13, 'INITIAL_STOCK', 1000, 'Stok awal seed database', 'PRODUCT', 13),
(16, 'INITIAL_STOCK', 1000, 'Stok awal seed database', 'PRODUCT', 16);

INSERT INTO purchaseorders (po_id, company_id, dibuat_oleh, status_po, metode_pembayaran, total_tagihan, tanggal_dipesan) VALUES
(1, 1, 1, 'Pending_Approval', 'Tempo_30_Hari', 250301.06, '2026-02-25 06:37:44'),
(2, 1, 1, 'Approved', 'Cash', 62646.05, '2026-02-25 07:37:44'),
(3, 2, 4, 'Processing', 'Tempo_30_Hari', 244141.41, '2026-02-26 09:12:00');

INSERT INTO orderdetails (detail_id, po_id, product_id, kuantitas, harga_final) VALUES
(1, 1, 5, 2, 125150.53),
(2, 2, 6, 1, 62646.05),
(3, 3, 16, 3, 40700.88),
(4, 3, 1, 1, 102345.08);

SELECT setval('companies_company_id_seq', (SELECT MAX(company_id) FROM companies));
SELECT setval('users_user_id_seq', (SELECT MAX(user_id) FROM users));
SELECT setval('products_product_id_seq', (SELECT MAX(product_id) FROM products));
SELECT setval('purchaseorders_po_id_seq', (SELECT MAX(po_id) FROM purchaseorders));
SELECT setval('orderdetails_detail_id_seq', (SELECT MAX(detail_id) FROM orderdetails));

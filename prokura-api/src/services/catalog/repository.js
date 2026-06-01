async function listProducts(pool, filters) {
  const params = [];
  const conditions = [];

  if (!filters.includeEmpty) {
    conditions.push("p.stok_gudang > 0");
  }

  if (filters.q) {
    params.push(`%${filters.q}%`);
    conditions.push(`(p.nama_produk ILIKE $${params.length} OR p.sku ILIKE $${params.length})`);
  }

  if (filters.category) {
    params.push(filters.category);
    conditions.push(`p.kategori = $${params.length}`);
  }

  const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
  const { rows } = await pool.query(
    `
      SELECT p.product_id, p.sku, p.nama_produk, p.kategori, p.satuan,
             p.harga_dasar, p.stok_gudang, i.image_url
      FROM products p
      LEFT JOIN productimages i ON p.product_id = i.product_id AND i.is_primary = TRUE
      ${where}
      ORDER BY p.nama_produk ASC
    `,
    params,
  );
  return rows;
}

async function createProduct(client, product) {
  const { rows } = await client.query(
    `
      INSERT INTO products (sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang)
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang
    `,
    [
      product.sku,
      product.nama_produk,
      product.kategori || null,
      product.satuan,
      product.harga_dasar,
      product.stok_gudang || 0,
    ],
  );
  return rows[0];
}

async function updateProduct(pool, productId, product) {
  const { rows } = await pool.query(
    `
      UPDATE products
      SET nama_produk = $1, kategori = $2, satuan = $3, harga_dasar = $4, stok_gudang = $5
      WHERE product_id = $6
      RETURNING product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang
    `,
    [
      product.nama_produk,
      product.kategori || null,
      product.satuan,
      product.harga_dasar,
      product.stok_gudang,
      productId,
    ],
  );
  return rows[0] || null;
}

async function countOrderDetailsByProduct(pool, productId) {
  const { rows } = await pool.query(
    "SELECT COUNT(*)::int AS count FROM orderdetails WHERE product_id = $1",
    [productId],
  );
  return rows[0].count;
}

async function deleteProduct(pool, productId) {
  const result = await pool.query("DELETE FROM products WHERE product_id = $1", [productId]);
  return result.rowCount;
}

module.exports = {
  countOrderDetailsByProduct,
  createProduct,
  deleteProduct,
  listProducts,
  updateProduct,
};

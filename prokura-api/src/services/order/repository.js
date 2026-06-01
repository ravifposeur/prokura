async function listOrders(pool) {
  const { rows } = await pool.query(`
    SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
           po.tanggal_dipesan, c.nama_perusahaan AS company,
           u.nama_lengkap AS pembuat
    FROM purchaseorders po
    JOIN companies c ON po.company_id = c.company_id
    JOIN users u ON po.dibuat_oleh = u.user_id
    ORDER BY po.tanggal_dipesan DESC
  `);
  return rows;
}

async function listCompanyOrders(pool, companyId) {
  const { rows } = await pool.query(
    `
      SELECT po.po_id, po.status_po, po.metode_pembayaran, po.total_tagihan,
             po.tanggal_dipesan, u.nama_lengkap AS pembuat
      FROM purchaseorders po
      JOIN users u ON po.dibuat_oleh = u.user_id
      WHERE po.company_id = $1
      ORDER BY po.tanggal_dipesan DESC
    `,
    [companyId],
  );
  return rows;
}

async function listOrderDetails(pool, poId) {
  const { rows } = await pool.query(
    `
      SELECT p.sku, p.nama_produk, p.satuan, od.kuantitas, od.harga_final,
             (od.kuantitas * od.harga_final) AS subtotal
      FROM orderdetails od
      JOIN products p ON od.product_id = p.product_id
      WHERE od.po_id = $1
      ORDER BY od.detail_id ASC
    `,
    [poId],
  );
  return rows;
}

async function lockProductStock(client, productId) {
  const { rows } = await client.query(
    "SELECT stok_gudang FROM products WHERE product_id = $1 FOR UPDATE",
    [productId],
  );
  return rows[0] || null;
}

async function createPurchaseOrder(client, order) {
  const { rows } = await client.query(
    `
      INSERT INTO purchaseorders (company_id, dibuat_oleh, metode_pembayaran, total_tagihan)
      VALUES ($1, $2, $3, $4)
      RETURNING po_id
    `,
    [order.company_id, order.dibuat_oleh, order.metode_pembayaran, order.total_tagihan],
  );
  return rows[0].po_id;
}

async function createOrderDetail(client, poId, item) {
  await client.query(
    `
      INSERT INTO orderdetails (po_id, product_id, kuantitas, harga_final)
      VALUES ($1, $2, $3, $4)
    `,
    [poId, item.product_id, item.kuantitas, item.harga_final],
  );
}

async function decrementProductStock(client, item) {
  await client.query(
    `
      UPDATE products
      SET stok_gudang = stok_gudang - $1
      WHERE product_id = $2
    `,
    [item.kuantitas, item.product_id],
  );
}

async function getOrderStatusForUpdate(client, poId) {
  const { rows } = await client.query(
    "SELECT status_po FROM purchaseorders WHERE po_id = $1 FOR UPDATE",
    [poId],
  );
  return rows[0] || null;
}

async function updateOrderStatus(client, poId, statusPo) {
  const { rows } = await client.query(
    `
      UPDATE purchaseorders
      SET status_po = $1
      WHERE po_id = $2
      RETURNING po_id, status_po
    `,
    [statusPo, poId],
  );
  return rows[0];
}

async function listOrderStockItems(client, poId) {
  const { rows } = await client.query(
    "SELECT product_id, kuantitas FROM orderdetails WHERE po_id = $1",
    [poId],
  );
  return rows;
}

async function incrementProductStock(client, item) {
  await client.query(
    "UPDATE products SET stok_gudang = stok_gudang + $1 WHERE product_id = $2",
    [item.kuantitas, item.product_id],
  );
}

module.exports = {
  createOrderDetail,
  createPurchaseOrder,
  decrementProductStock,
  getOrderStatusForUpdate,
  incrementProductStock,
  listCompanyOrders,
  listOrderDetails,
  listOrders,
  listOrderStockItems,
  lockProductStock,
  updateOrderStatus,
};

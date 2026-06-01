const assert = require("node:assert/strict");
const test = require("node:test");

const API_BASE_URL = process.env.PROKURA_API_BASE_URL || "http://127.0.0.1:5000";

async function api(method, path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json();
  assert.equal(payload.success, true, `${method} ${path} failed: ${payload.message || response.status}`);
  return payload.data;
}

async function apiFailure(method, path, body, expectedStatus) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json();
  assert.equal(response.status, expectedStatus);
  assert.equal(payload.success, false);
  return payload;
}

async function createProductCompanyUser(stamp, stock = 8) {
  const product = await api("POST", "/api/products", {
    sku: `SKU-IT-${stamp}`,
    nama_produk: `Integration Product ${stamp}`,
    kategori: "Bahan Pokok",
    satuan: "Kg",
    harga_dasar: 12000,
    stok_gudang: stock,
  });

  const company = await api("POST", "/api/companies", {
    nama_perusahaan: `PT Integration ${stamp}`,
    npwp: `IT-${stamp}`,
    kategori_industri: "Cafe",
    limit_kredit: 5000000,
  });

  const user = await api("POST", "/api/users", {
    company_id: company.company_id,
    nama_lengkap: `Integration User ${stamp}`,
    email: `integration.${stamp}@prokura.test`,
    peran: "Procurement",
  });

  return { company, product, user };
}

test("final project API flow works across services", async () => {
  const stamp = `${Date.now()}-main`;
  const { company, product, user } = await createProductCompanyUser(stamp);
  assert.equal(product.stok_gudang, 8);

  const searchResult = await api("GET", `/api/products?q=Integration%20Product%20${stamp}&include_empty=true`);
  assert.equal(searchResult.length, 1);

  const stocked = await api("PATCH", `/api/products/${product.product_id}/stock`, {
    quantity: 4,
    note: "Integration restock",
  });
  assert.equal(stocked.stok_gudang, 12);

  const order = await api("POST", "/api/orders", {
    company_id: company.company_id,
    dibuat_oleh: user.user_id,
    metode_pembayaran: "Cash",
    total_tagihan: 24000,
    items: [
      {
        product_id: product.product_id,
        kuantitas: 2,
        harga_final: 12000,
      },
    ],
  });
  assert.ok(order.po_id);

  const history = await api("GET", `/api/companies/${company.company_id}/orders`);
  assert.equal(history.length, 1);

  const movements = await api("GET", `/api/inventory/movements?product_id=${product.product_id}`);
  assert.equal(movements.some((movement) => movement.movement_type === "INITIAL_STOCK"), true);
  assert.equal(movements.some((movement) => movement.movement_type === "STOCK_IN"), true);
  assert.equal(movements.some((movement) => movement.movement_type === "STOCK_OUT"), true);

  const report = await api("GET", "/api/reports/sales?start=2026-01-01&end=2999-12-31");
  assert.ok(report.summary.total_po >= 1);
  assert.ok(report.top_products.length >= 1);
  assert.ok(report.top_clients.length >= 1);
});

test("order rejection returns stock and used products cannot be deleted", async () => {
  const stamp = `${Date.now()}-reject`;
  const beforeSummary = await api("GET", "/api/admin/summary");
  const { company, product, user } = await createProductCompanyUser(stamp, 5);

  const order = await api("POST", "/api/orders", {
    company_id: company.company_id,
    dibuat_oleh: user.user_id,
    metode_pembayaran: "Cash",
    items: [
      {
        product_id: product.product_id,
        kuantitas: 2,
        harga_final: 12000,
      },
    ],
  });
  assert.ok(order.po_id);

  const afterCheckout = await api("GET", `/api/products?q=SKU-IT-${stamp}&include_empty=true`);
  assert.equal(afterCheckout[0].stok_gudang, 3);

  const rejected = await api("PATCH", `/api/orders/${order.po_id}/status`, {
    status_po: "Rejected",
  });
  assert.equal(rejected.status_po, "Rejected");

  const afterReject = await api("GET", `/api/products?q=SKU-IT-${stamp}&include_empty=true`);
  assert.equal(afterReject[0].stok_gudang, 5);

  const movements = await api("GET", `/api/inventory/movements?product_id=${product.product_id}`);
  assert.equal(movements.some((movement) => movement.movement_type === "STOCK_RETURN"), true);

  const deleteFailure = await apiFailure("DELETE", `/api/products/${product.product_id}`, undefined, 409);
  assert.match(deleteFailure.message, /PO/);

  const afterSummary = await api("GET", "/api/admin/summary");
  assert.ok(afterSummary.products >= beforeSummary.products + 1);
  assert.ok(afterSummary.orders >= beforeSummary.orders + 1);
});

test("order approval keeps stock deducted without stock return movement", async () => {
  const stamp = `${Date.now()}-approve`;
  const { company, product, user } = await createProductCompanyUser(stamp, 5);

  const order = await api("POST", "/api/orders", {
    company_id: company.company_id,
    dibuat_oleh: user.user_id,
    metode_pembayaran: "Cash",
    items: [
      {
        product_id: product.product_id,
        kuantitas: 2,
        harga_final: 12000,
      },
    ],
  });

  const approved = await api("PATCH", `/api/orders/${order.po_id}/status`, {
    status_po: "Approved",
  });
  assert.equal(approved.status_po, "Approved");

  const afterApprove = await api("GET", `/api/products?q=SKU-IT-${stamp}&include_empty=true`);
  assert.equal(afterApprove[0].stok_gudang, 3);

  const movements = await api("GET", `/api/inventory/movements?product_id=${product.product_id}`);
  assert.equal(movements.some((movement) => movement.movement_type === "STOCK_OUT"), true);
  assert.equal(movements.some((movement) => movement.movement_type === "STOCK_RETURN"), false);
});

const assert = require("node:assert/strict");
const test = require("node:test");

const catalogRepository = require("../../src/services/catalog/repository");
const customerRepository = require("../../src/services/customer/repository");
const orderRepository = require("../../src/services/order/repository");
const reportingRepository = require("../../src/services/reporting/repository");

function createDbMock(handler) {
  const calls = [];
  return {
    calls,
    async query(sql, params = []) {
      calls.push({ sql, params });
      return handler({ sql, params, index: calls.length - 1 });
    },
  };
}

test("catalog repository lists products with search filters", async () => {
  const pool = createDbMock(() => ({
    rows: [{ product_id: 1, sku: "SKU-1", nama_produk: "Beras" }],
  }));

  const products = await catalogRepository.listProducts(pool, {
    includeEmpty: true,
    q: "beras",
    category: "Bahan Pokok",
  });

  assert.equal(products.length, 1);
  assert.match(pool.calls[0].sql, /ILIKE/);
  assert.match(pool.calls[0].sql, /p\.kategori/);
  assert.deepEqual(pool.calls[0].params, ["%beras%", "Bahan Pokok"]);
});

test("catalog repository creates product and returns inserted row", async () => {
  const client = createDbMock(() => ({
    rows: [{ product_id: 10, sku: "SKU-10" }],
  }));

  const product = await catalogRepository.createProduct(client, {
    sku: "SKU-10",
    nama_produk: "Tepung",
    kategori: "Bahan Pokok",
    satuan: "Kg",
    harga_dasar: 12000,
    stok_gudang: 5,
  });

  assert.equal(product.product_id, 10);
  assert.match(client.calls[0].sql, /INSERT INTO products/);
  assert.deepEqual(client.calls[0].params, ["SKU-10", "Tepung", "Bahan Pokok", "Kg", 12000, 5]);
});

test("customer repository filters users by company", async () => {
  const pool = createDbMock(() => ({
    rows: [{ user_id: 7, company_id: 3 }],
  }));

  const users = await customerRepository.listUsers(pool, 3);

  assert.equal(users.length, 1);
  assert.match(pool.calls[0].sql, /WHERE u\.company_id = \$1/);
  assert.deepEqual(pool.calls[0].params, [3]);
});

test("customer repository reads company credit or null", async () => {
  const pool = createDbMock(() => ({ rows: [] }));

  const credit = await customerRepository.getCompanyCredit(pool, 404);

  assert.equal(credit, null);
  assert.deepEqual(pool.calls[0].params, [404]);
});

test("order repository creates purchase order and locks stock", async () => {
  const client = createDbMock(({ index }) => {
    if (index === 0) {
      return { rows: [{ stok_gudang: 12 }] };
    }
    return { rows: [{ po_id: 99 }] };
  });

  const stock = await orderRepository.lockProductStock(client, 5);
  const poId = await orderRepository.createPurchaseOrder(client, {
    company_id: 1,
    dibuat_oleh: 2,
    metode_pembayaran: "Cash",
    total_tagihan: 50000,
  });

  assert.equal(stock.stok_gudang, 12);
  assert.equal(poId, 99);
  assert.match(client.calls[0].sql, /FOR UPDATE/);
  assert.match(client.calls[1].sql, /INSERT INTO purchaseorders/);
});

test("order repository updates status and returns updated row", async () => {
  const client = createDbMock(() => ({
    rows: [{ po_id: 2, status_po: "Approved" }],
  }));

  const updated = await orderRepository.updateOrderStatus(client, 2, "Approved");

  assert.deepEqual(updated, { po_id: 2, status_po: "Approved" });
  assert.deepEqual(client.calls[0].params, ["Approved", 2]);
});

test("reporting repository returns admin summary", async () => {
  const pool = createDbMock(() => ({
    rows: [{ companies: 2, products: 3, orders: 4, pending_orders: 1 }],
  }));

  const summary = await reportingRepository.getAdminSummary(pool);

  assert.equal(summary.orders, 4);
  assert.match(pool.calls[0].sql, /COUNT\(\*\)::int FROM purchaseorders/);
});

test("reporting repository builds sales report sections", async () => {
  const responses = [
    [{ total_po: 1 }],
    [{ bulan: "2026-01", revenue: 1000 }],
    [{ segmen: "Cafe", revenue: 1000 }],
    [{ produk: "Beras", total_qty: 2 }],
    [{ klien: "PT Demo", jumlah_po: 1 }],
    [{ po_id: 1, status: "Approved" }],
  ];
  const pool = createDbMock(({ index }) => ({ rows: responses[index] }));

  const report = await reportingRepository.getSalesReport(pool, {
    start: "2026-01-01",
    end: "2026-12-31",
  });

  assert.equal(report.summary.total_po, 1);
  assert.equal(report.monthly[0].bulan, "2026-01");
  assert.equal(report.transactions[0].po_id, 1);
  assert.equal(pool.calls.length, 6);
  assert.deepEqual(pool.calls[0].params, ["2026-01-01", "2026-12-31"]);
});

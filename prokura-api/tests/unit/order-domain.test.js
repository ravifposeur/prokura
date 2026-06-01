const assert = require("node:assert/strict");
const test = require("node:test");

const {
  calculateOrderTotal,
  validateOrderPayload,
} = require("../../src/services/order/domain");

test("calculateOrderTotal sums quantity multiplied by final price", () => {
  assert.equal(
    calculateOrderTotal([
      { kuantitas: 2, harga_final: 10000 },
      { kuantitas: 3, harga_final: 5000 },
    ]),
    35000,
  );
});

test("validateOrderPayload accepts complete checkout payload", () => {
  assert.equal(
    validateOrderPayload({
      company_id: 1,
      dibuat_oleh: 2,
      metode_pembayaran: "Cash",
      items: [{ product_id: 3, kuantitas: 1, harga_final: 12000 }],
    }),
    true,
  );
});

test("validateOrderPayload rejects empty item list", () => {
  assert.throws(
    () =>
      validateOrderPayload({
        company_id: 1,
        dibuat_oleh: 2,
        metode_pembayaran: "Cash",
        items: [],
      }),
    /minimal satu item/,
  );
});

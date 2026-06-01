const assert = require("node:assert/strict");
const test = require("node:test");

const {
  buildInventoryMovement,
  parsePositiveInteger,
} = require("../../src/services/inventory/domain");

test("parsePositiveInteger accepts positive integers", () => {
  assert.equal(parsePositiveInteger(1), 1);
  assert.equal(parsePositiveInteger("25"), 25);
});

test("parsePositiveInteger rejects invalid quantities", () => {
  assert.throws(() => parsePositiveInteger(0), /quantity/);
  assert.throws(() => parsePositiveInteger(-1), /quantity/);
  assert.throws(() => parsePositiveInteger("1.5"), /quantity/);
  assert.throws(() => parsePositiveInteger("abc"), /quantity/);
});

test("buildInventoryMovement normalizes movement payload", () => {
  assert.deepEqual(
    buildInventoryMovement({
      productId: "10",
      movementType: "STOCK_IN",
      quantity: "5",
      note: "Restock",
      referenceType: "PRODUCT",
      referenceId: "10",
    }),
    {
      productId: 10,
      movementType: "STOCK_IN",
      quantity: 5,
      note: "Restock",
      referenceType: "PRODUCT",
      referenceId: 10,
    },
  );
});

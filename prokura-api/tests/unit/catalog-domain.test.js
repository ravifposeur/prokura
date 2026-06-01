const assert = require("node:assert/strict");
const test = require("node:test");

const {
  buildProductSearchFilters,
  normalizeSku,
} = require("../../src/services/catalog/domain");

test("normalizeSku trims and uppercases SKU", () => {
  assert.equal(normalizeSku(" sku-001 "), "SKU-001");
});

test("normalizeSku rejects blank SKU", () => {
  assert.throws(() => normalizeSku(""), /SKU/);
});

test("buildProductSearchFilters normalizes catalog query", () => {
  assert.deepEqual(
    buildProductSearchFilters({
      include_empty: "true",
      q: " beras ",
      category: "Bahan Pokok",
    }),
    {
      includeEmpty: true,
      q: "beras",
      category: "Bahan Pokok",
    },
  );
});

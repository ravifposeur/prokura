const assert = require("node:assert/strict");
const test = require("node:test");

const { normalizeDateRange } = require("../../src/services/reporting/domain");

test("normalizeDateRange applies default report range", () => {
  assert.deepEqual(normalizeDateRange(), {
    start: "1900-01-01",
    end: "2999-12-31",
  });
});

test("normalizeDateRange accepts valid explicit range", () => {
  assert.deepEqual(normalizeDateRange({ start: "2026-01-01", end: "2026-12-31" }), {
    start: "2026-01-01",
    end: "2026-12-31",
  });
});

test("normalizeDateRange rejects inverted date range", () => {
  assert.throws(
    () => normalizeDateRange({ start: "2026-12-31", end: "2026-01-01" }),
    /setelah tanggal akhir/,
  );
});

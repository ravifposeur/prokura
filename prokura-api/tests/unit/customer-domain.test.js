const assert = require("node:assert/strict");
const test = require("node:test");

const {
  normalizeCompanyName,
  validateEmail,
} = require("../../src/services/customer/domain");

test("validateEmail normalizes valid email", () => {
  assert.equal(validateEmail(" USER@PROKURA.TEST "), "user@prokura.test");
});

test("validateEmail rejects invalid email", () => {
  assert.throws(() => validateEmail("not-an-email"), /email/i);
});

test("normalizeCompanyName trims company name", () => {
  assert.equal(normalizeCompanyName(" PT Prokura Demo "), "PT Prokura Demo");
});

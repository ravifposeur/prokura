function normalizeSku(value) {
  if (!value || typeof value !== "string") {
    throw new Error("SKU wajib diisi");
  }
  return value.trim().toUpperCase();
}

function buildProductSearchFilters(query = {}) {
  return {
    includeEmpty: query.include_empty === "true",
    q: query.q ? String(query.q).trim() : "",
    category: query.category ? String(query.category).trim() : "",
  };
}

module.exports = {
  buildProductSearchFilters,
  normalizeSku,
};

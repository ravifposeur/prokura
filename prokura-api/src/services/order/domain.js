function validateOrderPayload(payload = {}) {
  const { company_id, dibuat_oleh, metode_pembayaran, items } = payload;

  if (!company_id || !dibuat_oleh || !metode_pembayaran) {
    throw new Error("Payload order tidak lengkap");
  }

  if (!Array.isArray(items) || items.length === 0) {
    throw new Error("Order harus memiliki minimal satu item");
  }

  for (const item of items) {
    if (!item.product_id || !Number.isInteger(Number(item.kuantitas)) || Number(item.kuantitas) <= 0) {
      throw new Error("Item order tidak valid");
    }
    if (!Number.isFinite(Number(item.harga_final)) || Number(item.harga_final) < 0) {
      throw new Error("Harga item order tidak valid");
    }
  }

  return true;
}

function calculateOrderTotal(items = []) {
  return items.reduce(
    (total, item) => total + Number(item.kuantitas) * Number(item.harga_final),
    0,
  );
}

module.exports = {
  calculateOrderTotal,
  validateOrderPayload,
};

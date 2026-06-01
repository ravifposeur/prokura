function parsePositiveInteger(value, fieldName = "quantity") {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error(`${fieldName} harus bilangan bulat positif`);
  }
  return parsed;
}

function buildInventoryMovement({
  productId,
  movementType,
  quantity,
  note = null,
  referenceType = null,
  referenceId = null,
}) {
  if (!productId) {
    throw new Error("productId wajib diisi");
  }
  if (!movementType) {
    throw new Error("movementType wajib diisi");
  }

  return {
    productId: Number(productId),
    movementType,
    quantity: Number(quantity),
    note,
    referenceType,
    referenceId: referenceId == null ? null : Number(referenceId),
  };
}

module.exports = {
  buildInventoryMovement,
  parsePositiveInteger,
};

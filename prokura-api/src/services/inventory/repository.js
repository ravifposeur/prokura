const { buildInventoryMovement } = require("./domain");

async function recordInventoryMovement(client, {
  productId,
  movementType,
  quantity,
  note = null,
  referenceType = null,
  referenceId = null,
}) {
  const movement = buildInventoryMovement({
    productId,
    movementType,
    quantity,
    note,
    referenceType,
    referenceId,
  });

  await client.query(
    `
      INSERT INTO inventory_movements
        (product_id, movement_type, quantity, note, reference_type, reference_id)
      VALUES ($1, $2, $3, $4, $5, $6)
    `,
    [
      movement.productId,
      movement.movementType,
      movement.quantity,
      movement.note,
      movement.referenceType,
      movement.referenceId,
    ],
  );
}

module.exports = {
  recordInventoryMovement,
};

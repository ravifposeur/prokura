function sendError(res, error, message = "Terjadi kesalahan server") {
  console.error(message, error);
  res.status(500).json({ success: false, message });
}

module.exports = {
  sendError,
};

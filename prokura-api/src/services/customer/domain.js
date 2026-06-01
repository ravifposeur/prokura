function validateEmail(email) {
  if (!email || typeof email !== "string") {
    throw new Error("Email wajib diisi");
  }

  const normalized = email.trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized)) {
    throw new Error("Format email tidak valid");
  }

  return normalized;
}

function normalizeCompanyName(name) {
  if (!name || typeof name !== "string") {
    throw new Error("Nama perusahaan wajib diisi");
  }
  return name.trim();
}

module.exports = {
  normalizeCompanyName,
  validateEmail,
};

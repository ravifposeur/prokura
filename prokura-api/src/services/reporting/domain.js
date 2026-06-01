function normalizeDateRange({ start, end } = {}) {
  const normalizedStart = start || "1900-01-01";
  const normalizedEnd = end || "2999-12-31";

  if (Number.isNaN(Date.parse(normalizedStart)) || Number.isNaN(Date.parse(normalizedEnd))) {
    throw new Error("Rentang tanggal laporan tidak valid");
  }

  if (new Date(normalizedStart) > new Date(normalizedEnd)) {
    throw new Error("Tanggal mulai laporan tidak boleh setelah tanggal akhir");
  }

  return {
    start: normalizedStart,
    end: normalizedEnd,
  };
}

module.exports = {
  normalizeDateRange,
};

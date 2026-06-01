"use client";
import { useEffect, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:5000";

export default function ProkuraUnifiedDashboard() {
  // --- STATE MANAJEMEN ---
  const [activeRole, setActiveRole] = useState<
    "Chef" | "Finance" | "Procurement"
  >("Chef");

  // State Chef (Katalog & Cart)
  const [products, setProducts] = useState<any[]>([]);
  const [cart, setCart] = useState<any[]>([]);
  const [companyData, setCompanyData] = useState<any>(null);

  // State Finance (Approval & History)
  const [poHistory, setPoHistory] = useState<any[]>([]);
  const [selectedPO, setSelectedPO] = useState<any>(null);
  const [poDetails, setPoDetails] = useState<any[]>([]);

  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);

  const COMPANY_ID = 1;
  const USER_ID = 1;

  // --- FETCH DATA AWAL ---
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [prodRes, credRes, histRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/products`).then((r) => r.json()),
        fetch(`${API_BASE_URL}/api/companies/${COMPANY_ID}/credit`).then(
          (r) => r.json(),
        ),
        fetch(`${API_BASE_URL}/api/companies/${COMPANY_ID}/orders`).then(
          (r) => r.json(),
        ),
      ]);
      if (prodRes.success) setProducts(prodRes.data);
      if (credRes.success) setCompanyData(credRes.data);
      if (histRes.success) setPoHistory(histRes.data);
    } catch (err) {
      console.error("Gagal terhubung ke server:", err);
    } finally {
      setLoading(false);
    }
  };

  // --- LOGIKA CHEF (PENGADAAN) ---
  const addToCart = (product: any) => {
    setCart((prev) => {
      const existing = prev.find(
        (item) => item.product_id === product.product_id,
      );
      if (existing) {
        return prev.map((item) =>
          item.product_id === product.product_id
            ? { ...item, kuantitas: item.kuantitas + 1 }
            : item,
        );
      }
      return [
        ...prev,
        {
          ...product,
          kuantitas: 1,
          harga_final: parseInt(product.harga_dasar),
        },
      ];
    });
  };

  const removeFromCart = (productId: number) => {
    setCart((prev) => prev.filter((item) => item.product_id !== productId));
  };

  const totalTagihan = cart.reduce(
    (sum, item) => sum + item.harga_final * item.kuantitas,
    0,
  );
  const sisaLimit = companyData
    ? parseFloat(companyData.limit_kredit) - totalTagihan
    : 0;
  const isLimitExceeded = sisaLimit < 0;

  const handleCheckout = async () => {
    if (cart.length === 0 || isLimitExceeded) return;
    setIsProcessing(true);
    const payload = {
      company_id: COMPANY_ID,
      dibuat_oleh: USER_ID,
      metode_pembayaran: "Tempo_30_Hari",
      total_tagihan: totalTagihan,
      items: cart.map((item) => ({
        product_id: item.product_id,
        kuantitas: item.kuantitas,
        harga_final: item.harga_final,
      })),
    };

    try {
      const res = await fetch(`${API_BASE_URL}/api/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.success) {
        setCart([]);
        await fetchInitialData(); // Refresh data transparan
        alert(`Sukses! PO #${data.po_id} diajukan.`);
      }
    } catch (error) {
      alert("Gagal memproses pesanan.");
    } finally {
      setIsProcessing(false);
    }
  };

  // --- LOGIKA FINANCE (APPROVAL) ---
  const viewPoDetails = async (po: any) => {
    setSelectedPO(po);
    setPoDetails([]); // loading state
    try {
      const res = await fetch(`${API_BASE_URL}/api/orders/${po.po_id}`);
      const data = await res.json();
      if (data.success) setPoDetails(data.data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleApproval = async (
    poId: number,
    status: "Approved" | "Rejected",
  ) => {
    if (
      !confirm(`Anda yakin ingin memberikan status ${status} pada PO #${poId}?`)
    )
      return;
    setIsProcessing(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/orders/${poId}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status_po: status }),
        },
      );
      const data = await res.json();
      if (data.success) {
        setSelectedPO({ ...selectedPO, status_po: status });
        await fetchInitialData(); // Refresh list & stok produk secara real-time
      }
    } catch (error) {
      alert("Gagal memproses approval.");
    } finally {
      setIsProcessing(false);
    }
  };

  // --- RENDER UTILITY ---
  const getStatusColor = (status: string) => {
    if (status === "Approved")
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
    if (status === "Rejected") return "bg-red-100 text-red-700 border-red-200";
    return "bg-amber-100 text-amber-700 border-amber-200";
  };

  if (loading && products.length === 0)
    return (
      <div className="h-screen flex items-center justify-center bg-[#f8fafc] text-slate-400 tracking-widest animate-pulse">
        SINKRONISASI DATA...
      </div>
    );

  return (
    <main className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans p-8 box-border selection:bg-blue-200">
      {/* HEADER & ROLE SWITCHER */}
      <header className="max-w-[1600px] mx-auto mb-10 flex justify-between items-center bg-white p-6 rounded-[2rem] shadow-sm border border-slate-100">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
            Prokura<span className="text-blue-600">.</span>
          </h1>
          <p className="text-xs font-bold text-slate-400 mt-1 uppercase tracking-widest">
            B2B Core Infrastructure
          </p>
        </div>

        {/* Toggle Transparansi Peran */}
        <div className="bg-slate-100 p-1.5 rounded-2xl flex gap-2 border border-slate-200">
          <button
            onClick={() => setActiveRole("Chef")}
            className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-300 ${activeRole === "Chef" ? "bg-white text-blue-700 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
          >
            Terminal Pengadaan (Chef)
          </button>
          <button
            onClick={() => setActiveRole("Finance")}
            className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-300 ${activeRole === "Finance" ? "bg-slate-900 text-white shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
          >
            Otoritas Anggaran (Finance)
          </button>
          <button
            onClick={() => setActiveRole("Procurement")}
            className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-300 ${activeRole === "Procurement" ? "bg-indigo-600 text-white shadow-sm shadow-indigo-200" : "text-slate-500 hover:text-slate-700"}`}
          >
            Gudang & Logistik (Procurement)
          </button>
        </div>

        {companyData && (
          <div className="text-right border-l border-slate-100 pl-8">
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">
              Limit PayLater ({companyData.nama_perusahaan})
            </p>
            <p className="text-xl font-black text-slate-800">
              Rp {parseInt(companyData.limit_kredit).toLocaleString("id-ID")}
            </p>
          </div>
        )}
      </header>

      {/* ========================================================= */}
      {/* WORKSPACE 1: PENGADAAN BARANG (CHEF) */}
      {/* ========================================================= */}
      {activeRole === "Chef" && (
        <div className="max-w-[1600px] mx-auto flex gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* PANEL KIRI: Katalog */}
          <div className="flex-1">
            <div className="grid grid-cols-3 gap-6">
              {products.map((p) => (
                <div
                  key={p.product_id}
                  className="bg-white rounded-3xl p-5 shadow-sm hover:shadow-xl transition-all duration-300 border border-slate-100 group flex flex-col justify-between"
                >
                  <div>
                    <div className="aspect-square bg-slate-50 rounded-2xl mb-5 flex items-center justify-center overflow-hidden relative">
                      {p.image_url ? (
                        <img
                          src={p.image_url}
                          alt={p.nama_produk}
                          className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <span className="text-slate-300 font-medium">
                          No Image
                        </span>
                      )}
                      <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full text-[10px] font-bold tracking-wider text-slate-600 border border-white/50">
                        STOK: {p.stok_gudang}
                      </div>
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 leading-snug">
                      {p.nama_produk}
                    </h3>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded-md uppercase tracking-wider">
                        {p.kategori}
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        {p.sku}
                      </span>
                    </div>
                  </div>
                  <div className="mt-6 pt-5 border-t border-slate-50 flex items-center justify-between">
                    <div>
                      <p className="text-xl font-extrabold text-slate-800">
                        Rp {parseInt(p.harga_dasar).toLocaleString("id-ID")}
                      </p>
                      <p className="text-[10px] text-slate-400 font-bold uppercase mt-1">
                        per {p.satuan}
                      </p>
                    </div>
                    <button
                      onClick={() => addToCart(p)}
                      className="h-10 w-10 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center hover:bg-blue-600 hover:text-white hover:rotate-90 transition-all duration-300"
                    >
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2.5}
                          d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* PANEL KANAN: Keranjang */}
          <aside className="w-[420px] relative">
            <div className="bg-slate-900 text-white rounded-[2.5rem] p-8 shadow-2xl sticky top-8 h-[calc(100vh-4rem)] flex flex-col">
              <h2 className="text-2xl font-bold mb-1">Draft PO F&B</h2>
              <p className="text-slate-400 text-sm mb-6">
                Alokasi Gudang Pusat
              </p>

              <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                {cart.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-slate-600 font-medium">
                    Menunggu input barang...
                  </div>
                ) : (
                  cart.map((item) => (
                    <div
                      key={item.product_id}
                      className="bg-slate-800/50 p-4 rounded-2xl flex gap-4 items-center border border-slate-700/50"
                    >
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-slate-100 text-sm truncate">
                          {item.nama_produk}
                        </h4>
                        <p className="text-xs text-slate-400 mt-1">
                          Rp {item.harga_final.toLocaleString("id-ID")} ×{" "}
                          {item.kuantitas}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-white text-sm">
                          Rp{" "}
                          {(item.harga_final * item.kuantitas).toLocaleString(
                            "id-ID",
                          )}
                        </p>
                        <button
                          onClick={() => removeFromCart(item.product_id)}
                          className="text-[10px] uppercase font-bold tracking-wider text-red-400 hover:text-red-300 mt-1"
                        >
                          Hapus
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div className="mt-6 pt-6 border-t border-slate-800">
                <div className="flex justify-between items-end mb-4">
                  <span className="text-slate-400 font-medium text-sm">
                    Total Estimasi
                  </span>
                  <span className="text-3xl font-black">
                    Rp {totalTagihan.toLocaleString("id-ID")}
                  </span>
                </div>
                <div className="bg-slate-800 rounded-2xl p-4 mb-6">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-400 uppercase font-bold tracking-wider">
                      Sisa Saldo B2B
                    </span>
                    <span
                      className={`text-sm font-bold ${isLimitExceeded ? "text-red-400" : "text-emerald-400"}`}
                    >
                      Rp {sisaLimit.toLocaleString("id-ID")}
                    </span>
                  </div>
                </div>
                <button
                  onClick={handleCheckout}
                  disabled={
                    cart.length === 0 || isLimitExceeded || isProcessing
                  }
                  className={`w-full py-4 rounded-2xl font-bold text-sm uppercase tracking-widest transition-all duration-300 ${
                    cart.length === 0 || isLimitExceeded
                      ? "bg-slate-800 text-slate-600 cursor-not-allowed"
                      : "bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-900/50"
                  }`}
                >
                  {isProcessing ? "Menyinkronkan..." : "Ajukan Approval"}
                </button>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* ========================================================= */}
      {/* WORKSPACE 2: OTORITAS ANGGARAN (FINANCE MANAGER) */}
      {/* ========================================================= */}
      {activeRole === "Finance" && (
        <div className="max-w-[1600px] mx-auto flex gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* PANEL KIRI: Antrean Purchase Orders */}
          <div className="w-[500px] flex flex-col gap-4 h-[calc(100vh-10rem)] overflow-y-auto custom-scrollbar pr-2">
            <h2 className="text-xl font-black text-slate-800 mb-2">
              Riwayat & Antrean PO
            </h2>
            {poHistory.map((po) => (
              <div
                key={po.po_id}
                onClick={() => viewPoDetails(po)}
                className={`p-5 rounded-3xl border-2 cursor-pointer transition-all duration-200 ${
                  selectedPO?.po_id === po.po_id
                    ? "bg-white border-blue-600 shadow-lg shadow-blue-100"
                    : "bg-white border-slate-100 hover:border-slate-300 hover:shadow-md"
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
                      PO ID #{po.po_id}
                    </span>
                    <h3 className="font-bold text-slate-800 mt-1">
                      {po.pembuat} (Chef)
                    </h3>
                  </div>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-lg border ${getStatusColor(po.status_po)}`}
                  >
                    {po.status_po.replace("_", " ")}
                  </span>
                </div>
                <div className="flex justify-between items-end pt-3 border-t border-slate-50 mt-2">
                  <div>
                    <p className="text-[10px] text-slate-400 font-bold uppercase">
                      Nilai Transaksi
                    </p>
                    <p className="font-black text-slate-800">
                      Rp {parseInt(po.total_tagihan).toLocaleString("id-ID")}
                    </p>
                  </div>
                  <p className="text-xs font-mono text-slate-400">
                    {new Date(po.tanggal_dipesan).toLocaleDateString("id-ID")}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* PANEL KANAN: Inspeksi Detail & Eksekusi */}
          <div className="flex-1 bg-white rounded-[2.5rem] border border-slate-100 shadow-sm p-8 h-[calc(100vh-10rem)] flex flex-col relative overflow-hidden">
            {!selectedPO ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4">
                <svg
                  className="w-16 h-16 opacity-20"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
                <p className="font-medium tracking-wide">
                  Pilih dokumen PO untuk inspeksi detail.
                </p>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <h2 className="text-3xl font-black text-slate-900">
                      Inspeksi PO #{selectedPO.po_id}
                    </h2>
                    <p className="text-sm font-medium text-slate-500 mt-2 flex gap-4">
                      <span>
                        Metode:{" "}
                        <b className="text-slate-700">
                          {selectedPO.metode_pembayaran.replace(/_/g, " ")}
                        </b>
                      </span>
                      <span>
                        Tanggal:{" "}
                        <b className="text-slate-700">
                          {new Date(selectedPO.tanggal_dipesan).toLocaleString(
                            "id-ID",
                          )}
                        </b>
                      </span>
                    </p>
                  </div>
                  <span
                    className={`text-xs font-bold uppercase tracking-wider px-4 py-2 rounded-xl border ${getStatusColor(selectedPO.status_po)}`}
                  >
                    Status Saat Ini: {selectedPO.status_po.replace("_", " ")}
                  </span>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 border border-slate-100 rounded-2xl bg-slate-50">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-100 sticky top-0">
                      <tr>
                        <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                          SKU
                        </th>
                        <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                          Nama Barang
                        </th>
                        <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200 text-right">
                          Kuantitas
                        </th>
                        <th className="py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200 text-right">
                          Subtotal
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {poDetails.length === 0 ? (
                        <tr>
                          <td
                            colSpan={4}
                            className="py-8 text-center text-sm text-slate-400"
                          >
                            Memuat rincian aset...
                          </td>
                        </tr>
                      ) : (
                        poDetails.map((item, idx) => (
                          <tr
                            key={idx}
                            className="hover:bg-slate-50 transition-colors"
                          >
                            <td className="py-4 px-6 text-xs font-mono text-slate-400">
                              {item.sku}
                            </td>
                            <td className="py-4 px-6 text-sm font-bold text-slate-800">
                              {item.nama_produk}
                            </td>
                            <td className="py-4 px-6 text-sm font-bold text-slate-700 text-right">
                              {item.kuantitas} {item.satuan}
                            </td>
                            <td className="py-4 px-6 text-sm font-black text-slate-900 text-right">
                              Rp{" "}
                              {parseInt(item.subtotal).toLocaleString("id-ID")}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Panel Eksekusi (Hanya muncul jika Pending) */}
                {selectedPO.status_po === "Pending_Approval" && (
                  <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between bg-slate-50 p-6 rounded-2xl border">
                    <div>
                      <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">
                        Total Validasi
                      </p>
                      <p className="text-3xl font-black text-slate-900">
                        Rp{" "}
                        {parseInt(selectedPO.total_tagihan).toLocaleString(
                          "id-ID",
                        )}
                      </p>
                    </div>
                    <div className="flex gap-4">
                      <button
                        onClick={() =>
                          handleApproval(selectedPO.po_id, "Rejected")
                        }
                        disabled={isProcessing}
                        className="px-8 py-4 rounded-xl font-bold text-sm uppercase tracking-widest bg-red-100 text-red-600 hover:bg-red-600 hover:text-white transition-all border border-red-200 hover:border-red-600 shadow-sm"
                      >
                        Tolak Anggaran
                      </button>
                      <button
                        onClick={() =>
                          handleApproval(selectedPO.po_id, "Approved")
                        }
                        disabled={isProcessing}
                        className="px-8 py-4 rounded-xl font-bold text-sm uppercase tracking-widest bg-emerald-600 text-white hover:bg-emerald-500 transition-all shadow-lg shadow-emerald-200"
                      >
                        Sah-kan PO
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
      {/* ========================================================= */}
      {/* WORKSPACE 3: GUDANG & LOGISTIK (PROCUREMENT) */}
      {/* ========================================================= */}
      {activeRole === "Procurement" && (
        <div className="max-w-[1600px] mx-auto flex gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* PANEL KIRI: Monitor Inventaris (Real-time Stock) */}
          <div className="flex-1 bg-white rounded-[2.5rem] border border-slate-100 shadow-sm p-8 h-[calc(100vh-10rem)] flex flex-col relative overflow-hidden">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-black text-slate-900">
                  Monitor Inventaris Fisik
                </h2>
                <p className="text-sm text-slate-500 mt-1">
                  Status ketersediaan bahan baku di gudang pusat.
                </p>
              </div>
              <span className="bg-indigo-50 text-indigo-700 font-bold px-4 py-2 rounded-xl text-xs uppercase tracking-wider">
                Total SKU: {products.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 grid grid-cols-2 gap-4">
              {products.map((p) => {
                // Logika peringatan stok menipis
                const isLowStock = p.stok_gudang < 50;
                return (
                  <div
                    key={p.product_id}
                    className={`p-4 rounded-2xl border-2 flex items-center gap-4 transition-all ${isLowStock ? "border-amber-200 bg-amber-50/50" : "border-slate-100 bg-white hover:border-slate-200"}`}
                  >
                    <div className="h-16 w-16 bg-slate-100 rounded-xl overflow-hidden flex-shrink-0">
                      {p.image_url ? (
                        <img
                          src={p.image_url}
                          alt={p.nama_produk}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-slate-200" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-bold text-slate-800 truncate">
                        {p.nama_produk}
                      </h4>
                      <p className="text-xs font-mono text-slate-400 mt-1">
                        {p.sku}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mb-1">
                        Fisik (Sisa)
                      </p>
                      <p
                        className={`text-xl font-black ${isLowStock ? "text-amber-600" : "text-slate-800"}`}
                      >
                        {p.stok_gudang}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* PANEL KANAN: Antrean Distribusi / Ekspedisi (Hanya PO Approved) */}
          <aside className="w-[450px] relative">
            <div className="bg-slate-900 text-white rounded-[2.5rem] p-8 shadow-2xl sticky top-8 h-[calc(100vh-10rem)] flex flex-col">
              <h2 className="text-2xl font-bold mb-1">Manifest Distribusi</h2>
              <p className="text-slate-400 text-sm mb-6">
                Daftar PO yang siap di-packing dan dikirim ke klien.
              </p>

              <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
                {poHistory.filter((po) => po.status_po === "Approved")
                  .length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
                    <svg
                      className="w-16 h-16 opacity-20"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1}
                        d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"
                      />
                    </svg>
                    <p className="font-medium">Tidak ada antrean pengiriman.</p>
                  </div>
                ) : (
                  poHistory
                    .filter((po) => po.status_po === "Approved")
                    .map((po) => (
                      <div
                        key={po.po_id}
                        className="bg-indigo-900/40 p-5 rounded-2xl border border-indigo-500/30"
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <span className="text-[10px] text-indigo-300 font-bold uppercase tracking-widest">
                              Siap Kirim
                            </span>
                            <h4 className="font-bold text-slate-100 mt-1">
                              PO #{po.po_id}
                            </h4>
                          </div>
                          <span className="bg-indigo-500 text-white text-[10px] font-bold px-2 py-1 rounded uppercase">
                            Approved
                          </span>
                        </div>
                        <p className="text-sm text-slate-300 mb-4">
                          Tujuan:{" "}
                          <span className="font-semibold text-white">
                            {companyData?.nama_perusahaan || "Klien"}
                          </span>
                        </p>

                        <button
                          onClick={() =>
                            alert(
                              `Mencetak Surat Jalan untuk PO #${po.po_id}... (Fitur Cetak PDF dapat disambungkan ke sini)`,
                            )
                          }
                          className="w-full py-3 rounded-xl font-bold text-xs uppercase tracking-widest bg-indigo-500 text-white hover:bg-indigo-400 transition-all shadow-md shadow-indigo-900"
                        >
                          Cetak Surat Jalan & Proses
                        </button>
                      </div>
                    ))
                )}
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Global Styles */}
      <style
        dangerouslySetInnerHTML={{
          __html: `
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
      `,
        }}
      />
    </main>
  );
}

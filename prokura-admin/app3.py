from datetime import date
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API_BASE_URL = os.getenv("PROKURA_API_BASE_URL", "http://127.0.0.1:5000")
WEB_URL = os.getenv("PROKURA_WEB_URL", "http://127.0.0.1:3000")
STOK_MINIMUM = 10


st.set_page_config(
    page_title="HoReCa Supply Management",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 700; }
      [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
      [data-testid="stSidebar"] { border-right: 1px solid #e5e7eb; }
      .stAlert { border-radius: 8px; }
      div[data-testid="stExpander"] { border: 1px solid #ffc107; border-radius: 8px; }
      div[data-testid="stDataFrame"] { border: 1px solid #e5e7eb; border-radius: 8px; }

      /* === PORTAL PEMBELIAN STYLES: matched to legacy app_mysql_legacy.py === */
      .portal-header {
        background: linear-gradient(135deg, #0077B6 0%, #023e8a 100%);
        color: white;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
      }
      .product-card {
        background: #ffffff;
        border: 1px solid #e8ecf0;
        border-radius: 14px;
        padding: 0;
        margin-bottom: 16px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
      }
      .product-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
      }
      .product-img-wrap {
        width: 100%;
        height: 180px;
        overflow: hidden;
        border-bottom: 1px solid #e8ecf0;
        background: #f1f5f9;
        position: relative;
      }
      .product-img-wrap img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        transition: transform 0.35s ease;
      }
      .product-card:hover .product-img-wrap img {
        transform: scale(1.06);
      }
      .product-body {
        padding: 12px 14px 14px;
      }
      .product-name {
        font-size: 0.92rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 2px;
        line-height: 1.35;
        min-height: 38px;
      }
      .product-sku {
        font-size: 0.72rem;
        color: #8a94a6;
        margin-bottom: 6px;
        font-family: monospace;
      }
      .product-price {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0077B6;
        margin-bottom: 4px;
      }
      .product-satuan {
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 8px;
      }
      .stok-badge-aman {
        display: inline-block;
        background: #d1fae5;
        color: #065f46;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-bottom: 10px;
      }
      .stok-badge-menipis {
        display: inline-block;
        background: #fef3c7;
        color: #92400e;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-bottom: 10px;
      }
      .stok-badge-habis {
        display: inline-block;
        background: #fee2e2;
        color: #991b1b;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-bottom: 10px;
      }
      .cart-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
      }
      .cart-total-box {
        background: linear-gradient(135deg, #0077B6, #023e8a);
        color: white;
        border-radius: 12px;
        padding: 16px 20px;
        margin-top: 12px;
      }
      .login-box {
        background: #f0f7ff;
        border: 1.5px solid #bfdbfe;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
      }
      .order-status-badge {
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.76rem;
        font-weight: 700;
        display: inline-block;
      }
      .kategori-chip {
        display: inline-block;
        background: #eff6ff;
        color: #1d4ed8;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        cursor: pointer;
        border: 1.5px solid #bfdbfe;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method, path, body=None):
    response = requests.request(
        method,
        f"{API_BASE_URL}{path}",
        json=body,
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success", False):
        raise RuntimeError(payload.get("message", "API request failed"))
    return payload.get("data")


def api_get(path):
    return api_request("GET", path)


def api_post(path, body):
    return api_request("POST", path, body)


def api_patch(path, body):
    return api_request("PATCH", path, body)


def api_delete(path):
    return api_request("DELETE", path)


@st.cache_data(ttl=5)
def load_data():
    summary = api_get("/api/admin/summary")
    orders = pd.DataFrame(api_get("/api/orders"))
    products = pd.DataFrame(api_get("/api/products?include_empty=true"))
    companies = pd.DataFrame(api_get("/api/companies"))
    users = pd.DataFrame(api_get("/api/users"))

    if not orders.empty:
        orders["tanggal_dipesan"] = pd.to_datetime(orders["tanggal_dipesan"])
        orders["total_tagihan"] = pd.to_numeric(orders["total_tagihan"])
        orders["tanggal"] = orders["tanggal_dipesan"].dt.date
        orders["bulan"] = orders["tanggal_dipesan"].dt.to_period("M").astype(str)

    if not products.empty:
        products["harga_dasar"] = pd.to_numeric(products["harga_dasar"])
        products["stok_gudang"] = pd.to_numeric(products["stok_gudang"])
        products["total_nilai_aset"] = products["harga_dasar"] * products["stok_gudang"]

    if not companies.empty:
        companies["limit_kredit"] = pd.to_numeric(companies["limit_kredit"])
        companies["created_at"] = pd.to_datetime(companies["created_at"])

    return summary, orders, products, companies, users


def clear_and_rerun():
    st.cache_data.clear()
    st.rerun()


def money(value):
    return f"Rp {float(value):,.0f}".replace(",", ".")


def format_money_columns(df, columns):
    shown = df.copy()
    for column in columns:
        if column in shown.columns:
            shown[column] = shown[column].map(money)
    return shown


def order_detail(po_id):
    detail = pd.DataFrame(api_get(f"/api/orders/{po_id}"))
    if not detail.empty:
        detail["harga_final"] = pd.to_numeric(detail["harga_final"])
        detail["subtotal"] = pd.to_numeric(detail["subtotal"])
    return detail


def init_portal_state():
    defaults = {
        "cart": {},
        "portal_company_id": None,
        "portal_user_id": None,
        "portal_company_name": "",
        "portal_user_name": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def cart_total_items():
    return sum(item["qty"] for item in st.session_state.cart.values())


def cart_total_price():
    return sum(item["qty"] * item["harga"] for item in st.session_state.cart.values())


def product_image_url(row, width=400, height=220):
    image_url = row.get("image_url")
    if isinstance(image_url, str) and image_url:
        if image_url.startswith("/"):
            return f"{WEB_URL}{image_url}"
        return image_url
    return f"https://picsum.photos/seed/prokura-{row.get('product_id', 'product')}/{width}/{height}"


init_portal_state()


try:
    summary, orders, products, companies, users = load_data()
except Exception as exc:
    st.error(f"API tidak bisa diakses: {exc}")
    st.stop()


with st.sidebar:
    st.title("🍽️ HoReCa Supply")
    st.caption("B2B Supply Management System")
    st.divider()
    menu_labels = {
        "Dashboard Utama": "📊 Dashboard Utama",
        "Manajemen Stok Gudang": "📦 Manajemen Stok Gudang",
        "Manajemen Klien B2B": "🏢 Manajemen Klien B2B",
        "Manajemen Pesanan (PO)": "🛒 Manajemen Pesanan (PO)",
        "Laporan & Analitik": "📈 Laporan & Analitik",
        "Portal Pembelian (User)": "🛍️ Portal Pembelian (User)",
        "API Monitor": "🔌 API Monitor",
    }
    pilihan_menu = st.radio(
        "Pilih Modul:",
        list(menu_labels.keys()),
        format_func=lambda value: menu_labels[value],
    )
    st.divider()
    st.caption(f"API: {API_BASE_URL}")
    st.caption(f"Web: {WEB_URL}")
    if pilihan_menu == "Portal Pembelian (User)":
        st.divider()
        total_item = cart_total_items()
        if total_item:
            st.markdown(f"**Keranjang ({total_item} item)**")
            for item in st.session_state.cart.values():
                st.caption(f"{item['nama'][:28]} - {item['qty']} {item['satuan']}")
            st.markdown(f"**Total: {money(cart_total_price())}**")
            if st.button("Kosongkan Keranjang", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()
        else:
            st.caption("Keranjang kosong")


if pilihan_menu == "Dashboard Utama":
    st.title("📊 Dashboard HoReCa Supply B2B")
    st.caption("Ringkasan operasional real-time dari PostgreSQL melalui Prokura API.")

    revenue = 0 if orders.empty else orders["total_tagihan"].sum()
    nilai_aset = 0 if products.empty else products["total_nilai_aset"].sum()
    stok_kritis = 0 if products.empty else int((products["stok_gudang"] < STOK_MINIMUM).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Klien", summary["companies"])
    c2.metric("Total SKU", summary["products"])
    c3.metric("Total PO", summary["orders"])
    c4.metric("Revenue", money(revenue))
    c5.metric("Stok Kritis", stok_kritis)

    st.divider()
    left, right = st.columns([3, 2])

    with left:
        st.subheader("Pesanan Terbaru")
        if orders.empty:
            st.info("Belum ada pesanan masuk.")
        else:
            shown = orders.head(10).copy()
            shown["tanggal_dipesan"] = shown["tanggal_dipesan"].dt.strftime("%d %b %Y")
            shown = format_money_columns(shown, ["total_tagihan"])
            st.dataframe(
                shown[["po_id", "company", "pembuat", "status_po", "metode_pembayaran", "total_tagihan", "tanggal_dipesan"]],
                use_container_width=True,
                hide_index=True,
            )

    with right:
        st.subheader("Peringatan Stok Kritis")
        if products.empty:
            st.info("Katalog produk kosong.")
        else:
            kritis = products[products["stok_gudang"] < STOK_MINIMUM].sort_values("stok_gudang")
            if kritis.empty:
                st.success("Semua stok dalam kondisi aman.")
            else:
                for _, row in kritis.head(8).iterrows():
                    st.warning(f"{row['nama_produk']} - sisa {int(row['stok_gudang'])} {row['satuan']}")

    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader("Tren Revenue Bulanan")
        if not orders.empty:
            revenue_month = orders.groupby("bulan", as_index=False)["total_tagihan"].sum()
            fig = px.bar(revenue_month, x="bulan", y="total_tagihan", text_auto=".2s")
            fig.update_layout(height=320, xaxis_title="Bulan", yaxis_title="Revenue", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    with chart2:
        st.subheader("Status Purchase Order")
        if not orders.empty:
            status_df = orders.groupby("status_po", as_index=False).size()
            fig = px.pie(status_df, names="status_po", values="size", hole=0.45)
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)


elif pilihan_menu == "Manajemen Stok Gudang":
    st.title("📦 Manajemen Stok & Aset Gudang")
    tab_stok1, tab_stok2, tab_stok3 = st.tabs(
        ["📋 Katalog & Ringkasan", "➕ Tambah Produk Baru", "📝 Ubah / Hapus Produk"]
    )

    with tab_stok1:
        if products.empty:
            st.info("Katalog produk kosong.")
        else:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total SKU", products["sku"].nunique())
            m2.metric("Total Stok Fisik", f"{int(products['stok_gudang'].sum()):,}".replace(",", "."))
            m3.metric("Nilai Aset Gudang", money(products["total_nilai_aset"].sum()))
            m4.metric("Kategori Terbesar", products.groupby("kategori")["stok_gudang"].sum().idxmax())
            m5.metric("SKU Stok Kritis", int((products["stok_gudang"] < STOK_MINIMUM).sum()))

            st.divider()
            fc1, fc2 = st.columns([3, 1])
            with fc1:
                search = st.text_input("Cari produk", placeholder="Nama produk atau SKU")
            with fc2:
                kategori = st.selectbox("Kategori", ["Semua"] + sorted(products["kategori"].dropna().unique().tolist()))

            shown = products.copy()
            if search:
                needle = search.lower()
                shown = shown[
                    shown["nama_produk"].str.lower().str.contains(needle)
                    | shown["sku"].str.lower().str.contains(needle)
                ]
            if kategori != "Semua":
                shown = shown[shown["kategori"] == kategori]

            g1, g2 = st.columns(2)
            with g1:
                df_k = products.groupby("kategori", as_index=False)["stok_gudang"].sum()
                fig = px.pie(df_k, names="kategori", values="stok_gudang", hole=0.4)
                fig.update_layout(height=320)
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                df_a = products.groupby("kategori", as_index=False)["total_nilai_aset"].sum()
                fig = px.bar(df_a, x="kategori", y="total_nilai_aset", text_auto=".2s", color="kategori")
                fig.update_layout(height=320, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Katalog Produk Lengkap")
            table = format_money_columns(shown, ["harga_dasar", "total_nilai_aset"])
            table["status_stok"] = shown["stok_gudang"].apply(
                lambda x: "Kritis" if x <= 3 else ("Menipis" if x < STOK_MINIMUM else "Aman")
            )
            st.dataframe(
                table[["sku", "nama_produk", "kategori", "harga_dasar", "stok_gudang", "satuan", "total_nilai_aset", "status_stok"]],
                use_container_width=True,
                hide_index=True,
            )

    with tab_stok2:
        st.subheader("➕ Tambah Produk Baru ke Katalog")
        kategori_existing = sorted(products["kategori"].dropna().unique().tolist()) if not products.empty else []
        satuan_umum = ["Kg", "Gram", "Liter", "mL", "Pcs", "Dus", "Karton", "Pak", "Botol", "Kaleng", "Sak", "Lusin", "Roll", "Meter", "box", "kg", "pcs"]

        with st.form("form_tambah_produk", clear_on_submit=True):
            fp1, fp2 = st.columns(2)
            with fp1:
                sku_baru = st.text_input("SKU *")
                nama_produk_baru = st.text_input("Nama Produk *")
            with fp2:
                opsi_kat = kategori_existing + ["Ketik kategori baru"]
                pilihan_kat = st.selectbox("Kategori *", opsi_kat)
                kategori_baru = st.text_input("Nama Kategori Baru *") if pilihan_kat == "Ketik kategori baru" else pilihan_kat
                satuan_pilih = st.selectbox("Satuan *", satuan_umum)

            fh1, fh2 = st.columns(2)
            with fh1:
                harga_dasar_baru = st.number_input("Harga Dasar (Rp) *", min_value=0.0, step=500.0)
            with fh2:
                stok_awal = st.number_input("Stok Awal *", min_value=0, step=1)

            if st.form_submit_button("Simpan Produk", type="primary"):
                if not sku_baru.strip() or not nama_produk_baru.strip() or not kategori_baru.strip() or harga_dasar_baru <= 0:
                    st.error("SKU, nama, kategori, dan harga dasar wajib valid.")
                else:
                    try:
                        api_post(
                            "/api/products",
                            {
                                "sku": sku_baru.strip().upper(),
                                "nama_produk": nama_produk_baru.strip(),
                                "kategori": kategori_baru.strip(),
                                "satuan": satuan_pilih,
                                "harga_dasar": harga_dasar_baru,
                                "stok_gudang": stok_awal,
                            },
                        )
                        st.success("Produk berhasil ditambahkan.")
                        clear_and_rerun()
                    except Exception as exc:
                        st.error(f"Gagal menyimpan: {exc}")

        st.divider()
        st.subheader("📥 Import Produk via CSV")
        template_csv = "sku,nama_produk,kategori,satuan,harga_dasar,stok_gudang\nBRS-001,Beras Premium 5kg,Bahan Pokok,Sak,85000,100\n"
        st.download_button("Download Template CSV", data=template_csv, file_name="template_produk.csv", mime="text/csv")
        uploaded_csv = st.file_uploader("Upload CSV Produk", type=["csv"])
        if uploaded_csv is not None:
            imported = pd.read_csv(uploaded_csv)
            st.dataframe(imported.head(10), use_container_width=True, hide_index=True)
            if st.button("Mulai Import", type="primary"):
                berhasil = 0
                gagal = []
                for _, row in imported.iterrows():
                    try:
                        api_post(
                            "/api/products",
                            {
                                "sku": str(row["sku"]).strip().upper(),
                                "nama_produk": str(row["nama_produk"]).strip(),
                                "kategori": str(row["kategori"]).strip(),
                                "satuan": str(row["satuan"]).strip(),
                                "harga_dasar": float(row["harga_dasar"]),
                                "stok_gudang": int(row["stok_gudang"]),
                            },
                        )
                        berhasil += 1
                    except Exception as exc:
                        gagal.append(f"{row.get('sku', '-')}: {exc}")
                st.success(f"{berhasil} produk berhasil diimport.")
                if gagal:
                    st.warning("\n".join(gagal))
                clear_and_rerun()

    with tab_stok3:
        if products.empty:
            st.info("Katalog produk kosong.")
        else:
            st.subheader("📝 Ubah Data Produk")
            opsi_edit = (products["sku"] + " - " + products["nama_produk"]).tolist()
            produk_dipilih = st.selectbox("Pilih produk", opsi_edit)
            sku_sel = produk_dipilih.split(" - ")[0]
            row = products[products["sku"] == sku_sel].iloc[0]

            with st.form("form_update_produk"):
                eu1, eu2 = st.columns(2)
                with eu1:
                    nama_edit = st.text_input("Nama Produk *", value=row["nama_produk"])
                    kat_edit = st.text_input("Kategori *", value=row["kategori"] or "")
                    satuan_edit = st.text_input("Satuan *", value=row["satuan"])
                with eu2:
                    stok_baru = st.number_input("Stok Gudang *", min_value=0, value=int(row["stok_gudang"]))
                    harga_baru = st.number_input("Harga Dasar (Rp) *", min_value=0.0, value=float(row["harga_dasar"]), step=500.0)

                if st.form_submit_button("Simpan Perubahan", type="primary"):
                    try:
                        api_patch(
                            f"/api/products/{int(row['product_id'])}",
                            {
                                "nama_produk": nama_edit.strip(),
                                "kategori": kat_edit.strip(),
                                "satuan": satuan_edit.strip(),
                                "harga_dasar": harga_baru,
                                "stok_gudang": stok_baru,
                            },
                        )
                        st.success("Produk berhasil diperbarui.")
                        clear_and_rerun()
                    except Exception as exc:
                        st.error(f"Gagal: {exc}")

            st.divider()
            st.subheader("🗑️ Hapus Produk dari Katalog")
            st.warning("Produk yang sudah masuk PO tidak dapat dihapus.")
            confirm = st.checkbox(f"Saya yakin ingin menghapus {produk_dipilih}")
            if st.button("Hapus Produk", type="primary", disabled=not confirm):
                try:
                    api_delete(f"/api/products/{int(row['product_id'])}")
                    st.success("Produk berhasil dihapus.")
                    clear_and_rerun()
                except Exception as exc:
                    st.error(f"Gagal: {exc}")


elif pilihan_menu == "Manajemen Klien B2B":
    st.title("🏢 Manajemen Klien B2B")
    tab1, tab2, tab3 = st.tabs(["📋 Daftar Klien", "➕ Tambah Klien Baru", "👥 Manajemen Pengguna"])

    with tab1:
        st.subheader("Semua Perusahaan Terdaftar")
        if companies.empty:
            st.info("Belum ada klien.")
        else:
            company_stats = companies.copy()
            order_stats = orders.groupby("company", as_index=False).agg(jumlah_po=("po_id", "count"), total_transaksi=("total_tagihan", "sum")) if not orders.empty else pd.DataFrame(columns=["company", "jumlah_po", "total_transaksi"])
            user_stats = users.groupby("company", as_index=False).size().rename(columns={"size": "jumlah_user"}) if not users.empty else pd.DataFrame(columns=["company", "jumlah_user"])
            company_stats = company_stats.merge(order_stats, left_on="nama_perusahaan", right_on="company", how="left")
            company_stats = company_stats.merge(user_stats, left_on="nama_perusahaan", right_on="company", how="left", suffixes=("", "_user"))
            company_stats[["jumlah_po", "total_transaksi", "jumlah_user"]] = company_stats[["jumlah_po", "total_transaksi", "jumlah_user"]].fillna(0)

            km1, km2, km3, km4 = st.columns(4)
            km1.metric("Total Klien", len(company_stats))
            km2.metric("Total Pengguna", int(company_stats["jumlah_user"].sum()))
            km3.metric("Total PO", int(company_stats["jumlah_po"].sum()))
            km4.metric("Total Transaksi", money(company_stats["total_transaksi"].sum()))

            df_ind = company_stats["kategori_industri"].value_counts().reset_index()
            df_ind.columns = ["Industri", "Jumlah"]
            fig = px.bar(df_ind, x="Industri", y="Jumlah", color="Industri", title="Distribusi Klien per Segmen Industri")
            fig.update_layout(showlegend=False, height=280)
            st.plotly_chart(fig, use_container_width=True)

            table = format_money_columns(company_stats, ["limit_kredit", "total_transaksi"])
            table["bergabung"] = company_stats["created_at"].dt.date
            st.dataframe(
                table[["nama_perusahaan", "kategori_industri", "npwp", "limit_kredit", "jumlah_user", "jumlah_po", "total_transaksi", "bergabung"]],
                use_container_width=True,
                hide_index=True,
            )

    with tab2:
        st.subheader("Daftarkan Klien B2B Baru")
        with st.form("form_tambah_klien"):
            tc1, tc2 = st.columns(2)
            with tc1:
                nama_perusahaan = st.text_input("Nama Perusahaan *")
                npwp = st.text_input("NPWP")
            with tc2:
                kategori_ind = st.selectbox("Segmen Industri *", ["Hotel", "Restaurant", "Cafe", "Catering"])
                limit_kredit = st.number_input("Limit Kredit (Rp)", min_value=0.0, step=1_000_000.0)
            if st.form_submit_button("Daftarkan Klien", type="primary"):
                try:
                    api_post(
                        "/api/companies",
                        {
                            "nama_perusahaan": nama_perusahaan.strip(),
                            "npwp": npwp.strip() or None,
                            "kategori_industri": kategori_ind,
                            "limit_kredit": limit_kredit,
                        },
                    )
                    st.success("Klien berhasil didaftarkan.")
                    clear_and_rerun()
                except Exception as exc:
                    st.error(f"Gagal: {exc}")

    with tab3:
        st.subheader("Pengguna per Perusahaan")
        if companies.empty:
            st.info("Belum ada perusahaan.")
        else:
            company_name = st.selectbox("Pilih Perusahaan", companies["nama_perusahaan"].tolist())
            company_id = int(companies[companies["nama_perusahaan"] == company_name]["company_id"].iloc[0])
            company_users = users[users["company_id"] == company_id] if not users.empty else pd.DataFrame()
            col_u1, col_u2 = st.columns([2, 1])
            with col_u1:
                st.markdown(f"Staff terdaftar di {company_name}")
                if company_users.empty:
                    st.info("Belum ada pengguna.")
                else:
                    st.dataframe(company_users[["user_id", "nama_lengkap", "email", "peran"]], use_container_width=True, hide_index=True)
            with col_u2:
                st.markdown("Tambah Pengguna")
                with st.form("form_tambah_user"):
                    nama_user = st.text_input("Nama Lengkap *")
                    email_user = st.text_input("Email *")
                    peran_user = st.selectbox("Peran", ["Chef", "Procurement", "Finance_Manager"])
                    if st.form_submit_button("Tambah", type="primary"):
                        try:
                            api_post(
                                "/api/users",
                                {
                                    "company_id": company_id,
                                    "nama_lengkap": nama_user.strip(),
                                    "email": email_user.strip(),
                                    "peran": peran_user,
                                },
                            )
                            st.success("Pengguna berhasil ditambahkan.")
                            clear_and_rerun()
                        except Exception as exc:
                            st.error(f"Gagal: {exc}")


elif pilihan_menu == "Manajemen Pesanan (PO)":
    st.title("🛒 Manajemen Purchase Order (PO)")
    status_list = ["Pending_Approval", "Approved", "Processing", "Delivered", "Rejected", "Cancelled"]
    tab_po1, tab_po2, tab_po3 = st.tabs(["📋 Daftar PO", "➕ Buat PO Baru", "🔄 Update Status PO"])

    with tab_po1:
        st.subheader("Semua Purchase Order")
        filter_status = st.multiselect("Filter Status", status_list, default=["Pending_Approval", "Approved", "Processing"])
        shown = orders.copy()
        if filter_status and not shown.empty:
            shown = shown[shown["status_po"].isin(filter_status)]

        if shown.empty:
            st.info("Tidak ada PO dengan filter yang dipilih.")
        else:
            pm1, pm2, pm3 = st.columns(3)
            pm1.metric("Total PO Tampil", len(shown))
            pm2.metric("Total Nilai", money(shown["total_tagihan"].sum()))
            pm3.metric("Pending Approval", int((shown["status_po"] == "Pending_Approval").sum()))

            table = shown.copy()
            table["tanggal_dipesan"] = table["tanggal_dipesan"].dt.date
            table = format_money_columns(table, ["total_tagihan"])
            st.dataframe(
                table[["po_id", "company", "pembuat", "status_po", "metode_pembayaran", "total_tagihan", "tanggal_dipesan"]],
                use_container_width=True,
                hide_index=True,
            )

            st.divider()
            st.subheader("Detail Item PO")
            po_id = st.selectbox("Pilih PO", shown["po_id"].tolist())
            detail = order_detail(po_id)
            if detail.empty:
                st.info("Detail tidak ditemukan.")
            else:
                detail_table = format_money_columns(detail, ["harga_final", "subtotal"])
                st.dataframe(detail_table, use_container_width=True, hide_index=True)

    with tab_po2:
        st.subheader("Buat Purchase Order Baru")
        if companies.empty or products.empty:
            st.warning("Perusahaan dan produk harus tersedia.")
        else:
            with st.form("form_buat_po"):
                ci1, ci2, ci3 = st.columns(3)
                with ci1:
                    company_name = st.selectbox("Perusahaan Klien *", companies["nama_perusahaan"].tolist())
                    company_id = int(companies[companies["nama_perusahaan"] == company_name]["company_id"].iloc[0])
                company_users = users[users["company_id"] == company_id] if not users.empty else pd.DataFrame()
                with ci2:
                    if company_users.empty:
                        st.caption("Klien belum punya pengguna.")
                        user_id = None
                    else:
                        user_name = st.selectbox("Dipesan Oleh", company_users["nama_lengkap"].tolist())
                        user_id = int(company_users[company_users["nama_lengkap"] == user_name]["user_id"].iloc[0])
                with ci3:
                    metode_bayar = st.selectbox("Metode Pembayaran *", ["Cash", "Tempo_30_Hari"])

                available_products = products[products["stok_gudang"] > 0]
                options = ["-- Pilih Produk --"] + (available_products["sku"] + " | " + available_products["nama_produk"]).tolist()
                items = []
                total_po = 0.0
                for i in range(1, 7):
                    r1, r2, r3 = st.columns([5, 2, 2])
                    with r1:
                        selected_product = st.selectbox(f"Produk {i}", options, key=f"po_prod_{i}")
                    with r2:
                        qty = st.number_input(f"Qty {i}", min_value=0, value=0, step=1, key=f"po_qty_{i}")
                    with r3:
                        if selected_product != "-- Pilih Produk --" and qty > 0:
                            sku = selected_product.split(" | ")[0]
                            product = available_products[available_products["sku"] == sku].iloc[0]
                            if qty > int(product["stok_gudang"]):
                                st.error(f"Stok hanya {int(product['stok_gudang'])}")
                            else:
                                subtotal = float(product["harga_dasar"]) * qty
                                total_po += subtotal
                                st.metric(f"Sub {i}", money(subtotal))
                                items.append(
                                    {
                                        "product_id": int(product["product_id"]),
                                        "kuantitas": qty,
                                        "harga_final": float(product["harga_dasar"]),
                                    }
                                )

                st.markdown(f"### Total Tagihan: {money(total_po)}")
                if st.form_submit_button("Buat Purchase Order", type="primary"):
                    if not user_id:
                        st.error("Perusahaan ini belum punya user pemesan.")
                    elif not items:
                        st.error("Minimal pilih 1 produk.")
                    else:
                        try:
                            created = api_post(
                                "/api/orders",
                                {
                                    "company_id": company_id,
                                    "dibuat_oleh": user_id,
                                    "metode_pembayaran": metode_bayar,
                                    "total_tagihan": total_po,
                                    "items": items,
                                },
                            )
                            st.success(f"PO #{created['po_id']} berhasil dibuat.")
                            clear_and_rerun()
                        except Exception as exc:
                            st.error(f"Gagal: {exc}")

    with tab_po3:
        st.subheader("Update Status Purchase Order")
        active_orders = orders[~orders["status_po"].isin(["Delivered", "Cancelled"])] if not orders.empty else pd.DataFrame()
        if active_orders.empty:
            st.info("Tidak ada PO aktif.")
        else:
            po_id = st.selectbox("Pilih PO", active_orders["po_id"].tolist(), key="status_po_id")
            selected = active_orders[active_orders["po_id"] == po_id].iloc[0]
            status_baru = st.selectbox("Status Baru", [s for s in status_list if s != selected["status_po"]])
            if st.button("Update Status", type="primary"):
                try:
                    api_patch(f"/api/orders/{po_id}/status", {"status_po": status_baru})
                    st.success(f"PO #{po_id} menjadi {status_baru}.")
                    clear_and_rerun()
                except Exception as exc:
                    st.error(f"Gagal: {exc}")


elif pilihan_menu == "Laporan & Analitik":
    st.title("📈 Laporan & Analitik Penjualan")
    lc1, lc2 = st.columns(2)
    with lc1:
        tgl_mulai = st.date_input("Dari Tanggal", value=date(date.today().year, 1, 1))
    with lc2:
        tgl_akhir = st.date_input("Sampai Tanggal", value=date.today())

    if tgl_mulai > tgl_akhir:
        st.error("Tanggal mulai tidak boleh lebih besar.")
        st.stop()

    report = api_get(f"/api/reports/sales?start={tgl_mulai.isoformat()}&end={tgl_akhir.isoformat()}")
    report_summary = report["summary"]
    monthly = pd.DataFrame(report["monthly"])
    segments = pd.DataFrame(report["segments"])
    top_products = pd.DataFrame(report["top_products"])
    top_clients = pd.DataFrame(report["top_clients"])
    transactions = pd.DataFrame(report["transactions"])

    sk1, sk2, sk3, sk4 = st.columns(4)
    sk1.metric("Total PO", int(report_summary["total_po"]))
    sk2.metric("Total Revenue", money(report_summary["total_revenue"]))
    sk3.metric("Rata-rata Nilai PO", money(report_summary["avg_po"]))
    sk4.metric("Klien Aktif", int(report_summary["klien_aktif"]))

    st.divider()
    gc1, gc2 = st.columns(2)
    with gc1:
        st.subheader("Revenue per Bulan")
        if monthly.empty:
            st.info("Tidak ada data.")
        else:
            fig = px.bar(monthly, x="bulan", y="revenue", text_auto=".2s")
            fig.update_layout(height=310)
            st.plotly_chart(fig, use_container_width=True)
    with gc2:
        st.subheader("Revenue per Segmen Industri")
        if segments.empty:
            st.info("Tidak ada data.")
        else:
            fig = px.pie(segments, names="segmen", values="revenue", hole=0.4)
            fig.update_layout(height=310)
            st.plotly_chart(fig, use_container_width=True)

    gc3, gc4 = st.columns(2)
    with gc3:
        st.subheader("Top 10 Produk Terlaris")
        if top_products.empty:
            st.info("Tidak ada data.")
        else:
            fig = px.bar(top_products, x="total_qty", y="produk", orientation="h", color="kategori")
            fig.update_layout(height=380, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
    with gc4:
        st.subheader("Top 10 Klien")
        if top_clients.empty:
            st.info("Tidak ada data.")
        else:
            fig = px.bar(top_clients, x="revenue", y="klien", orientation="h", color="segmen")
            fig.update_layout(height=380, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Tabel Transaksi Lengkap")
    if transactions.empty:
        st.info("Tidak ada transaksi pada periode ini.")
    else:
        table = format_money_columns(transactions, ["total_tagihan"])
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Laporan CSV",
            data=transactions.to_csv(index=False).encode("utf-8"),
            file_name=f"laporan_{tgl_mulai}_sd_{tgl_akhir}.csv",
            mime="text/csv",
        )


elif pilihan_menu == "Portal Pembelian (User)":
    st.markdown(
        """
        <div class="portal-header">
          <h1 style="margin:0;font-size:2rem;">🛍️ Portal Pembelian HoReCa</h1>
          <p style="margin:4px 0 0;opacity:0.88;font-size:1rem;">
            Selamat datang di katalog grosir B2B - pilih produk, tambahkan ke keranjang, lalu checkout.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.portal_user_id:
        st.markdown("#### 👤 Masuk atau Daftarkan Perusahaan Anda")
        tab_login, tab_register = st.tabs(["🔑 Login", "🏢 Daftar Perusahaan Baru"])

        with tab_login:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown("Masukkan email yang sudah terdaftar di sistem untuk melanjutkan.")
            with st.form("form_login_portal"):
                email_login = st.text_input("📧 Alamat Email *", placeholder="contoh: budi@hotelmelati.com")
                submitted_login = st.form_submit_button("🔑 Masuk ke Portal", type="primary", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if submitted_login:
                if not email_login.strip():
                    st.error("Email tidak boleh kosong.")
                elif users.empty:
                    st.error("Belum ada pengguna terdaftar.")
                else:
                    matched = users[users["email"].str.lower() == email_login.strip().lower()]
                    if matched.empty:
                        st.error("Email tidak ditemukan. Daftarkan perusahaan baru atau minta admin menambahkan akun.")
                    else:
                        row = matched.iloc[0]
                        st.session_state.portal_user_id = int(row["user_id"])
                        st.session_state.portal_user_name = row["nama_lengkap"]
                        st.session_state.portal_company_id = int(row["company_id"])
                        st.session_state.portal_company_name = row["company"]
                        st.success(f"✅ Selamat datang, **{row['nama_lengkap']}** dari **{row['company']}**.")
                        st.rerun()

            st.divider()
            st.caption("Belum punya akun? Gunakan tab Daftar Perusahaan Baru.")

        with tab_register:
            st.markdown("Daftarkan perusahaan dan akun pengguna pertama. Setelah berhasil, akun langsung login.")
            with st.form("form_register_portal", clear_on_submit=False):
                st.markdown("#### 🏢 Data Perusahaan")
                rc1, rc2 = st.columns(2)
                with rc1:
                    reg_nama_perusahaan = st.text_input("Nama Perusahaan *", placeholder="PT. Hotel Bintang Lima")
                    reg_npwp = st.text_input("NPWP", placeholder="XX.XXX.XXX.X-XXX.XXX")
                with rc2:
                    reg_kategori = st.selectbox("Segmen Industri *", ["Hotel", "Restaurant", "Cafe", "Catering"])
                    reg_limit_kredit = st.number_input("Limit Kredit (Rp)", min_value=0.0, step=1_000_000.0)

                st.markdown("#### 👤 Data Pengguna Pertama")
                ru1, ru2 = st.columns(2)
                with ru1:
                    reg_nama_user = st.text_input("Nama Lengkap *", placeholder="Budi Santoso")
                    reg_email = st.text_input("Email *", placeholder="budi@hotelmelati.com")
                with ru2:
                    reg_peran = st.selectbox("Jabatan / Peran *", ["Procurement", "Chef", "Finance_Manager"])

                submitted_register = st.form_submit_button(
                    "🚀 Daftarkan Perusahaan & Buat Akun", type="primary", use_container_width=True
                )

            if submitted_register:
                errors = []
                if not reg_nama_perusahaan.strip():
                    errors.append("Nama perusahaan wajib diisi.")
                if not reg_nama_user.strip():
                    errors.append("Nama pengguna wajib diisi.")
                if not reg_email.strip() or "@" not in reg_email:
                    errors.append("Email wajib valid.")
                if not users.empty and reg_email.strip().lower() in users["email"].str.lower().tolist():
                    errors.append("Email sudah terdaftar.")
                if not companies.empty and reg_nama_perusahaan.strip().lower() in companies["nama_perusahaan"].str.lower().tolist():
                    errors.append("Perusahaan sudah terdaftar. Minta admin perusahaan menambahkan akun.")

                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        company = api_post(
                            "/api/companies",
                            {
                                "nama_perusahaan": reg_nama_perusahaan.strip(),
                                "npwp": reg_npwp.strip() or None,
                                "kategori_industri": reg_kategori,
                                "limit_kredit": reg_limit_kredit,
                            },
                        )
                        user = api_post(
                            "/api/users",
                            {
                                "company_id": company["company_id"],
                                "nama_lengkap": reg_nama_user.strip(),
                                "email": reg_email.strip().lower(),
                                "peran": reg_peran,
                            },
                        )
                        st.session_state.portal_user_id = int(user["user_id"])
                        st.session_state.portal_user_name = user["nama_lengkap"]
                        st.session_state.portal_company_id = int(company["company_id"])
                        st.session_state.portal_company_name = company["nama_perusahaan"]
                        st.cache_data.clear()
                        st.success("🎉 Perusahaan dan akun berhasil dibuat.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal mendaftar: {exc}")

    else:
        col_welcome, col_logout = st.columns([4, 1])
        with col_welcome:
            st.success(
                f"✅ Login sebagai **{st.session_state.portal_user_name}** - "
                f"{st.session_state.portal_company_name}"
            )
        with col_logout:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.portal_user_id = None
                st.session_state.portal_company_id = None
                st.session_state.portal_user_name = ""
                st.session_state.portal_company_name = ""
                st.session_state.cart = {}
                st.rerun()

        tab_katalog, tab_keranjang, tab_riwayat = st.tabs(
            ["🏪 Katalog Produk", "🛒 Keranjang & Checkout", "📜 Riwayat Pesanan Saya"]
        )

        with tab_katalog:
            if products.empty:
                st.info("Katalog produk kosong. Hubungi admin.")
            else:
                filter_col1, filter_col2, filter_col3 = st.columns([3, 2, 1])
                with filter_col1:
                    cari_produk = st.text_input("🔍 Cari produk", placeholder="Nama produk atau SKU")
                with filter_col2:
                    kat_list = ["Semua Kategori"] + sorted(products["kategori"].dropna().unique().tolist())
                    filter_kat = st.selectbox("Kategori", kat_list)
                with filter_col3:
                    available_only = st.checkbox("Stok tersedia saja", value=True)

                filtered = products.copy()
                if cari_produk:
                    needle = cari_produk.lower()
                    filtered = filtered[
                        filtered["nama_produk"].str.lower().str.contains(needle)
                        | filtered["sku"].str.lower().str.contains(needle)
                    ]
                if filter_kat != "Semua Kategori":
                    filtered = filtered[filtered["kategori"] == filter_kat]
                if available_only:
                    filtered = filtered[filtered["stok_gudang"] > 0]

                st.caption(f"Menampilkan {len(filtered)} produk")
                if filtered.empty:
                    st.info("Tidak ada produk yang cocok dengan filter.")
                else:
                    cols_per_row = 3
                    for start in range(0, len(filtered), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for col, (_, product) in zip(cols, filtered.iloc[start:start + cols_per_row].iterrows()):
                            pid = int(product["product_id"])
                            nama = product["nama_produk"]
                            sku = product["sku"]
                            kategori = product["kategori"] or ""
                            satuan = product["satuan"]
                            harga = float(product["harga_dasar"])
                            stok = int(product["stok_gudang"])

                            if stok == 0:
                                badge = '<span class="stok-badge-habis">❌ Habis</span>'
                            elif stok <= 10:
                                badge = f'<span class="stok-badge-menipis">⚠️ Sisa {stok} {satuan}</span>'
                            else:
                                badge = f'<span class="stok-badge-aman">✅ Stok {stok} {satuan}</span>'

                            with col:
                                st.markdown(
                                    f"""
                                    <div class="product-card">
                                      <div class="product-img-wrap">
                                        <img src="{product_image_url(product)}" alt="{nama}" loading="lazy" />
                                      </div>
                                      <div class="product-body">
                                        <div class="product-name">{nama}</div>
                                        <div class="product-sku">SKU: {sku} · {kategori}</div>
                                        <div class="product-price">{money(harga)}</div>
                                        <div class="product-satuan">per {satuan}</div>
                                        {badge}
                                      </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                                if stok > 0:
                                    qty = st.number_input(
                                        f"Jumlah ({satuan})",
                                        min_value=1,
                                        max_value=stok,
                                        value=1,
                                        step=1,
                                        key=f"qty_katalog_{pid}",
                                        label_visibility="collapsed",
                                    )
                                    if st.button("🛒 Tambah ke Keranjang", key=f"btn_add_{pid}", use_container_width=True):
                                        if pid in st.session_state.cart:
                                            new_qty = st.session_state.cart[pid]["qty"] + qty
                                            if new_qty > stok:
                                                st.error(f"Maksimal {stok} {satuan}.")
                                            else:
                                                st.session_state.cart[pid]["qty"] = new_qty
                                                st.success(f"✅ Diperbarui: {nama} x {new_qty}")
                                        else:
                                            st.session_state.cart[pid] = {
                                                "nama": nama,
                                                "harga": harga,
                                                "qty": qty,
                                                "satuan": satuan,
                                                "stok": stok,
                                                "kategori": kategori,
                                            }
                                            st.success(f"✅ {nama} ditambahkan.")
                                        st.rerun()
                                else:
                                    st.button("Stok Habis", disabled=True, use_container_width=True, key=f"btn_habis_{pid}")

        with tab_keranjang:
            st.subheader("🛒 Keranjang Belanja Anda")
            if not st.session_state.cart:
                st.info("Keranjang Anda masih kosong. Tambahkan produk dari tab Katalog Produk.")
            else:
                items_to_delete = []
                total_belanja = 0.0
                for pid, item in list(st.session_state.cart.items()):
                    subtotal = item["qty"] * item["harga"]
                    total_belanja += subtotal
                    c_info, c_qty, c_sub, c_del = st.columns([4, 2, 2, 1])
                    with c_info:
                        st.markdown(f"**{item['nama']}**")
                        st.caption(f"{money(item['harga'])} / {item['satuan']}")
                    with c_qty:
                        new_qty = st.number_input(
                            "Qty",
                            min_value=1,
                            max_value=item["stok"],
                            value=item["qty"],
                            step=1,
                            key=f"cart_qty_{pid}",
                            label_visibility="collapsed",
                        )
                        if new_qty != item["qty"]:
                            st.session_state.cart[pid]["qty"] = new_qty
                            st.rerun()
                    with c_sub:
                        st.markdown(f"**{money(new_qty * item['harga'])}**")
                    with c_del:
                        if st.button("🗑️", key=f"del_{pid}", help="Hapus item"):
                            items_to_delete.append(pid)
                    st.divider()

                for pid in items_to_delete:
                    del st.session_state.cart[pid]
                if items_to_delete:
                    st.rerun()

                st.markdown(
                    f"""
                    <div class="cart-total-box">
                      <div style="font-size:0.9rem;opacity:0.85;margin-bottom:4px;">Total Belanja ({cart_total_items()} item)</div>
                      <div style="font-size:1.8rem;font-weight:800;">{money(total_belanja)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.divider()
                st.subheader("📋 Informasi Checkout")
                st.info(
                    f"Memesan atas nama: {st.session_state.portal_user_name} - "
                    f"{st.session_state.portal_company_name}"
                )

                with st.form("form_checkout_portal"):
                    co1, co2 = st.columns(2)
                    with co1:
                        metode_checkout = st.selectbox("Metode Pembayaran *", ["Cash", "Tempo_30_Hari"])
                    with co2:
                        st.text_input("Catatan Tambahan", placeholder="Contoh: mohon kirim pagi hari")

                    st.markdown("#### 🧾 Ringkasan Pesanan")
                    for item in st.session_state.cart.values():
                        st.markdown(
                            f"- **{item['nama']}** x {item['qty']} {item['satuan']} = "
                            f"{money(item['qty'] * item['harga'])}"
                        )
                    st.markdown(f"**Total: {money(total_belanja)}**")

                    submitted_checkout = st.form_submit_button(
                        f"✅ Konfirmasi & Kirim Pesanan - {money(total_belanja)}",
                        type="primary",
                        use_container_width=True,
                    )

                if submitted_checkout:
                    try:
                        payload_items = [
                            {
                                "product_id": int(pid),
                                "kuantitas": item["qty"],
                                "harga_final": item["harga"],
                            }
                            for pid, item in st.session_state.cart.items()
                        ]
                        created = api_post(
                            "/api/orders",
                            {
                                "company_id": st.session_state.portal_company_id,
                                "dibuat_oleh": st.session_state.portal_user_id,
                                "metode_pembayaran": metode_checkout,
                                "total_tagihan": total_belanja,
                                "items": payload_items,
                            },
                        )
                        st.session_state.cart = {}
                        st.cache_data.clear()
                        st.success(f"🎉 Pesanan PO #{created['po_id']} berhasil dikirim. Status: Pending Approval.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal membuat pesanan: {exc}")

        with tab_riwayat:
            st.subheader("📜 Riwayat Pesanan Saya")
            company_orders = pd.DataFrame(
                api_get(f"/api/companies/{st.session_state.portal_company_id}/orders")
            )
            if company_orders.empty:
                st.info("Belum ada pesanan dari perusahaan Anda.")
            else:
                company_orders["total_tagihan"] = pd.to_numeric(company_orders["total_tagihan"])
                company_orders["tanggal_dipesan"] = pd.to_datetime(company_orders["tanggal_dipesan"])

                rh1, rh2, rh3, rh4 = st.columns(4)
                rh1.metric("Total PO", len(company_orders))
                rh2.metric("Total Belanja", money(company_orders["total_tagihan"].sum()))
                rh3.metric(
                    "Pending / Proses",
                    int(company_orders["status_po"].isin(["Pending_Approval", "Approved", "Processing"]).sum()),
                )
                rh4.metric("Terkirim", int((company_orders["status_po"] == "Delivered").sum()))

                st.divider()
                for _, po_row in company_orders.iterrows():
                    with st.expander(
                        f"PO #{po_row['po_id']} - {po_row['tanggal_dipesan'].date()} - "
                        f"{money(po_row['total_tagihan'])} - {po_row['status_po']}"
                    ):
                        detail = order_detail(int(po_row["po_id"]))
                        d1, d2 = st.columns([3, 1])
                        with d1:
                            if detail.empty:
                                st.caption("Detail item tidak tersedia.")
                            else:
                                shown = format_money_columns(detail, ["harga_final", "subtotal"])
                                st.dataframe(shown, use_container_width=True, hide_index=True)
                        with d2:
                            st.markdown(f"**Status:** {po_row['status_po']}")
                            st.markdown(f"**Pembayaran:** {po_row['metode_pembayaran']}")
                            st.markdown(f"**Dipesan oleh:** {po_row['pembuat']}")
                            st.markdown(f"**Total:** {money(po_row['total_tagihan'])}")


elif pilihan_menu == "API Monitor":
    st.title("API Monitor")
    health = api_get("/api/health")
    st.success("API dan PostgreSQL dapat diakses.")
    st.json({"api_base_url": API_BASE_URL, "web_url": WEB_URL, "health": health, "summary": summary})

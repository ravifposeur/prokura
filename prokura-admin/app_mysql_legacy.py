import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import os
from datetime import datetime, date

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Horeca Supply Management",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    .stAlert { border-radius: 8px; }
    div[data-testid="stExpander"] { border: 1px solid #ffc107; border-radius: 8px; }

    /* === PORTAL PEMBELIAN STYLES === */
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
    .portal-header {
        background: linear-gradient(135deg, #0077B6 0%, #023e8a 100%);
        color: white;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
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
""", unsafe_allow_html=True)

# ==========================================
# KONEKSI DATABASE
# ==========================================
@st.cache_resource
def init_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "hanyatamayangbisa16"),
        database=os.getenv("MYSQL_DATABASE", "wise"),
    )

try:
    conn = init_connection()
except Exception as e:
    st.error(f"Koneksi Database Gagal: {e}")
    st.stop()


def run_query(query, params=None):
    """Menjalankan SELECT query dan mengembalikan DataFrame."""
    conn.ping(reconnect=True)
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(query, params or ())
        return pd.DataFrame(cursor.fetchall())


def execute_query(query, params=None):
    """Menjalankan INSERT/UPDATE/DELETE dan mengembalikan lastrowid."""
    conn.ping(reconnect=True)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()


# ==========================================
# SESSION STATE — CART & LOGIN
# ==========================================
if 'cart' not in st.session_state:
    st.session_state.cart = {}   # {product_id: {'nama': ..., 'harga': ..., 'qty': ..., 'satuan': ..., 'stok': ...}}

if 'portal_company_id' not in st.session_state:
    st.session_state.portal_company_id = None

if 'portal_user_id' not in st.session_state:
    st.session_state.portal_user_id = None

if 'portal_company_name' not in st.session_state:
    st.session_state.portal_company_name = ""

if 'portal_user_name' not in st.session_state:
    st.session_state.portal_user_name = ""


# Helper: total item di cart
def cart_total_items():
    return sum(v['qty'] for v in st.session_state.cart.values())

def cart_total_price():
    return sum(v['qty'] * v['harga'] for v in st.session_state.cart.values())


# ==========================================
# GAMBAR PRODUK — ASET PUBLIK
# ==========================================
# Menggunakan Unsplash Source (gratis, tanpa API key).
# URL format: https://source.unsplash.com/featured/WIDTHxHEIGHT/?keyword
# Setiap keyword dipetakan ke kategori produk HoReCa.
# Jika Unsplash tidak tersedia, fallback ke Picsum berdasarkan product_id.

KATEGORI_KEYWORD = {
    "bahan pokok" : "rice,grain,staple food",
    "sayuran"     : "fresh vegetables,greens",
    "buah"        : "fresh fruits,tropical fruit",
    "daging"      : "raw meat,beef,butcher",
    "seafood"     : "fresh seafood,fish market",
    "unggas"      : "chicken,poultry,farm",
    "susu"        : "milk,dairy,fresh milk",
    "dairy"       : "cheese,dairy,yogurt",
    "telur"       : "eggs,farm eggs",
    "minyak"      : "cooking oil,olive oil",
    "bumbu"       : "spices,herbs,seasoning",
    "minuman"     : "beverage,drink,refreshment",
    "tepung"      : "flour,baking,wheat",
    "frozen"      : "frozen food,ice",
    "snack"       : "snack,chips,biscuit",
    "kemasan"     : "food packaging,container",
    "peralatan"   : "kitchen tools,cooking equipment",
    "kebersihan"  : "cleaning supplies",
    "gula"        : "sugar,sweet",
    "kopi"        : "coffee,coffee beans,cafe",
    "teh"         : "tea,herbal tea,teapot",
    "roti"        : "bread,bakery,loaf",
    "pasta"       : "pasta,noodles,italian food",
    "saus"        : "sauce,condiment",
    "kaldu"       : "broth,stock,soup",
    "keju"        : "cheese,dairy",
    "cokelat"     : "chocolate,cacao",
    "makanan"     : "food,cuisine",
}

DEFAULT_KEYWORD = "food,grocery,market"


def get_product_img_url(kategori: str, product_id: int, width: int = 400, height: int = 220) -> str:
    """
    Mengembalikan URL gambar publik berdasarkan kategori produk.
    Sumber utama: Unsplash Source (https://source.unsplash.com)
    Fallback     : Picsum Photos  (https://picsum.photos/seed/...)
    """
    keyword = DEFAULT_KEYWORD
    if kategori:
        k = kategori.lower().strip()
        for key, kw in KATEGORI_KEYWORD.items():
            if key in k:
                keyword = kw
                break

    # Unsplash Source — konsisten per (keyword + product_id) lewat parameter seed
    # Format: featured/?keyword — mengembalikan foto relevan acak tapi bisa di-cache browser
    unsplash_url = (
        f"https://source.unsplash.com/{width}x{height}/"
        f"?{keyword.replace(' ', '%20')}&sig={product_id}"
    )
    return unsplash_url


def get_picsum_url(product_id: int, width: int = 400, height: int = 220) -> str:
    """Fallback: Picsum Photos — gambar konsisten per product_id."""
    return f"https://picsum.photos/seed/prod{product_id}/{width}/{height}"


def get_product_emoji(kategori: str) -> str:
    """Tetap disimpan untuk dipakai di keranjang & riwayat pesanan (tidak perlu gambar di sana)."""
    EMOJI_MAP = {
        "bahan pokok": "🌾", "sayuran": "🥬", "buah": "🍎", "daging": "🥩",
        "seafood": "🦐", "unggas": "🍗", "susu": "🥛", "telur": "🥚",
        "minyak": "🫙", "bumbu": "🧄", "minuman": "🥤", "tepung": "🌽",
        "frozen": "🧊", "snack": "🍿", "kemasan": "📦", "peralatan": "🔪",
        "kebersihan": "🧹", "gula": "🍬", "kopi": "☕", "teh": "🍵",
        "roti": "🍞", "pasta": "🍝",
    }
    if not kategori:
        return "📦"
    k = kategori.lower().strip()
    for key, emoji in EMOJI_MAP.items():
        if key in k:
            return emoji
    return "📦"


# ==========================================
# SIDEBAR NAVIGASI
# ==========================================
with st.sidebar:
    st.title("🍽️ HoReCa Supply")
    st.caption("B2B Supply Management System")
    st.divider()
    pilihan_menu = st.radio(
        "Pilih Modul:",
        [
            "📊 Dashboard Utama",
            "📦 Manajemen Stok Gudang",
            "🏢 Manajemen Klien B2B",
            "🛒 Manajemen Pesanan (PO)",
            "📈 Laporan & Analitik",
            "🛍️ Portal Pembelian (User)",
        ]
    )
    st.divider()

    # Tampilkan keranjang di sidebar jika di Portal Pembelian
    if pilihan_menu == "🛍️ Portal Pembelian (User)":
        total_item = cart_total_items()
        if total_item > 0:
            st.markdown(f"### 🛒 Keranjang ({total_item} item)")
            for pid, item in st.session_state.cart.items():
                st.markdown(
                    f"**{item['nama'][:28]}{'...' if len(item['nama']) > 28 else ''}**  \n"
                    f"`{item['qty']} {item['satuan']}` × Rp {item['harga']:,.0f}"
                )
            st.markdown(f"**Total: Rp {cart_total_price():,.0f}**")
            if st.button("🗑️ Kosongkan Keranjang", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()
        else:
            st.caption("🛒 Keranjang kosong")

    st.caption(f"🕐 {datetime.now().strftime('%d %b %Y, %H:%M')}")


# ==============================================================
# 1. DASHBOARD UTAMA
# ==============================================================
if pilihan_menu == "📊 Dashboard Utama":
    st.title("📊 Dashboard HoReCa Supply B2B")
    st.caption("Ringkasan operasional real-time seluruh lini bisnis.")
    st.divider()

    df_kpi_klien   = run_query("SELECT COUNT(*) AS v FROM Companies")
    df_kpi_produk  = run_query("SELECT COUNT(*) AS v FROM Products")
    df_kpi_bulan   = run_query("""
        SELECT COUNT(*) AS po, COALESCE(SUM(total_tagihan),0) AS rev
        FROM PurchaseOrders
        WHERE MONTH(tanggal_dipesan)=MONTH(CURDATE())
          AND YEAR(tanggal_dipesan)=YEAR(CURDATE())
          AND status_po != 'Cancelled'
    """)
    df_kpi_pending = run_query("SELECT COUNT(*) AS v FROM PurchaseOrders WHERE status_po='Pending_Approval'")
    df_kpi_kritis  = run_query("SELECT COUNT(*) AS v FROM Products WHERE stok_gudang < 10")

    total_klien   = int(df_kpi_klien['v'].iloc[0])   if not df_kpi_klien.empty   else 0
    total_produk  = int(df_kpi_produk['v'].iloc[0])  if not df_kpi_produk.empty  else 0
    total_po_bln  = int(df_kpi_bulan['po'].iloc[0])  if not df_kpi_bulan.empty   else 0
    rev_bln       = float(df_kpi_bulan['rev'].iloc[0]) if not df_kpi_bulan.empty else 0.0
    pending       = int(df_kpi_pending['v'].iloc[0]) if not df_kpi_pending.empty else 0
    stok_kritis   = int(df_kpi_kritis['v'].iloc[0])  if not df_kpi_kritis.empty  else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🏢 Total Klien",        f"{total_klien}")
    c2.metric("📦 Total SKU",           f"{total_produk}")
    c3.metric("🛒 PO Bulan Ini",        f"{total_po_bln}")
    c4.metric("💰 Revenue Bulan Ini",  f"Rp {rev_bln:,.0f}")
    c5.metric("⚠️ Stok Kritis",         f"{stok_kritis} SKU",
              delta=f"-{stok_kritis}" if stok_kritis else None,
              delta_color="inverse")

    st.divider()
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("📋 Pesanan Terbaru")
        df_recent = run_query("""
            SELECT po.po_id AS `PO#`, c.nama_perusahaan AS Klien,
                   c.kategori_industri AS Segmen, po.status_po AS Status,
                   po.metode_pembayaran AS Pembayaran,
                   po.total_tagihan AS Total,
                   DATE(po.tanggal_dipesan) AS Tanggal
            FROM PurchaseOrders po
            JOIN Companies c ON po.company_id = c.company_id
            ORDER BY po.tanggal_dipesan DESC LIMIT 10
        """)
        if not df_recent.empty:
            df_recent['Total'] = df_recent['Total'].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada pesanan masuk.")

    with col_right:
        st.subheader("⚠️ Peringatan Stok Kritis (< 10 unit)")
        df_kritis_list = run_query("""
            SELECT nama_produk, kategori, stok_gudang, satuan
            FROM Products WHERE stok_gudang < 10 ORDER BY stok_gudang ASC LIMIT 10
        """)
        if not df_kritis_list.empty:
            for _, row in df_kritis_list.iterrows():
                stok = int(row['stok_gudang'])
                icon = "🔴" if stok <= 3 else "🟡"
                st.warning(f"{icon} **{row['nama_produk']}** — Sisa: **{stok} {row['satuan']}**")
        else:
            st.success("✅ Semua stok dalam kondisi aman.")

    st.divider()
    st.subheader("📈 Tren Revenue 6 Bulan Terakhir")
    df_trend = run_query("""
        SELECT DATE_FORMAT(tanggal_dipesan,'%Y-%m') AS Bulan,
               SUM(total_tagihan) AS Revenue, COUNT(*) AS Jumlah_PO
        FROM PurchaseOrders
        WHERE tanggal_dipesan >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
          AND status_po != 'Cancelled'
        GROUP BY DATE_FORMAT(tanggal_dipesan,'%Y-%m') ORDER BY Bulan
    """)
    if not df_trend.empty:
        fig_trend = px.bar(df_trend, x='Bulan', y='Revenue', text_auto='.2s',
                           color_discrete_sequence=['#0077B6'],
                           labels={'Revenue': 'Revenue (Rp)', 'Bulan': 'Bulan'})
        fig_trend.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Belum ada data revenue untuk ditampilkan.")


# ==============================================================
# 2. MANAJEMEN STOK GUDANG
# ==============================================================
elif pilihan_menu == "📦 Manajemen Stok Gudang":
    st.title("📦 Manajemen Stok & Aset Gudang")
    STOK_MINIMUM = 10

    tab_stok1, tab_stok2, tab_stok3 = st.tabs([
        "📋 Katalog & Ringkasan", "➕ Tambah Produk Baru", "📝 Ubah / Hapus Produk",
    ])

    with tab_stok1:
        df_produk = run_query("""
            SELECT product_id, sku, nama_produk, kategori, satuan,
                   harga_dasar, stok_gudang, (harga_dasar * stok_gudang) AS total_nilai_aset
            FROM Products ORDER BY kategori, nama_produk
        """)
        if df_produk.empty:
            st.info("Katalog produk kosong.")
        else:
            st.subheader("Ringkasan Gudang (Real-Time)")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total SKU",         df_produk['sku'].nunique())
            m2.metric("Total Stok Fisik",  f"{int(df_produk['stok_gudang'].sum()):,} unit")
            m3.metric("Nilai Aset Gudang", f"Rp {float(df_produk['total_nilai_aset'].sum()):,.0f}")
            m4.metric("Kategori Terbesar", df_produk.groupby('kategori')['stok_gudang'].sum().idxmax())
            m5.metric("SKU Stok Kritis",   int((df_produk['stok_gudang'] < STOK_MINIMUM).sum()),
                      delta_color="inverse")
            st.divider()

            fc1, fc2 = st.columns([3, 1])
            with fc1:
                search = st.text_input("🔍 Cari produk (nama / SKU):", placeholder="Contoh: beras, SKU-001 ...")
            with fc2:
                kat_list   = ["Semua"] + sorted(df_produk['kategori'].dropna().unique().tolist())
                filter_kat = st.selectbox("Kategori:", kat_list)

            df_f = df_produk.copy()
            if search:
                mask = (df_f['nama_produk'].str.contains(search, case=False, na=False) |
                        df_f['sku'].str.contains(search, case=False, na=False))
                df_f = df_f[mask]
            if filter_kat != "Semua":
                df_f = df_f[df_f['kategori'] == filter_kat]

            gc1, gc2 = st.columns(2)
            with gc1:
                st.markdown("**Distribusi Stok per Kategori**")
                df_k = df_produk.groupby('kategori', as_index=False)['stok_gudang'].sum()
                fig1 = px.pie(df_k, names='kategori', values='stok_gudang', hole=0.4,
                              color_discrete_sequence=px.colors.sequential.Teal)
                st.plotly_chart(fig1, use_container_width=True)
            with gc2:
                st.markdown("**Nilai Aset per Kategori (Rp)**")
                df_a = df_produk.groupby('kategori', as_index=False)['total_nilai_aset'].sum()
                df_a = df_a.sort_values('total_nilai_aset', ascending=False)
                fig2 = px.bar(df_a, x='kategori', y='total_nilai_aset', text_auto='.2s',
                              color='kategori', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

            st.divider()
            df_kritis = df_f[df_f['stok_gudang'] < STOK_MINIMUM]
            if not df_kritis.empty:
                with st.expander(f"⚠️  {len(df_kritis)} produk stok di bawah {STOK_MINIMUM} unit", expanded=True):
                    st.dataframe(
                        df_kritis[['sku', 'nama_produk', 'kategori', 'stok_gudang', 'satuan']].rename(
                            columns={'sku': 'SKU', 'nama_produk': 'Nama Produk',
                                     'kategori': 'Kategori', 'stok_gudang': 'Stok', 'satuan': 'Satuan'}),
                        use_container_width=True, hide_index=True)

            st.subheader("Katalog Produk Lengkap")
            df_tampil = df_f.copy()
            df_tampil['harga_dasar']      = df_tampil['harga_dasar'].apply(lambda x: f"Rp {x:,.0f}")
            df_tampil['total_nilai_aset'] = df_tampil['total_nilai_aset'].apply(lambda x: f"Rp {x:,.0f}")
            df_tampil['Status Stok']      = df_f['stok_gudang'].apply(
                lambda x: "🔴 Kritis" if x <= 3 else ("🟡 Menipis" if x < STOK_MINIMUM else "🟢 Aman"))
            st.dataframe(
                df_tampil[['sku', 'nama_produk', 'kategori', 'harga_dasar',
                           'stok_gudang', 'satuan', 'total_nilai_aset', 'Status Stok']].rename(columns={
                    'sku': 'SKU', 'nama_produk': 'Nama Produk', 'kategori': 'Kategori',
                    'harga_dasar': 'Harga Dasar', 'stok_gudang': 'Stok',
                    'satuan': 'Satuan', 'total_nilai_aset': 'Nilai Aset'}),
                use_container_width=True, hide_index=True)

    with tab_stok2:
        st.subheader("➕ Tambah Produk Baru ke Katalog")
        st.caption("Isi semua field bertanda * lalu klik Simpan.")
        df_kat_existing = run_query("SELECT DISTINCT kategori FROM Products WHERE kategori IS NOT NULL ORDER BY kategori")
        kategori_existing = df_kat_existing['kategori'].tolist() if not df_kat_existing.empty else []
        SATUAN_UMUM = ["Kg", "Gram", "Liter", "mL", "Pcs", "Dus", "Karton",
                       "Pak", "Botol", "Kaleng", "Sak", "Lusin", "Roll", "Meter"]

        with st.form("form_tambah_produk", clear_on_submit=True):
            st.markdown("#### Identitas Produk")
            fp1, fp2 = st.columns(2)
            with fp1:
                sku_baru         = st.text_input("SKU *", placeholder="Contoh: BRS-001")
                nama_produk_baru = st.text_input("Nama Produk *", placeholder="Contoh: Beras Premium 5kg")
            with fp2:
                opsi_kat    = kategori_existing + ["✏️ Ketik kategori baru..."]
                pilihan_kat = st.selectbox("Kategori *", opsi_kat)
                kategori_baru = (st.text_input("Nama Kategori Baru *", placeholder="Contoh: Bumbu Dapur")
                                 if pilihan_kat == "✏️ Ketik kategori baru..." else pilihan_kat)
                satuan_pilih = st.selectbox("Satuan *", SATUAN_UMUM)

            st.markdown("#### Harga & Stok Awal")
            fh1, fh2, fh3 = st.columns(3)
            with fh1:
                harga_dasar_baru = st.number_input("Harga Dasar (Rp) *", min_value=0.0, step=500.0, value=0.0)
            with fh2:
                harga_jual_baru  = st.number_input("Harga Jual B2B (Rp)", min_value=0.0, step=500.0, value=0.0)
            with fh3:
                stok_awal        = st.number_input("Stok Awal (unit) *", min_value=0, step=1, value=0)

            submitted_produk = st.form_submit_button("💾 Simpan Produk", type="primary")
            if submitted_produk:
                errors = []
                if not sku_baru.strip():          errors.append("SKU wajib diisi.")
                if not nama_produk_baru.strip():  errors.append("Nama produk wajib diisi.")
                if not kategori_baru or not kategori_baru.strip(): errors.append("Kategori wajib diisi.")
                if harga_dasar_baru <= 0:         errors.append("Harga dasar harus lebih dari 0.")
                if errors:
                    for err in errors: st.error(err)
                else:
                    df_cek_sku = run_query("SELECT product_id FROM Products WHERE sku = %s", (sku_baru.strip().upper(),))
                    if not df_cek_sku.empty:
                        st.error(f"SKU **{sku_baru.upper()}** sudah terdaftar.")
                    else:
                        try:
                            execute_query(
                                "INSERT INTO Products (sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang) VALUES (%s,%s,%s,%s,%s,%s)",
                                (sku_baru.strip().upper(), nama_produk_baru.strip(), kategori_baru.strip(), satuan_pilih, harga_dasar_baru, stok_awal))
                            st.success(f"✅ Produk **{nama_produk_baru}** berhasil ditambahkan!")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Gagal menyimpan: {e}")

        st.divider()
        st.subheader("📥 Import Produk via CSV")
        template_csv = "sku,nama_produk,kategori,satuan,harga_dasar,stok_gudang\nBRS-001,Beras Premium 5kg,Bahan Pokok,Sak,85000,100\n"
        st.download_button("⬇️ Download Template CSV", data=template_csv.encode('utf-8'),
                           file_name="template_produk.csv", mime="text/csv")
        uploaded_csv = st.file_uploader("Upload CSV Produk:", type=["csv"])
        if uploaded_csv:
            try:
                df_import = pd.read_csv(uploaded_csv)
                kolom_wajib = {'sku', 'nama_produk', 'kategori', 'satuan', 'harga_dasar', 'stok_gudang'}
                if not kolom_wajib.issubset(set(df_import.columns)):
                    st.error(f"Kolom CSV tidak lengkap.")
                else:
                    st.dataframe(df_import.head(10), use_container_width=True, hide_index=True)
                    if st.button("🚀 Mulai Import", type="primary"):
                        berhasil, dilewati, gagal = 0, 0, []
                        for _, row_csv in df_import.iterrows():
                            sku_csv = str(row_csv['sku']).strip().upper()
                            if not run_query("SELECT product_id FROM Products WHERE sku=%s", (sku_csv,)).empty:
                                dilewati += 1; continue
                            try:
                                execute_query(
                                    "INSERT INTO Products (sku,nama_produk,kategori,satuan,harga_dasar,stok_gudang) VALUES(%s,%s,%s,%s,%s,%s)",
                                    (sku_csv, str(row_csv['nama_produk']).strip(), str(row_csv['kategori']).strip(),
                                     str(row_csv['satuan']).strip(), float(row_csv['harga_dasar']), int(row_csv['stok_gudang'])))
                                berhasil += 1
                            except Exception as ex:
                                gagal.append(f"{sku_csv}: {ex}")
                        st.success(f"✅ {berhasil} berhasil, {dilewati} dilewati.")
                        if gagal: st.warning("Gagal:\n" + "\n".join(gagal))
                        st.rerun()
            except Exception as e:
                st.error(f"Gagal membaca CSV: {e}")

    with tab_stok3:
        df_produk_edit = run_query("""
            SELECT product_id, sku, nama_produk, kategori, satuan,
                   harga_dasar, stok_gudang, (harga_dasar*stok_gudang) AS total_nilai_aset
            FROM Products ORDER BY kategori, nama_produk
        """)
        if df_produk_edit.empty:
            st.info("Katalog produk kosong.")
        else:
            st.subheader("📝 Ubah Data Produk")
            opsi_edit      = (df_produk_edit['sku'] + " — " + df_produk_edit['nama_produk']).tolist()
            produk_dipilih = st.selectbox("Pilih Produk yang ingin diubah:", opsi_edit)
            sku_sel        = produk_dipilih.split(" — ")[0]
            baris          = df_produk_edit[df_produk_edit['sku'] == sku_sel].iloc[0]

            with st.form("form_update_produk"):
                st.info(f"Mengedit: **{produk_dipilih}**")
                eu1, eu2 = st.columns(2)
                SATUAN_LIST = ["Kg", "Gram", "Liter", "mL", "Pcs", "Dus", "Karton",
                               "Pak", "Botol", "Kaleng", "Sak", "Lusin", "Roll", "Meter"]
                with eu1:
                    nama_edit = st.text_input("Nama Produk *", value=str(baris['nama_produk']))
                    kat_edit_existing = run_query(
                        "SELECT DISTINCT kategori FROM Products WHERE kategori IS NOT NULL ORDER BY kategori"
                    )['kategori'].tolist()
                    kat_default_idx = kat_edit_existing.index(baris['kategori']) if baris['kategori'] in kat_edit_existing else 0
                    kat_edit  = st.selectbox("Kategori *", kat_edit_existing, index=kat_default_idx)
                with eu2:
                    sat_idx     = SATUAN_LIST.index(baris['satuan']) if baris['satuan'] in SATUAN_LIST else 0
                    satuan_edit = st.selectbox("Satuan *", SATUAN_LIST, index=sat_idx)

                ep1, ep2 = st.columns(2)
                with ep1:
                    stok_baru  = st.number_input("Stok Gudang *", min_value=0, value=int(baris['stok_gudang']), step=1)
                with ep2:
                    harga_baru = st.number_input("Harga Dasar (Rp) *", min_value=0.0, value=float(baris['harga_dasar']), step=500.0)

                if st.form_submit_button("💾 Simpan Perubahan", type="primary"):
                    if not nama_edit.strip():
                        st.error("Nama produk tidak boleh kosong.")
                    else:
                        try:
                            execute_query(
                                "UPDATE Products SET nama_produk=%s,kategori=%s,satuan=%s,stok_gudang=%s,harga_dasar=%s WHERE product_id=%s",
                                (nama_edit.strip(), kat_edit, satuan_edit, stok_baru, harga_baru, int(baris['product_id'])))
                            st.success("✅ Data produk berhasil diperbarui!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")

            st.divider()
            st.subheader("🗑️ Hapus Produk dari Katalog")
            st.warning("⚠️ Produk yang sudah pernah masuk PO tidak dapat dihapus.")
            opsi_hapus   = (df_produk_edit['sku'] + " — " + df_produk_edit['nama_produk']).tolist()
            produk_hapus = st.selectbox("Pilih Produk yang akan dihapus:", opsi_hapus, key="sel_hapus")
            sku_hapus    = produk_hapus.split(" — ")[0]
            id_hapus     = int(df_produk_edit[df_produk_edit['sku'] == sku_hapus]['product_id'].iloc[0])
            df_cek_po    = run_query("SELECT COUNT(*) AS n FROM OrderDetails WHERE product_id=%s", (id_hapus,))
            ada_po       = int(df_cek_po['n'].iloc[0]) > 0 if not df_cek_po.empty else False
            konfirmasi   = st.checkbox(f'Saya yakin ingin menghapus **{produk_hapus}**')
            btn_hapus    = st.button("🗑️ Hapus Produk", type="primary", disabled=ada_po or not konfirmasi)
            if ada_po:
                st.error("Produk ini memiliki riwayat PO dan tidak dapat dihapus.")
            elif btn_hapus and konfirmasi:
                try:
                    execute_query("DELETE FROM Products WHERE product_id=%s", (id_hapus,))
                    st.success(f"Produk **{produk_hapus}** berhasil dihapus.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal: {e}")


# ==============================================================
# 3. MANAJEMEN KLIEN B2B
# ==============================================================
elif pilihan_menu == "🏢 Manajemen Klien B2B":
    st.title("🏢 Manajemen Klien B2B")
    tab1, tab2, tab3 = st.tabs(["📋 Daftar Klien", "➕ Tambah Klien Baru", "👥 Manajemen Pengguna"])

    with tab1:
        st.subheader("Semua Perusahaan Terdaftar")
        df_comp = run_query("""
            SELECT c.company_id, c.nama_perusahaan, c.npwp, c.kategori_industri, c.limit_kredit,
                   DATE(c.created_at) AS bergabung,
                   COUNT(DISTINCT u.user_id) AS jumlah_user,
                   COUNT(DISTINCT po.po_id) AS jumlah_po,
                   COALESCE(SUM(po.total_tagihan),0) AS total_transaksi
            FROM Companies c
            LEFT JOIN Users u ON c.company_id=u.company_id
            LEFT JOIN PurchaseOrders po ON c.company_id=po.company_id
            GROUP BY c.company_id ORDER BY total_transaksi DESC
        """)
        if not df_comp.empty:
            km1, km2, km3, km4 = st.columns(4)
            km1.metric("Total Klien",     len(df_comp))
            km2.metric("Total Pengguna",  int(df_comp['jumlah_user'].sum()))
            km3.metric("Total PO",        int(df_comp['jumlah_po'].sum()))
            km4.metric("Total Transaksi", f"Rp {df_comp['total_transaksi'].sum():,.0f}")
            st.divider()
            df_ind = df_comp['kategori_industri'].value_counts().reset_index()
            df_ind.columns = ['Industri', 'Jumlah']
            fig_ind = px.bar(df_ind, x='Industri', y='Jumlah', color='Industri',
                             color_discrete_sequence=px.colors.qualitative.Set2,
                             title="Distribusi Klien per Segmen Industri")
            fig_ind.update_layout(showlegend=False, height=250)
            st.plotly_chart(fig_ind, use_container_width=True)
            df_comp_tampil = df_comp.copy()
            df_comp_tampil['limit_kredit']   = df_comp_tampil['limit_kredit'].apply(lambda x: f"Rp {x:,.0f}")
            df_comp_tampil['total_transaksi'] = df_comp_tampil['total_transaksi'].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(
                df_comp_tampil[['nama_perusahaan','kategori_industri','npwp','limit_kredit',
                                'jumlah_user','jumlah_po','total_transaksi','bergabung']].rename(columns={
                    'nama_perusahaan':'Perusahaan','kategori_industri':'Segmen','npwp':'NPWP',
                    'limit_kredit':'Limit Kredit','jumlah_user':'Users','jumlah_po':'Total PO',
                    'total_transaksi':'Total Transaksi','bergabung':'Bergabung'}),
                use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada klien terdaftar.")

    with tab2:
        st.subheader("Daftarkan Klien B2B Baru")
        with st.form("form_tambah_klien"):
            tc1, tc2 = st.columns(2)
            with tc1:
                nama_perusahaan  = st.text_input("Nama Perusahaan *", placeholder="PT. Hotel Bintang Lima")
                npwp             = st.text_input("NPWP", placeholder="XX.XXX.XXX.X-XXX.XXX")
            with tc2:
                kategori_ind     = st.selectbox("Segmen Industri *", ['Hotel','Restaurant','Cafe','Catering'])
                limit_kredit_inp = st.number_input("Limit Kredit (Rp)", min_value=0.0, step=1_000_000.0, value=0.0)
            if st.form_submit_button("💾 Daftarkan Klien"):
                if not nama_perusahaan.strip():
                    st.error("Nama perusahaan wajib diisi!")
                else:
                    try:
                        execute_query(
                            "INSERT INTO Companies (nama_perusahaan,npwp,kategori_industri,limit_kredit) VALUES(%s,%s,%s,%s)",
                            (nama_perusahaan.strip(), npwp.strip() or None, kategori_ind, limit_kredit_inp))
                        st.success(f"✅ Klien **{nama_perusahaan}** berhasil didaftarkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {e}")

    with tab3:
        st.subheader("Pengguna (Staff) per Perusahaan")
        df_comp_list = run_query("SELECT company_id, nama_perusahaan FROM Companies ORDER BY nama_perusahaan")
        if df_comp_list.empty:
            st.info("Belum ada perusahaan.")
        else:
            perusahaan_sel = st.selectbox("Pilih Perusahaan:", df_comp_list['nama_perusahaan'].tolist())
            comp_id_sel    = int(df_comp_list[df_comp_list['nama_perusahaan']==perusahaan_sel]['company_id'].iloc[0])
            df_users       = run_query("SELECT user_id, nama_lengkap, email, peran FROM Users WHERE company_id=%s", (comp_id_sel,))
            col_u1, col_u2 = st.columns([2,1])
            with col_u1:
                st.markdown(f"**Staff terdaftar di {perusahaan_sel}:**")
                if not df_users.empty:
                    st.dataframe(df_users.rename(columns={'user_id':'ID','nama_lengkap':'Nama','email':'Email','peran':'Peran'}),
                                 use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada pengguna.")
            with col_u2:
                st.markdown("**➕ Tambah Pengguna:**")
                with st.form("form_tambah_user"):
                    nama_user  = st.text_input("Nama Lengkap *")
                    email_user = st.text_input("Email *")
                    peran_user = st.selectbox("Peran", ['Chef','Procurement','Finance_Manager'])
                    if st.form_submit_button("Tambah"):
                        if not nama_user.strip() or not email_user.strip():
                            st.error("Nama dan email wajib diisi!")
                        else:
                            try:
                                execute_query(
                                    "INSERT INTO Users (company_id,nama_lengkap,email,peran) VALUES(%s,%s,%s,%s)",
                                    (comp_id_sel, nama_user.strip(), email_user.strip(), peran_user))
                                st.success("Pengguna berhasil ditambahkan!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal: {e}")


# ==============================================================
# 4. MANAJEMEN PESANAN (PO)
# ==============================================================
elif pilihan_menu == "🛒 Manajemen Pesanan (PO)":
    st.title("🛒 Manajemen Purchase Order (PO)")
    STATUS_LIST = ['Pending_Approval','Approved','Processing','Delivered','Cancelled']
    tab_po1, tab_po2, tab_po3 = st.tabs(["📋 Daftar PO", "➕ Buat PO Baru", "🔄 Update Status PO"])

    with tab_po1:
        st.subheader("Semua Purchase Order")
        filter_status = st.multiselect("Filter Status:", STATUS_LIST,
                                       default=['Pending_Approval','Approved','Processing'])
        if filter_status:
            ph     = ','.join(['%s']*len(filter_status))
            df_po  = run_query(f"""
                SELECT po.po_id AS `PO#`, c.nama_perusahaan AS Klien,
                       c.kategori_industri AS Segmen,
                       IFNULL(u.nama_lengkap,'-') AS `Dipesan Oleh`,
                       po.status_po AS Status, po.metode_pembayaran AS Pembayaran,
                       po.total_tagihan AS Total, DATE(po.tanggal_dipesan) AS Tanggal
                FROM PurchaseOrders po
                JOIN Companies c ON po.company_id=c.company_id
                LEFT JOIN Users u ON po.dibuat_oleh=u.user_id
                WHERE po.status_po IN ({ph}) ORDER BY po.tanggal_dipesan DESC
            """, tuple(filter_status))
        else:
            df_po = run_query("""
                SELECT po.po_id AS `PO#`, c.nama_perusahaan AS Klien,
                       c.kategori_industri AS Segmen,
                       IFNULL(u.nama_lengkap,'-') AS `Dipesan Oleh`,
                       po.status_po AS Status, po.metode_pembayaran AS Pembayaran,
                       po.total_tagihan AS Total, DATE(po.tanggal_dipesan) AS Tanggal
                FROM PurchaseOrders po
                JOIN Companies c ON po.company_id=c.company_id
                LEFT JOIN Users u ON po.dibuat_oleh=u.user_id
                ORDER BY po.tanggal_dipesan DESC
            """)

        if not df_po.empty:
            pm1, pm2, pm3 = st.columns(3)
            pm1.metric("Total PO Tampil",  len(df_po))
            pm2.metric("Total Nilai",      f"Rp {df_po['Total'].sum():,.0f}")
            pm3.metric("Pending Approval", len(df_po[df_po['Status']=='Pending_Approval']))
            df_po_tampil = df_po.copy()
            df_po_tampil['Total'] = df_po_tampil['Total'].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(df_po_tampil, use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("🔍 Detail Item PO")
            pilih_detail = st.selectbox("Pilih PO#:", [f"PO #{p}" for p in df_po['PO#'].tolist()])
            po_id_detail = int(pilih_detail.replace("PO #",""))
            df_detail = run_query("""
                SELECT p.sku AS SKU, p.nama_produk AS Produk, p.kategori AS Kategori,
                       p.satuan AS Satuan, od.kuantitas AS Qty, od.harga_final AS `Harga/Unit`,
                       (od.kuantitas*od.harga_final) AS Subtotal
                FROM OrderDetails od JOIN Products p ON od.product_id=p.product_id
                WHERE od.po_id=%s
            """, (po_id_detail,))
            if not df_detail.empty:
                df_detail['Harga/Unit'] = df_detail['Harga/Unit'].apply(lambda x: f"Rp {x:,.0f}")
                df_detail['Subtotal']   = df_detail['Subtotal'].apply(lambda x: f"Rp {x:,.0f}")
                st.dataframe(df_detail, use_container_width=True, hide_index=True)
            else:
                st.info("Detail tidak ditemukan.")
        else:
            st.info("Tidak ada PO dengan filter yang dipilih.")

    with tab_po2:
        st.subheader("Buat Purchase Order Baru")
        df_comp_po = run_query("SELECT company_id, nama_perusahaan FROM Companies ORDER BY nama_perusahaan")
        df_prod_po = run_query("SELECT product_id, sku, nama_produk, harga_dasar, stok_gudang, satuan FROM Products WHERE stok_gudang>0 ORDER BY nama_produk")
        if df_comp_po.empty:
            st.warning("⚠️ Belum ada klien terdaftar.")
        elif df_prod_po.empty:
            st.warning("⚠️ Tidak ada produk tersedia.")
        else:
            with st.form("form_buat_po"):
                ci1, ci2, ci3 = st.columns(3)
                with ci1:
                    pilih_perusahaan = st.selectbox("Perusahaan Klien *", df_comp_po['nama_perusahaan'].tolist())
                    comp_id_po = int(df_comp_po[df_comp_po['nama_perusahaan']==pilih_perusahaan]['company_id'].iloc[0])
                with ci2:
                    df_user_po = run_query("SELECT user_id, nama_lengkap FROM Users WHERE company_id=%s", (comp_id_po,))
                    if not df_user_po.empty:
                        pilih_user = st.selectbox("Dipesan Oleh", df_user_po['nama_lengkap'].tolist())
                        user_id_po = int(df_user_po[df_user_po['nama_lengkap']==pilih_user]['user_id'].iloc[0])
                    else:
                        st.caption("Klien belum punya pengguna.")
                        user_id_po = None
                with ci3:
                    metode_bayar = st.selectbox("Metode Pembayaran *", ['Cash','Tempo_30_Hari'])

                opsi_produk = ["-- Pilih Produk --"] + (df_prod_po['sku'] + " | " + df_prod_po['nama_produk']).tolist()
                items    = []
                total_po = 0.0
                for i in range(1, 7):
                    r1, r2, r3 = st.columns([5, 2, 2])
                    with r1: sel = st.selectbox(f"Produk {i}", opsi_produk, key=f"p{i}")
                    with r2: qty = st.number_input(f"Qty {i}", min_value=0, value=0, step=1, key=f"q{i}")
                    with r3:
                        if sel != "-- Pilih Produk --" and qty > 0:
                            sku_sel = sel.split(" | ")[0]
                            baris_p = df_prod_po[df_prod_po['sku']==sku_sel].iloc[0]
                            harga_p = float(baris_p['harga_dasar'])
                            stok_p  = int(baris_p['stok_gudang'])
                            if qty > stok_p:
                                st.error(f"Stok hanya {stok_p}!")
                            else:
                                sub = harga_p * qty
                                total_po += sub
                                st.metric(f"Sub {i}", f"Rp {sub:,.0f}")
                                items.append({'product_id': int(baris_p['product_id']), 'kuantitas': qty, 'harga_final': harga_p})

                st.markdown(f"### 🧾 Total Tagihan: **Rp {total_po:,.0f}**")
                if st.form_submit_button("🛒 Buat Purchase Order", type="primary"):
                    if not items:
                        st.error("Minimal pilih 1 produk!")
                    else:
                        try:
                            po_id_baru = execute_query(
                                "INSERT INTO PurchaseOrders (company_id,dibuat_oleh,status_po,metode_pembayaran,total_tagihan) VALUES(%s,%s,'Pending_Approval',%s,%s)",
                                (comp_id_po, user_id_po, metode_bayar, total_po))
                            for item in items:
                                execute_query("INSERT INTO OrderDetails (po_id,product_id,kuantitas,harga_final) VALUES(%s,%s,%s,%s)",
                                              (po_id_baru, item['product_id'], item['kuantitas'], item['harga_final']))
                                execute_query("UPDATE Products SET stok_gudang=stok_gudang-%s WHERE product_id=%s",
                                              (item['kuantitas'], item['product_id']))
                            st.success(f"✅ PO #{po_id_baru} berhasil dibuat — Rp {total_po:,.0f}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")

    with tab_po3:
        st.subheader("Update Status Purchase Order")
        df_po_aktif = run_query("""
            SELECT po.po_id, c.nama_perusahaan, po.status_po, po.total_tagihan, DATE(po.tanggal_dipesan) AS tanggal
            FROM PurchaseOrders po JOIN Companies c ON po.company_id=c.company_id
            WHERE po.status_po NOT IN ('Delivered','Cancelled') ORDER BY po.tanggal_dipesan DESC
        """)
        if df_po_aktif.empty:
            st.info("Tidak ada PO aktif.")
        else:
            STATUS_LIST2 = ['Pending_Approval','Approved','Processing','Delivered','Cancelled']
            opsi_po = [f"PO #{r['po_id']} | {r['nama_perusahaan']} | Rp {r['total_tagihan']:,.0f} | {r['status_po']}"
                       for _, r in df_po_aktif.iterrows()]
            pilih_po_upd = st.selectbox("Pilih PO:", opsi_po)
            po_id_upd    = int(pilih_po_upd.split("#")[1].split(" ")[0])
            status_skrng = pilih_po_upd.split(" | ")[-1]
            status_baru  = st.selectbox("Status Baru:", [s for s in STATUS_LIST2 if s != status_skrng])
            if st.button("🔄 Update Status", type="primary"):
                try:
                    execute_query("UPDATE PurchaseOrders SET status_po=%s WHERE po_id=%s", (status_baru, po_id_upd))
                    if status_baru == 'Cancelled':
                        df_items_cancel = run_query("SELECT product_id, kuantitas FROM OrderDetails WHERE po_id=%s", (po_id_upd,))
                        for _, it in df_items_cancel.iterrows():
                            execute_query("UPDATE Products SET stok_gudang=stok_gudang+%s WHERE product_id=%s",
                                          (int(it['kuantitas']), int(it['product_id'])))
                        st.success(f"PO #{po_id_upd} dibatalkan. Stok dikembalikan.")
                    else:
                        st.success(f"✅ PO #{po_id_upd} → **{status_baru}**")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal: {e}")


# ==============================================================
# 5. LAPORAN & ANALITIK
# ==============================================================
elif pilihan_menu == "📈 Laporan & Analitik":
    st.title("📈 Laporan & Analitik Penjualan")
    lc1, lc2 = st.columns(2)
    with lc1: tgl_mulai = st.date_input("Dari Tanggal:", value=date(date.today().year,1,1))
    with lc2: tgl_akhir = st.date_input("Sampai Tanggal:", value=date.today())
    if tgl_mulai > tgl_akhir:
        st.error("Tanggal mulai tidak boleh lebih besar.")
        st.stop()

    df_sum = run_query("""
        SELECT COUNT(*) AS total_po, COALESCE(SUM(total_tagihan),0) AS total_revenue,
               COALESCE(AVG(total_tagihan),0) AS avg_po, COUNT(DISTINCT company_id) AS klien_aktif
        FROM PurchaseOrders
        WHERE DATE(tanggal_dipesan) BETWEEN %s AND %s AND status_po != 'Cancelled'
    """, (tgl_mulai, tgl_akhir))
    if not df_sum.empty:
        rs = df_sum.iloc[0]
        sk1, sk2, sk3, sk4 = st.columns(4)
        sk1.metric("Total PO",           f"{int(rs['total_po'])}")
        sk2.metric("Total Revenue",      f"Rp {float(rs['total_revenue']):,.0f}")
        sk3.metric("Rata-rata Nilai PO", f"Rp {float(rs['avg_po']):,.0f}")
        sk4.metric("Klien Aktif",        f"{int(rs['klien_aktif'])}")

    st.divider()
    gc1, gc2 = st.columns(2)
    with gc1:
        st.subheader("Revenue per Bulan")
        df_rev_bln = run_query("""
            SELECT DATE_FORMAT(tanggal_dipesan,'%Y-%m') AS Bulan,
                   SUM(total_tagihan) AS Revenue, COUNT(*) AS Jumlah_PO
            FROM PurchaseOrders WHERE DATE(tanggal_dipesan) BETWEEN %s AND %s AND status_po!='Cancelled'
            GROUP BY DATE_FORMAT(tanggal_dipesan,'%Y-%m') ORDER BY Bulan
        """, (tgl_mulai, tgl_akhir))
        if not df_rev_bln.empty:
            fig_rb = px.bar(df_rev_bln, x='Bulan', y='Revenue', text_auto='.2s',
                            color_discrete_sequence=['#0077B6'])
            fig_rb.update_layout(height=300)
            st.plotly_chart(fig_rb, use_container_width=True)
        else:
            st.info("Tidak ada data.")
    with gc2:
        st.subheader("Revenue per Segmen Industri")
        df_rev_seg = run_query("""
            SELECT c.kategori_industri AS Segmen, SUM(po.total_tagihan) AS Revenue
            FROM PurchaseOrders po JOIN Companies c ON po.company_id=c.company_id
            WHERE DATE(po.tanggal_dipesan) BETWEEN %s AND %s AND po.status_po!='Cancelled'
            GROUP BY c.kategori_industri ORDER BY Revenue DESC
        """, (tgl_mulai, tgl_akhir))
        if not df_rev_seg.empty:
            fig_seg = px.pie(df_rev_seg, names='Segmen', values='Revenue', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set2)
            fig_seg.update_layout(height=300)
            st.plotly_chart(fig_seg, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    st.divider()
    gc3, gc4 = st.columns(2)
    with gc3:
        st.subheader("Top 10 Produk Terlaris (Volume)")
        df_top_prod = run_query("""
            SELECT p.nama_produk AS Produk, p.kategori AS Kategori,
                   SUM(od.kuantitas) AS Total_Qty,
                   SUM(od.kuantitas*od.harga_final) AS Revenue
            FROM OrderDetails od JOIN Products p ON od.product_id=p.product_id
            JOIN PurchaseOrders po ON od.po_id=po.po_id
            WHERE DATE(po.tanggal_dipesan) BETWEEN %s AND %s AND po.status_po!='Cancelled'
            GROUP BY p.product_id ORDER BY Total_Qty DESC LIMIT 10
        """, (tgl_mulai, tgl_akhir))
        if not df_top_prod.empty:
            fig_tp = px.bar(df_top_prod, x='Total_Qty', y='Produk', orientation='h',
                            color='Kategori', color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_tp.update_layout(height=370, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_tp, use_container_width=True)
        else:
            st.info("Tidak ada data.")
    with gc4:
        st.subheader("Top 10 Klien (Revenue)")
        df_top_kl = run_query("""
            SELECT c.nama_perusahaan AS Klien, c.kategori_industri AS Segmen,
                   COUNT(po.po_id) AS Jumlah_PO, SUM(po.total_tagihan) AS Revenue
            FROM PurchaseOrders po JOIN Companies c ON po.company_id=c.company_id
            WHERE DATE(po.tanggal_dipesan) BETWEEN %s AND %s AND po.status_po!='Cancelled'
            GROUP BY c.company_id ORDER BY Revenue DESC LIMIT 10
        """, (tgl_mulai, tgl_akhir))
        if not df_top_kl.empty:
            fig_tk = px.bar(df_top_kl, x='Revenue', y='Klien', orientation='h',
                            color='Segmen', color_discrete_sequence=px.colors.qualitative.Set2)
            fig_tk.update_layout(height=370, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_tk, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    st.divider()
    st.subheader("📋 Tabel Transaksi Lengkap")
    df_trans = run_query("""
        SELECT po.po_id AS `PO#`, DATE(po.tanggal_dipesan) AS Tanggal,
               c.nama_perusahaan AS Klien, c.kategori_industri AS Segmen,
               po.metode_pembayaran AS Pembayaran, po.status_po AS Status,
               po.total_tagihan AS Total
        FROM PurchaseOrders po JOIN Companies c ON po.company_id=c.company_id
        WHERE DATE(po.tanggal_dipesan) BETWEEN %s AND %s ORDER BY po.tanggal_dipesan DESC
    """, (tgl_mulai, tgl_akhir))
    if not df_trans.empty:
        df_trans_tampil = df_trans.copy()
        df_trans_tampil['Total'] = df_trans_tampil['Total'].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(df_trans_tampil, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download Laporan (.csv)",
                           data=df_trans.to_csv(index=False).encode('utf-8'),
                           file_name=f"laporan_{tgl_mulai}_sd_{tgl_akhir}.csv",
                           mime="text/csv")
    else:
        st.info("Tidak ada transaksi pada periode ini.")


# ==============================================================
# 6. PORTAL PEMBELIAN (USER)
# ==============================================================
elif pilihan_menu == "🛍️ Portal Pembelian (User)":

    # ── HEADER ──────────────────────────────────────────────────
    st.markdown("""
    <div class="portal-header">
        <h1 style="margin:0;font-size:2rem;">🛍️ Portal Pembelian HoReCa</h1>
        <p style="margin:4px 0 0;opacity:0.85;font-size:1rem;">
            Selamat datang di katalog grosir B2B — pilih produk, tambahkan ke keranjang, lalu checkout.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # GATE: Tampilkan Login/Register jika belum login
    # ============================================================
    if not st.session_state.portal_user_id:

        st.markdown("#### 👤 Masuk atau Daftarkan Perusahaan Anda")
        tab_login, tab_register = st.tabs(["🔑 Login", "🏢 Daftar Perusahaan Baru"])

        # ── TAB LOGIN ───────────────────────────────────────────
        with tab_login:
            st.markdown("Masukkan email yang sudah terdaftar di sistem untuk melanjutkan.")
            st.markdown("")

            with st.form("form_login_portal"):
                email_login = st.text_input(
                    "📧 Alamat Email *",
                    placeholder="contoh: budi@hotelmelati.com"
                )
                submitted_login = st.form_submit_button(
                    "🔑 Masuk ke Portal", type="primary", use_container_width=True
                )

            if submitted_login:
                if not email_login.strip():
                    st.error("Email tidak boleh kosong.")
                else:
                    df_cek_user = run_query("""
                        SELECT u.user_id, u.nama_lengkap, u.peran,
                               c.company_id, c.nama_perusahaan
                        FROM Users u
                        JOIN Companies c ON u.company_id = c.company_id
                        WHERE u.email = %s
                    """, (email_login.strip().lower(),))

                    if df_cek_user.empty:
                        st.error(
                            "❌ Email tidak ditemukan. Pastikan email sudah terdaftar, "
                            "atau daftarkan perusahaan baru di tab **🏢 Daftar Perusahaan Baru**."
                        )
                    else:
                        row = df_cek_user.iloc[0]
                        st.session_state.portal_user_id      = int(row['user_id'])
                        st.session_state.portal_user_name    = str(row['nama_lengkap'])
                        st.session_state.portal_company_id   = int(row['company_id'])
                        st.session_state.portal_company_name = str(row['nama_perusahaan'])
                        st.success(
                            f"✅ Selamat datang, **{row['nama_lengkap']}** "
                            f"({row['peran']}) dari **{row['nama_perusahaan']}**! 👋"
                        )
                        st.rerun()

            st.divider()
            st.caption(
                "Belum punya akun? Buka tab **🏢 Daftar Perusahaan Baru** untuk mendaftarkan "
                "perusahaan dan akun pertama Anda."
            )

        # ── TAB REGISTER ─────────────────────────────────────────
        with tab_register:
            st.markdown(
                "Isi data di bawah untuk mendaftarkan perusahaan Anda dan membuat akun pengguna pertama. "
                "Setelah terdaftar, Anda bisa langsung login menggunakan email."
            )
            st.markdown("")

            with st.form("form_register_portal", clear_on_submit=False):

                # ── Data Perusahaan ──────────────────────────────
                st.markdown("#### 🏢 Data Perusahaan")
                rc1, rc2 = st.columns(2)
                with rc1:
                    reg_nama_perusahaan = st.text_input(
                        "Nama Perusahaan *",
                        placeholder="PT. Hotel Bintang Lima"
                    )
                    reg_npwp = st.text_input(
                        "NPWP (opsional)",
                        placeholder="XX.XXX.XXX.X-XXX.XXX"
                    )
                with rc2:
                    reg_kategori = st.selectbox(
                        "Segmen Industri *",
                        ['Hotel', 'Restaurant', 'Cafe', 'Catering']
                    )
                    reg_limit_kredit = st.number_input(
                        "Limit Kredit (Rp, opsional)",
                        min_value=0.0,
                        step=1_000_000.0,
                        value=0.0,
                        help="Kosongkan atau isi 0 jika tidak ada limit kredit awal."
                    )

                st.markdown("#### 👤 Data Pengguna Pertama (Admin Perusahaan)")
                ru1, ru2 = st.columns(2)
                with ru1:
                    reg_nama_user = st.text_input(
                        "Nama Lengkap *",
                        placeholder="Budi Santoso"
                    )
                    reg_email = st.text_input(
                        "Email *",
                        placeholder="budi@hotelmelati.com"
                    )
                with ru2:
                    reg_peran = st.selectbox(
                        "Jabatan / Peran *",
                        ['Procurement', 'Chef', 'Finance_Manager'],
                        help="Procurement: pembelian bahan, Chef: dapur, Finance_Manager: keuangan"
                    )

                st.markdown("")
                submitted_register = st.form_submit_button(
                    "🚀 Daftarkan Perusahaan & Buat Akun", type="primary", use_container_width=True
                )

            if submitted_register:
                # Validasi
                reg_errors = []
                if not reg_nama_perusahaan.strip():
                    reg_errors.append("Nama perusahaan wajib diisi.")
                if not reg_nama_user.strip():
                    reg_errors.append("Nama lengkap pengguna wajib diisi.")
                if not reg_email.strip():
                    reg_errors.append("Email wajib diisi.")
                elif "@" not in reg_email or "." not in reg_email.split("@")[-1]:
                    reg_errors.append("Format email tidak valid.")

                if reg_errors:
                    for err in reg_errors:
                        st.error(err)
                else:
                    # Cek email sudah terdaftar
                    df_cek_email = run_query(
                        "SELECT user_id FROM Users WHERE email = %s",
                        (reg_email.strip().lower(),)
                    )
                    if not df_cek_email.empty:
                        st.error(
                            f"❌ Email **{reg_email.strip()}** sudah terdaftar. "
                            "Gunakan email lain atau login langsung."
                        )
                    else:
                        # Cek nama perusahaan sudah terdaftar
                        df_cek_comp = run_query(
                            "SELECT company_id FROM Companies WHERE nama_perusahaan = %s",
                            (reg_nama_perusahaan.strip(),)
                        )
                        if not df_cek_comp.empty:
                            st.warning(
                                f"⚠️ Perusahaan **{reg_nama_perusahaan.strip()}** sudah terdaftar. "
                                "Minta admin perusahaan Anda untuk menambahkan akun Anda melalui modul "
                                "**🏢 Manajemen Klien B2B → Manajemen Pengguna**."
                            )
                        else:
                            try:
                                # 1. Insert Companies
                                new_company_id = execute_query(
                                    """INSERT INTO Companies
                                           (nama_perusahaan, npwp, kategori_industri, limit_kredit)
                                       VALUES (%s, %s, %s, %s)""",
                                    (
                                        reg_nama_perusahaan.strip(),
                                        reg_npwp.strip() or None,
                                        reg_kategori,
                                        reg_limit_kredit
                                    )
                                )
                                # 2. Insert Users
                                new_user_id = execute_query(
                                    """INSERT INTO Users
                                           (company_id, nama_lengkap, email, peran)
                                       VALUES (%s, %s, %s, %s)""",
                                    (
                                        new_company_id,
                                        reg_nama_user.strip(),
                                        reg_email.strip().lower(),
                                        reg_peran
                                    )
                                )
                                # 3. Auto-login
                                st.session_state.portal_user_id      = new_user_id
                                st.session_state.portal_user_name    = reg_nama_user.strip()
                                st.session_state.portal_company_id   = new_company_id
                                st.session_state.portal_company_name = reg_nama_perusahaan.strip()

                                st.success(
                                    f"🎉 Perusahaan **{reg_nama_perusahaan.strip()}** berhasil didaftarkan! "
                                    f"Akun **{reg_nama_user.strip()}** ({reg_peran}) telah dibuat. "
                                    f"Anda akan diarahkan ke portal..."
                                )
                                st.balloons()
                                st.rerun()

                            except Exception as e:
                                st.error(f"Gagal mendaftar: {e}")

    # ============================================================
    # PORTAL UTAMA (sudah login)
    # ============================================================
    else:
        # ── Info & Logout bar ────────────────────────────────────
        col_welcome, col_logout = st.columns([4, 1])
        with col_welcome:
            st.success(
                f"✅ Login sebagai **{st.session_state.portal_user_name}** "
                f"— {st.session_state.portal_company_name}"
            )
        with col_logout:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.portal_user_id      = None
                st.session_state.portal_company_id   = None
                st.session_state.portal_user_name    = ""
                st.session_state.portal_company_name = ""
                st.session_state.cart                = {}
                st.rerun()

        # ── TABS ────────────────────────────────────────────────
        tab_katalog, tab_keranjang, tab_riwayat = st.tabs([
            "🏪 Katalog Produk", "🛒 Keranjang & Checkout", "📜 Riwayat Pesanan Saya"
        ])

        # ============================================================
        # TAB 1 — KATALOG PRODUK
        # ============================================================
        with tab_katalog:

            df_katalog = run_query("""
                SELECT product_id, sku, nama_produk, kategori, satuan, harga_dasar, stok_gudang
                FROM Products ORDER BY kategori, nama_produk
            """)

            if df_katalog.empty:
                st.info("Katalog produk kosong. Hubungi admin.")
            else:
                filter_col1, filter_col2, filter_col3 = st.columns([3, 2, 1])
                with filter_col1:
                    cari_produk = st.text_input(
                        "🔍 Cari produk:", placeholder="Nama produk atau SKU...",
                        label_visibility="collapsed"
                    )
                with filter_col2:
                    kat_list_portal = ["Semua Kategori"] + sorted(
                        df_katalog['kategori'].dropna().unique().tolist()
                    )
                    filter_kat_portal = st.selectbox(
                        "Kategori", kat_list_portal, label_visibility="collapsed"
                    )
                with filter_col3:
                    tampilkan_tersedia = st.checkbox("Stok tersedia saja", value=True)

                df_fil = df_katalog.copy()
                if cari_produk:
                    mask = (
                        df_fil['nama_produk'].str.contains(cari_produk, case=False, na=False) |
                        df_fil['sku'].str.contains(cari_produk, case=False, na=False)
                    )
                    df_fil = df_fil[mask]
                if filter_kat_portal != "Semua Kategori":
                    df_fil = df_fil[df_fil['kategori'] == filter_kat_portal]
                if tampilkan_tersedia:
                    df_fil = df_fil[df_fil['stok_gudang'] > 0]

                st.caption(f"Menampilkan **{len(df_fil)}** produk")

                if df_fil.empty:
                    st.info("Tidak ada produk yang cocok dengan filter Anda.")
                else:
                    COLS = 3
                    rows = [df_fil.iloc[i:i+COLS] for i in range(0, len(df_fil), COLS)]

                    for row in rows:
                        cols = st.columns(COLS)
                        for col_idx, (_, prod) in enumerate(row.iterrows()):
                            pid    = int(prod['product_id'])
                            nama   = str(prod['nama_produk'])
                            sku    = str(prod['sku'])
                            kat    = str(prod['kategori']) if prod['kategori'] else ""
                            satuan = str(prod['satuan'])
                            harga  = float(prod['harga_dasar'])
                            stok   = int(prod['stok_gudang'])

                            img_url      = get_product_img_url(kat, pid, width=400, height=220)
                            fallback_url = get_picsum_url(pid, width=400, height=220)
                            img_filter   = "grayscale(80%) opacity(0.6)" if stok == 0 else "none"

                            if stok == 0:
                                badge = '<span class="stok-badge-habis">❌ Habis</span>'
                            elif stok <= 10:
                                badge = f'<span class="stok-badge-menipis">⚠️ Sisa {stok} {satuan}</span>'
                            else:
                                badge = f'<span class="stok-badge-aman">✅ Stok {stok} {satuan}</span>'

                            with cols[col_idx]:
                                st.markdown(f"""
                                <div class="product-card">
                                    <div class="product-img-wrap">
                                        <img
                                            src="{img_url}"
                                            alt="{nama}"
                                            loading="lazy"
                                            style="filter:{img_filter};"
                                            onerror="this.onerror=null;this.src='{fallback_url}';"
                                        />
                                    </div>
                                    <div class="product-body">
                                        <div class="product-name">{nama}</div>
                                        <div class="product-sku">SKU: {sku} · {kat}</div>
                                        <div class="product-price">Rp {harga:,.0f}</div>
                                        <div class="product-satuan">per {satuan}</div>
                                        {badge}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                                if stok > 0:
                                    qty_inp = st.number_input(
                                        f"Jumlah ({satuan})",
                                        min_value=1, max_value=stok,
                                        value=1, step=1,
                                        key=f"qty_katalog_{pid}",
                                        label_visibility="collapsed"
                                    )
                                    if st.button(
                                        "🛒 Tambah ke Keranjang",
                                        key=f"btn_add_{pid}",
                                        use_container_width=True
                                    ):
                                        if pid in st.session_state.cart:
                                            new_qty = st.session_state.cart[pid]['qty'] + qty_inp
                                            if new_qty > stok:
                                                st.error(f"Maksimal {stok} {satuan}!")
                                            else:
                                                st.session_state.cart[pid]['qty'] = new_qty
                                                st.success(f"✅ Diperbarui: {nama} × {new_qty}")
                                        else:
                                            st.session_state.cart[pid] = {
                                                'nama'  : nama,
                                                'harga' : harga,
                                                'qty'   : qty_inp,
                                                'satuan': satuan,
                                                'stok'  : stok,
                                                'kat'   : kat,
                                            }
                                            st.success(f"✅ {nama} ditambahkan!")
                                        st.rerun()
                                else:
                                    st.button(
                                        "Stok Habis", disabled=True,
                                        use_container_width=True, key=f"btn_habis_{pid}"
                                    )

        # ============================================================
        # TAB 2 — KERANJANG & CHECKOUT
        # ============================================================
        with tab_keranjang:
            st.subheader("🛒 Keranjang Belanja Anda")

            if not st.session_state.cart:
                st.info("Keranjang Anda masih kosong. Tambahkan produk dari tab **🏪 Katalog Produk**.")
            else:
                st.markdown("---")
                items_to_delete = []
                total_belanja   = 0.0

                for pid, item in st.session_state.cart.items():
                    subtotal = item['qty'] * item['harga']
                    total_belanja += subtotal

                    c_img, c_info, c_qty, c_sub, c_del = st.columns([1, 4, 2, 2, 1])
                    with c_img:
                        cart_img_url      = get_product_img_url(item.get('kat',''), pid, 80, 80)
                        cart_fallback_url = get_picsum_url(pid, 80, 80)
                        st.markdown(
                            f'<div style="width:60px;height:60px;border-radius:10px;overflow:hidden;'
                            f'border:1px solid #e2e8f0;">'
                            f'<img src="{cart_img_url}" alt="{item["nama"]}" loading="lazy"'
                            f' style="width:100%;height:100%;object-fit:cover;"'
                            f' onerror="this.onerror=null;this.src=\'{cart_fallback_url}\';">'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    with c_info:
                        st.markdown(f"**{item['nama']}**")
                        st.caption(f"Rp {item['harga']:,.0f} / {item['satuan']}")
                    with c_qty:
                        new_qty = st.number_input(
                            "Qty", min_value=1, max_value=item['stok'],
                            value=item['qty'], step=1,
                            key=f"cart_qty_{pid}", label_visibility="collapsed"
                        )
                        if new_qty != item['qty']:
                            st.session_state.cart[pid]['qty'] = new_qty
                            st.rerun()
                    with c_sub:
                        st.markdown(f"**Rp {new_qty * item['harga']:,.0f}**")
                    with c_del:
                        if st.button("🗑️", key=f"del_{pid}", help="Hapus item"):
                            items_to_delete.append(pid)

                    st.markdown(
                        '<hr style="margin:4px 0;border:none;border-top:1px solid #f0f0f0;">',
                        unsafe_allow_html=True
                    )

                for pid in items_to_delete:
                    del st.session_state.cart[pid]
                if items_to_delete:
                    st.rerun()

                st.markdown(f"""
                <div class="cart-total-box">
                    <div style="font-size:0.9rem;opacity:0.85;margin-bottom:4px;">
                        Total Belanja ({cart_total_items()} item)
                    </div>
                    <div style="font-size:1.8rem;font-weight:800;">Rp {total_belanja:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

                st.divider()
                st.subheader("📋 Informasi Checkout")
                st.info(
                    f"**Memesan atas nama:** {st.session_state.portal_user_name} "
                    f"— {st.session_state.portal_company_name}"
                )

                with st.form("form_checkout_portal"):
                    co1, co2 = st.columns(2)
                    with co1:
                        metode_checkout = st.selectbox(
                            "Metode Pembayaran *", ['Cash', 'Tempo_30_Hari'],
                            help="Tempo 30 hari tersedia jika perusahaan memiliki limit kredit."
                        )
                    with co2:
                        catatan_po = st.text_input(
                            "Catatan Tambahan (opsional)",
                            placeholder="Contoh: mohon kirim pagi hari, packing vakum ..."
                        )

                    st.markdown("#### 🧾 Ringkasan Pesanan")
                    for pid, item in st.session_state.cart.items():
                        st.markdown(
                            f"- **{item['nama']}** × {item['qty']} {item['satuan']} "
                            f"= Rp {item['qty']*item['harga']:,.0f}"
                        )
                    st.markdown(f"**Total: Rp {total_belanja:,.0f}**")

                    submitted_checkout = st.form_submit_button(
                        f"✅ Konfirmasi & Kirim Pesanan — Rp {total_belanja:,.0f}",
                        type="primary", use_container_width=True
                    )

                    if submitted_checkout:
                        stok_errors = []
                        for pid, item in st.session_state.cart.items():
                            df_stok_cek = run_query(
                                "SELECT stok_gudang FROM Products WHERE product_id=%s", (pid,)
                            )
                            if not df_stok_cek.empty:
                                stok_aktual = int(df_stok_cek['stok_gudang'].iloc[0])
                                if item['qty'] > stok_aktual:
                                    stok_errors.append(
                                        f"**{item['nama']}**: diminta {item['qty']}, "
                                        f"tersisa {stok_aktual} {item['satuan']}"
                                    )

                        if stok_errors:
                            st.error("⚠️ Stok tidak mencukupi:\n" + "\n".join(stok_errors))
                        else:
                            try:
                                po_id_checkout = execute_query(
                                    """INSERT INTO PurchaseOrders
                                           (company_id, dibuat_oleh, status_po,
                                            metode_pembayaran, total_tagihan)
                                       VALUES (%s, %s, 'Pending_Approval', %s, %s)""",
                                    (
                                        st.session_state.portal_company_id,
                                        st.session_state.portal_user_id,
                                        metode_checkout,
                                        total_belanja
                                    )
                                )
                                for pid, item in st.session_state.cart.items():
                                    execute_query(
                                        """INSERT INTO OrderDetails
                                               (po_id, product_id, kuantitas, harga_final)
                                           VALUES (%s, %s, %s, %s)""",
                                        (po_id_checkout, pid, item['qty'], item['harga'])
                                    )
                                    execute_query(
                                        "UPDATE Products SET stok_gudang=stok_gudang-%s WHERE product_id=%s",
                                        (item['qty'], pid)
                                    )
                                st.session_state.cart = {}
                                st.success(
                                    f"🎉 Pesanan **PO #{po_id_checkout}** berhasil dikirim!\n\n"
                                    f"Total: **Rp {total_belanja:,.0f}** · Status: **Pending Approval**"
                                )
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal membuat pesanan: {e}")

        # ============================================================
        # TAB 3 — RIWAYAT PESANAN
        # ============================================================
        with tab_riwayat:
            st.subheader("📜 Riwayat Pesanan Saya")
            st.caption(
                f"Pesanan perusahaan: **{st.session_state.portal_user_name}** "
                f"— {st.session_state.portal_company_name}"
            )

            df_riwayat = run_query("""
                SELECT
                    po.po_id                  AS po_id,
                    DATE(po.tanggal_dipesan)  AS tanggal,
                    IFNULL(u.nama_lengkap,'-') AS dipesan_oleh,
                    po.status_po              AS status,
                    po.metode_pembayaran      AS metode,
                    po.total_tagihan          AS total
                FROM PurchaseOrders po
                LEFT JOIN Users u ON po.dibuat_oleh = u.user_id
                WHERE po.company_id = %s
                ORDER BY po.tanggal_dipesan DESC
            """, (st.session_state.portal_company_id,))

            if df_riwayat.empty:
                st.info("Belum ada pesanan dari perusahaan Anda.")
            else:
                rh1, rh2, rh3, rh4 = st.columns(4)
                rh1.metric("Total PO",          len(df_riwayat))
                rh2.metric("Total Belanja",      f"Rp {float(df_riwayat['total'].sum()):,.0f}")
                rh3.metric("Pending / Proses",
                           len(df_riwayat[df_riwayat['status'].isin(
                               ['Pending_Approval', 'Approved', 'Processing']
                           )]))
                rh4.metric("Terkirim",           len(df_riwayat[df_riwayat['status'] == 'Delivered']))

                st.divider()

                STATUS_COLOR = {
                    'Pending_Approval': '#f59e0b',
                    'Approved':         '#3b82f6',
                    'Processing':       '#8b5cf6',
                    'Delivered':        '#10b981',
                    'Cancelled':        '#ef4444',
                }
                STATUS_LABEL = {
                    'Pending_Approval': '🕐 Menunggu Persetujuan',
                    'Approved':         '✅ Disetujui',
                    'Processing':       '⚙️ Diproses',
                    'Delivered':        '📦 Terkirim',
                    'Cancelled':        '❌ Dibatalkan',
                }

                for _, po_row in df_riwayat.iterrows():
                    status_txt   = STATUS_LABEL.get(po_row['status'], po_row['status'])
                    status_color = STATUS_COLOR.get(po_row['status'], '#6b7280')

                    with st.expander(
                        f"PO #{po_row['po_id']}  ·  {po_row['tanggal']}  ·  "
                        f"Rp {float(po_row['total']):,.0f}  ·  {status_txt}",
                        expanded=False
                    ):
                        detail_col1, detail_col2 = st.columns([3, 1])
                        with detail_col2:
                            st.markdown(
                                f'<div style="background:{status_color};color:white;border-radius:8px;'
                                f'padding:8px 14px;font-weight:700;font-size:0.85rem;text-align:center;">'
                                f'{status_txt}</div>',
                                unsafe_allow_html=True
                            )
                            st.markdown(f"**Pembayaran:** {po_row['metode']}")
                            st.markdown(f"**Dipesan oleh:** {po_row['dipesan_oleh']}")
                            st.markdown(f"**Total:** **Rp {float(po_row['total']):,.0f}**")

                        with detail_col1:
                            df_det = run_query("""
                                SELECT p.nama_produk, p.kategori, p.satuan,
                                       od.kuantitas, od.harga_final,
                                       (od.kuantitas * od.harga_final) AS subtotal
                                FROM OrderDetails od
                                JOIN Products p ON od.product_id = p.product_id
                                WHERE od.po_id = %s
                            """, (int(po_row['po_id']),))

                            if not df_det.empty:
                                for _, det in df_det.iterrows():
                                    emoji_d = get_product_emoji(str(det['kategori']))
                                    st.markdown(
                                        f"{emoji_d} **{det['nama_produk']}** — "
                                        f"{int(det['kuantitas'])} {det['satuan']} × "
                                        f"Rp {float(det['harga_final']):,.0f} = "
                                        f"**Rp {float(det['subtotal']):,.0f}**"
                                    )
                            else:
                                st.caption("Detail item tidak tersedia.")

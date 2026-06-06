"""
06_dashboard.py — Dashboard Interaktif Segmentasi UMKM Jawa Barat
Peran   : Visualization / Dashboard Developer

Jalankan:
    streamlit run 06_dashboard.py
"""

import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

CLUSTER_COLORS = {
    1: "#FF5C8D",  # Stellar Strawberry — Siap Scale-Up
    2: "#732553",  # Pico Eggplant      — Tumbuh Butuh Fondasi
    3: "#85A3B2",  # Grauzone           — Padat Tapi Jenuh
}

CLUSTER_LABELS = {
    1: "Siap Scale-Up",
    2: "Tumbuh Butuh Fondasi",
    3: "Padat Tapi Jenuh",
}

REKOMENDASI = {
    1: "KUR ekspansi, pembiayaan digitalisasi & akses pasar luar daerah.",
    2: "KUR modal kerja + pendampingan pencatatan, pemasaran, dan legalitas.",
    3: "Pembiayaan inovasi produk & branding — bukan tambah modal baru.",
}

SEKTOR_RENAME = {
    "binaan_agribisnis":   "Agribisnis",
    "binaan_aksesoris":    "Aksesoris",
    "binaan_batik":        "Batik",
    "binaan_bordir":       "Bordir",
    "binaan_craft":        "Craft",
    "binaan_dekorasi":     "Dekorasi",
    "binaan_fashion":      "Fashion",
    "binaan_industri":     "Industri",
    "binaan_jasa":         "Jasa",
    "binaan_konveksi":     "Konveksi",
    "binaan_kuliner":      "Kuliner",
    "binaan_makanan":      "Makanan",
    "binaan_mebel":        "Mebel",
    "binaan_minuman":      "Minuman",
    "binaan_obat-obatan":  "Obat-obatan",
}

SEKTOR_COLORS = [
    "#FF5C8D", "#732553", "#85A3B2", "#E9D8C8", "#142030",
    "#FFB3C6", "#9B6B8A", "#B8CDD6", "#F4EDE5", "#4A6572",
    "#FF8FAB", "#5C1F3D", "#637B84", "#D4C5B8", "#1E3442",
]

# Koordinat sentroid tiap kab/kota Jawa Barat (lat, lon)
COORDS_JABAR = {
    "KABUPATEN BANDUNG":       (-7.04,  107.56),
    "KABUPATEN BANDUNG BARAT": (-6.84,  107.52),
    "KABUPATEN BEKASI":        (-6.28,  107.23),
    "KABUPATEN BOGOR":         (-6.65,  106.83),
    "KABUPATEN CIAMIS":        (-7.33,  108.36),
    "KABUPATEN CIANJUR":       (-6.82,  107.14),
    "KABUPATEN CIREBON":       (-6.73,  108.55),
    "KABUPATEN GARUT":         (-7.22,  107.90),
    "KABUPATEN INDRAMAYU":     (-6.33,  108.32),
    "KABUPATEN KARAWANG":      (-6.32,  107.30),
    "KABUPATEN KUNINGAN":      (-6.98,  108.48),
    "KABUPATEN MAJALENGKA":    (-6.84,  108.23),
    "KABUPATEN PANGANDARAN":   (-7.68,  108.53),
    "KABUPATEN PURWAKARTA":    (-6.56,  107.44),
    "KABUPATEN SUBANG":        (-6.57,  107.76),
    "KABUPATEN SUKABUMI":      (-6.84,  106.93),
    "KABUPATEN SUMEDANG":      (-6.85,  107.92),
    "KABUPATEN TASIKMALAYA":   (-7.34,  108.07),
    "KOTA BANDUNG":            (-6.92,  107.61),
    "KOTA BANJAR":             (-7.37,  108.54),
    "KOTA BEKASI":             (-6.24,  106.99),
    "KOTA BOGOR":              (-6.60,  106.79),
    "KOTA CIMAHI":             (-6.87,  107.54),
    "KOTA CIREBON":            (-6.71,  108.56),
    "KOTA DEPOK":              (-6.40,  106.82),
    "KOTA SUKABUMI":           (-6.92,  106.93),
    "KOTA TASIKMALAYA":        (-7.35,  108.22),
}

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Dashboard UMKM Jawa Barat",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CSS — Plus Jakarta Sans + card styles
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,opsz,wght@0,8..18,300..800;1,8..18,300..800&display=swap');

html, body, [class*="css"], .stMarkdown, p, span, div,
button, input, label, select, textarea,
h1, h2, h3, h4, h5, h6,
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

.stApp { background-color: #F7F8FA; }

/* Sidebar — fixed width, no drag-to-resize */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E8EAED;
    min-width: 280px !important;
    max-width: 280px !important;
    width: 280px !important;
}
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
[data-testid="stSidebarResizeHandle"] { display: none !important; }

.block-container {
    padding-top: 1.75rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1280px !important;
}

/* KPI card */
.kpi-card {
    background: #FFFFFF;
    border-radius: 16px;
    border: 1px solid #E8EAED;
    box-shadow: 0 1px 3px rgba(16,24,40,0.06), 0 1px 2px rgba(16,24,40,0.04);
    padding: 20px 22px 18px;
}
.kpi-label {
    font-size: 11.5px; font-weight: 600;
    color: #6B7280; letter-spacing: 0.06em;
    text-transform: uppercase; margin-bottom: 8px;
}
.kpi-value {
    font-size: 28px; font-weight: 800;
    color: #111827; line-height: 1; margin-bottom: 8px;
}
.kpi-sub { font-size: 12px; color: #9CA3AF; font-weight: 400; }

/* Chart card */
.chart-card {
    background: #FFFFFF;
    border-radius: 16px;
    border: 1px solid #E8EAED;
    box-shadow: 0 1px 3px rgba(16,24,40,0.06);
    padding: 22px 24px 16px;
    margin-bottom: 20px;
}

/* Section header */
.sec-head { margin-bottom: 18px; }
.sec-title {
    font-size: 17px; font-weight: 700;
    color: #111827; margin: 0 0 3px;
}
.sec-sub { font-size: 13px; color: #6B7280; margin: 0; }

/* Rekomendasi card */
.rek-card {
    border-radius: 12px;
    padding: 13px 15px;
    margin-bottom: 10px;
    border-left: 4px solid;
}
.rek-klaster { font-size: 11px; font-weight: 700; margin-bottom: 4px; }
.rek-text { font-size: 12px; color: #374151; line-height: 1.5; }

/* Sidebar brand */
.sidebar-brand {
    padding: 4px 0 20px;
    border-bottom: 1px solid #E8EAED;
    margin-bottom: 20px;
}
.sidebar-title {
    font-size: 18px; font-weight: 800;
    color: #111827; letter-spacing: -0.4px;
}
.sidebar-sub { font-size: 12px; color: #9CA3AF; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    clean_df    = pd.read_csv("clean_data/clean_dataset.csv")
    cluster_res = pd.read_csv("output/models/clustering_result.csv")
    cluster_pro = pd.read_csv("output/models/clustering_profile.csv", index_col=0)
    binaan_df   = pd.read_csv("clean_data/umkm_binaan_pivot.csv")

    # Gabungkan cluster ke clean_df
    if len(clean_df) == len(cluster_res):
        clean_df = clean_df.copy()
        clean_df["cluster"] = cluster_res["cluster"].values
    else:
        merge_cols = ["kepadatan_per_1000", "pertumbuhan_pct", "daya_beli"]
        clean_df = clean_df.merge(
            cluster_res[merge_cols + ["cluster"]], on=merge_cols, how="left"
        )

    clean_df["cluster"] = clean_df["cluster"].astype("Int64")
    clean_df["cluster_label"] = clean_df["cluster"].map(
        lambda x: f"Klaster {x} — {CLUSTER_LABELS.get(int(x), '')}" if pd.notna(x) else "–"
    )
    clean_df["nama_short"] = (
        clean_df["nama_kabupaten_kota"]
        .str.title()
        .str.replace("Kabupaten", "Kab.", regex=False)
    )

    clean_2023 = clean_df[clean_df["tahun"] == clean_df["tahun"].max()].reset_index(drop=True)

    # Rename sektor kolom
    binaan_df = binaan_df.rename(columns=SEKTOR_RENAME)
    sektor_cols = [v for v in SEKTOR_RENAME.values() if v in binaan_df.columns]

    return clean_df, clean_2023, cluster_pro, binaan_df, sektor_cols



# ─────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────

def plotly_base(fig, height=380, show_legend=True, margin=None):
    """Apply shared Plotly styling."""
    m = margin or dict(l=12, r=12, t=36, b=12)
    fig.update_layout(
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#374151", size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=height,
        margin=m,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font_size=11.5, bgcolor="rgba(0,0,0,0)", borderwidth=0,
            itemsizing="constant",
        ) if show_legend else dict(visible=False),
        hoverlabel=dict(
            font_family="Plus Jakarta Sans", font_size=12.5,
            bgcolor="white", bordercolor="#E8EAED",
        ),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E8EAED", tickfont_size=11.5, tickcolor="#E8EAED")
    fig.update_yaxes(gridcolor="#F2F4F7", linecolor="#E8EAED", tickfont_size=11.5, tickcolor="#E8EAED")
    return fig


def kpi_card(col, bg, label, value, sub):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{bg};">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def section(title, sub=""):
    st.markdown(f"""
    <div class="sec-head">
        <p class="sec-title">{title}</p>
        {"" if not sub else f'<p class="sec-sub">{sub}</p>'}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────────────────

try:
    clean_df, clean_2023, cluster_pro, binaan_df, sektor_cols = load_data()
except FileNotFoundError as e:
    st.error(f"**File tidak ditemukan:** {e}  \nPastikan pipeline 01–04 sudah dijalankan terlebih dahulu.")
    st.stop()

all_kab    = sorted(clean_df["nama_kabupaten_kota"].unique())
all_tahun  = sorted(clean_df["tahun"].unique())
n_clusters = int(clean_df["cluster"].nunique())


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-title">UMKM Jawa Barat</div>
        <div class="sidebar-sub">Segmentasi &amp; Analitik Wilayah</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Filter Data**")

    tahun_range = st.slider(
        "Periode Tahun",
        min_value=min(all_tahun), max_value=max(all_tahun),
        value=(min(all_tahun), max(all_tahun)), step=1,
    )

    kab_filter = st.multiselect(
        "Kabupaten / Kota",
        options=all_kab,
        placeholder="Semua wilayah",
        format_func=lambda x: str(x).title(),
    )

    cluster_filter = st.multiselect(
        "Klaster",
        options=list(range(1, n_clusters + 1)),
        default=list(range(1, n_clusters + 1)),
        format_func=lambda x: f"Klaster {x} — {CLUSTER_LABELS.get(x, '')}",
    )
    if not cluster_filter:
        cluster_filter = list(range(1, n_clusters + 1))

    st.divider()
    st.caption("Sumber data: Dinas Koperasi Jabar & BPS  \nPeriode: 2019–2023")


# ─────────────────────────────────────────────────────────────
# FILTER APPLY
# ─────────────────────────────────────────────────────────────

mask = (
    clean_df["tahun"].between(*tahun_range) &
    clean_df["cluster"].isin(cluster_filter)
)
if kab_filter:
    mask &= clean_df["nama_kabupaten_kota"].isin(kab_filter)
df = clean_df[mask].copy()

mask_2023 = clean_2023["cluster"].isin(cluster_filter)
if kab_filter:
    mask_2023 &= clean_2023["nama_kabupaten_kota"].isin(kab_filter)
df_2023 = clean_2023[mask_2023].copy()

mask_bin = binaan_df["tahun"].between(*tahun_range)
if kab_filter:
    mask_bin &= binaan_df["nama_kabupaten_kota"].isin(kab_filter)
df_bin = binaan_df[mask_bin].copy()


# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────

st.markdown("""
<h1 style="font-size:28px;font-weight:800;color:#111827;margin:0 0 6px;letter-spacing:-0.5px;">
    Segmentasi Potensi Wilayah UMKM
</h1>
<p style="font-size:14px;color:#6B7280;margin:0 0 24px;">
    Analisis berbasis kepadatan, pertumbuhan &amp; daya beli · Jawa Barat 2019–2023
</p>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────

total_umkm = int(df_2023["jumlah_umkm"].sum()) if len(df_2023) > 0 else 0
avg_tumbuh = df["pertumbuhan_pct"].mean() if len(df) > 0 else 0
avg_daya   = df_2023["daya_beli"].mean() if len(df_2023) > 0 else 0
n_kab      = df_2023["nama_kabupaten_kota"].nunique()

if len(df_2023) > 0:
    top_row = df_2023.sort_values("jumlah_umkm", ascending=False).iloc[0]
    top_kab = str(top_row["nama_kabupaten_kota"]).title().replace("Kabupaten", "Kab.")
    top_val = int(top_row["jumlah_umkm"])
else:
    top_kab, top_val = "–", 0

c1, c2, c3, c4 = st.columns(4, gap="small")
kpi_card(c1, "#FF5C8D", "Total UMKM", f"{total_umkm:,}", f"{n_kab} kab/kota · tahun {tahun_range[1]}")
kpi_card(c2, "#732553", "Rata-Rata Pertumbuhan", f"{avg_tumbuh:.1f}%", f"Periode {tahun_range[0]}–{tahun_range[1]}")
kpi_card(c3, "#85A3B2", "Rata-Rata Daya Beli", f"Rp {avg_daya:,.0f}", "Pengeluaran per kapita (ribu Rp)")
kpi_card(c4, "#142030", "UMKM Terbanyak", top_kab, f"{top_val:,} UMKM")

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# TREN UMKM
# ─────────────────────────────────────────────────────────────

section("Tren Jumlah UMKM per Tahun",
        "Perkembangan UMKM per kabupaten/kota — hover untuk detail")

kab_tren = kab_filter if kab_filter else (
    clean_df.groupby("nama_kabupaten_kota")["jumlah_umkm"]
    .sum().nlargest(8).index.tolist()
)

df_tren = clean_df[
    clean_df["nama_kabupaten_kota"].isin(kab_tren) &
    clean_df["tahun"].between(*tahun_range)
].copy()

fig_tren = px.line(
    df_tren,
    x="tahun", y="jumlah_umkm", color="nama_short",
    markers=True,
    labels={"tahun": "Tahun", "jumlah_umkm": "Jumlah UMKM", "nama_short": "Wilayah"},
    custom_data=["nama_short", "jumlah_umkm", "pertumbuhan_pct", "cluster_label"],
    color_discrete_sequence=px.colors.qualitative.Vivid,
)
fig_tren.update_traces(
    line_width=2.2, marker_size=7, marker_line_width=1.5, marker_line_color="white",
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "Jumlah UMKM: <b>%{customdata[1]:,}</b><br>"
        "Pertumbuhan: %{customdata[2]:.1f}%<br>"
        "%{customdata[3]}"
        "<extra></extra>"
    ),
)
plotly_base(fig_tren, height=360)

# Gradient area fill di bawah tiap line
vivid = px.colors.qualitative.Vivid
for i, trace in enumerate(fig_tren.data):
    hex_c = vivid[i % len(vivid)]
    try:
        r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
        trace.update(fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.07)")
    except Exception:
        pass

fig_tren.update_xaxes(tickmode="linear", dtick=1)
fig_tren.update_yaxes(tickformat=",")
st.plotly_chart(fig_tren, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SCATTER KLASTER + PROFIL KLASTER
# ─────────────────────────────────────────────────────────────

section("Sebaran & Profil Klaster UMKM",
        "Kepadatan vs Daya Beli per kab/kota · ukuran bubble ∝ pertumbuhan · hover untuk detail lengkap")

col_l, col_r = st.columns([3, 2], gap="large")

with col_l:

    df_sc = df_2023.dropna(subset=["cluster"]).copy()
    df_sc["klaster_str"] = df_sc["cluster"].map(
        lambda x: f"Klaster {int(x)} — {CLUSTER_LABELS.get(int(x), '')}"
    )
    df_sc["bubble"] = np.clip(np.abs(df_sc["pertumbuhan_pct"].fillna(0)) * 5 + 10, 10, 45)

    color_map = {f"Klaster {k} — {CLUSTER_LABELS.get(k, '')}": v for k, v in CLUSTER_COLORS.items()}

    fig_sc = px.scatter(
        df_sc,
        x="kepadatan_per_1000", y="daya_beli",
        color="klaster_str", size="bubble", size_max=45,
        hover_name="nama_short",
        color_discrete_map=color_map,
        custom_data=["nama_short", "klaster_str", "kepadatan_per_1000",
                     "daya_beli", "pertumbuhan_pct", "sektor_dominan"],
        labels={
            "kepadatan_per_1000": "Kepadatan UMKM / 1.000 Penduduk",
            "daya_beli": "Daya Beli (ribu Rp/kapita)",
            "klaster_str": "Klaster",
        },
    )
    fig_sc.update_traces(
        marker_opacity=0.82,
        marker_line_width=1.5,
        marker_line_color="white",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "<span style='color:#6B7280'>%{customdata[1]}</span><br><br>"
            "Kepadatan: <b>%{customdata[2]:.1f}</b> per 1.000<br>"
            "Daya Beli: <b>Rp %{customdata[3]:,.0f}</b><br>"
            "Pertumbuhan: <b>%{customdata[4]:.1f}%</b><br>"
            "Sektor: %{customdata[5]}"
            "<extra></extra>"
        ),
    )
    plotly_base(fig_sc, height=420,
                margin=dict(l=12, r=12, t=36, b=12))
    fig_sc.update_layout(legend=dict(
        orientation="v", yanchor="top", y=1, xanchor="left", x=0,
        font_size=11.5, bgcolor="rgba(255,255,255,0.8)",
        borderwidth=1, bordercolor="#E8EAED",
    ))
    fig_sc.update_yaxes(tickformat=",")
    st.plotly_chart(fig_sc, use_container_width=True)

with col_r:
    st.markdown('<p class="sec-title" style="margin-bottom:16px;">Profil &amp; Rekomendasi per Klaster</p>', unsafe_allow_html=True)

    prof = cluster_pro.reset_index()
    prof.columns = ["cluster", "Kepadatan\n/1.000", "Pertumbuhan (%)", "Daya Beli"]
    prof_f = prof[prof["cluster"].isin(cluster_filter)]
    prof_long = prof_f.melt("cluster", var_name="Indikator", value_name="Nilai")
    prof_long["Klaster"] = prof_long["cluster"].map(lambda x: f"Klaster {int(x)}")

    fig_prof = px.bar(
        prof_long, x="Nilai", y="Indikator", color="Klaster",
        barmode="group", orientation="h",
        color_discrete_map={f"Klaster {k}": v for k, v in CLUSTER_COLORS.items()},
        custom_data=["Klaster", "Indikator", "Nilai"],
    )
    fig_prof.update_traces(
        marker_line_width=0,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]}: <b>%{customdata[2]:,.1f}</b>"
            "<extra></extra>"
        ),
    )
    plotly_base(fig_prof, height=220)
    fig_prof.update_xaxes(showgrid=True, gridcolor="#F2F4F7", showticklabels=False)
    fig_prof.update_yaxes(autorange="reversed", showgrid=False)
    st.plotly_chart(fig_prof, use_container_width=True)

    st.markdown("**Rekomendasi Pembiayaan**")
    for cid in sorted(cluster_filter):
        c = CLUSTER_COLORS.get(cid, "#999")
        st.markdown(f"""
        <div class="rek-card" style="background:{c}10;border-color:{c};">
            <div class="rek-klaster" style="color:{c};">
                Klaster {cid} — {CLUSTER_LABELS.get(cid, '')}
            </div>
            <div class="rek-text">{REKOMENDASI.get(cid, '–')}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SEKTOR BREAKDOWN
# ─────────────────────────────────────────────────────────────

section("Komposisi UMKM Binaan per Sektor",
        "Pilih kabupaten/kota untuk melihat tren sektor dari tahun ke tahun")

col_sel, _ = st.columns([2, 3])
with col_sel:
    kab_sektor = st.selectbox(
        "Pilih Wilayah",
        options=all_kab,
        format_func=lambda x: str(x).title(),
        key="kab_sektor",
        label_visibility="collapsed",
    )

df_sek = binaan_df[
    (binaan_df["nama_kabupaten_kota"] == kab_sektor) &
    (binaan_df["tahun"].between(*tahun_range))
].copy()

avail_sek = [s for s in sektor_cols if s in df_sek.columns]

if len(df_sek) > 0 and avail_sek:
    sek_long = df_sek[["tahun"] + avail_sek].melt(
        "tahun", var_name="Sektor", value_name="Jumlah UMKM Binaan"
    )
    # Top 10 sektor by total
    top10 = (sek_long.groupby("Sektor")["Jumlah UMKM Binaan"]
             .sum().nlargest(10).index.tolist())
    sek_top = sek_long[sek_long["Sektor"].isin(top10)]

    col_sbar, col_spie = st.columns([2, 1], gap="large")

    with col_sbar:
        fig_sek = px.bar(
            sek_top, x="tahun", y="Jumlah UMKM Binaan", color="Sektor",
            barmode="stack",
            custom_data=["Sektor", "Jumlah UMKM Binaan"],
            color_discrete_sequence=SEKTOR_COLORS,
            labels={"tahun": "Tahun", "Jumlah UMKM Binaan": "Jumlah UMKM Binaan"},
            title=f"Tren Sektor · {str(kab_sektor).title()}",
        )
        fig_sek.update_traces(
            marker_line_width=0,
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,} UMKM<extra></extra>",
        )
        plotly_base(fig_sek, height=340, show_legend=False)
        fig_sek.update_xaxes(tickmode="linear", dtick=1)
        fig_sek.update_yaxes(tickformat=",")
        fig_sek.update_layout(legend=dict(
            orientation="v", yanchor="top", y=1, xanchor="left", x=1.01,
            font_size=11,
        ))
        st.plotly_chart(fig_sek, use_container_width=True)

    with col_spie:
        # Pie: total per sektor (semua tahun filter)
        sek_total = (sek_long.groupby("Sektor")["Jumlah UMKM Binaan"]
                     .sum().reset_index().sort_values("Jumlah UMKM Binaan", ascending=False))
        fig_pie = px.pie(
            sek_total, values="Jumlah UMKM Binaan", names="Sektor",
            color_discrete_sequence=SEKTOR_COLORS,
            title=f"Komposisi Total",
            hole=0.4,
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>%{value:,} UMKM<br>%{percent}<extra></extra>",
        )
        plotly_base(fig_pie, height=340, show_legend=False)
        fig_pie.update_layout(
            legend=dict(
                orientation="v", yanchor="middle", y=0.5,
                xanchor="left", x=1.01, font_size=10,
            ),
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("Data sektor tidak tersedia untuk filter ini.")

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PETA SEBARAN
# ─────────────────────────────────────────────────────────────

section("Peta Sebaran Klaster Jawa Barat",
        "Ukuran bubble ∝ jumlah UMKM · warna = klaster · hover untuk detail")

df_map = df_2023.dropna(subset=["cluster"]).copy()
df_map["lat"] = df_map["nama_kabupaten_kota"].map(
    lambda x: COORDS_JABAR.get(str(x).upper(), (None, None))[0]
)
df_map["lon"] = df_map["nama_kabupaten_kota"].map(
    lambda x: COORDS_JABAR.get(str(x).upper(), (None, None))[1]
)
df_map = df_map.dropna(subset=["lat", "lon"])
df_map["klaster_str"] = df_map["cluster"].map(
    lambda x: f"Klaster {int(x)} — {CLUSTER_LABELS.get(int(x), '')}"
)

color_map_peta = {
    f"Klaster {k} — {CLUSTER_LABELS.get(k, '')}": v for k, v in CLUSTER_COLORS.items()
}

fig_peta = px.scatter_mapbox(
    df_map,
    lat="lat", lon="lon",
    color="klaster_str",
    size="jumlah_umkm",
    size_max=55,
    hover_name="nama_short",
    color_discrete_map=color_map_peta,
    zoom=7.2,
    center={"lat": -7.0, "lon": 107.6},
    mapbox_style="open-street-map",
    custom_data=["nama_short", "klaster_str", "jumlah_umkm",
                 "kepadatan_per_1000", "daya_beli", "sektor_dominan"],
    labels={"klaster_str": "Klaster"},
)
fig_peta.update_traces(
    marker_opacity=0.80,
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "<span style='color:#6B7280'>%{customdata[1]}</span><br><br>"
        "Jumlah UMKM: <b>%{customdata[2]:,}</b><br>"
        "Kepadatan: <b>%{customdata[3]:.1f}</b> per 1.000<br>"
        "Daya Beli: <b>Rp %{customdata[4]:,.0f}</b><br>"
        "Sektor: %{customdata[5]}"
        "<extra></extra>"
    ),
)
plotly_base(fig_peta, height=540, margin=dict(l=0, r=0, t=0, b=0))
fig_peta.update_layout(legend=dict(
    orientation="v", yanchor="top", y=0.97, xanchor="left", x=0.01,
    bgcolor="rgba(255,255,255,0.9)", borderwidth=1, bordercolor="#E8EAED",
    font_size=12,
))
st.plotly_chart(fig_peta, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# DATA TABLE
# ─────────────────────────────────────────────────────────────

with st.expander("Lihat & Unduh Data Lengkap", expanded=False):
    cols_show = [c for c in [
        "nama_kabupaten_kota", "tahun", "cluster_label",
        "jumlah_umkm", "kepadatan_per_1000", "pertumbuhan_pct",
        "daya_beli", "sektor_dominan", "share_sektor_dominan_pct",
    ] if c in df.columns]

    df_show = df[cols_show].rename(columns={
        "nama_kabupaten_kota":      "Kab/Kota",
        "tahun":                    "Tahun",
        "cluster_label":            "Klaster",
        "jumlah_umkm":              "Jml. UMKM",
        "kepadatan_per_1000":       "Kepadatan/1.000",
        "pertumbuhan_pct":          "Pertumbuhan (%)",
        "daya_beli":                "Daya Beli (ribu Rp)",
        "sektor_dominan":           "Sektor Dominan",
        "share_sektor_dominan_pct": "Share Sektor (%)",
    }).sort_values(["Tahun", "Kab/Kota"])

    st.dataframe(df_show, use_container_width=True, hide_index=True)

    st.download_button(
        label="Download CSV",
        data=df_show.to_csv(index=False).encode("utf-8"),
        file_name=f"umkm_jabar_{tahun_range[0]}-{tahun_range[1]}.csv",
        mime="text/csv",
    )

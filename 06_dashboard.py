"""
06_dashboard.py — Dashboard Interaktif Segmentasi UMKM Jawa Barat
Peran   : Visualization / Dashboard Developer

Jalankan:
    streamlit run 06_dashboard.py

Pastikan sudah menjalankan 01–05 terlebih dahulu agar output tersedia.
"""

import os
import math
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import folium
import streamlit as st
import streamlit.components.v1 as components

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# KONSTANTA
# ─────────────────────────────────────────

CLUSTER_COLORS = {
    1: "#1D9E75",
    2: "#378ADD",
    3: "#EF9F27",
    4: "#888780",
}

CLUSTER_LABELS = {
    1: "Siap Scale-Up",
    2: "Tumbuh Butuh Fondasi",
    3: "Padat Tapi Jenuh",
    4: "Perlu Fondasi Dulu",
}

CLUSTER_LABELS_FULL = {
    1: "Klaster 1 — Siap Scale-Up",
    2: "Klaster 2 — Tumbuh Butuh Fondasi",
    3: "Klaster 3 — Padat Tapi Jenuh",
    4: "Klaster 4 — Perlu Fondasi Dulu",
}

REKOMENDASI = {
    1: "KUR ekspansi, pembiayaan digitalisasi & akses pasar luar daerah.",
    2: "KUR modal kerja + pendampingan pencatatan, pemasaran, dan legalitas.",
    3: "Pembiayaan inovasi produk & branding — bukan tambah modal baru.",
    4: "Hibah / dana bergulir + pelatihan dasar kewirausahaan.",
}


# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────

@st.cache_data
def load_data():
    clean_df        = pd.read_csv("clean_data/clean_dataset.csv")
    cluster_result  = pd.read_csv("output/models/clustering_result.csv")
    cluster_profile = pd.read_csv("output/models/clustering_profile.csv", index_col=0)

    clean_2023 = clean_df[clean_df["tahun"] == 2023].reset_index(drop=True)

    if len(clean_2023) == len(cluster_result):
        clean_2023 = clean_2023.copy()
        clean_2023["cluster"] = cluster_result["cluster"].values
    else:
        merge_cols = ["kepadatan_per_1000", "pertumbuhan_pct", "daya_beli"]
        clean_2023 = clean_2023.merge(
            cluster_result[merge_cols + ["cluster"]],
            on=merge_cols, how="left",
        )

    return clean_df, clean_2023, cluster_profile


# ─────────────────────────────────────────
# CHART FUNCTIONS
# ─────────────────────────────────────────

def chart_bar(cluster_profile):
    metrics      = ["Rata-Rata Kepadatan per 1000", "Rata-Rata Pertumbuhan PCT", "Rata-Rata Daya Beli"]
    labels_short = ["Kepadatan\nper 1.000 Penduduk", "Pertumbuhan\nUMKM (%)", "Daya Beli\n(ribu Rp/kapita)"]
    n_clusters   = len(cluster_profile)
    x            = np.arange(len(metrics))
    width        = 0.22
    offsets      = np.linspace(-(n_clusters - 1) / 2, (n_clusters - 1) / 2, n_clusters) * width

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    for i, (cid, row) in enumerate(cluster_profile.iterrows()):
        vals  = [row.get(m, 0) for m in metrics]
        color = CLUSTER_COLORS.get(cid, "#CCCCCC")
        label = CLUSTER_LABELS_FULL.get(cid, f"Klaster {cid}")
        bars  = ax.bar(x + offsets[i], vals, width, label=label,
                       color=color, alpha=0.88, edgecolor="white", linewidth=0.8, zorder=3)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=8, color="#333333")

    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, fontsize=10)
    ax.set_ylabel("Nilai Rata-Rata", fontsize=10)
    ax.set_title("Profil Rata-Rata Indikator per Klaster UMKM — Jawa Barat 2019–2023",
                 fontsize=13, fontweight="bold", pad=14)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=8)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    return fig


def chart_radar(cluster_profile):
    metrics      = ["Rata-Rata Kepadatan per 1000", "Rata-Rata Pertumbuhan PCT", "Rata-Rata Daya Beli"]
    labels_short = ["Kepadatan\nper 1.000", "Pertumbuhan\nUMKM (%)", "Daya Beli"]
    N            = len(metrics)
    angles       = [n / float(N) * 2 * math.pi for n in range(N)]
    angles      += angles[:1]

    df_norm = cluster_profile[metrics].copy()
    for col in metrics:
        cmin, cmax = df_norm[col].min(), df_norm[col].max()
        df_norm[col] = (df_norm[col] - cmin) / (cmax - cmin) if cmax > cmin else 0.5

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels_short, fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7, color="#999999")
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.grid(True, linestyle="--", alpha=0.3)

    for cid, row in df_norm.iterrows():
        vals   = row[metrics].tolist() + [row[metrics[0]]]
        color  = CLUSTER_COLORS.get(cid, "#CCCCCC")
        label  = CLUSTER_LABELS_FULL.get(cid, f"Klaster {cid}")
        ax.plot(angles, vals, "o-", linewidth=2, color=color, label=label)
        ax.fill(angles, vals, alpha=0.12, color=color)

    ax.set_title("Radar Chart — Profil Klaster UMKM\n(Nilai dinormalisasi 0–1)",
                 fontsize=12, fontweight="bold", pad=28)
    ax.legend(loc="upper right", bbox_to_anchor=(1.4, 1.15), fontsize=8, framealpha=0.9)
    plt.tight_layout()
    return fig


def chart_scatter(clean_2023):
    fig, ax = plt.subplots(figsize=(11, 7))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    for cid in sorted(clean_2023["cluster"].dropna().unique()):
        sub   = clean_2023[clean_2023["cluster"] == cid]
        color = CLUSTER_COLORS.get(int(cid), "#CCCCCC")
        label = CLUSTER_LABELS_FULL.get(int(cid), f"Klaster {cid}")
        sizes = np.clip(np.abs(sub["pertumbuhan_pct"].fillna(0)) * 8 + 40, 30, 350)
        ax.scatter(sub["kepadatan_per_1000"], sub["daya_beli"],
                   s=sizes, c=color, alpha=0.78,
                   edgecolors="white", linewidths=0.6, label=label, zorder=3)

    highlight = ["KOTA BANDUNG", "KABUPATEN BOGOR", "KABUPATEN GARUT",
                 "KOTA BEKASI", "KABUPATEN SUKABUMI"]
    for _, row in clean_2023.iterrows():
        if row.get("nama_kabupaten_kota", "") in highlight:
            nama = str(row["nama_kabupaten_kota"]).title().replace("Kabupaten", "Kab.")
            ax.annotate(nama, xy=(row["kepadatan_per_1000"], row["daya_beli"]),
                        xytext=(6, 4), textcoords="offset points", fontsize=7.5,
                        color="#333333",
                        arrowprops=dict(arrowstyle="-", color="#BBBBBB", lw=0.8))

    ax.set_xlabel("Kepadatan UMKM per 1.000 Penduduk", fontsize=10)
    ax.set_ylabel("Daya Beli (Pengeluaran per Kapita, ribu Rp)", fontsize=10)
    ax.set_title("Scatter Plot Klaster — Kepadatan vs Daya Beli\n(Ukuran bubble ∝ Pertumbuhan UMKM %)",
                 fontsize=12, fontweight="bold", pad=14)
    ax.legend(loc="upper left", framealpha=0.9, fontsize=8)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.xaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    return fig


@st.cache_data
def build_folium_map(clean_2023_json: str) -> str:
    """Return folium map as HTML string. Input as JSON string for cache compatibility."""
    import requests as req

    clean_2023 = pd.read_json(clean_2023_json, orient="records")

    sources = [
        "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/jawa-barat.geojson",
        "https://raw.githubusercontent.com/ans-4175/peta-indonesia-geojson/master/jawa-barat.geojson",
    ]
    geojson = None
    for url in sources:
        try:
            r = req.get(url, timeout=15)
            if r.status_code == 200:
                geojson = r.json()
                break
        except Exception:
            continue

    if geojson is None:
        return None

    df_map = clean_2023[["nama_kabupaten_kota", "cluster"]].dropna().copy()
    df_map["cluster"] = df_map["cluster"].astype(int)

    m = folium.Map(location=[-7.0, 107.5], zoom_start=8, tiles="CartoDB positron")

    def style_fn(feature):
        geo_name = (feature.get("properties", {}).get("name", "") or
                    feature.get("properties", {}).get("NAME_2", "") or
                    feature.get("properties", {}).get("kabkot", ""))
        geo_name = str(geo_name).upper().strip()
        cid = None
        for _, row in df_map.iterrows():
            kab = str(row["nama_kabupaten_kota"]).upper()
            if geo_name in kab or kab in geo_name or any(p in geo_name for p in kab.split() if len(p) > 4):
                cid = int(row["cluster"])
                break
        return {"fillColor": CLUSTER_COLORS.get(cid, "#D3D3D3"),
                "color": "#FFFFFF", "weight": 1.5, "fillOpacity": 0.75}

    folium.GeoJson(
        geojson,
        name="Klaster UMKM",
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=list(geojson["features"][0]["properties"].keys())[:2],
            aliases=["Wilayah:"] * 2,
            sticky=True,
        ),
    ).add_to(m)

    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;background:white;
                padding:14px 18px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.18);
                font-family:Arial;font-size:13px;">
      <b style="font-size:14px">Klaster UMKM Jawa Barat</b><br><br>
      <span style="background:#1D9E75;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Klaster 1 — Siap Scale-Up<br>
      <span style="background:#378ADD;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Klaster 2 — Tumbuh Butuh Fondasi<br>
      <span style="background:#EF9F27;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Klaster 3 — Padat Tapi Jenuh<br>
      <span style="background:#888780;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Klaster 4 — Perlu Fondasi Dulu<br>
      <span style="background:#D3D3D3;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Tidak tersedia
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m._repr_html_()


# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    page_title="Dashboard UMKM Jawa Barat",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📊 Dashboard UMKM Jabar")
    st.markdown("**Segmentasi Potensi Wilayah UMKM**  \nuntuk Rekomendasi Pembiayaan")
    st.divider()
    st.markdown("**Sumber Data**")
    st.markdown("- Dinas Koperasi Jawa Barat  \n- BPS Jawa Barat")
    st.markdown("**Periode:** 2019–2023")
    st.markdown("**Model:** K-Means Clustering")
    st.divider()

    # Filter klaster
    st.markdown("**Filter Klaster**")
    semua_klaster = list(CLUSTER_LABELS.keys())
    pilihan = st.multiselect(
        "Tampilkan klaster:",
        options=semua_klaster,
        default=semua_klaster,
        format_func=lambda x: f"Klaster {x} — {CLUSTER_LABELS[x]}",
    )
    if not pilihan:
        pilihan = semua_klaster

    st.divider()
    st.caption("Tugas Besar Data Analytics · 2024")


# ─────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────

try:
    clean_df, clean_2023, cluster_profile = load_data()
except FileNotFoundError as e:
    st.error(f"File tidak ditemukan: {e}\n\nPastikan sudah menjalankan pipeline 01–04 terlebih dahulu.")
    st.stop()

# Terapkan filter klaster ke scatter data
clean_filtered = clean_2023[clean_2023["cluster"].isin(pilihan)]
profile_filtered = cluster_profile[cluster_profile.index.isin(pilihan)]


# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.title("Segmentasi Potensi Wilayah UMKM Jawa Barat")
st.markdown("Analisis K-Means Clustering terhadap **kepadatan UMKM**, **pertumbuhan**, dan **daya beli** per kabupaten/kota.")
st.divider()


# ─────────────────────────────────────────
# METRIK RINGKASAN
# ─────────────────────────────────────────

n_kab    = clean_2023["nama_kabupaten_kota"].nunique() if "nama_kabupaten_kota" in clean_2023.columns else "-"
n_klaster = int(clean_2023["cluster"].nunique())
tahun_min = int(clean_df["tahun"].min()) if "tahun" in clean_df.columns else "-"
tahun_max = int(clean_df["tahun"].max()) if "tahun" in clean_df.columns else "-"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Kab/Kota", n_kab)
col2.metric("Jumlah Klaster", n_klaster)
col3.metric("Periode Data", f"{tahun_min}–{tahun_max}")
col4.metric("Total Baris Data", f"{len(clean_df):,}")

st.divider()


# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Profil Klaster",
    "🔵 Scatter Plot",
    "🗺️ Peta Choropleth",
    "📄 Data Tabel",
])


# ── TAB 1: Profil Klaster ──────────────────

with tab1:
    st.subheader("Profil Rata-Rata Indikator per Klaster")

    col_bar, col_radar = st.columns([3, 2])

    with col_bar:
        st.markdown("**Bar Chart**")
        if len(profile_filtered) == 0:
            st.info("Tidak ada klaster yang dipilih.")
        else:
            fig_bar = chart_bar(profile_filtered)
            st.pyplot(fig_bar, use_container_width=True)
            plt.close(fig_bar)

    with col_radar:
        st.markdown("**Radar Chart (Ternormalisasi)**")
        if len(profile_filtered) == 0:
            st.info("Tidak ada klaster yang dipilih.")
        else:
            fig_radar = chart_radar(profile_filtered)
            st.pyplot(fig_radar, use_container_width=True)
            plt.close(fig_radar)

    st.divider()
    st.subheader("Rekomendasi Pembiayaan per Klaster")

    cols = st.columns(len(pilihan)) if len(pilihan) > 0 else st.columns(1)
    for col, cid in zip(cols, sorted(pilihan)):
        with col:
            color = CLUSTER_COLORS.get(cid, "#CCCCCC")
            st.markdown(
                f"""<div style="background:{color}22;border-left:4px solid {color};
                    padding:12px 14px;border-radius:6px;margin-bottom:8px;">
                    <b style="color:{color}">Klaster {cid}</b><br>
                    <span style="font-size:13px;font-weight:600">{CLUSTER_LABELS.get(cid)}</span><br><br>
                    <span style="font-size:12px">{REKOMENDASI.get(cid, "-")}</span>
                </div>""",
                unsafe_allow_html=True,
            )


# ── TAB 2: Scatter Plot ────────────────────

with tab2:
    st.subheader("Scatter Plot — Kepadatan vs Daya Beli")
    st.caption("Ukuran bubble proporsional dengan pertumbuhan UMKM (%).")

    if len(clean_filtered) == 0:
        st.info("Tidak ada data untuk klaster yang dipilih.")
    else:
        fig_scatter = chart_scatter(clean_filtered)
        st.pyplot(fig_scatter, use_container_width=True)
        plt.close(fig_scatter)


# ── TAB 3: Peta Choropleth ─────────────────

with tab3:
    st.subheader("Peta Klaster UMKM — Jawa Barat 2023")
    st.caption("Setiap kabupaten/kota diwarnai sesuai klaster hasil K-Means.")

    with st.spinner("Memuat peta..."):
        map_html = build_folium_map(clean_2023.to_json(orient="records"))

    if map_html is None:
        # Fallback ke file HTML yang sudah disimpan
        html_path = "output/visualizations/peta_klaster_jabar.html"
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                map_html = f.read()
            st.info("Peta dimuat dari file lokal (GeoJSON tidak bisa diunduh saat ini).")
        else:
            st.warning("Peta tidak tersedia. Jalankan 05_visualize.py terlebih dahulu atau pastikan koneksi internet aktif.")
            map_html = None

    if map_html:
        components.html(map_html, height=550, scrolling=False)


# ── TAB 4: Tabel Data ──────────────────────

with tab4:
    st.subheader("Data Kab/Kota per Klaster (2023)")

    cols_tampil = [c for c in ["nama_kabupaten_kota", "cluster", "kepadatan_per_1000",
                                "pertumbuhan_pct", "daya_beli"] if c in clean_filtered.columns]
    df_tampil = clean_filtered[cols_tampil].copy()

    if "cluster" in df_tampil.columns:
        df_tampil["klaster"] = df_tampil["cluster"].map(
            lambda x: f"Klaster {int(x)} — {CLUSTER_LABELS.get(int(x), '')}" if pd.notna(x) else "-"
        )
        df_tampil = df_tampil.drop(columns=["cluster"])

    rename_map = {
        "nama_kabupaten_kota": "Kab/Kota",
        "kepadatan_per_1000":  "Kepadatan per 1.000",
        "pertumbuhan_pct":     "Pertumbuhan (%)",
        "daya_beli":           "Daya Beli (ribu Rp)",
        "klaster":             "Klaster",
    }
    df_tampil = df_tampil.rename(columns=rename_map)

    st.dataframe(
        df_tampil.sort_values("Klaster"),
        use_container_width=True,
        hide_index=True,
    )

    csv = df_tampil.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="segmentasi_umkm_jabar_2023.csv",
        mime="text/csv",
    )

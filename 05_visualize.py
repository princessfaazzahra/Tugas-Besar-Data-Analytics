"""
05_visualize.py  —  Data Pipeline: Tahap N (iNterpret) — Visualisasi
Peran   : Visualization / Dashboard Developer

Tasks:
  1. Bar chart profil klaster (3 indikator per klaster)
  2. Radar chart profil klaster
  3. Scatter plot final diwarnai per klaster
  4. Peta choropleth Jawa Barat — klaster per kab/kota (folium)

Input : clean_data/clean_dataset.csv
        output/models/clustering_result.csv
        output/models/clustering_profile.csv
Output: output/visualizations/bar_profil_klaster.png
        output/visualizations/radar_profil_klaster.png
        output/visualizations/scatter_klaster.png
        output/visualizations/peta_klaster_jabar.html
"""

import os
import json
import math
import warnings
import requests
import tempfile

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
import folium

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# 0. SETUP
# ─────────────────────────────────────────

FOLDER_OUTPUT = "output/visualizations"
os.makedirs(FOLDER_OUTPUT, exist_ok=True)

# Palet warna klaster — konsisten di semua chart
CLUSTER_COLORS = {
    1: "#1D9E75",   # Hijau  — Siap scale-up
    2: "#378ADD",   # Biru   — Tumbuh butuh fondasi
    3: "#EF9F27",   # Amber  — Padat tapi jenuh
    4: "#888780",   # Abu    — Perlu fondasi dulu (jika K=4)
}

CLUSTER_LABELS = {
    1: "Klaster 1 — Siap Scale-Up",
    2: "Klaster 2 — Tumbuh Butuh Fondasi",
    3: "Klaster 3 — Padat Tapi Jenuh",
    4: "Klaster 4 — Perlu Fondasi Dulu",
}

CLUSTER_COLORS_MAP = {
    1: "#1D9E75",
    2: "#378ADD",
    3: "#EF9F27",
    4: "#888780",
}


# ─────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────

def load_data():
    """Membaca semua dataset yang dibutuhkan."""
    clean_df       = pd.read_csv("clean_data/clean_dataset.csv")
    cluster_result = pd.read_csv("output/models/clustering_result.csv")
    cluster_profile = pd.read_csv("output/models/clustering_profile.csv", index_col=0)

    # Gabungkan label klaster ke clean_dataset (join by index baris)
    # clustering_result hanya berisi fitur + cluster, tanpa nama kab/kota
    # → kita perlu ambil nama dari clean_dataset dengan tahun tertentu
    # Ambil data tahun terbaru (2023) sebagai representasi per kab/kota
    clean_2023 = clean_df[clean_df["tahun"] == 2023].reset_index(drop=True)

    # Pastikan panjang sama
    if len(clean_2023) == len(cluster_result):
        clean_2023 = clean_2023.copy()
        clean_2023["cluster"] = cluster_result["cluster"].values
    else:
        # Fallback: merge berdasarkan 3 fitur (exact match)
        merge_cols = ["kepadatan_per_1000", "pertumbuhan_pct", "daya_beli"]
        clean_2023 = clean_2023.merge(
            cluster_result[merge_cols + ["cluster"]],
            on=merge_cols, how="left"
        )

    return clean_df, clean_2023, cluster_profile


# ─────────────────────────────────────────
# 2. BAR CHART PROFIL KLASTER
# ─────────────────────────────────────────

def viz_bar_profil(cluster_profile):
    """
    Bar chart kelompok: membandingkan rata-rata 3 indikator per klaster.
    Satu grup bar per indikator, tiap bar adalah satu klaster.
    """
    n_clusters = len(cluster_profile)
    n_metrics  = 3
    metrics    = ["Rata-Rata Kepadatan per 1000", "Rata-Rata Pertumbuhan PCT", "Rata-Rata Daya Beli"]
    labels_short = ["Kepadatan\nper 1.000\nPenduduk", "Pertumbuhan\nUMKM (%)", "Daya Beli\n(Pengeluaran\nper Kapita)"]

    x      = np.arange(n_metrics)
    width  = 0.22
    offsets = np.linspace(-(n_clusters-1)/2, (n_clusters-1)/2, n_clusters) * width

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    for i, (cluster_id, row) in enumerate(cluster_profile.iterrows()):
        values = [row.get(m, 0) for m in metrics]
        color  = CLUSTER_COLORS_MAP.get(cluster_id, "#CCCCCC")
        label  = CLUSTER_LABELS.get(cluster_id, f"Klaster {cluster_id}")
        bars   = ax.bar(x + offsets[i], values, width, label=label,
                        color=color, alpha=0.88, edgecolor="white", linewidth=0.8,
                        zorder=3)
        # Nilai di atas bar
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=8.5,
                    fontweight="500", color="#333333")

    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, fontsize=11)
    ax.set_ylabel("Nilai Rata-Rata", fontsize=11)
    ax.set_title("Profil Rata-Rata Indikator per Klaster UMKM\nJawa Barat 2019–2023",
                 fontsize=14, fontweight="bold", pad=16)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)

    plt.tight_layout()
    path = os.path.join(FOLDER_OUTPUT, "bar_profil_klaster.png")
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  [OK] Tersimpan: {path}")


# ─────────────────────────────────────────
# 3. RADAR CHART PROFIL KLASTER
# ─────────────────────────────────────────

def viz_radar_profil(cluster_profile):
    """
    Radar / spider chart: tiap klaster punya satu poligon.
    Nilai dinormalisasi 0-1 agar bisa dibandingkan.
    """
    metrics       = ["Rata-Rata Kepadatan per 1000", "Rata-Rata Pertumbuhan PCT", "Rata-Rata Daya Beli"]
    labels_short  = ["Kepadatan\nper 1.000", "Pertumbuhan\nUMKM (%)", "Daya Beli"]
    N             = len(metrics)
    angles        = [n / float(N) * 2 * math.pi for n in range(N)]
    angles       += angles[:1]  # tutup poligon

    # Normalisasi min-max per metrik
    df_norm = cluster_profile[metrics].copy()
    for col in metrics:
        col_min, col_max = df_norm[col].min(), df_norm[col].max()
        if col_max > col_min:
            df_norm[col] = (df_norm[col] - col_min) / (col_max - col_min)
        else:
            df_norm[col] = 0.5

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels_short, fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7, color="#999999")
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.grid(True, linestyle="--", alpha=0.3)

    for cluster_id, row in df_norm.iterrows():
        values  = row[metrics].tolist()
        values += values[:1]
        color   = CLUSTER_COLORS_MAP.get(cluster_id, "#CCCCCC")
        label   = CLUSTER_LABELS.get(cluster_id, f"Klaster {cluster_id}")
        ax.plot(angles, values, "o-", linewidth=2, color=color, label=label)
        ax.fill(angles, values, alpha=0.12, color=color)

    ax.set_title("Radar Chart — Profil Klaster UMKM Jawa Barat\n(Nilai dinormalisasi 0–1)",
                 fontsize=13, fontweight="bold", pad=28)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=9, framealpha=0.9)

    plt.tight_layout()
    path = os.path.join(FOLDER_OUTPUT, "radar_profil_klaster.png")
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  [OK] Tersimpan: {path}")


# ─────────────────────────────────────────
# 4. SCATTER PLOT KLASTER (KEPADATAN vs DAYA BELI)
# ─────────────────────────────────────────

def viz_scatter_klaster(clean_2023):
    """
    Scatter plot kepadatan_per_1000 vs daya_beli, diwarnai per klaster.
    Ukuran titik proporsional dengan pertumbuhan_pct (bubble chart).
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    for cluster_id in sorted(clean_2023["cluster"].dropna().unique()):
        subset = clean_2023[clean_2023["cluster"] == cluster_id]
        color  = CLUSTER_COLORS_MAP.get(int(cluster_id), "#CCCCCC")
        label  = CLUSTER_LABELS.get(int(cluster_id), f"Klaster {cluster_id}")

        # Ukuran bubble: pertumbuhan_pct (min 30, max 300 agar terlihat)
        pct_vals = subset["pertumbuhan_pct"].fillna(0)
        sizes    = np.clip(np.abs(pct_vals) * 8 + 40, 30, 350)

        sc = ax.scatter(
            subset["kepadatan_per_1000"],
            subset["daya_beli"],
            s=sizes, c=color, alpha=0.78,
            edgecolors="white", linewidths=0.6,
            label=label, zorder=3
        )

    # Annotate beberapa kab/kota penting
    annotate_kota = [
        "KOTA BANDUNG", "KABUPATEN BOGOR", "KABUPATEN GARUT",
        "KOTA BEKASI", "KABUPATEN SUKABUMI"
    ]
    for _, row in clean_2023.iterrows():
        if row.get("nama_kabupaten_kota", "") in annotate_kota:
            nama = str(row["nama_kabupaten_kota"]).title().replace("Kabupaten", "Kab.")
            ax.annotate(nama,
                        xy=(row["kepadatan_per_1000"], row["daya_beli"]),
                        xytext=(6, 4), textcoords="offset points",
                        fontsize=7.5, color="#333333",
                        arrowprops=dict(arrowstyle="-", color="#BBBBBB", lw=0.8))

    ax.set_xlabel("Kepadatan UMKM per 1.000 Penduduk", fontsize=11)
    ax.set_ylabel("Daya Beli (Pengeluaran per Kapita, ribu Rp)", fontsize=11)
    ax.set_title("Scatter Plot Klaster UMKM — Kepadatan vs Daya Beli\nJawa Barat 2023 · Ukuran bubble ∝ Pertumbuhan UMKM (%)",
                 fontsize=13, fontweight="bold", pad=14)
    ax.legend(loc="upper left", framealpha=0.9, fontsize=9)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.xaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.spines[["top","right"]].set_visible(False)

    plt.tight_layout()
    path = os.path.join(FOLDER_OUTPUT, "scatter_klaster.png")
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  [OK] Tersimpan: {path}")


# ─────────────────────────────────────────
# 5. PETA CHOROPLETH FOLIUM
# ─────────────────────────────────────────

def download_geojson_jabar():
    """
    Download GeoJSON batas kab/kota Jawa Barat dari sumber publik.
    Coba beberapa sumber, gunakan yang berhasil.
    """
    sources = [
        "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/jawa-barat.geojson",
        "https://raw.githubusercontent.com/ans-4175/peta-indonesia-geojson/master/jawa-barat.geojson",
    ]
    for url in sources:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                print(f"  [OK] GeoJSON berhasil didownload dari: {url}")
                return data
        except Exception:
            continue

    print("  [WARN] GeoJSON tidak bisa didownload. Peta choropleth dilewati.")
    return None


def standardize_name(name: str) -> str:
    """Standardisasi nama kab/kota untuk matching dengan GeoJSON."""
    name = str(name).upper().strip()
    name = name.replace("KABUPATEN ", "KAB. ").replace("KOTA ", "KOTA ")
    return name


def viz_choropleth(clean_2023):
    """
    Peta choropleth Jawa Barat: tiap kab/kota diwarnai sesuai klaster.
    Disimpan sebagai HTML interaktif.
    """
    geojson = download_geojson_jabar()

    if geojson is None:
        print("  [SKIP] Peta choropleth tidak dibuat karena GeoJSON tidak tersedia.")
        return

    # Siapkan dataframe mapping nama → klaster
    df_map = clean_2023[["nama_kabupaten_kota", "cluster"]].dropna().copy()
    df_map["cluster"] = df_map["cluster"].astype(int)
    df_map["cluster_label"] = df_map["cluster"].map(CLUSTER_LABELS)

    # Warna hex per klaster untuk folium
    color_map = {
        1: "#1D9E75",
        2: "#378ADD",
        3: "#EF9F27",
        4: "#888780",
    }

    # Buat peta dasar
    m = folium.Map(
        location=[-7.0, 107.5],
        zoom_start=8,
        tiles="CartoDB positron"
    )

    # Tambahkan layer GeoJSON
    def style_function(feature):
        # Coba match nama dari GeoJSON ke dataframe
        geo_name = (feature.get("properties", {}).get("name", "") or
                    feature.get("properties", {}).get("NAME_2", "") or
                    feature.get("properties", {}).get("kabkot", ""))
        geo_name = str(geo_name).upper().strip()

        # Cari klaster yang sesuai
        cluster_id = None
        for _, row in df_map.iterrows():
            kab_name = str(row["nama_kabupaten_kota"]).upper()
            # Fuzzy match: cek apakah nama GeoJSON ada di nama dataset
            if (geo_name in kab_name or kab_name in geo_name or
                any(part in geo_name for part in kab_name.split() if len(part) > 4)):
                cluster_id = int(row["cluster"])
                break

        fill_color = color_map.get(cluster_id, "#D3D3D3")
        return {
            "fillColor": fill_color,
            "color": "#FFFFFF",
            "weight": 1.5,
            "fillOpacity": 0.75,
        }

    def tooltip_function(feature):
        geo_name = (feature.get("properties", {}).get("name", "") or
                    feature.get("properties", {}).get("NAME_2", "") or
                    feature.get("properties", {}).get("kabkot", "Tidak diketahui"))
        return geo_name

    folium.GeoJson(
        geojson,
        name="Klaster UMKM",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=list(geojson["features"][0]["properties"].keys())[:2],
            aliases=["Wilayah:"] * 2,
            sticky=True
        )
    ).add_to(m)

    # Legend manual via HTML
    legend_html = """
    <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                background:white; padding:14px 18px; border-radius:10px;
                box-shadow:0 2px 8px rgba(0,0,0,0.18); font-family:Arial; font-size:13px;">
      <b style="font-size:14px">Klaster UMKM Jawa Barat</b><br><br>
      <span style="background:#1D9E75;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Klaster 1 — Siap Scale-Up<br>
      <span style="background:#378ADD;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Klaster 2 — Tumbuh Butuh Fondasi<br>
      <span style="background:#EF9F27;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Klaster 3 — Padat Tapi Jenuh<br>
      <span style="background:#888780;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Klaster 4 — Perlu Fondasi Dulu<br>
      <span style="background:#D3D3D3;width:14px;height:14px;display:inline-block;border-radius:3px;margin-right:6px"></span>Tidak tersedia
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Simpan
    path = os.path.join(FOLDER_OUTPUT, "peta_klaster_jabar.html")
    m.save(path)
    print(f"  [OK] Peta choropleth tersimpan: {path}")


# ─────────────────────────────────────────
# 6. MAIN
# ─────────────────────────────────────────

def main():
    print("\n" + "="*55)
    print("  05_visualize.py — Tahap N: iNterpret (Visualisasi)")
    print("="*55)

    print("\n[Load] Membaca data...")
    clean_df, clean_2023, cluster_profile = load_data()
    print(f"  clean_dataset  : {len(clean_df)} baris")
    print(f"  clean_2023     : {len(clean_2023)} baris (kab/kota + klaster)")
    print(f"  cluster_profile: {len(cluster_profile)} klaster")

    print("\n[1/4] Bar chart profil klaster...")
    viz_bar_profil(cluster_profile)

    print("\n[2/4] Radar chart profil klaster...")
    viz_radar_profil(cluster_profile)

    print("\n[3/4] Scatter plot klaster (kepadatan vs daya beli)...")
    viz_scatter_klaster(clean_2023)

    print("\n[4/4] Peta choropleth Jawa Barat...")
    viz_choropleth(clean_2023)

    print("\n" + "="*55)
    print("  Semua visualisasi selesai!")
    print(f"  Output disimpan di: {FOLDER_OUTPUT}/")
    print("="*55 + "\n")


if __name__ == "__main__":
    main()
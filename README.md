# Segmentasi Potensi Wilayah UMKM untuk Rekomendasi Pembiayaan

Proyek analitik data untuk mensegmentasi kabupaten/kota di Jawa Barat berdasarkan kepadatan UMKM, pertumbuhan, dan daya beli menggunakan K-Means Clustering — dilengkapi dashboard interaktif berbasis Streamlit.

---

## Struktur Folder

```
Tugas-Besar-Data-Analytics/
│
├── raw_data/                         ← [DE] Dataset mentah (jangan diedit)
│   ├── Utama_Jumlah_Proyeksi_UMKM_Jabar.csv
│   ├── Utama_Jumlah_UMKM_Binaan_Jabar.csv
│   ├── Pendukung_Jumlah_Penduduk.csv
│   └── Pendukung_Pengeluaran.csv
│
├── clean_data/                       ← [Preprocessing] Output 02_scrub.py
│   ├── clean_dataset.csv
│   └── umkm_binaan_pivot.csv
│
├── output/
│   ├── visualizations/               ← [Viz] PNG/HTML dari 05_visualize.py
│   └── models/                       ← [Model] CSV hasil clustering
│
├── docs/
│   ├── dataset_inventory.csv
│   ├── dataset_inventory.json
│   ├── obtain_log.txt
│   ├── scrub_documentation.csv
│   └── scrub_summary.json
│
├── .streamlit/
│   └── config.toml                   ← Konfigurasi tema Streamlit dashboard
│
├── 01_obtain.py                      ← [DE] Pipeline pengambilan & validasi data
├── 02_scrub.py                       ← [Preprocessing] Cleaning & integrasi
├── 03_explore.py                     ← [Analyst] Eksplorasi & statistik deskriptif
├── 04_model.py                       ← [Analyst] K-Means clustering
├── 05_visualize.py                   ← [Viz] Visualisasi statis (PNG)
├── 06_dashboard.py                   ← [Viz] Dashboard interaktif Streamlit
│
├── run_all_pipeline.py               ← Jalankan pipeline 01–05 sekaligus
├── README.md
└── .gitignore
```

**Keterangan peran:**
`[DE]` Data Engineer · `[Preprocessing]` Data Preprocessing Lead · `[Analyst]` Data Analyst/Modeler · `[Viz]` Visualization / Dashboard Developer

---

## Dataset

### Dataset Utama (sumber: Dinas Koperasi Jabar)

| # | File | Nama Dataset | Periode | Baris | Kolom |
|---|------|-------------|---------|-------|-------|
| 1 | `Utama_Jumlah_Proyeksi_UMKM_Jabar.csv` | Proyeksi Jumlah UMKM per Kab/Kota | 2016–2023 | 216 | 8 |
| 2 | `Utama_Jumlah_UMKM_Binaan_Jabar.csv` | UMKM Binaan per Jenis Usaha per Kab/Kota | 2019–2023 | 2.025 | 9 |

### Dataset Pendukung (sumber: BPS Jawa Barat)

| # | File | Nama Dataset | Periode | Baris | Kolom |
|---|------|-------------|---------|-------|-------|
| 3 | `Pendukung_Jumlah_Penduduk.csv` | Proyeksi Jumlah Penduduk per Kab/Kota | 2010–2025 | 432 | 8 |
| 4 | `Pendukung_Pengeluaran.csv` | Pengeluaran Per Kapita Disesuaikan per Kab/Kota | 2010–2024 | 402 | 8 |

> **Kunci join:** `nama_kabupaten_kota` + `tahun`
> **Periode overlap:** 2019–2023 (5 tahun, digunakan untuk analisis)

---

## Cara Menjalankan

### Prasyarat

```
Python >= 3.9
```

Aktifkan virtual environment lalu install semua dependensi:

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install pandas scikit-learn matplotlib seaborn folium numpy requests streamlit plotly
```

### 1. Jalankan Pipeline Analitik (01–05)

Jalankan script secara berurutan dari root folder proyek:

```bash
python 01_obtain.py    # Validasi & simpan data mentah
python 02_scrub.py     # Cleaning, standarisasi, feature engineering
python 03_explore.py   # Statistik deskriptif & visualisasi EDA
python 04_model.py     # K-Means clustering & evaluasi
python 05_visualize.py # Visualisasi statis (PNG) profil klaster
```

Atau jalankan semuanya sekaligus:

```bash
python run_all_pipeline.py
```

### 2. Jalankan Dashboard Interaktif

Setelah pipeline 01–04 selesai (minimal), jalankan dashboard:

```bash
streamlit run 06_dashboard.py
```

Dashboard akan terbuka otomatis di browser pada `http://localhost:8501`.

---

## Fitur Dashboard (`06_dashboard.py`)

Dashboard dibangun dengan **Streamlit** dan **Plotly** — semua grafik interaktif (hover, zoom, pan, klik legend).

### Tampilan & Desain
- Font: **Plus Jakarta Sans** (Google Fonts)
- Warna palette: Stellar Strawberry · Pico Eggplant · Grauzone · Siesta Tan
- Grafik dengan background transparan, container rounded corners + shadow
- Judul grafik di luar area plot

### Sidebar Filters
| Filter | Keterangan |
|--------|-----------|
| Tahun | Slider periode 2019–2023 |
| Kabupaten / Kota | Multiselect, default semua 27 wilayah |
| Klaster | Multiselect, filter berdasarkan hasil segmentasi |

### Konten Utama

| Seksi | Visualisasi | Interaktivitas |
|-------|-------------|----------------|
| **KPI Cards** | Total UMKM, Rata-rata pertumbuhan, Rata-rata daya beli, Kab terbanyak | Responsif terhadap filter |
| **Tren UMKM per Tahun** | Line chart, default top 8 kab/kota | Hover detail, klik legend untuk isolate |
| **Sebaran Klaster** | Bubble scatter — sumbu X: kepadatan, Y: daya beli, ukuran: pertumbuhan, warna: klaster | Hover, zoom, pan |
| **Profil Klaster** | Grouped horizontal bar — rata-rata 3 indikator per klaster | Hover, filter via legend |
| **Rekomendasi Pembiayaan** | Card per klaster dengan strategi pembiayaan | — |
| **Komposisi Sektor** | Stacked bar tren tahunan + donut komposisi total | Filter kab/kota & sektor (multiselect) |
| **Peta Sebaran** | Scatter mapbox (OpenStreetMap) — bubble ukuran UMKM, warna klaster | Hover, zoom, drag |
| **Data Tabel** | Tabel lengkap dengan semua filter aktif | Download CSV |

---

## Fitur yang Dihasilkan (Feature Engineering)

| Nama Fitur | Rumus | Peran dalam Model |
|------------|-------|-------------------|
| `kepadatan_per_1000` | `jumlah_umkm / jumlah_penduduk_ribu` | Input K-Means #1 |
| `pertumbuhan_pct` | `(umkm_t - umkm_t-1) / umkm_t-1 × 100` | Input K-Means #2 |
| `daya_beli` | `pengeluaran_per_kapita` (langsung) | Input K-Means #3 |
| `sektor_dominan` | `argmax(jumlah per jenis usaha)` | Konteks per wilayah |

---

## Hasil Klaster & Rekomendasi Pembiayaan

Model K-Means menghasilkan **3 klaster** dari 27 kabupaten/kota Jawa Barat:

| Klaster | Label | Karakteristik | Rekomendasi |
|---------|-------|---------------|-------------|
| **1** | Siap Scale-Up | Kepadatan tinggi, daya beli rendah | KUR ekspansi, pembiayaan digitalisasi & akses pasar luar daerah |
| **2** | Tumbuh Butuh Fondasi | Kepadatan sedang, daya beli tinggi | KUR modal kerja + pendampingan pencatatan, pemasaran, legalitas |
| **3** | Padat Tapi Jenuh | Kepadatan sedang, daya beli menengah | Pembiayaan inovasi produk & branding — bukan tambah modal baru |

### Palet Warna Klaster

| Klaster | Warna | Kode Hex |
|---------|-------|----------|
| Klaster 1 — Siap Scale-Up | Stellar Strawberry | `#FF5C8D` |
| Klaster 2 — Tumbuh Butuh Fondasi | Pico Eggplant | `#732553` |
| Klaster 3 — Padat Tapi Jenuh | Grauzone | `#85A3B2` |

---

## Output Pipeline

### `02_scrub.py`
| File | Isi |
|------|-----|
| `clean_data/clean_dataset.csv` | Dataset bersih 135 baris (27 kab/kota × 5 tahun), 17 kolom |
| `clean_data/umkm_binaan_pivot.csv` | Pivot 15 sektor UMKM binaan per kab/kota per tahun |
| `docs/scrub_documentation.csv` | Log keputusan cleaning |
| `docs/scrub_summary.json` | Ringkasan validasi |

### `04_model.py`
| File | Isi |
|------|-----|
| `output/models/clustering_result.csv` | Label klaster per baris data (135 baris) |
| `output/models/clustering_profile.csv` | Rata-rata indikator per klaster (3 baris) |
| `output/models/elbow_method_visualization.jpg` | Grafik elbow K=1–10 |
| `output/models/visualization_clustering_result.png` | Scatter 3D hasil clustering |

### `05_visualize.py`
| File | Isi |
|------|-----|
| `output/visualizations/bar_profil_klaster.png` | Bar chart profil rata-rata per klaster |
| `output/visualizations/radar_profil_klaster.png` | Radar chart profil ternormalisasi |
| `output/visualizations/scatter_klaster.png` | Bubble scatter kepadatan vs daya beli |

---

## Catatan Teknis

- Semua path dalam script bersifat **relatif terhadap lokasi script**.
- Folder `raw_data/` berisi data mentah yang tidak dimodifikasi — seluruh transformasi terjadi di `clean_data/`.
- Script `01_obtain.py` dapat dijalankan ulang kapan saja tanpa efek samping (idempotent).
- Encoding file: UTF-8. Di Windows jalankan dengan `PYTHONUTF8=1` jika ada masalah karakter.
- Dashboard (`06_dashboard.py`) membutuhkan koneksi internet untuk memuat tile peta OpenStreetMap.
- Folder `.venv/` di-ignore oleh git — setiap anggota tim perlu membuat venv sendiri.

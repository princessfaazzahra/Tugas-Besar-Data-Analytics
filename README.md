# **Segmentasi Potensi Wilayah UMKM untuk Rekomendasi Pembiayaan**

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
│   ├── dataset_inventory.csv         ← [DE] Tabel dokumentasi 4 dataset
│   ├── dataset_inventory.json        ← [DE] Inventaris format JSON
│   ├── obtain_log.txt                ← [DE] Log lengkap pipeline
│   ├── scrub_documentation.csv       ← [Preprocessing] Keputusan cleaning Bab 3
│   └── scrub_summary.json            ← [Preprocessing] Ringkasan validasi output
│
├── 01_obtain.py                      ← [DE] Pipeline pengambilan & validasi data
├── 02_scrub.py                       ← [Preprocessing] Cleaning & integrasi
├── 03_explore.py                     ← [Analyst] Eksplorasi & statistik deskriptif
├── 04_model.py                       ← [Analyst] K-Means clustering
├── 05_visualize.py                   ← [Viz] Choropleth & visualisasi profil klaster
│
├── README.md                         ← Dokumen ini
└── Spek Tubes dan Ide.md             ← Spesifikasi & ide proyek
```

**Keterangan peran:**  
`[DE]` Data Engineer · `[Preprocessing]` Data Preprocessing Lead · `[Analyst]` Data Analyst/Modeler · `[Viz]` Visualization Developer

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
> **Catatan:** `Pendukung_Pengeluaran.csv` memiliki 402 baris (bukan 405) karena Kabupaten Pangandaran baru terbentuk tahun 2012 sehingga data 2010–2011 tidak tersedia — **ini bukan missing value, ini ketiadaan wilayah**, ditangani di `02_scrub.py`.

---

## Cara Menjalankan Pipeline

### Prasyarat

```bash
Python >= 3.9
pandas >= 1.5
scikit-learn >= 1.2
matplotlib >= 3.6
seaborn >= 0.12
folium >= 0.14        
geopandas >= 0.13  
```

Install semua dependensi:

```bash
pip install pandas scikit-learn matplotlib seaborn folium geopandas
```

### Urutan Eksekusi

Jalankan script secara berurutan dari root folder proyek:

```bash
# Tahap Obtain: validasi & simpan data mentah
python 01_obtain.py

# Tahap Scrub: cleaning, standarisasi, feature engineering
python 02_scrub.py

# Tahap Explore: statistik deskriptif & visualisasi awal
python 03_explore.py

# Tahap Model: K-Means clustering & evaluasi
python 04_model.py

# Tahap iNterpret: visualisasi final & peta choropleth
python 05_visualize.py
```

---

## Output Preprocessing

Script `02_scrub.py` menghasilkan:

| File | Isi |
|------|-----|
| `clean_data/clean_dataset.csv` | Dataset bersih hasil join 4 dataset, level kab/kota-tahun, periode 2019-2023 |
| `clean_data/umkm_binaan_pivot.csv` | Pivot jumlah UMKM binaan per jenis usaha, siap dipakai untuk eksplorasi sektor |
| `docs/scrub_documentation.csv` | Dokumentasi cleaning: kondisi awal, tindakan, kondisi akhir, alasan |
| `docs/scrub_summary.json` | Ringkasan validasi output preprocessing |

## Fitur yang Dihasilkan

| Nama Fitur | Rumus | Peran dalam Model |
|------------|-------|-------------------|
| `kepadatan_per_1000` | `jumlah_umkm / jumlah_penduduk_ribu` | Input K-Means #1 |
| `pertumbuhan_pct` | `(umkm_t - umkm_t-1) / umkm_t-1 × 100` | Input K-Means #2 |
| `daya_beli` | `pengeluaran_per_kapita` (langsung) | Input K-Means #3 |
| `sektor_dominan` | `argmax(jumlah per jenis usaha)` | Personalisasi rekomendasi |

---

## Klaster & Rekomendasi Pembiayaan

| Klaster | Kondisi | Rekomendasi |
|---------|---------|-------------|
| **A — Siap scale-up** | Kepadatan tinggi, tumbuh positif, daya beli kuat | KUR ekspansi, pembiayaan digitalisasi & akses pasar luar daerah |
| **B — Tumbuh butuh fondasi** | Pertumbuhan cepat, daya beli lemah | KUR modal kerja + pendampingan pencatatan, pemasaran, legalitas |
| **C — Padat tapi jenuh** | Kepadatan sangat tinggi, pertumbuhan stagnan | Pembiayaan inovasi produk & branding, bukan tambah modal baru |
| **D — Perlu fondasi dulu** | Kepadatan rendah, tumbuh lambat, daya beli lemah | Hibah/dana bergulir + pelatihan dasar |

---

## Dokumentasi Dataset Lengkap

File `docs/dataset_inventory.csv` berisi dokumentasi lengkap setiap dataset meliputi:
nama, sumber, URL, periode, format, jumlah baris/kolom, level wilayah, fungsi dalam analisis, MD5 checksum, dan status validasi.

---

## Catatan Teknis
- Semua path dalam script bersifat **relatif terhadap lokasi script** — bisa dijalankan dari direktori mana pun.
- Folder `raw_data/` berisi **data mentah yang tidak dimodifikasi** — seluruh transformasi terjadi di `clean_data/`.
- Script `01_obtain.py` dapat dijalankan ulang kapan saja tanpa efek samping (idempotent).
- Encoding file: UTF-8. Jalankan dengan `PYTHONUTF8=1` di Windows jika ada masalah karakter.

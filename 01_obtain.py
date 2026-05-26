"""
============================================================
01_obtain.py  —  Data Pipeline: Tahap O (Obtain)
============================================================
Proyek  : Segmentasi Potensi Wilayah UMKM untuk Rekomendasi Pembiayaan
Tim     : Kelompok Data Analytics — Semester 6
Peran   : Data Engineer

Tanggung jawab script ini:
  1. Menyalin 4 dataset mentah ke folder /raw_data/ (reproducible storage)
  2. Memvalidasi integritas setiap dataset (baris, kolom, range tahun)
  3. Memeriksa konsistensi nama kabupaten/kota antar dataset
  4. Menghasilkan tabel dokumentasi dataset (docs/dataset_inventory.csv)
  5. Mencatat seluruh operasi ke log (docs/obtain_log.txt)

Cara menjalankan:
  python 01_obtain.py

Output yang dihasilkan:
  raw_data/Utama_Jumlah_Proyeksi_UMKM_Jabar.csv
  raw_data/Utama_Jumlah_UMKM_Binaan_Jabar.csv
  raw_data/Pendukung_Jumlah_Penduduk.csv
  raw_data/Pendukung_Pengeluaran.csv
  docs/dataset_inventory.csv
  docs/obtain_log.txt
============================================================
"""

import os
import sys
import shutil
import hashlib
import csv
import json
from datetime import datetime
from pathlib import Path

# Fix encoding untuk Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────
# KONFIGURASI PATH
# ─────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
SOURCE_DIR  = BASE_DIR          # CSV sumber ada di root proyek
RAW_DIR     = BASE_DIR / "raw_data"
DOCS_DIR    = BASE_DIR / "docs"

# Pastikan folder target ada
RAW_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# METADATA DATASET
# Dokumentasi lengkap sumber, periode, dan peran
# setiap dataset dalam pipeline analitik.
# ─────────────────────────────────────────────
DATASETS = [
    {
        "filename"    : "Utama_Jumlah_Proyeksi_UMKM_Jabar.csv",
        "kategori"    : "Utama",
        "nama_dataset": "Proyeksi Jumlah UMKM per Kabupaten/Kota di Jawa Barat",
        "sumber"      : "Dinas Koperasi dan UKM Provinsi Jawa Barat",
        "url"         : "https://opendata.jabarprov.go.id/id/dataset/"
                        "jumlah-ukm-berdasarkan-kabupatenkota-di-jawa-barat",
        "periode"     : "2016–2023",
        "format"      : "CSV",
        "level_wilayah": "Kabupaten/Kota",
        "kolom_kunci" : ["nama_kabupaten_kota", "tahun"],
        "kolom_nilai" : "proyeksi_jumlah_umkm",
        "satuan"      : "Unit",
        "fungsi"      : (
            "Menghitung kepadatan UMKM (UMKM per 1.000 penduduk) "
            "dan pertumbuhan UMKM tahunan. Input utama K-Means."
        ),
        "expected_rows": 216,   # 27 kab/kota × 8 tahun
        "expected_cols": 8,
    },
    {
        "filename"    : "Utama_Jumlah_UMKM_Binaan_Jabar.csv",
        "kategori"    : "Utama",
        "nama_dataset": "Jumlah UMKM Binaan per Jenis Usaha per Kabupaten/Kota di Jawa Barat",
        "sumber"      : "Dinas Koperasi dan UKM Provinsi Jawa Barat",
        "url"         : "https://opendata.jabarprov.go.id/id/dataset/"
                        "jumlah-umkm-binaan-berdasarkan-jenis-usaha-dan-kabupatenkota-di-jawa-barat",
        "periode"     : "2019–2023",
        "format"      : "CSV",
        "level_wilayah": "Kabupaten/Kota × Jenis Usaha",
        "kolom_kunci" : ["nama_kabupaten_kota", "jenis_usaha", "tahun"],
        "kolom_nilai" : "jumlah_umkm",
        "satuan"      : "Unit",
        "fungsi"      : (
            "Mengidentifikasi sektor dominan per wilayah "
            "(argmax jenis usaha) untuk personalisasi rekomendasi pembiayaan per klaster."
        ),
        "expected_rows": 2025,  # 27 kab/kota × 15 jenis usaha × 5 tahun
        "expected_cols": 9,
    },
    {
        "filename"    : "Pendukung_Jumlah_Penduduk.csv",
        "kategori"    : "Pendukung",
        "nama_dataset": "Proyeksi Jumlah Penduduk per Kabupaten/Kota di Jawa Barat",
        "sumber"      : "BPS Provinsi Jawa Barat",
        "url"         : "https://opendata.jabarprov.go.id/id/dataset/"
                        "jumlah-penduduk-berdasarkan-kabupatenkota-di-jawa-barat",
        "periode"     : "2010–2025",
        "format"      : "CSV",
        "level_wilayah": "Kabupaten/Kota",
        "kolom_kunci" : ["nama_kabupaten_kota", "tahun"],
        "kolom_nilai" : "jumlah_penduduk",
        "satuan"      : "Ribu Orang",
        "fungsi"      : (
            "Normalisasi jumlah UMKM menjadi kepadatan per 1.000 penduduk, "
            "mencegah kabupaten berpenduduk besar selalu mendominasi secara absolut."
        ),
        "expected_rows": 432,   # 27 kab/kota × 16 tahun
        "expected_cols": 8,
    },
    {
        "filename"    : "Pendukung_Pengeluaran.csv",
        "kategori"    : "Pendukung",
        "nama_dataset": "Pengeluaran Per Kapita Disesuaikan per Kabupaten/Kota di Jawa Barat",
        "sumber"      : "BPS Provinsi Jawa Barat",
        "url"         : "https://opendata.jabarprov.go.id/id/dataset/"
                        "pengeluaran-per-kapita-disesuaikan-berdasarkan-kabupatenkota-di-jawa-barat",
        "periode"     : "2010–2024",
        "format"      : "CSV",
        "level_wilayah": "Kabupaten/Kota",
        "kolom_kunci" : ["nama_kabupaten_kota", "tahun"],
        "kolom_nilai" : "pengeluaran_per_kapita",
        "satuan"      : "Ribu Rupiah/Orang/Tahun",
        "fungsi"      : (
            "Proxy daya beli masyarakat. Dimensi ke-3 input K-Means. "
            "Membedakan wilayah dengan ekosistem ekonomi kuat vs rentan."
        ),
        "expected_rows": 402,   # 27 kab/kota × 15 tahun (Kab. Pangandaran lahir 2012, minus 3 baris)
        "expected_cols": 8,
    },
]


# ─────────────────────────────────────────────
# UTILITAS
# ─────────────────────────────────────────────

def md5_file(filepath: Path) -> str:
    """Hitung MD5 checksum file untuk verifikasi integritas."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def log(message: str, log_lines: list):
    """Cetak ke konsol dan simpan ke buffer log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    log_lines.append(line)


def validate_dataset(filepath: Path, meta: dict, log_lines: list) -> dict:
    """
    Baca CSV dan validasi:
      - Jumlah baris vs expected_rows
      - Jumlah kolom vs expected_cols
      - Range tahun
      - Tidak ada nilai kosong di kolom kunci
      - 27 kabupaten/kota hadir
    Kembalikan dict hasil validasi.
    """
    result = {
        "filename"  : meta["filename"],
        "status"    : "OK",
        "issues"    : [],
    }

    with open(filepath, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    header = rows[0].keys() if rows else []
    n_rows = len(rows)
    n_cols = len(list(header))

    # ── Validasi jumlah baris ──
    if n_rows != meta["expected_rows"]:
        msg = (f"Jumlah baris {n_rows} ≠ expected {meta['expected_rows']}")
        result["issues"].append(msg)
        log(f"  ⚠  {meta['filename']}: {msg}", log_lines)
    else:
        log(f"  ✓  {meta['filename']}: {n_rows} baris (sesuai)", log_lines)

    # ── Validasi jumlah kolom ──
    if n_cols != meta["expected_cols"]:
        msg = f"Jumlah kolom {n_cols} ≠ expected {meta['expected_cols']}"
        result["issues"].append(msg)
        log(f"  ⚠  {meta['filename']}: {msg}", log_lines)

    # ── Validasi nilai kosong di kolom kunci ──
    for col in meta["kolom_kunci"]:
        empty = sum(1 for r in rows if not r.get(col, "").strip())
        if empty:
            msg = f"Kolom '{col}' memiliki {empty} nilai kosong"
            result["issues"].append(msg)
            log(f"  ⚠  {meta['filename']}: {msg}", log_lines)

    # ── Validasi jumlah kabupaten/kota unik ──
    kk_set = set(r["nama_kabupaten_kota"] for r in rows if r.get("nama_kabupaten_kota"))
    n_kk = len(kk_set)
    if n_kk != 27:
        msg = f"Jumlah kabupaten/kota unik = {n_kk} (expected 27)"
        result["issues"].append(msg)
        log(f"  ⚠  {meta['filename']}: {msg}", log_lines)
    else:
        log(f"  ✓  {meta['filename']}: 27 kabupaten/kota hadir", log_lines)

    # ── Info range tahun ──
    if "tahun" in (rows[0].keys() if rows else []):
        years = sorted(set(r["tahun"] for r in rows))
        result["years"] = f"{years[0]}–{years[-1]}"
        log(f"  ✓  {meta['filename']}: tahun {years[0]}–{years[-1]}", log_lines)

    result["n_rows"] = n_rows
    result["n_cols"] = n_cols
    result["n_kab_kota"] = n_kk
    if result["issues"]:
        result["status"] = "WARNING"
    return result


def check_kab_kota_consistency(raw_dir: Path, filenames: list, log_lines: list):
    """
    Periksa apakah nama kabupaten/kota konsisten di semua dataset.
    Tampilkan perbedaan jika ada.
    """
    log("\n── Pemeriksaan Konsistensi Nama Kabupaten/Kota ──", log_lines)
    kk_per_file = {}
    for fn in filenames:
        fp = raw_dir / fn
        with open(fp, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        kk_per_file[fn] = set(r["nama_kabupaten_kota"] for r in rows)

    reference = list(kk_per_file.values())[0]
    all_consistent = True
    for fn, kk_set in kk_per_file.items():
        diff = reference.symmetric_difference(kk_set)
        if diff:
            log(f"  ⚠  Perbedaan nama di {fn}: {sorted(diff)}", log_lines)
            all_consistent = False
        else:
            log(f"  ✓  {fn}: nama kabupaten/kota konsisten", log_lines)

    if all_consistent:
        log("  ✓  Semua dataset konsisten — join siap dilakukan", log_lines)
    else:
        log("  ⚠  Perbedaan ditemukan — perlu standarisasi di 02_scrub.py", log_lines)
    return all_consistent


def save_inventory(datasets_meta: list, validations: dict, raw_dir: Path,
                   docs_dir: Path, log_lines: list):
    """Simpan tabel inventaris dataset ke CSV dan JSON."""

    # ── CSV ──
    csv_path = docs_dir / "dataset_inventory.csv"
    fieldnames = [
        "filename", "kategori", "nama_dataset", "sumber", "url",
        "periode", "format", "level_wilayah", "n_rows", "n_cols",
        "n_kab_kota", "kolom_nilai", "satuan", "fungsi",
        "md5_checksum", "status", "catatan",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for meta in datasets_meta:
            v = validations.get(meta["filename"], {})
            checksum = md5_file(raw_dir / meta["filename"])
            row = {
                "filename"     : meta["filename"],
                "kategori"     : meta["kategori"],
                "nama_dataset" : meta["nama_dataset"],
                "sumber"       : meta["sumber"],
                "url"          : meta["url"],
                "periode"      : meta["periode"],
                "format"       : meta["format"],
                "level_wilayah": meta["level_wilayah"],
                "n_rows"       : v.get("n_rows", ""),
                "n_cols"       : v.get("n_cols", ""),
                "n_kab_kota"   : v.get("n_kab_kota", ""),
                "kolom_nilai"  : meta["kolom_nilai"],
                "satuan"       : meta["satuan"],
                "fungsi"       : meta["fungsi"],
                "md5_checksum" : checksum,
                "status"       : v.get("status", ""),
                "catatan"      : "; ".join(v.get("issues", [])) or "-",
            }
            writer.writerow(row)
    log(f"\n  ✓  Inventaris disimpan → {csv_path}", log_lines)

    # ── JSON (untuk referensi programatik) ──
    json_path = docs_dir / "dataset_inventory.json"
    inventory_json = []
    for meta in datasets_meta:
        v = validations.get(meta["filename"], {})
        checksum = md5_file(raw_dir / meta["filename"])
        entry = {**meta, **{
            "n_rows"       : v.get("n_rows"),
            "n_cols"       : v.get("n_cols"),
            "n_kab_kota"   : v.get("n_kab_kota"),
            "years_actual" : v.get("years"),
            "md5_checksum" : checksum,
            "status"       : v.get("status"),
            "issues"       : v.get("issues", []),
        }}
        # Buat kolom_kunci serializable
        entry["kolom_kunci"] = meta["kolom_kunci"]
        inventory_json.append(entry)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(inventory_json, f, ensure_ascii=False, indent=2)
    log(f"  ✓  Inventaris JSON disimpan → {json_path}", log_lines)


# ─────────────────────────────────────────────
# PIPELINE UTAMA
# ─────────────────────────────────────────────

def run_pipeline():
    log_lines = []
    log("=" * 60, log_lines)
    log("  PIPELINE TAHAP O (OBTAIN) — Mulai", log_lines)
    log("=" * 60, log_lines)
    log(f"  Base dir : {BASE_DIR}", log_lines)
    log(f"  Raw data : {RAW_DIR}", log_lines)
    log(f"  Docs     : {DOCS_DIR}", log_lines)

    # ── LANGKAH 1: Salin dataset mentah ke /raw_data/ ──
    log("\n── Langkah 1: Menyalin dataset mentah ke /raw_data/ ──", log_lines)
    copied = []
    for meta in DATASETS:
        src = SOURCE_DIR / meta["filename"]
        dst = RAW_DIR     / meta["filename"]

        if not src.exists():
            log(f"  ✗  FILE TIDAK DITEMUKAN: {src}", log_lines)
            log(f"     → Unduh dari: {meta['url']}", log_lines)
            continue

        shutil.copy2(src, dst)
        log(f"  ✓  Disalin: {meta['filename']}", log_lines)
        copied.append(meta["filename"])

    if len(copied) < len(DATASETS):
        log(f"\n  ⚠  {len(DATASETS) - len(copied)} dataset tidak ditemukan. "
            f"Periksa folder sumber.", log_lines)

    # ── LANGKAH 2: Validasi integritas setiap dataset ──
    log("\n── Langkah 2: Validasi Integritas Dataset ──", log_lines)
    validations = {}
    for meta in DATASETS:
        fp = RAW_DIR / meta["filename"]
        if not fp.exists():
            continue
        log(f"\n  Memvalidasi: {meta['filename']}", log_lines)
        result = validate_dataset(fp, meta, log_lines)
        validations[meta["filename"]] = result

    # ── LANGKAH 3: Periksa konsistensi nama kab/kota ──
    check_kab_kota_consistency(
        RAW_DIR,
        [m["filename"] for m in DATASETS if (RAW_DIR / m["filename"]).exists()],
        log_lines
    )

    # ── LANGKAH 4: Simpan inventaris dataset ──
    log("\n── Langkah 4: Menyimpan Inventaris Dataset ──", log_lines)
    save_inventory(DATASETS, validations, RAW_DIR, DOCS_DIR, log_lines)

    # ── LANGKAH 5: Ringkasan ──
    log("\n" + "=" * 60, log_lines)
    log("  RINGKASAN PIPELINE", log_lines)
    log("=" * 60, log_lines)
    ok  = sum(1 for v in validations.values() if v["status"] == "OK")
    warn = sum(1 for v in validations.values() if v["status"] == "WARNING")
    log(f"  Dataset diproses : {len(validations)}", log_lines)
    log(f"  Status OK        : {ok}", log_lines)
    log(f"  Status WARNING   : {warn}", log_lines)
    log(f"  File output      :", log_lines)
    for fn in copied:
        log(f"    raw_data/{fn}", log_lines)
    log(f"    docs/dataset_inventory.csv", log_lines)
    log(f"    docs/dataset_inventory.json", log_lines)
    log(f"    docs/obtain_log.txt", log_lines)
    log("\n  Pipeline Tahap O selesai. Lanjut ke 02_scrub.py.", log_lines)
    log("=" * 60, log_lines)

    # Simpan log
    log_path = DOCS_DIR / "obtain_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"\n  Log disimpan → {log_path}")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline()

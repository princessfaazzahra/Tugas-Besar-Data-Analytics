"""
02_scrub.py - Data Pipeline: Tahap S (Scrub)
Peran   : Data Preprocessing Lead

Tanggung jawab:
  1. Standarisasi nama kabupaten/kota.
  2. Tangani missing value, duplikasi, dan tipe data tidak konsisten.
  3. Join 4 dataset dengan kunci nama_kabupaten_kota + tahun, periode 2019-2023.
  4. Feature engineering:
       - kepadatan_per_1000
       - pertumbuhan_pct
       - daya_beli
       - sektor_dominan
  5. Simpan dokumentasi keputusan preprocessing.

Input : raw_data/*.csv
Output: clean_data/clean_dataset.csv
        docs/scrub_documentation.csv
        docs/scrub_summary.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


BASE_DIR = Path(__file__).parent
OVERLAP_YEARS = range(2019, 2024)

DATASET_FILES = {
    "proyeksi_umkm": "Utama_Jumlah_Proyeksi_UMKM_Jabar.csv",
    "umkm_binaan": "Utama_Jumlah_UMKM_Binaan_Jabar.csv",
    "penduduk": "Pendukung_Jumlah_Penduduk.csv",
    "pengeluaran": "Pendukung_Pengeluaran.csv",
}

KEY_COLUMNS = ["nama_kabupaten_kota", "tahun"]

NUMERIC_COLUMNS = {
    "proyeksi_umkm": ["kode_provinsi", "kode_kabupaten_kota", "proyeksi_jumlah_umkm", "tahun"],
    "umkm_binaan": ["kode_provinsi", "kode_kabupaten_kota", "jumlah_umkm", "tahun"],
    "penduduk": ["kode_provinsi", "kode_kabupaten_kota", "jumlah_penduduk", "tahun"],
    "pengeluaran": ["kode_provinsi", "kode_kabupaten_kota", "pengeluaran_per_kapita", "tahun"],
}


def cleaning_note(
    masalah_data: str,
    kondisi_awal: str,
    tindakan_perbaikan: str,
    kondisi_akhir: str,
    alasan: str,
) -> dict[str, str]:
    return {
        "masalah_data": masalah_data,
        "kondisi_awal": kondisi_awal,
        "tindakan_perbaikan": tindakan_perbaikan,
        "kondisi_akhir": kondisi_akhir,
        "alasan": alasan,
    }


def normalize_text(value: object) -> str:
    """Normalize text values used as categorical/join keys."""
    if pd.isna(value):
        return ""

    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("KAB. ", "KABUPATEN ")
    text = text.replace("KAB ", "KABUPATEN ")
    text = text.replace("KOTA. ", "KOTA ")
    return text


def read_raw_dataset(raw_dir: Path, key: str) -> pd.DataFrame:
    path = raw_dir / DATASET_FILES[key]
    if not path.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {path}")
    return pd.read_csv(path)


def build_region_reference(datasets: Iterable[pd.DataFrame]) -> dict[int, str]:
    """
    Build canonical region names from kode_kabupaten_kota.
    Codes are more stable than spelling, but the final join still uses the
    standardized nama_kabupaten_kota + tahun key required by the project.
    """
    candidates = []
    for df in datasets:
        if {"kode_kabupaten_kota", "nama_kabupaten_kota"}.issubset(df.columns):
            subset = df[["kode_kabupaten_kota", "nama_kabupaten_kota"]].copy()
            subset["kode_kabupaten_kota"] = pd.to_numeric(
                subset["kode_kabupaten_kota"], errors="coerce"
            )
            subset["nama_kabupaten_kota"] = subset["nama_kabupaten_kota"].map(normalize_text)
            candidates.append(subset.dropna())

    if not candidates:
        return {}

    combined = pd.concat(candidates, ignore_index=True)
    combined["kode_kabupaten_kota"] = combined["kode_kabupaten_kota"].astype(int)

    reference = {}
    for code, group in combined.groupby("kode_kabupaten_kota"):
        modes = group["nama_kabupaten_kota"].mode()
        reference[int(code)] = modes.iloc[0]
    return reference


def standardize_dataset(df: pd.DataFrame, dataset_key: str, region_reference: dict[int, str]) -> pd.DataFrame:
    clean = df.copy()

    for col in clean.select_dtypes(include="object").columns:
        clean[col] = clean[col].map(normalize_text)

    for col in NUMERIC_COLUMNS[dataset_key]:
        if col in clean.columns:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")

    if "kode_kabupaten_kota" in clean.columns:
        clean["kode_kabupaten_kota"] = clean["kode_kabupaten_kota"].astype("Int64")
        canonical = clean["kode_kabupaten_kota"].map(region_reference)
        clean["nama_kabupaten_kota"] = canonical.fillna(clean["nama_kabupaten_kota"])

    if "tahun" in clean.columns:
        clean["tahun"] = clean["tahun"].astype("Int64")

    return clean


def count_outliers_iqr(series: pd.Series) -> int:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return 0

    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((numeric < lower) | (numeric > upper)).sum())


def validate_required_columns(datasets: dict[str, pd.DataFrame]) -> None:
    required = {
        "proyeksi_umkm": set(KEY_COLUMNS + ["kode_kabupaten_kota", "proyeksi_jumlah_umkm"]),
        "umkm_binaan": set(KEY_COLUMNS + ["kode_kabupaten_kota", "jenis_usaha", "jumlah_umkm"]),
        "penduduk": set(KEY_COLUMNS + ["kode_kabupaten_kota", "jumlah_penduduk"]),
        "pengeluaran": set(KEY_COLUMNS + ["kode_kabupaten_kota", "pengeluaran_per_kapita"]),
    }

    for key, columns in required.items():
        missing = columns.difference(datasets[key].columns)
        if missing:
            raise ValueError(f"Kolom wajib hilang di {DATASET_FILES[key]}: {sorted(missing)}")


def remove_duplicate_rows(df: pd.DataFrame, subset: list[str]) -> tuple[pd.DataFrame, int]:
    before = len(df)
    clean = df.drop_duplicates(subset=subset, keep="first").copy()
    return clean, before - len(clean)


def prepare_proyeksi_umkm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=KEY_COLUMNS + ["kode_kabupaten_kota", "proyeksi_jumlah_umkm"]).copy()
    df, _ = remove_duplicate_rows(df, KEY_COLUMNS)
    df = df.sort_values(["nama_kabupaten_kota", "tahun"])
    df["pertumbuhan_pct"] = (
        df.groupby("nama_kabupaten_kota")["proyeksi_jumlah_umkm"]
        .pct_change()
        .mul(100)
        .round(4)
    )
    df["pertumbuhan_abs"] = (
        df.groupby("nama_kabupaten_kota")["proyeksi_jumlah_umkm"].diff()
    )
    return df[df["tahun"].isin(OVERLAP_YEARS)].copy()


def prepare_penduduk(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=KEY_COLUMNS + ["jumlah_penduduk"]).copy()
    df, _ = remove_duplicate_rows(df, KEY_COLUMNS)
    return df[df["tahun"].isin(OVERLAP_YEARS)].copy()


def prepare_pengeluaran(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=KEY_COLUMNS + ["pengeluaran_per_kapita"]).copy()
    df, _ = remove_duplicate_rows(df, KEY_COLUMNS)
    return df[df["tahun"].isin(OVERLAP_YEARS)].copy()


def prepare_umkm_binaan(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.dropna(subset=KEY_COLUMNS + ["jenis_usaha", "jumlah_umkm"]).copy()
    df, _ = remove_duplicate_rows(df, KEY_COLUMNS + ["jenis_usaha"])
    df = df[df["tahun"].isin(OVERLAP_YEARS)].copy()

    sector_totals = (
        df.groupby(KEY_COLUMNS + ["jenis_usaha"], as_index=False)["jumlah_umkm"]
        .sum()
        .sort_values(KEY_COLUMNS + ["jumlah_umkm", "jenis_usaha"], ascending=[True, True, False, True])
    )

    dominant = sector_totals.loc[
        sector_totals.groupby(KEY_COLUMNS)["jumlah_umkm"].idxmax()
    ].rename(
        columns={
            "jenis_usaha": "sektor_dominan",
            "jumlah_umkm": "jumlah_sektor_dominan",
        }
    )

    total = (
        df.groupby(KEY_COLUMNS, as_index=False)["jumlah_umkm"]
        .sum()
        .rename(columns={"jumlah_umkm": "total_umkm_binaan"})
    )

    summary = total.merge(dominant, on=KEY_COLUMNS, how="left")
    summary["share_sektor_dominan_pct"] = (
        summary["jumlah_sektor_dominan"] / summary["total_umkm_binaan"] * 100
    ).fillna(0).round(4)

    pivot = sector_totals.pivot_table(
        index=KEY_COLUMNS,
        columns="jenis_usaha",
        values="jumlah_umkm",
        fill_value=0,
        aggfunc="sum",
    )
    pivot.columns = [f"binaan_{normalize_text(col).lower().replace(' ', '_')}" for col in pivot.columns]
    pivot = pivot.reset_index()

    return summary, pivot


def create_clean_dataset(datasets: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    proyeksi = prepare_proyeksi_umkm(datasets["proyeksi_umkm"])
    penduduk = prepare_penduduk(datasets["penduduk"])
    pengeluaran = prepare_pengeluaran(datasets["pengeluaran"])
    binaan_summary, binaan_pivot = prepare_umkm_binaan(datasets["umkm_binaan"])

    clean = proyeksi[
        [
            "kode_provinsi",
            "nama_provinsi",
            "kode_kabupaten_kota",
            "nama_kabupaten_kota",
            "tahun",
            "proyeksi_jumlah_umkm",
            "pertumbuhan_abs",
            "pertumbuhan_pct",
        ]
    ].merge(
        penduduk[KEY_COLUMNS + ["jumlah_penduduk"]],
        on=KEY_COLUMNS,
        how="inner",
        validate="one_to_one",
    ).merge(
        pengeluaran[KEY_COLUMNS + ["pengeluaran_per_kapita"]],
        on=KEY_COLUMNS,
        how="inner",
        validate="one_to_one",
    ).merge(
        binaan_summary,
        on=KEY_COLUMNS,
        how="inner",
        validate="one_to_one",
    )

    clean["jumlah_umkm"] = clean["proyeksi_jumlah_umkm"]
    clean["jumlah_penduduk_ribu"] = clean["jumlah_penduduk"]
    clean["daya_beli"] = clean["pengeluaran_per_kapita"]
    clean["kepadatan_per_1000"] = (
        clean["jumlah_umkm"] / clean["jumlah_penduduk_ribu"]
    ).round(4)

    ordered_columns = [
        "kode_provinsi",
        "nama_provinsi",
        "kode_kabupaten_kota",
        "nama_kabupaten_kota",
        "tahun",
        "jumlah_umkm",
        "proyeksi_jumlah_umkm",
        "jumlah_penduduk_ribu",
        "pengeluaran_per_kapita",
        "daya_beli",
        "total_umkm_binaan",
        "sektor_dominan",
        "jumlah_sektor_dominan",
        "share_sektor_dominan_pct",
        "kepadatan_per_1000",
        "pertumbuhan_abs",
        "pertumbuhan_pct",
    ]
    clean = clean[ordered_columns].sort_values(KEY_COLUMNS).reset_index(drop=True)

    return clean, binaan_pivot


def make_documentation(
    original: dict[str, pd.DataFrame],
    standardized: dict[str, pd.DataFrame],
    clean: pd.DataFrame,
) -> pd.DataFrame:
    initial_missing = sum(int(df.isna().sum().sum()) for df in original.values())
    final_missing = int(clean.isna().sum().sum())
    initial_duplicates = sum(
        int(df.duplicated().sum()) for df in original.values()
    )
    final_duplicates = int(clean.duplicated(KEY_COLUMNS).sum())

    region_counts_before = {
        key: int(df["nama_kabupaten_kota"].nunique())
        for key, df in original.items()
        if "nama_kabupaten_kota" in df.columns
    }
    region_counts_after = {
        key: int(df["nama_kabupaten_kota"].nunique())
        for key, df in standardized.items()
        if "nama_kabupaten_kota" in df.columns
    }

    numeric_nulls_after_coerce = {
        key: int(df[NUMERIC_COLUMNS[key]].isna().sum().sum())
        for key, df in standardized.items()
    }
    outliers = {
        "proyeksi_jumlah_umkm": count_outliers_iqr(standardized["proyeksi_umkm"]["proyeksi_jumlah_umkm"]),
        "jumlah_penduduk": count_outliers_iqr(standardized["penduduk"]["jumlah_penduduk"]),
        "pengeluaran_per_kapita": count_outliers_iqr(standardized["pengeluaran"]["pengeluaran_per_kapita"]),
        "jumlah_umkm_binaan": count_outliers_iqr(standardized["umkm_binaan"]["jumlah_umkm"]),
    }

    notes = [
        cleaning_note(
            "missing_value",
            f"Total nilai kosong awal: {initial_missing}.",
            "Baris dengan nilai kosong pada kolom kunci/nilai wajib disisihkan sebelum join.",
            f"Total nilai kosong pada clean dataset: {final_missing}.",
            "Kolom kunci dan indikator numerik harus lengkap agar clustering tidak bias.",
        ),
        cleaning_note(
            "duplikasi",
            f"Total duplikasi baris penuh awal: {initial_duplicates}.",
            "Duplikasi dihapus berdasarkan grain masing-masing dataset: wilayah+tahun atau wilayah+tahun+jenis_usaha.",
            f"Duplikasi kunci nama_kabupaten_kota+tahun pada clean dataset: {final_duplicates}.",
            "Join one-to-one membutuhkan satu observasi per wilayah per tahun.",
        ),
        cleaning_note(
            "format_wilayah",
            f"Jumlah wilayah unik awal per dataset: {region_counts_before}.",
            "Nama wilayah dibuat uppercase, whitespace dirapikan, singkatan KAB. dinormalisasi, dan diselaraskan memakai kode_kabupaten_kota.",
            f"Jumlah wilayah unik setelah standardisasi: {region_counts_after}.",
            "Nama kabupaten/kota adalah kunci join utama bersama tahun.",
        ),
        cleaning_note(
            "tipe_data",
            "Kolom numerik dibaca dari CSV dan berpotensi menjadi object jika ada format tidak konsisten.",
            "Kolom tahun, kode wilayah, dan indikator numerik dikonversi dengan pandas.to_numeric.",
            f"Nilai gagal konversi numerik setelah standardisasi: {numeric_nulls_after_coerce}.",
            "Perhitungan pertumbuhan, kepadatan, dan daya beli membutuhkan tipe numerik.",
        ),
        cleaning_note(
            "outlier",
            f"Jumlah kandidat outlier IQR: {outliers}.",
            "Outlier dideteksi, tetapi tidak dihapus karena nilai ekstrem dapat merepresentasikan karakteristik wilayah besar/kota.",
            "Seluruh observasi wilayah 2019-2023 dipertahankan selama kunci dan nilai wajib lengkap.",
            "Clustering membutuhkan variasi antarwilayah; penghapusan outlier geografis dapat menghilangkan sinyal penting.",
        ),
        cleaning_note(
            "integrasi_dataset",
            "Dataset memiliki periode berbeda: UMKM 2016-2023, binaan 2019-2023, penduduk 2010-2025, pengeluaran 2010-2024.",
            "Semua dataset dibatasi ke periode overlap 2019-2023, lalu di-inner join dengan kunci nama_kabupaten_kota+tahun.",
            f"Clean dataset berisi {len(clean)} baris, {clean['nama_kabupaten_kota'].nunique()} wilayah, tahun {int(clean['tahun'].min())}-{int(clean['tahun'].max())}.",
            "Periode overlap memastikan semua indikator tersedia untuk setiap observasi analisis.",
        ),
        cleaning_note(
            "feature_engineering",
            "Dataset mentah belum memiliki kepadatan UMKM, pertumbuhan tahunan, daya beli terstandar, dan sektor dominan.",
            "Membuat kepadatan_per_1000, pertumbuhan_pct, daya_beli, total_umkm_binaan, sektor_dominan, dan share_sektor_dominan_pct.",
            "Kolom fitur baru tersedia di clean_dataset.csv.",
            "Fitur ini sesuai variabel input dan personalisasi rekomendasi pada desain proyek.",
        ),
    ]

    return pd.DataFrame(notes)


def validate_clean_dataset(clean: pd.DataFrame) -> None:
    expected_rows = 27 * len(list(OVERLAP_YEARS))
    if len(clean) != expected_rows:
        raise ValueError(f"Jumlah baris clean dataset {len(clean)} != expected {expected_rows}")
    if clean["nama_kabupaten_kota"].nunique() != 27:
        raise ValueError("Clean dataset tidak memuat 27 kabupaten/kota.")
    if sorted(clean["tahun"].unique().tolist()) != list(OVERLAP_YEARS):
        raise ValueError("Clean dataset tidak terbatas pada tahun 2019-2023.")
    if clean.duplicated(KEY_COLUMNS).any():
        raise ValueError("Clean dataset masih memiliki duplikasi kunci wilayah+tahun.")
    if clean.isna().any().any():
        null_counts = clean.isna().sum()
        raise ValueError(f"Clean dataset masih memiliki missing value: {null_counts[null_counts > 0].to_dict()}")


def run_scrub(base_dir: Path | str = BASE_DIR) -> dict[str, Path]:
    base_dir = Path(base_dir)
    raw_dir = base_dir / "raw_data"
    clean_dir = base_dir / "clean_data"
    docs_dir = base_dir / "docs"
    clean_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)

    original = {key: read_raw_dataset(raw_dir, key) for key in DATASET_FILES}
    region_reference = build_region_reference(original.values())
    standardized = {
        key: standardize_dataset(df, key, region_reference)
        for key, df in original.items()
    }
    validate_required_columns(standardized)

    clean, binaan_pivot = create_clean_dataset(standardized)
    validate_clean_dataset(clean)

    documentation = make_documentation(original, standardized, clean)

    clean_path = clean_dir / "clean_dataset.csv"
    pivot_path = clean_dir / "umkm_binaan_pivot.csv"
    doc_path = docs_dir / "scrub_documentation.csv"
    summary_path = docs_dir / "scrub_summary.json"

    clean.to_csv(clean_path, index=False)
    binaan_pivot.to_csv(pivot_path, index=False)
    documentation.to_csv(doc_path, index=False)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_files": DATASET_FILES,
        "output_files": {
            "clean_dataset": str(clean_path),
            "umkm_binaan_pivot": str(pivot_path),
            "scrub_documentation": str(doc_path),
        },
        "periode_analisis": "2019-2023",
        "rows": int(len(clean)),
        "columns": int(clean.shape[1]),
        "kabupaten_kota": int(clean["nama_kabupaten_kota"].nunique()),
        "missing_values": int(clean.isna().sum().sum()),
        "duplicate_keys": int(clean.duplicated(KEY_COLUMNS).sum()),
        "feature_columns": [
            "kepadatan_per_1000",
            "pertumbuhan_pct",
            "daya_beli",
            "sektor_dominan",
            "total_umkm_binaan",
            "share_sektor_dominan_pct",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return {
        "clean_dataset": clean_path,
        "umkm_binaan_pivot": pivot_path,
        "scrub_documentation": doc_path,
        "scrub_summary": summary_path,
    }


def main() -> None:
    outputs = run_scrub(BASE_DIR)
    print("Tahap S (Scrub) selesai.")
    print(f"- Clean dataset      : {outputs['clean_dataset']}")
    print(f"- Pivot UMKM binaan  : {outputs['umkm_binaan_pivot']}")
    print(f"- Dokumentasi scrub  : {outputs['scrub_documentation']}")
    print(f"- Ringkasan scrub    : {outputs['scrub_summary']}")


if __name__ == "__main__":
    main()

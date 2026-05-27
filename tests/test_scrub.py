import importlib.util
import shutil
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_scrub_module():
    spec = importlib.util.spec_from_file_location("scrub", PROJECT_ROOT / "02_scrub.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_raw_data(tmp_path):
    raw_dir = tmp_path / "raw_data"
    raw_dir.mkdir()
    for source in (PROJECT_ROOT / "raw_data").glob("*.csv"):
        shutil.copy(source, raw_dir / source.name)
    return raw_dir


def test_scrub_pipeline_creates_joined_clean_dataset_for_overlap_years(tmp_path):
    copy_raw_data(tmp_path)
    scrub = load_scrub_module()

    result = scrub.run_scrub(base_dir=tmp_path)

    clean_path = tmp_path / "clean_data" / "clean_dataset.csv"
    assert result["clean_dataset"] == clean_path
    assert clean_path.exists()

    clean = pd.read_csv(clean_path)
    assert clean.shape[0] == 135
    assert clean["nama_kabupaten_kota"].nunique() == 27
    assert sorted(clean["tahun"].unique()) == [2019, 2020, 2021, 2022, 2023]
    assert clean.duplicated(["nama_kabupaten_kota", "tahun"]).sum() == 0
    assert clean.isna().sum().sum() == 0


def test_scrub_pipeline_builds_required_features_and_documentation(tmp_path):
    copy_raw_data(tmp_path)
    scrub = load_scrub_module()

    scrub.run_scrub(base_dir=tmp_path)

    clean = pd.read_csv(tmp_path / "clean_data" / "clean_dataset.csv")
    required_columns = {
        "kepadatan_per_1000",
        "pertumbuhan_pct",
        "daya_beli",
        "sektor_dominan",
        "total_umkm_binaan",
    }
    assert required_columns.issubset(clean.columns)
    assert (clean["kepadatan_per_1000"] > 0).all()
    assert clean["pertumbuhan_pct"].between(-100, 100).all()
    assert clean["sektor_dominan"].str.len().gt(0).all()

    doc_path = tmp_path / "docs" / "scrub_documentation.csv"
    assert doc_path.exists()
    docs = pd.read_csv(doc_path)
    assert {
        "missing_value",
        "duplikasi",
        "format_wilayah",
        "tipe_data",
        "outlier",
        "integrasi_dataset",
        "feature_engineering",
    }.issubset(set(docs["masalah_data"]))

import csv
with open("docs/dataset_inventory.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
for r in rows:
    print("[" + r["kategori"] + "] " + r["filename"])
    print("  Nama   : " + r["nama_dataset"])
    print("  Sumber : " + r["sumber"])
    print("  Periode: " + r["periode"] + "  | Baris: " + r["n_rows"] + "  | Kolom: " + r["n_cols"])
    print("  Status : " + r["status"] + "  | MD5: " + r["md5_checksum"][:16] + "...")
    print()

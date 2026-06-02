"""
03_explore.py  —  Data Pipeline: Tahap E (Explore)
Peran   : Data Analyst 
Tasks:
  1. Statistik deskriptif 3 indikator utama
  2. Distribusi UMKM per kab/kota
  3. Tren pertumbuhan 2019-2023
  4. Perbandingan daya beli antar wilayah
  5. Min. 3 visualisasi eksploratif (PNG)

Input : clean_data/clean_dataset.csv
Output: output/visualizations/*.png
"""

import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Membuat folder output/visualization
folder_output = "output/visualization"
os.makedirs(folder_output)

# Gathering Data
clean_dataset = pd.read_csv("clean_data/clean_dataset.csv")
umkm_binaan_pivot = pd.read_csv("clean_data/umkm_binaan_pivot.csv")

# Membuat folder untuk menyimpan hasil visualisasi
folder_utama = "output/visualization"

# 1. Membuat data dan visualisasi untuk eksplorasi "Distribusi UMKM per Kab/Kota"
periode = [2019, 2020, 2021, 2022, 2023]
def umkm_distribution(t, n_top):
  tahun = clean_dataset[clean_dataset["tahun"] == t]
  lima_baris_pertama = tahun.sort_values(by="proyeksi_jumlah_umkm", ascending=False).iloc[0:n_top, :]
  value_umkm = list(lima_baris_pertama["proyeksi_jumlah_umkm"].values.tolist())
  return value_umkm

def visualization_umkm_distribution(n_top):
    tahun = clean_dataset[clean_dataset["tahun"] == 2019]
    lima_baris_pertama = tahun.sort_values(by="proyeksi_jumlah_umkm", ascending=False).iloc[0:n_top, :]
    nama_kabupaten_kota = lima_baris_pertama["nama_kabupaten_kota"].values.tolist()

    value_kota1 = [umkm_distribution(tahun_ke, 5)[0] for tahun_ke in periode]
    value_kota2 = [umkm_distribution(tahun_ke, 5)[1] for tahun_ke in periode]
    value_kota3 = [umkm_distribution(tahun_ke, 5)[2] for tahun_ke in periode]
    value_kota4 = [umkm_distribution(tahun_ke, 5)[3] for tahun_ke in periode]
    value_kota5 = [umkm_distribution(tahun_ke, 5)[4] for tahun_ke in periode]

    plt.figure(figsize=(12, 6))
    plt.plot(["2019", "2020", "2021", "2022", "2023"], value_kota1, marker="o", color='#2E5A88', label=nama_kabupaten_kota[0])
    plt.plot(["2019", "2020", "2021", "2022", "2023"], value_kota2, marker="^", color='#D9822B', label=nama_kabupaten_kota[1])
    plt.plot(["2019", "2020", "2021", "2022", "2023"], value_kota3, marker="x", color='#538053', label=nama_kabupaten_kota[2])
    plt.plot(["2019", "2020", "2021", "2022", "2023"], value_kota4, marker="*", color='#A64B2A', label=nama_kabupaten_kota[3])
    plt.plot(["2019", "2020", "2021", "2022", "2023"], value_kota5, marker="d", color='#8E6C88', label=nama_kabupaten_kota[4])

    plt.title("Distribusi Jumlah UMKM untuk 5 Kab/Kota Teratas selama Periode 2019 - 2023")
    plt.xlabel("Tahun")
    plt.ylabel("Proyeksi Jumlah UMKM")
    plt.legend()

    nama_file_gambar = os.path.join(folder_utama, "distribusi_umkm_per_kab_kota.png")
    plt.savefig(nama_file_gambar, format="jpg", dpi=300, bbox_inches="tight")
    plt.close()


# 2. Membuat data dan visualisasi untuk eksplorasi "Tren Pertumbuhan ABS Periode 2019-2023"
def pertumbuhan_abs():
    label = ['KABUPATEN BOGOR', 'KABUPATEN BANDUNG', 'KOTA BANDUNG', 'KABUPATEN SUKABUMI', 'KABUPATEN GARUT']
    color = ['green', 'red', 'orange', 'blue', 'purple']

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=clean_dataset, x='tahun', y='pertumbuhan_abs', hue='nama_kabupaten_kota', 
            palette=['#D3D3D3']*clean_dataset['nama_kabupaten_kota'].nunique(), legend=False, alpha=0.5)
    
    for i, daerah in enumerate(label):
        df_highlight = clean_dataset[clean_dataset['nama_kabupaten_kota'] == daerah]
        sns.lineplot(data=df_highlight, x='tahun', y='pertumbuhan_abs', color=color[i], linewidth=3, label=daerah.title())
    plt.title('Tren Pertumbuhan Absolut UMKM', fontsize=14)
    plt.xlabel('Tahun')
    plt.ylabel('Pertumbuhan Absolut')
    plt.xticks(clean_dataset['tahun'].unique())
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend()
    nama_file_gambar = os.path.join(folder_utama, "tren_pertumbuhan_abs.png")
    plt.savefig(nama_file_gambar, format="jpg", dpi=300, bbox_inches="tight")
    plt.close()


# 3. Membuat data dan visualisasi untuk eksplorasi "Perbandingan Daya Beli antar Wilayah"
def distribusi_daya_beli(t):
    tahun = clean_dataset[clean_dataset["tahun"] == t]
    daya_beli = tahun.groupby("nama_kabupaten_kota")["daya_beli"].agg({"sum"}).reset_index()
    daya_beli = daya_beli.sort_values(by="sum", ascending=True).reset_index()
    daya_beli.drop(columns="index", inplace=True)
    daya_beli = daya_beli["sum"].iloc[0:5].values.tolist()
    return daya_beli

def visualization_purchasing_power (daya_beli_data):
    fig, ax = plt.subplots(3, 2, figsize=(18, 10))
    ax = ax.flatten()

    tahun_2019 = clean_dataset[clean_dataset["tahun"] == 2019]
    kota_kab = tahun_2019.groupby("nama_kabupaten_kota")["daya_beli"].agg({"sum"}).reset_index()
    kota_kab = kota_kab.sort_values(by="sum", ascending=True).reset_index()
    kota_kab = list(kota_kab["nama_kabupaten_kota"].iloc[0:5].values)
    tahun = [2019, 2020, 2021, 2022, 2023]

    for i, data in enumerate(daya_beli_data):
        ax[i].barh(kota_kab, data, height=0.5)
        ax[i].set_xlim(left=4000)
        ax[i].set_title(f"Daya Beli Tahun {tahun[i]}")
        ax[i].set_xlabel("Jumlah")
        ax[i].set_ylabel("Nama Kabupaten/Kota")
    fig.delaxes(ax[5])
    plt.suptitle("Top 5 dengan Daya Beli Tertinggi pada Periode 2019 - 2023")
    plt.tight_layout()
    nama_file_gambar = os.path.join(folder_utama, "perbandingan_daya_beli.png")
    plt.savefig(nama_file_gambar, format="jpg", dpi=300, bbox_inches="tight")
    plt.close()


# 4. Membuat data dan visualisasi untuk eksplorasi "Analisis Sektor Unggulan tiap Tahun"
def leading_sector_analysis(t):
    semua_sektor_tiap_tahun = [umkm_binaan_pivot[umkm_binaan_pivot["tahun"] == t[i]] for i in range(5)]

    for i in range(len(semua_sektor_tiap_tahun)):
        total_per_kolom = semua_sektor_tiap_tahun[i].sum(numeric_only=True)
        semua_sektor_tiap_tahun[i].loc['TOTAL'] = total_per_kolom
        semua_sektor_tiap_tahun[i].loc['TOTAL', "nama_kabupaten_kota"] = "TOTAL KESELURUHAN"
        semua_sektor_tiap_tahun[i].loc['TOTAL', "tahun"] = "-"
    baris_total_sektor = [semua_sektor_tiap_tahun[j].iloc[-1:, 2:17] for j in range(5)]
    list_value = [baris_total_sektor[k].loc["TOTAL", baris_total_sektor[k].dtypes != "object"].tolist() for k in range(5)]
    return list_value

def visualization_sector_analysis(t):
    semua_sektor = ["Agribisnis","Aksesoris","Batik","Bordir","Craft","Dekorasi","Fashion","Industri","Jasa","Konveksi","Kuliner","Makanan","Mebel","Minuman","Obat-obatan"]

    plt.figure(figsize=(18, 8))
    plt.plot(semua_sektor, leading_sector_analysis(t)[0], marker="x", label="2019")
    plt.plot(semua_sektor, leading_sector_analysis(t)[1], marker="o", label="2020")
    plt.plot(semua_sektor, leading_sector_analysis(t)[2], marker="s", label="2021")
    plt.plot(semua_sektor, leading_sector_analysis(t)[3], marker="d", label="2022")
    plt.plot(semua_sektor, leading_sector_analysis(t)[4], marker="p", label="2023")

    plt.title("Jumlah UMKM untuk Setiap Sektor pada Periode 2019 - 2023")
    plt.xlabel("Sektor Bisnis")
    plt.ylabel("Jumlah UMKM")
    plt.legend()
    nama_file_gambar = os.path.join(folder_utama, "analisis_sektor_unggulan.png")
    plt.savefig(nama_file_gambar, format="jpg", dpi=300, bbox_inches="tight")
    plt.close()

# Fungsi utama untuk mengatur alur
def main():
    print("--- Memulai Program ---")
    visualization_umkm_distribution(5)
    pertumbuhan_abs()
    visualization_purchasing_power([distribusi_daya_beli(2019+i) for i in range(5)])
    visualization_sector_analysis([2019, 2020, 2021, 2022, 2023])
    print("--- Program Selesai ---")

# Blok pengeksekusi
if __name__ == '__main__':
    main()


















  

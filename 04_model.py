"""
04_model.py  —  Data Pipeline: Tahap M (Model)
Peran   : Data Analyst / Modeler
Tasks:
  1. Tentukan K optimal (Elbow Method / Silhouette Score)
  2. K-Means clustering (K=4) dengan 3 variabel input:
       - kepadatan_per_1000
       - pertumbuhan_pct
       - daya_beli
  3. Label klaster A/B/C/ berdasarkan profil rata-rata
  4. Analisis sektor dominan per klaster
Input : clean_data/clean_dataset.csv
Output: output/models/clustering_result.csv
        output/models/cluster_profile.csv
"""

import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans
from yellowbrick.cluster import KElbowVisualizer

# ==========================================
# 1. PERSIAPAN DATA & FOLDER
# ==========================================

# Membuat folder output
folder_output = "output/models"
os.makedirs(folder_output, exist_ok=True)

# Path untuk menyimpan hasil
clustering_result_path = os.path.join(folder_output, "clustering_result.csv")
clustering_profile_path = os.path.join(folder_output, "clustering_profile.csv")

# Membaca dataset utama sekali di awal
clean_dataset = pd.read_csv("clean_data/clean_dataset.csv")


def data_splitting(df):
    """Memisahkan fitur yang digunakan untuk clustering."""
    fitur = ["kepadatan_per_1000", "pertumbuhan_pct", "daya_beli"]
    input_data = df[fitur].copy()
    x = input_data.values
    return x, input_data


# ==========================================
# 2. FUNGSI UTAMA MODELING & ANALISIS
# ==========================================

def elbow_method(x):
    """Menampilkan dan menyimpan grafik Elbow Method."""
    kmeans = KMeans(random_state=42)
    visualizer = KElbowVisualizer(kmeans, k=(1, 10))
    visualizer.fit(x)
    
    # Simpan visualisasi
    output_img = os.path.join(folder_output, "elbow_method_visualization.jpg")
    visualizer.show(outpath=output_img, dpi=300)
    plt.close() # Menutup plot agar menghemat memori


def clustering_data(x, input_data, n_clusters=3):
    """Menjalankan KMeans clustering SEKALI saja."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(x)
    
    # Menambahkan label ke dataframe input (Skala 1-based cluster)
    df_hasil = input_data.copy()
    df_hasil["cluster"] = labels + 1
    
    return df_hasil, labels, kmeans


def analyze_clusters(df_hasil):
    """
    Menggantikan looping manual yang lambat dengan fungsi .groupby() Pandas.
    Jauh lebih cepat dan ringkas!
    """
    # Menghitung rata-rata untuk setiap fitur berdasarkan cluster
    clustering_profile = df_hasil.groupby('cluster').mean()
    
    # Rename kolom agar sesuai format awal Anda
    clustering_profile = clustering_profile.rename(columns={
        'kepadatan_per_1000': 'Rata-Rata Kepadatan per 1000',
        'pertumbuhan_pct': 'Rata-Rata Pertumbuhan PCT',
        'daya_beli': 'Rata-Rata Daya Beli'
    })
    
    # Membulatkan nilai ke 2 angka di belakang koma
    clustering_profile = clustering_profile.round(2)
    
    return clustering_profile


# ==========================================
# 3. FUNGSI VISUALISASI & PENYIMPANAN
# ==========================================

def visualization_clustering(df_hasil):
    """Membuat scatter plot 3D dari hasil clustering."""
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    colors = {1: 'red', 2: 'blue', 3: 'green'}
    
    for cluster_id in df_hasil['cluster'].unique():
        subset = df_hasil[df_hasil['cluster'] == cluster_id]
        ax.scatter(
            subset['kepadatan_per_1000'],
            subset['pertumbuhan_pct'],
            subset['daya_beli'],
            c=colors.get(cluster_id, 'black'),
            label=f'Cluster {cluster_id}',
            s=50,
            alpha=0.7
        )
        
    ax.set_title("Visualisasi 3D Hasil Clustering K-Means", fontsize=14, pad=20, fontweight='bold')
    ax.set_xlabel("Kepadatan per 1000", fontsize=11, labelpad=10)
    ax.set_ylabel("Pertumbuhan PCT", fontsize=11, labelpad=10)
    ax.set_zlabel("Daya Beli", fontsize=11, labelpad=10)
    ax.legend(title="Cluster")
    
    nama_file_gambar = os.path.join(folder_output, "visualization_clustering_result.png")
    plt.savefig(nama_file_gambar, format="png", dpi=300, bbox_inches="tight")
    plt.close()


# ==========================================
# 4. ALUR EKSEKUSI UTAMA (PROSEDUR UTAMA)
# ==========================================

def main():
    print("--- Memulai Proses Analisis Clustering ---")
    
    # 1. Split Data
    print("[1/5] Memisahkan data...")
    x, input_data = data_splitting(clean_dataset)
    
    # 2. Elbow Method
    print("[2/5] Menjalankan Elbow Method...")
    elbow_method(x)
    
    # 3. Clustering (Hanya running fit_predict 1 kali di sini!)
    print("[3/5] Menjalankan modeling KMeans...")
    df_hasil, labels, kmeans_model = clustering_data(x, input_data, n_clusters=3)
    
    # 4. Analisis Karakteristik Cluster (Sangat cepat menggunakan groupby)
    print("[4/5] Membuat profil karakteristik cluster...")
    df_profil = analyze_clusters(df_hasil)
    
    # 5. Visualisasi & Simpan Hasil
    print("[5/5] Menyimpan data hasil dan visualisasi 3D...")
    visualization_clustering(df_hasil)
    
    # Menyimpan file CSV
    df_hasil.to_csv(clustering_result_path, index=False)
    df_profil.to_csv(clustering_profile_path, index=True) # index=True karena index-nya adalah 'cluster'
    

# Proteksi boilerplate agar file bisa dijalankan via terminal/command prompt
if __name__ == "__main__":
    main()
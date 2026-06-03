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
from sklearn.metrics import silhouette_score

# Membuat folder untuk menyimpan hasil vlisualisasi
folder_output = "output/models"
os.makedirs(folder_output)

# path source
clustering_result_path = os.path.join(folder_output, clustering_result.csv)
clustering_profile_path = os.path.join(folder_output, clustering_profile.csv)

# Gathering Data
clean_dataset = pd.read_csv("clean_data/clean_dataset.csv")

# Membuat fungsi untuk Data Splitting
def data_splitting():
    input = clean_dataset[["kepadatan_per_1000", "pertumbuhan_pct", "daya_beli"]]
    x = input.values
    return x, input

# Membuat fungsi untuk Elbow Method
def elbow_method():
    kmeans = KMeans()
    visualizer = KElbowVisualizer(kmeans, k=(1, 10))
    visualizer.fit(data_splitting()[0])
    visualizer.show(outpath="output/models/elbow_method_visualization.jpg", dpi=300)

# Fungsi untuk membuat data hasil clustering
def clustering_data(x, input):
    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(x)

    # Mendapatkan label cluster
    labels = kmeans.labels_

    hasil_prediksi = kmeans.fit_predict(x)
    input["cluster"] = hasil_prediksi + 1

    return input, labels, kmeans
    
# Fungsi untuk analisis karakteristik cluster
def analyze_clusters(x, k):
    list_clustering_profile = []
    for cluster_id in range(k):
        # Mengambil data untuk cluster saat ini
        cluster_data = x[clustering_data(data_splitting()[0], data_splitting()[1].copy())[1] == cluster_id]

        # Menghitung rata-rata untuk setiap fitur
        mean_kepadatan_per_1000 = cluster_data[:, 0].mean()
        mean_pertumbuhan_pct = cluster_data[:, 1].mean()
        mean_daya_beli = cluster_data[:, 2].mean()

        # Menambahkan data ke DataFrame profil clustering
        list_clustering_profile.append({
            'Cluster': cluster_id + 1,
            'Rata-Rata Kepadatan per 1000': round(float(mean_kepadatan_per_1000), 2),
            'Rata-Rata Pertumbuhan PCT': round(float(mean_pertumbuhan_pct), 2),
            'Rata-Rata Daya Beli': round(float(mean_daya_beli), 2)
        })
    clustering_profile = pd.DataFrame(list_clustering_profile)
    clustering_profile.set_index('Cluster', inplace=True)
    return clustering_profile

# Membuat fungsi untuk visualisasi scatter plot hasil clustering
def visualization_clustering():
    x = data_splitting()[0]
    df_input = data_splitting()[1].copy()
    df_hasil, labels, kmeans_model = clustering_data(x, df_input)
    df = x[labels]

    # Inisialisasi grafik scatter 3d
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Mendefinisikan warna untuk masing-masing cluster
    colors = {1: 'red', 2: 'blue', 3: 'green'}

    # Plot data per cluster
    for cluster_id in df_hasil['cluster'].unique():
        subset = df_hasil[df_hasil['cluster'] == cluster_id]
        ax.scatter(subset['kepadatan_per_1000'], 
               subset['pertumbuhan_pct'], 
               subset['daya_beli'], 
               c=colors[cluster_id], 
               label=f'Cluster {cluster_id}', 
               s=50, alpha=0.7)
    ax.set_title("Visualisasi 3D Hasil Clustering K-Means", fontsize=14, pad=20, fontweight='bold')
    ax.set_xlabel("Kepadatan per 1000", fontsize=11, labelpad=10)
    ax.set_ylabel("Pertumbuhan PCT", fontsize=11, labelpad=10)
    ax.set_zlabel("Daya Beli", fontsize=11, labelpad=10)
    ax.legend(title="Cluster")
    nama_file_gambar = os.path.join(folder_output, "visualization_clustering_result.png")
    plt.savefig(nama_file_gambar, format="jpg", dpi=300, bbox_inches="tight")


def save():
    # Menyimpan clustering_result dalam format csv
    clustering_result = clustering_data(data_splitting()[0], data_splitting()[1].copy())[0]
    clustering_result.to_csv(clustering_result_path, index=False)

    # Menyimpan clustering_profile dalam format .csv
    clustering_profile = analyze_clusters(data_splitting()[0], 3)
    clustering_profile.to_csv(clustering_profile_path, index=False)

    # Menyimpan elbow method dalam format .jpg
    elbow_method()

    # Menyimpan visualisasi scatter plot hasi clustering
    visualization_clustering()


# Running model
save()











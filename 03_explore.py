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
raise NotImplementedError("03_explore.py belum diimplementasikan. "
                          "Silakan diisi oleh Data Analyst/Modeler.")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Gathering Data
clean_dataset = pd.read_csv("clean_data/clean_dataset.csv")
umkm_binaan_pivot = pd.read_csv("clean_data/umkm_binaan_pivot.csv")
\
# Analisis 2: Distribusi UMKM per Kab/Kota
def umkm_distribution(tahun, n_top=5):
  tahun_list = [2019, 2020, 2021, 2022, 2023





















  

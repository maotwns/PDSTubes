import pandas as pd
import numpy as np
import re

# 1. LOAD DATA
# Pake on_bad_lines='skip' biar baris yang berantakan otomatis ke-skip
df = pd.read_csv("DataMasterAll.csv", on_bad_lines='skip', engine='python')

# --- SOURCE CODE SEBELUMNYA (USER PROVIDED) ---
# [Note: Masukkan logic Drop Duplicate, Normalize Type, dll di sini]

# ==============================================================================
# 2. LOGIC AKSESIBILITAS (USING NUMPY & PANDAS VECTORIZATION)
# ==============================================================================

# Cek keberadaan 3 fitur positif secara massal
has_pintu = df['aksesibilitas'].str.contains('pintu masuk khusus pengguna kursi roda', case=False, na=False).astype(int)
has_parkir = df['aksesibilitas'].str.contains('tempat parkir khusus pengguna kursi roda', case=False, na=False).astype(int)
has_toilet = df['aksesibilitas'].str.contains('toilet khusus pengguna kursi roda', case=False, na=False).astype(int)

# Hitung skor total
df['score_temp'] = has_pintu + has_parkir + has_toilet

# Cek fitur negatif (Jika ada 'Tidak memiliki...', skor paksa jadi 0)
has_negative = df['aksesibilitas'].str.contains('Tidak memiliki', case=False, na=False)

# Tentukan skor final menggunakan NumPy
df['aksesibilitas'] = np.where(has_negative, 0, df['score_temp'])

# Tentukan Label menggunakan np.select (Gaya Data Science banget)
conditions = [
    (df['aksesibilitas'] == 0),
    (df['aksesibilitas'] < 3),
    (df['aksesibilitas'] >= 3)
]
choices = ["Tidak Tersedia", "Aksebilitas Cukup", "Aksebilitas Lengkap"]
df['Ketersediaan Akses'] = np.select(conditions, choices, default="Tidak Tersedia")

# Hapus kolom temp
df.drop(columns=['score_temp'], inplace=True)

# ==============================================================================
# 3. LOGIC ALAMAT (USING PANDAS STR EXTRACT & REGEX)
# ==============================================================================

# Ekstrak Jalan dan Kecamatan secara vectorized
df['street'] = df['alamat'].str.extract(r'([^,]*\b(?:Jl\.|Jalan|Jln\.)[^,]*)', flags=re.IGNORECASE).fillna('')
df['kec'] = df['alamat'].str.extract(r'((?:Kec\.|Kecamatan)\s+[A-Za-z\s]+)', flags=re.IGNORECASE).fillna('')

# Bersihkan segmen kecamatan dari sisa koma yang ikut terbawa
df['kec'] = df['kec'].str.split(',').str[0].str.strip()

# Gabungkan Jalan & Kecamatan
df['alamat'] = df['street'] + ", " + df['kec']
df['alamat'] = df['alamat'].str.strip(', ')

# Hapus Plus Code (e.g. 3JRQ+QC2) dan Kode Pos (5 digit) pake Regex massal
# \b[A-Z0-9]{4}\+[A-Z0-9]{2,}\b -> pola Plus Code Google Maps
# \b\d{5}\b -> pola Kode Pos Indonesia
df['alamat'] = df['alamat'].str.replace(r'\b[A-Z0-9]{4}\+[A-Z0-9]{2,}\b', '', regex=True)
df['alamat'] = df['alamat'].str.replace(r'\b\d{5}\b', '', regex=True)

# Final touch: bersihkan sisa koma berlebih atau spasi ganda
df['alamat'] = df['alamat'].str.replace(r',\s*,', ',', regex=True).str.strip(', ')

# Hapus kolom temp
df.drop(columns=['street', 'kec'], inplace=True)

# ==============================================================================
# 4. SAVE & RESULT
# ==============================================================================
df.to_csv("DataMaster_Final_Clean.csv", index=False)

print("Pembersihan Aksesibilitas & Alamat selesai pake Pandas/NumPy!")
print(df[['nama_tempat', 'alamat', 'Ketersediaan Akses', 'aksesibilitas']].head())
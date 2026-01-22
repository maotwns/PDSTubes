import pandas as pd
import re
import numpy as np


# Read CSV
df = pd.read_csv("DataMasterAll.csv")

# Drop Duplicate
df["nama_tempat_clean"] = (
    df["nama_tempat"]
    .str.lower()
    .str.strip()
)

df["alamat_clean"] = (
    df["alamat"]
    .str.lower()
    .str.strip()
)

df = df.drop_duplicates(
    subset=["nama_tempat_clean", "alamat_clean"]
)

df = df.drop(columns=["nama_tempat_clean", "alamat_clean"])

sebelum = pd.read_csv("DataMasterAll.csv").shape[0]
sesudah = df.shape[0]

print("Record sebelum:", sebelum)
print("Record sesudah :", sesudah)
print("Duplikat dihapus:", sebelum - sesudah)

# Normalisasi Tipe Tempat
katolik_keywords = [
    "katolik", "katedral", "keuskupan"
]

protestan_keywords = [
    "kristen", "protestan", "hkbp", "gki", "gpib",
    "gkj", "gkps", "gkp", "gbi", "gbit", "ifgf",
    "bethany", "gsja", "gbis", "gkkd"
]

def normalize_type(row):
    name = str(row["nama_tempat"]).lower()
    tp = str(row["type_place"]).lower()

    if "masjid" in name or "masjid" in tp:
        return "Masjid"

    if "vihara" in name or "vihara" in tp:
        return "Vihara"

    if "pura" in name or "pura" in tp:
        return "Pura"

    if "gereja" in name or "gereja" in tp:
        if any(k in name for k in katolik_keywords):
            return "Gereja Katolik"
        elif any(k in name for k in protestan_keywords):
            return "Gereja Protestan"
        else:
            return "Gereja Umum"

    return "Lainnya"

df["type_place_clean"] = df.apply(normalize_type, axis=1)

# drop yang Lainnya
df = df[df["type_place_clean"] != "Lainnya"]
df["type_place_clean"].value_counts()
df[["nama_tempat", "type_place", "type_place_clean"]].head(10)

# Cleaning Nama
master = pd.read_csv("master_wilayah_jabar.csv")

# Normalisasi master
master["alias"] = master["alias"].str.lower()

def extract_kota_kab_from_master(alamat):
    if pd.isna(alamat):
        return "Tidak diketahui"

    alamat = alamat.lower()

    for _, row in master.iterrows():
        # alias dipisah |
        patterns = row["alias"].split("|")

        for p in patterns:
            p = p.strip()
            if p and re.search(rf"\b{re.escape(p)}\b", alamat):
                return row["resmi"]

    return "Tidak diketahui"

df["kota_kabupaten"] = df["alamat"].apply(extract_kota_kab_from_master)
df["kota_kabupaten"].value_counts()
df[df["kota_kabupaten"] == "Tidak diketahui"][["alamat"]].head(20)


# Cleaning Jam Operasional

def clean_jam_operasional(text):
    if pd.isna(text):
        return pd.Series([False, None, None, "Tidak diketahui"])

    text = str(text).lower().strip()

    # 24 jam
    if "24 jam" in text or "buka 24" in text:
        return pd.Series([True, "00:00", "23:59", "24 Jam"])

    # format jam umum: 05.00-22.00 / 05:00–22:00
    match = re.search(
        r'(\d{1,2})[.:](\d{2}).*?(\d{1,2})[.:](\d{2})',
        text
    )

    if match:
        open_time = f"{match.group(1).zfill(2)}:{match.group(2)}"
        close_time = f"{match.group(3).zfill(2)}:{match.group(4)}"

        # validasi logis jam
        if open_time < close_time:
            return pd.Series([False, open_time, close_time, "Normal"])
        else:
            return pd.Series([False, open_time, close_time, "Tidak konsisten"])

    return pd.Series([False, None, None, "Tidak konsisten"])

df[[
    "is_24_hours",
    "open_time",
    "close_time",
    "operational_status"
]] = df["jam_operasional"].apply(clean_jam_operasional)

# Distribusi status jam operasional
df["operational_status"].value_counts()

# Contoh data bermasalah
df[df["operational_status"] != "Normal"][[
    "nama_tempat", "jam_operasional", "operational_status"
]].head(10)


#Cleaning Review
df["jumlah_review"] = pd.to_numeric(df["jumlah_review"], errors="coerce")

# jumlah data sebelum
sebelum = df.shape[0]

# drop review < 50
df = df[df["jumlah_review"] >= 50]

# jumlah data sesudah
sesudah = df.shape[0]

print("Record sebelum:", sebelum)
print("Record sesudah :", sesudah)
print("Record di-drop :", sebelum - sesudah)

# Cleaning no tlp

def extract_digits_only(val):
    if pd.isna(val):
        return np.nan

    # ambil semua digit, termasuk yang terpisah simbol aneh
    digits = re.findall(r"\d+", str(val))

    if not digits:
        return np.nan

    return "".join(digits)


df["telepon_digits"] = df["telepon"].apply(extract_digits_only)


# Normalisasi 0
def normalize_phone_strict0(number):
    if pd.isna(number):
        return np.nan

    number = str(number)

    # 62xxxxxxxx → 0xxxxxxxx
    if number.startswith("62"):
        return "0" + number[2:]

    # valid jika sudah diawali 0
    if number.startswith("0"):
        return number

    # selain itu → kosongkan
    return np.nan


df["telepon_clean"] = df["telepon_digits"].apply(normalize_phone_strict0)


df = df.drop(columns=["telepon_digits"])

df[["telepon", "telepon_clean"]].head(15)
df["telepon_clean"].isna().mean()


# Update Availability Telepon
df["stt_tlp"] = df["telepon_clean"].apply(
    lambda x: "Ada" if pd.notna(x) else "Tidak Ada"
)

df["stt_tlp"].value_counts()
df[df["stt_tlp"] == "Ada"][["telepon", "telepon_clean"]].head(10)
df[df["stt_tlp"] == "Tidak Ada"][["telepon", "telepon_clean"]].head(10)


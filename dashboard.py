from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

sns.set(style="dark")

base_dir = Path(__file__).resolve().parent
day_path = base_dir / "day.csv"
hour_path = base_dir / "hour.csv"
fallback_hour_path = base_dir.parent / "data" / "hour.csv"

data = pd.read_csv(day_path)
hour_data = pd.read_csv(hour_path if hour_path.exists() else fallback_hour_path)

data["dteday"] = pd.to_datetime(data["dteday"])
hour_data["dteday"] = pd.to_datetime(hour_data["dteday"])

season_map = {1: "Musim Semi", 2: "Musim Panas", 3: "Musim Gugur", 4: "Musim Dingin"}
data["season_label"] = data["season"].map(season_map).fillna(data["season"].astype(str))
if "season" in hour_data.columns:
    hour_data["season_label"] = hour_data["season"].map(season_map).fillna(
        hour_data["season"].astype(str)
    )

st.sidebar.header("Filter")
min_date = data["dteday"].min().date()
max_date = data["dteday"].max().date()
date_range = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

season_options = list(season_map.values())
selected_seasons = st.sidebar.multiselect(
    "Musim", season_options, default=season_options
)

data_filtered = data[
    (data["dteday"].dt.date >= start_date)
    & (data["dteday"].dt.date <= end_date)
    & (data["season_label"].isin(selected_seasons))
]

hour_filtered = hour_data[
    (hour_data["dteday"].dt.date >= start_date)
    & (hour_data["dteday"].dt.date <= end_date)
]
if "season_label" in hour_filtered.columns:
    hour_filtered = hour_filtered[hour_filtered["season_label"].isin(selected_seasons)]

st.title("Dashboard Penyewaan Sepeda :sparkles:")
st.subheader("Ringkasan Harian")

col1, col2 = st.columns(2)
with col1:
    working_day_rent = data_filtered[data_filtered["workingday"] == 1]
    total_rent = working_day_rent["cnt"].sum()
    st.metric("Total penyewaan (hari kerja)", value=total_rent)
    
with col2:
    holiday_rent = data_filtered[data_filtered["holiday"] == 1]
    total_rent_holiday = holiday_rent["cnt"].sum()
    st.metric("Total penyewaan (hari libur)", value=total_rent_holiday)

data_ten_day = data_filtered.sort_values("dteday").head(10)
fig, ax = plt.subplots(figsize=(16,8))
ax.plot(
    data_ten_day["dteday"],
    data_ten_day["cnt"],
    marker='o',
    linewidth = 2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
 
st.pyplot(fig)

st.subheader("Casual vs Registered (Hari Kerja)")
col1, col2 = st.columns(2)
with col1:
    working_day_casual = data_filtered[data_filtered["workingday"] == 1]
    total_rent = working_day_casual["casual"].sum()
    st.metric("Total casual (hari kerja)", value=total_rent)
    
with col2:
    working_day_registered = data_filtered[data_filtered["workingday"] == 1]
    total_rent_registered = working_day_registered["registered"].sum()
    st.metric("Total registered (hari kerja)", value=total_rent_registered)

workingday_data = data_filtered[data_filtered["workingday"] == 1]

# Hitung total penyewaan casual dan registered pada hari kerja
total_casual = workingday_data['casual'].sum()
total_registered = workingday_data['registered'].sum()

# Data untuk visualisasi
categories = ["Casual", "Registered"]
values = [total_casual, total_registered]

# Membuat plot bar
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(categories, values, color=["#D3D3D3", '#FFB74D'])

# Menambahkan label dan judul
ax.set_title("Total Penyewaan di Hari Kerja", fontsize=18)
ax.set_ylabel(None)

# Menampilkan plot pada Streamlit
st.pyplot(fig)

st.subheader("Casual vs Registered (Hari Libur)")
col1, col2 = st.columns(2)
with col1:
    working_day_casual = data_filtered[data_filtered["holiday"] == 1]
    total_rent = working_day_casual["casual"].sum()
    st.metric("Total casual (hari libur)", value=total_rent)
    
with col2:
    working_day_registered = data_filtered[data_filtered["holiday"] == 1]
    total_rent_registered = working_day_registered["registered"].sum()
    st.metric("Total registered (hari libur)", value=total_rent_registered)

holiday_data = data_filtered[data_filtered["holiday"] == 1]

# Hitung total penyewaan casual dan registered pada hari kerja
total_casual = holiday_data['casual'].sum()
total_registered = holiday_data['registered'].sum()

# Data untuk visualisasi
categories = ["Casual", "Registered"]
values = [total_casual, total_registered]

# Membuat plot bar
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(categories, values, color=["#D3D3D3", '#FFB74D'])

# Menambahkan label dan judul
ax.set_title("Total Penyewaan di Hari Libur", fontsize=18)
ax.set_ylabel(None)

# Menampilkan plot pada Streamlit
st.pyplot(fig)

st.subheader("Pengaruh Kondisi Cuaca terhadap Penyewaan")
fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(data_filtered[["temp", "atemp", "hum", "windspeed", "cnt"]].corr(), annot=True, ax=ax)
st.pyplot(fig)

st.subheader("Perbandingan Hari Kerja vs Hari Libur")
compare_df = (
    data_filtered.groupby("workingday")[["casual", "registered"]]
    .sum()
    .rename(index={0: "Bukan Hari Kerja", 1: "Hari Kerja"})
)
compare_df.index.name = "Jenis Hari"
compare_melted = compare_df.reset_index().melt(
    id_vars="Jenis Hari", var_name="Tipe Pengguna", value_name="Total Penyewaan"
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    data=compare_melted,
    x="Jenis Hari",
    y="Total Penyewaan",
    hue="Tipe Pengguna",
    palette=["#D3D3D3", "#72BCD4"],
    ax=ax,
)
ax.set_title("Total Penyewaan berdasarkan Jenis Hari")
ax.set_xlabel(None)
ax.set_ylabel(None)
st.pyplot(fig)

st.subheader("Faktor Cuaca (Per Jam) vs Penyewaan")
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
sns.scatterplot(x="temp", y="cnt", data=hour_filtered, ax=axes[0, 0])
axes[0, 0].set_title("Suhu vs Penyewaan")
axes[0, 0].set_xlabel("Suhu (Normalisasi)")
axes[0, 0].set_ylabel("Penyewaan")

sns.scatterplot(x="hum", y="cnt", data=hour_filtered, ax=axes[0, 1])
axes[0, 1].set_title("Kelembapan vs Penyewaan")
axes[0, 1].set_xlabel("Kelembapan (Normalisasi)")
axes[0, 1].set_ylabel("Penyewaan")

sns.scatterplot(x="windspeed", y="cnt", data=hour_filtered, ax=axes[1, 0])
axes[1, 0].set_title("Kecepatan Angin vs Penyewaan")
axes[1, 0].set_xlabel("Kecepatan Angin (Normalisasi)")
axes[1, 0].set_ylabel("Penyewaan")

sns.boxplot(x="weathersit", y="cnt", data=hour_filtered, ax=axes[1, 1])
axes[1, 1].set_title("Kondisi Cuaca vs Penyewaan")
axes[1, 1].set_xlabel("Kondisi Cuaca")
axes[1, 1].set_ylabel("Penyewaan")

st.pyplot(fig)

st.subheader("RFM Musiman (Casual vs Registered)")
rfm_base = data_filtered[["dteday", "season", "casual", "registered", "cnt"]].copy()
rfm_long = rfm_base.melt(
    id_vars=["dteday", "season"],
    value_vars=["casual", "registered"],
    var_name="user_type",
    value_name="rentals",
)
rfm_long = rfm_long[rfm_long["rentals"] > 0].copy()
analysis_date = rfm_long["dteday"].max()

rfm = (
    rfm_long.groupby(["season", "user_type"]).agg(
        recency_days=("dteday", lambda x: (analysis_date - x.max()).days),
        frequency=("dteday", "nunique"),
        monetary=("rentals", "sum"),
    )
    .reset_index()
)

rfm["season_label"] = rfm["season"].map(season_map).fillna(rfm["season"].astype(str))

rfm["R"] = (
    rfm.groupby("user_type")["recency_days"]
    .transform(lambda s: pd.qcut(s.rank(method="first"), q=4, labels=[4, 3, 2, 1]))
    .astype(int)
)
rfm["F"] = (
    rfm.groupby("user_type")["frequency"]
    .transform(lambda s: pd.qcut(s.rank(method="first"), q=4, labels=[1, 2, 3, 4]))
    .astype(int)
)
rfm["M"] = (
    rfm.groupby("user_type")["monetary"]
    .transform(lambda s: pd.qcut(s.rank(method="first"), q=4, labels=[1, 2, 3, 4]))
    .astype(int)
)
rfm["rfm_score"] = rfm[["R", "F", "M"]].sum(axis=1)

def label_segment(score):
    if score >= 10:
        return "Nilai Tinggi"
    if score >= 7:
        return "Loyal"
    if score >= 4:
        return "Berisiko"
    return "Nilai Rendah"

rfm["segment"] = rfm["rfm_score"].apply(label_segment)

rfm_summary = rfm[[
    "season_label",
    "user_type",
    "recency_days",
    "frequency",
    "monetary",
    "R",
    "F",
    "M",
    "rfm_score",
    "segment",
]].sort_values(["user_type", "rfm_score"], ascending=[True, False])

st.dataframe(rfm_summary, use_container_width=True)

pivot_score = rfm_summary.pivot(index="season_label", columns="user_type", values="rfm_score")
fig, ax = plt.subplots(figsize=(7, 4))
sns.heatmap(pivot_score, annot=True, cmap="Blues", fmt=".0f", ax=ax)
ax.set_title("Skor RFM per Musim dan Tipe Pengguna")
ax.set_xlabel("Tipe Pengguna")
ax.set_ylabel("Musim")
st.pyplot(fig)

top_segment = rfm_summary.sort_values("rfm_score", ascending=False).head(1)
bottom_segment = rfm_summary.sort_values("rfm_score", ascending=True).head(1)
st.caption(
    "Segmen musim tertinggi: "
    f"{top_segment.iloc[0]['season_label']} - {top_segment.iloc[0]['user_type']} "
    f"({top_segment.iloc[0]['segment']})."
)
st.caption(
    "Segmen musim terendah: "
    f"{bottom_segment.iloc[0]['season_label']} - {bottom_segment.iloc[0]['user_type']} "
    f"({bottom_segment.iloc[0]['segment']})."
)
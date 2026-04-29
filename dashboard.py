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
st.markdown(
    "Dashboard ini merangkum hasil analisis untuk menjawab dua pertanyaan bisnis: "
    "(1) perbedaan permintaan antar musim pada 2012 dan (2) perbedaan pola per jam "
    "antara hari kerja dan akhir pekan pada Q3 2011."
)

st.subheader("Pertanyaan 1: Perbandingan musim 2012")
day_2012 = data_filtered[data_filtered["yr"] == 1].copy()
season_avg = (
    day_2012.groupby("season_label", as_index=False)["cnt"]
    .mean()
    .rename(columns={"cnt": "avg_cnt"})
)

summer_avg = season_avg.loc[season_avg["season_label"] == "Musim Panas", "avg_cnt"].mean()
winter_avg = season_avg.loc[season_avg["season_label"] == "Musim Dingin", "avg_cnt"].mean()
season_gap = summer_avg - winter_avg
lowest_season = season_avg.sort_values("avg_cnt").head(1)

col1, col2, col3 = st.columns(3)
col1.metric("Rata-rata Musim Panas", f"{summer_avg:,.0f}")
col2.metric("Rata-rata Musim Dingin", f"{winter_avg:,.0f}")
col3.metric("Selisih Panas vs Dingin", f"{season_gap:,.0f}")

fig, ax = plt.subplots(figsize=(8, 4.5))
sns.barplot(
    data=season_avg,
    x="season_label",
    y="avg_cnt",
    order=["Musim Semi", "Musim Panas", "Musim Gugur", "Musim Dingin"],
    color="#4C78A8",
    ax=ax,
)
ax.set_title("Rata-rata Peminjaman Harian per Musim (2012)")
ax.set_xlabel("Musim")
ax.set_ylabel("Rata-rata Peminjaman (cnt)")
st.pyplot(fig)

st.markdown(
    "**Penjelasan:** Musim dengan rata-rata terendah adalah "
    f"**{lowest_season.iloc[0]['season_label']}** (~{lowest_season.iloc[0]['avg_cnt']:.0f}). "
    "Musim ini menjadi kandidat prioritas program peningkatan usage."
)

st.subheader("Pertanyaan 2: Pola per jam Q3 2011")
hour_q3 = hour_filtered[(hour_filtered["yr"] == 0) & (hour_filtered["mnth"].between(7, 9))].copy()
hour_q3["day_type"] = hour_q3["workingday"].map({1: "Hari Kerja", 0: "Akhir Pekan/Libur"})

total_by_day = hour_q3.groupby("day_type", as_index=False)["cnt"].sum()
working_total = total_by_day.loc[total_by_day["day_type"] == "Hari Kerja", "cnt"].sum()
weekend_total = total_by_day.loc[total_by_day["day_type"] == "Akhir Pekan/Libur", "cnt"].sum()
percent_diff = ((working_total - weekend_total) / weekend_total) * 100 if weekend_total else 0

hourly_pattern = (
    hour_q3.groupby(["day_type", "hr"], as_index=False)["cnt"]
    .mean()
    .rename(columns={"cnt": "avg_cnt"})
)
peak_hours = (
    hourly_pattern.sort_values(["day_type", "avg_cnt"], ascending=[True, False])
    .groupby("day_type", as_index=False)
    .head(3)
)

col1, col2, col3 = st.columns(3)
col1.metric("Total Hari Kerja", f"{working_total:,.0f}")
col2.metric("Total Akhir Pekan/Libur", f"{weekend_total:,.0f}")
col3.metric("Selisih (%)", f"{percent_diff:.1f}%")

fig, ax = plt.subplots(figsize=(9, 4.5))
sns.lineplot(data=hourly_pattern, x="hr", y="avg_cnt", hue="day_type", marker="o", ax=ax)
ax.set_title("Rata-rata Peminjaman per Jam di Q3 2011")
ax.set_xlabel("Jam")
ax.set_ylabel("Rata-rata Peminjaman (cnt)")
ax.set_xticks(range(0, 24, 2))
ax.legend(title="Tipe Hari")
st.pyplot(fig)

st.markdown("**Jam puncak (top 3) per tipe hari:**")
st.dataframe(peak_hours, use_container_width=True)

st.markdown(
    "**Penjelasan:** Jam puncak hari kerja biasanya pada rentang "
    "pagi dan sore, sedangkan akhir pekan cenderung naik pada siang hari. "
    "Informasi ini membantu alokasi armada pada jam-jam kritis."
)
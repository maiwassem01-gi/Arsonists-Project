import os
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui import apply_theme, style_fig, COLORS
from ui.components import header, kpi_card, panel_title, recent_table, alert_box

st.set_page_config(
    page_title="FIREWATCH INTELLIGENCE",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# ==============================================================================
# 1. CACHED DATA LOADERS  (unchanged)
# ==============================================================================
PROVINCE_RENAME = {
    "Orense": "Ourense",
    "Lérida": "Lleida",
    "Gerona": "Girona",
    "La Coruña": "A Coruña",
}


def resolve_path(filename: str) -> str:
    if os.path.exists(filename):
        return filename
    return os.path.join("data", filename)


@st.cache_data
def load_daily() -> pd.DataFrame:
    df = pd.read_parquet(resolve_path("harmonized_daily_by_province.parquet"))
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_monthly() -> pd.DataFrame:
    return pd.read_parquet(resolve_path("harmonized_monthly_by_province.parquet"))


@st.cache_data
def load_provinces() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(resolve_path("spain_provinces.gpkg")).to_crs("EPSG:4326")
    gdf = gdf[["name", "geometry"]].rename(columns={"name": "province"})
    gdf["province"] = gdf["province"].replace(PROVINCE_RENAME)
    return gdf


@st.cache_data
def load_hotspots() -> pd.DataFrame:
    df = pd.read_parquet(resolve_path("clean_hotspots.parquet"))
    df["date"] = pd.to_datetime(df["date"])
    return df


daily_df = load_daily()
monthly_df = load_monthly()
provinces_gdf = load_provinces()

# ==============================================================================
# 2. HEADER
# ==============================================================================
header("ARCHIVE DATA · NOV 2000 – DEC 2025")

# ==============================================================================
# 3. SIDEBAR FILTERS  (same widgets and logic as before)
# ==============================================================================
st.sidebar.header("Filter Controls")
all_provinces = ["All Spain"] + sorted(daily_df["province"].unique().tolist())

if "selected_province" not in st.session_state:
    st.session_state.selected_province = "All Spain"

selected_prov = st.sidebar.selectbox(
    "Province (or click on map)",
    options=all_provinces,
    index=all_provinces.index(st.session_state.selected_province),
)
if selected_prov != st.session_state.selected_province:
    st.session_state.selected_province = selected_prov

min_date = daily_df["date"].min().date()
max_date = daily_df["date"].max().date()
date_range = st.sidebar.date_input(
    "Date Range (ends Dec 2025)",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
else:
    start_dt, end_dt = pd.to_datetime(min_date), pd.to_datetime(max_date)

show_raw_sensors = st.sidebar.checkbox("Show raw Terra, Aqua & VIIRS lines", value=True)
exclude_artifacts = st.sidebar.checkbox(
    "Exclude La Palma volcano (2021–22) & static industrial heat sources", value=True
)

# ==============================================================================
# 4. FILTERED DATA + KPIs  (same calculations)
# ==============================================================================
d_period = daily_df[(daily_df["date"] >= start_dt) & (daily_df["date"] <= end_dt)]
if selected_prov == "All Spain":
    d_filt = d_period
    m_filt = monthly_df
else:
    d_filt = d_period[d_period["province"] == selected_prov]
    m_filt = monthly_df[monthly_df["province"] == selected_prov]

total_sq_days = d_filt["count_harmonized"].sum()
active_days = d_filt.groupby("date")["count_harmonized"].sum().gt(0).sum()
peak_row = d_filt.groupby("date")["count_harmonized"].sum()
peak_val = peak_row.max() if len(peak_row) > 0 else 0
peak_day = peak_row.idxmax().strftime("%Y-%m-%d") if peak_val > 0 else "—"

hs_df = load_hotspots()
hs_filt = hs_df[(hs_df["date"] >= start_dt) & (hs_df["date"] <= end_dt)]
if selected_prov != "All Spain":
    hs_filt = hs_filt[hs_filt["province"] == selected_prov]
if exclude_artifacts:
    hs_filt = hs_filt[~hs_filt["volcanic"] & ~hs_filt["static_source"]]

monthly_spark = (
    d_filt.set_index("date")["count_harmonized"].resample("ME").sum().values
    if len(d_filt) else []
)
hs_spark = (
    hs_filt.set_index("date").resample("ME").size().values if len(hs_filt) else []
)

# ==============================================================================
# 5. CHART BUILDERS  (same figures, restyled)
# ==============================================================================
def build_ts_fig(height):
    sensor_cols = ["count_harmonized", "count_terra_raw", "count_aqua_raw", "count_viirs_raw"]
    ts = d_filt.set_index("date")[sensor_cols].resample("ME").sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts["date"], y=ts["count_harmonized"], name="Harmonized",
                             line=dict(color=COLORS["orange"], width=3)))
    if show_raw_sensors:
        for col, label, color in [
            ("count_terra_raw", "Raw Terra (MODIS)", "#38bdf8"),
            ("count_aqua_raw", "Raw Aqua (MODIS)", "#22d3ee"),
            ("count_viirs_raw", "Raw VIIRS (S-NPP FRP≥6)", "#f5a524"),
        ]:
            fig.add_trace(go.Scatter(x=ts["date"], y=ts[col], name=label,
                                     line=dict(color=color, width=1.4, dash="dot")))
    fig.update_layout(yaxis_title="Monthly Burning Square-Days")
    return style_fig(fig, height)


def build_comp_fig(comp_year, height):
    by_ym = m_filt.groupby(["year", "month"], as_index=False)["count_harmonized"].sum()
    baseline = (
        by_ym[by_ym["year"] != comp_year]
        .groupby("month", as_index=False)["count_harmonized"]
        .agg(usual_mean="mean", usual_std="std")
    )
    target = by_ym[by_ym["year"] == comp_year]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=target["month"], y=target["count_harmonized"],
                         name=f"{comp_year}", marker_color=COLORS["cyan"]))
    fig.add_trace(go.Scatter(x=baseline["month"], y=baseline["usual_mean"],
                             name="Historical Mean ('The Usual')",
                             line=dict(color=COLORS["orange"], width=2.5, dash="dash")))
    fig.update_layout(xaxis=dict(dtick=1, title="Month"), yaxis_title="Burning Square-Days")
    yr_total = target["count_harmonized"].sum()
    usual_total = baseline["usual_mean"].sum()
    pct = ((yr_total - usual_total) / usual_total * 100) if usual_total > 0 else 0.0
    return style_fig(fig, height), yr_total, usual_total, pct


def build_points_map(height, show_legend=True):
    if len(hs_filt) > 6000:
        plot_pts = hs_filt.sample(6000, random_state=42)
        sampled = True
    else:
        plot_pts, sampled = hs_filt, False
    if len(plot_pts) == 0:
        return None, sampled
    fig = px.scatter_map(
        plot_pts, lat="lat", lon="lon", color="sensor",
        hover_data=["date", "province", "frp", "satellite"],
        zoom=4.5 if selected_prov == "All Spain" else 7.0,
        height=height, map_style="carto-darkmatter",
        color_discrete_sequence=[COLORS["red"], COLORS["orange"], COLORS["amber"], COLORS["cyan"]],
    )
    fig.update_traces(marker=dict(size=6, opacity=0.8))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        legend=dict(bgcolor="rgba(13,20,34,.85)", bordercolor=COLORS["border"], borderwidth=1,
                    x=0.99, xanchor="right", y=0.02, yanchor="bottom"),
    )
    return fig, sampled


# ==============================================================================
# 6. TOP NAVIGATION
# ==============================================================================
tab_overview, tab_activity, tab_sat, tab_reports = st.tabs(
    ["Overview", "Fire Activity", "Satellite Data", "Reports & About"]
)

# ------------------------------------------------------------------ OVERVIEW --
with tab_overview:
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Total Satellite Detections", f"{len(hs_filt):,}", COLORS["cyan"],
                 "individual detections", hs_spark)
    with k2:
        kpi_card("Harmonized Square-Days", f"{total_sq_days:,.0f}", COLORS["orange"],
                 selected_prov, monthly_spark)
    with k3:
        kpi_card("Active Days With Fire", f"{active_days:,}", COLORS["amber"],
                 "days with ≥1 burning cell")
    with k4:
        kpi_card("Peak Single-Day Activity", f"{peak_val:,.0f}", COLORS["red"], f"on {peak_day}")

    col_map, col_side = st.columns([3.6, 1.4])
    with col_map:
        with st.container(border=True):
            panel_title(f"Satellite Detections · {selected_prov}")
            fig_pts, sampled = build_points_map(470)
            if fig_pts is not None:
                st.plotly_chart(fig_pts, use_container_width=True, key="ov_points")
                if sampled:
                    st.caption(f"Showing a random sample of 6,000 of {len(hs_filt):,} detections.")
            else:
                st.info("No individual hotspots found for the selected filter.")
    with col_side:
        with st.container(border=True):
            panel_title("Latest Detections in Selection")
            if len(hs_filt):
                recent_table(hs_filt.sort_values("date", ascending=False).head(14)[["date", "lat", "lon", "sensor"]])
            else:
                st.caption("No detections.")
            if peak_val > 0:
                alert_box("PEAK ACTIVITY", f"{peak_val:,.0f} burning square-days on {peak_day} in {selected_prov}.")

    b1, b2 = st.columns(2)
    with b1:
        with st.container(border=True):
            panel_title("Harmonized Series vs. Raw Sensors")
            st.plotly_chart(build_ts_fig(300), use_container_width=True, key="ov_ts")
    with b2:
        with st.container(border=True):
            panel_title("This Year vs. The Usual (Historical Average)")
            avail_years = sorted(m_filt["year"].unique().tolist())
            comp_year = st.selectbox("Compare Year", avail_years, index=len(avail_years) - 1, key="comp_yr")
            fig_comp, yr_total, usual_total, pct_diff = build_comp_fig(comp_year, 250)
            st.caption(f"**{comp_year} total:** {yr_total:,.0f} square-days vs. "
                       f"**historical yearly mean:** {usual_total:,.0f} ({pct_diff:+.1f}%)")
            st.plotly_chart(fig_comp, use_container_width=True, key="ov_comp")

# -------------------------------------------------------------- FIRE ACTIVITY --
with tab_activity:
    col_cmap, col_heat = st.columns([1.05, 1.25])
    with col_cmap:
        with st.container(border=True):
            panel_title("Province Activity Map (Click to Select)")
            prov_totals = d_period.groupby("province", as_index=False)["count_harmonized"].sum()
            map_gdf = provinces_gdf.merge(prov_totals, on="province", how="left").fillna({"count_harmonized": 0})
            fig_map = px.choropleth(
                map_gdf, geojson=map_gdf.__geo_interface__, locations="province",
                featureidkey="properties.province", color="count_harmonized",
                color_continuous_scale="YlOrRd", labels={"count_harmonized": "Square-Days"},
            )
            fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
            style_fig(fig_map, 420, legend_top=False)
            map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", key="prov_map")
            if map_event and map_event.selection and map_event.selection.get("points"):
                clicked_prov = map_event.selection["points"][0].get("location")
                if (clicked_prov and clicked_prov in all_provinces
                        and clicked_prov != st.session_state.selected_province):
                    st.session_state.selected_province = clicked_prov
                    st.rerun()

    with col_heat:
        with st.container(border=True):
            panel_title("Calendar Heatmap")
            hm_mode = st.radio(
                "Granularity",
                ["Monthly Overview (Years × Months)", "Daily Calendar (Single Year)"],
                horizontal=True, label_visibility="collapsed",
            )
            if hm_mode == "Monthly Overview (Years × Months)":
                piv = m_filt.pivot_table(index="year", columns="month", values="count_harmonized",
                                         aggfunc="sum", fill_value=0)
                month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                piv.columns = [month_names[m - 1] for m in piv.columns]
                fig_heat = px.imshow(piv, color_continuous_scale="YlOrRd", aspect="auto",
                                     labels=dict(x="Month", y="Year", color="Square-Days"))
                fig_heat.update_yaxes(dtick=2)
                st.plotly_chart(style_fig(fig_heat, 400, False), use_container_width=True)
            else:
                avail_years_h = sorted(m_filt["year"].unique().tolist())
                cal_year = st.selectbox("Select Year", avail_years_h,
                                        index=len(avail_years_h) - 1, key="cal_yr")
                yr_daily = (
                    daily_df[
                        (daily_df["date"].dt.year == cal_year)
                        & (True if selected_prov == "All Spain" else daily_df["province"] == selected_prov)
                    ]
                    .groupby("date", as_index=False)["count_harmonized"].sum()
                )
                yr_daily["month"] = yr_daily["date"].dt.month
                yr_daily["day"] = yr_daily["date"].dt.day
                piv_d = yr_daily.pivot_table(index="month", columns="day", values="count_harmonized",
                                             aggfunc="sum", fill_value=0)
                fig_d = px.imshow(piv_d, color_continuous_scale="YlOrRd", aspect="auto",
                                  labels=dict(x="Day of Month", y="Month", color="Square-Days"))
                fig_d.update_yaxes(dtick=1)
                st.plotly_chart(style_fig(fig_d, 360, False), use_container_width=True)

    with st.container(border=True):
        panel_title("Harmonized Series vs. Raw Sensors")
        st.plotly_chart(build_ts_fig(340), use_container_width=True, key="fa_ts")

# ------------------------------------------------------------- SATELLITE DATA --
with tab_sat:
    with st.container(border=True):
        panel_title("Hotspot Detections Map")
        st.markdown(
            '<div class="fw-legend">'
            f'<span><i class="fw-dot" style="background:{COLORS["red"]}"></i>Detections by sensor (see legend on map)</span>'
            '<span>Hover a point for date, province, FRP and satellite</span></div>',
            unsafe_allow_html=True,
        )
        fig_big, sampled = build_points_map(620)
        if fig_big is not None:
            if sampled:
                st.caption(f"Showing a random sample of 6,000 out of {len(hs_filt):,} matching detections "
                           f"(CSV downloads all {len(hs_filt):,}).")
            st.plotly_chart(fig_big, use_container_width=True, key="sat_points")
        else:
            st.info("No individual hotspots found for the selected filter.")

    d1, d2 = st.columns(2)
    daily_export = (
        d_filt.groupby(["date"] + ([] if selected_prov == "All Spain" else ["province"]), as_index=False)[
            ["count_harmonized", "count_terra_raw", "count_aqua_raw", "count_viirs_raw"]
        ].sum()
    )
    with d1:
        with st.container(border=True):
            panel_title("1. Harmonized Daily Counts (Selected Region & Dates)")
            st.download_button(
                label=f"⬇️ Download Daily Harmonized CSV ({len(daily_export):,} rows)",
                data=daily_export.to_csv(index=False).encode("utf-8"),
                file_name=f"harmonized_daily_{selected_prov.replace(' ', '_')}.csv",
                mime="text/csv",
            )
    with d2:
        with st.container(border=True):
            panel_title("2. Individual Satellite Hotspot Detections")
            st.download_button(
                label=f"⬇️ Download Matching Hotspot Detections CSV ({len(hs_filt):,} detections)",
                data=hs_filt.to_csv(index=False).encode("utf-8"),
                file_name=f"clean_hotspots_{selected_prov.replace(' ', '_')}.csv",
                mime="text/csv",
            )
    st.warning(
        "ℹ️ **Why counts differ from the calendar above:** The charts and daily CSV count "
        "**harmonized burning square-days** (unique ~1 km cells active per day after FRP filtering and sensor scaling). "
        "The hotspot CSV contains **raw individual satellite detections** (multiple 375 m VIIRS points can fall "
        "inside one 1 km square on the same day)."
    )

# ------------------------------------------------------------ REPORTS & ABOUT --
with tab_reports:
    st.info(
        "📅 **Dataset Coverage:** November 2000 – **December 2025** (data ends in December 2025) "
        "across Peninsular Spain, the Balearic Islands, and the Canary Islands."
    )
    with st.container(border=True):
        st.markdown(
            """
            ### About the Data & Harmonization Method
            #### 1. Data Sources & Temporal Coverage
            - **Time Span:** **November 1, 2000 – December 31, 2025** (dataset ends in December 2025).
            - **Geographic Scope:** All 52 provinces of Spain, including the **Balearic Islands** and **Canary Islands**.
            - **Satellites & Instruments:** NASA FIRMS **MODIS Collection 6.1** (Terra & Aqua, 1 km resolution) and **VIIRS** (Suomi-NPP & NOAA-20, 375 m resolution).

            #### 2. Quality Filtering & Artifact Removal
            - **Vegetation Fire & Confidence Filter:** Retained presumed vegetation fires (`type == 0`) with MODIS confidence `≥ 30` and VIIRS confidence `nominal` or `high`.
            - **Volcanic Eruption Exclusion:** Flagged **30,263 detections** from the 2021–2022 Cumbre Vieja volcanic eruption in La Palma (Santa Cruz de Tenerife) so geological lava activity does not distort wildfire statistics.
            - **Static Heat Source Removal:** Flagged **3,908 detections** occurring in ~1 km grid cells active across `≥ 15` distinct years (persistent industrial plants, refineries, and urban heat anomalies).

            #### 3. Spatial & Cross-Sensor Harmonization
            - **1 km Grid Deduplication (`Burning Square-Days`):** Detections are snapped to a uniform ~1 km latitude/longitude grid (`0.01°` cells) and deduplicated per satellite, province, and day so higher-resolution 375 m VIIRS oversampling does not inflate counts relative to 1 km MODIS.
            - **FRP Threshold & Overlap Calibration:** S-NPP VIIRS detections are filtered at `FRP ≥ 6 MW` to align detection sensitivity with MODIS Aqua, then scaled using overlap-period ratios across three seamless eras:
              - **Nov 2000 – Jul 2002:** Scaled MODIS Terra (`Terra_scaled`)
              - **Aug 2002 – Dec 2011:** MODIS Aqua baseline (`Aqua`)
              - **Jan 2012 – Dec 2025:** Scaled VIIRS S-NPP (`VIIRS_scaled`)
            """
        )
    summary_path = resolve_path("data_quality_summary.csv")
    if os.path.exists(summary_path):
        with st.container(border=True):
            panel_title("Data Cleaning & Filtering Pipeline Summary")
            st.dataframe(pd.read_csv(summary_path), use_container_width=True, hide_index=True)
    plot_path = resolve_path("harmonized_yearly_plot.png")
    if os.path.exists(plot_path):
        with st.container(border=True):
            panel_title("Harmonized Spain Fire Activity (2000–2025)")
            st.image(plot_path, use_container_width=True)

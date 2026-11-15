import os
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="FIREWATCH INTELLIGENCE | Spain MODIS & VIIRS",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 0. ENTERPRISE DARK GEOSPATIAL THEME (CUSTOM CSS)
# ==============================================================================
st.markdown(
    """
    <style>
    /* Main canvas & typography */
    .stApp {
        background-color: #0b0f17;
        color: #e2e8f0;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(11, 15, 23, 0.85);
        border-bottom: 1px solid #1e293b;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.5rem;
        max-width: 98%;
    }

    /* Top Command Bar */
    .fw-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(90deg, #0f172a 0%, #131c2e 100%);
        border: 1px solid #1e293b;
        border-left: 4px solid #00e5ff;
        border-radius: 6px;
        padding: 12px 20px;
        margin-bottom: 14px;
    }
    .fw-brand {
        display: flex;
        align-items: baseline;
        gap: 14px;
        flex-wrap: wrap;
    }
    .fw-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        color: #00e5ff;
        margin: 0;
    }
    .fw-subtitle {
        font-size: 0.88rem;
        color: #94a3b8;
        font-weight: 500;
    }
    .fw-status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background-color: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        padding: 5px 12px;
        border-radius: 999px;
    }
    .fw-dot {
        height: 8px;
        width: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #10b981;
    }

    /* KPI Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #1e293b;
        border-top: 2px solid #00e5ff;
        border-radius: 6px;
        padding: 12px 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-size: 1.55rem !important;
        font-weight: 800 !important;
    }

    /* Panel Headers & Cards */
    .fw-panel-header {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #00e5ff;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    .fw-alert-box {
        background: linear-gradient(180deg, rgba(239, 68, 68, 0.12) 0%, rgba(127, 29, 29, 0.18) 100%);
        border: 1px solid rgba(239, 68, 68, 0.45);
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        padding: 12px 14px;
        margin-top: 10px;
        font-size: 0.82rem;
        color: #fecaca;
    }
    .fw-alert-title {
        color: #f87171;
        font-weight: 800;
        font-size: 0.76rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .fw-region-pill {
        display: inline-block;
        background-color: #1e293b;
        border: 1px solid #334155;
        color: #e2e8f0;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
    }

    /* Tabs styling */
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00e5ff !important;
        border-bottom-color: #00e5ff !important;
    }

    /* Download buttons */
    div[data-testid="stDownloadButton"] > button {
        width: 100%;
        background-color: #162033;
        color: #e2e8f0;
        border: 1px solid #334155;
        font-size: 0.8rem;
        font-weight: 600;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        border-color: #00e5ff;
        color: #00e5ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 1. CACHED DATA LOADERS
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
hs_df = load_hotspots()

if "selected_province" not in st.session_state:
    st.session_state.selected_province = "All Spain"

# ==============================================================================
# 2. TOP COMMAND BAR
# ==============================================================================
st.markdown(
    """
    <div class="fw-topbar">
        <div class="fw-brand">
            <span class="fw-title">🔥 FIREWATCH INTELLIGENCE</span>
            <span class="fw-subtitle">NASA MODIS &amp; VIIRS Satellite Monitoring Platform (ESP • 2000–2025)</span>
        </div>
        <div class="fw-status">
            <span class="fw-dot"></span>
            HARMONIZED ARCHIVE • COVERAGE: NOV 2000 – DEC 2025
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_overview, tab_temporal, tab_methodology = st.tabs(
    [
        "🛰️ Geospatial Command Center",
        "📅 Temporal Heatmaps & Annual Validation",
        "ℹ️ Satellite Data & Harmonization Methodology",
    ]
)

# ==============================================================================
# TAB 1: GEOSPATIAL COMMAND CENTER
# ==============================================================================
with tab_overview:
    min_date = daily_df["date"].min().date()
    max_date = daily_df["date"].max().date()
    all_provinces = ["All Spain"] + sorted(daily_df["province"].unique().tolist())

    # --- 3-Column Enterprise Layout: Controls (Left) | Map (Center) | Intelligence Stream (Right) ---
    col_ctrl, col_map, col_intel = st.columns([0.9, 2.25, 1.05], gap="medium")

    with col_ctrl:
        st.markdown('<div class="fw-panel-header">Mission Parameters</div>', unsafe_allow_html=True)

        d1, d2 = st.columns(2)
        start_date = d1.date_input(
            "Start Date", value=min_date, min_value=min_date, max_value=max_date
        )
        end_date = d2.date_input(
            "End Date", value=max_date, min_value=min_date, max_value=max_date
        )
        start_dt, end_dt = pd.to_datetime(start_date), pd.to_datetime(end_date)
        if start_dt > end_dt:
            start_dt, end_dt = end_dt, start_dt

        selected_prov = st.selectbox(
            "Province / Region Selector",
            options=all_provinces,
            index=all_provinces.index(st.session_state.selected_province),
        )
        if selected_prov != st.session_state.selected_province:
            st.session_state.selected_province = selected_prov

        st.markdown('<div class="fw-panel-header" style="margin-top:12px;">Sensor Inputs</div>', unsafe_allow_html=True)
        inc_terra = st.checkbox("MODIS Terra (1 km)", value=True)
        inc_aqua = st.checkbox("MODIS Aqua (1 km)", value=True)
        inc_viirs = st.checkbox("VIIRS S-NPP / N20 (375 m)", value=True)
        exclude_artifacts = st.checkbox(
            "Exclude La Palma volcano & static heat", value=True
        )

        # Apply filters to daily, monthly, and hotspot datasets
        d_period = daily_df[(daily_df["date"] >= start_dt) & (daily_df["date"] <= end_dt)]
        if selected_prov == "All Spain":
            d_filt = d_period
            m_filt = monthly_df
        else:
            d_filt = d_period[d_period["province"] == selected_prov]
            m_filt = monthly_df[monthly_df["province"] == selected_prov]

        hs_filt = hs_df[(hs_df["date"] >= start_dt) & (hs_df["date"] <= end_dt)]
        if selected_prov != "All Spain":
            hs_filt = hs_filt[hs_filt["province"] == selected_prov]
        if exclude_artifacts:
            hs_filt = hs_filt[~hs_filt["volcanic"] & ~hs_filt["static_source"]]

        # Sensor filtering for hotspots
        sensor_str = hs_filt["sensor"].astype(str).str.upper()
        sat_str = hs_filt["satellite"].astype(str).str.upper() if "satellite" in hs_filt.columns else sensor_str
        keep_mask = pd.Series(False, index=hs_filt.index)
        if inc_terra:
            keep_mask |= sat_str.str.contains("TERRA") | (sensor_str.str.contains("MODIS") & ~sat_str.str.contains("AQUA"))
        if inc_aqua:
            keep_mask |= sat_str.str.contains("AQUA") | (sensor_str.str.contains("MODIS") & ~sat_str.str.contains("TERRA"))
        if inc_viirs:
            keep_mask |= sensor_str.str.contains("VIIRS")
        hs_filt = hs_filt[keep_mask]

        st.markdown('<div class="fw-panel-header" style="margin-top:12px;">Data Exports</div>', unsafe_allow_html=True)
        daily_export = (
            d_filt.groupby(
                ["date"] + ([] if selected_prov == "All Spain" else ["province"]),
                as_index=False,
            )[
                [
                    "count_harmonized",
                    "count_terra_raw",
                    "count_aqua_raw",
                    "count_viirs_raw",
                ]
            ]
            .sum()
        )
        st.download_button(
            label=f"⬇️ Daily Harmonized CSV ({len(daily_export):,})",
            data=daily_export.to_csv(index=False).encode("utf-8"),
            file_name=f"harmonized_daily_{selected_prov.replace(' ', '_')}.csv",
            mime="text/csv",
        )
        st.download_button(
            label=f"⬇️ Filtered Hotspots CSV ({len(hs_filt):,})",
            data=hs_filt.to_csv(index=False).encode("utf-8"),
            file_name=f"clean_hotspots_{selected_prov.replace(' ', '_')}.csv",
            mime="text/csv",
        )

    # --- Top KPI Strip (rendered above map & intelligence feed via container) ---
    total_sq_days = d_filt["count_harmonized"].sum()
    active_days = d_filt.groupby("date")["count_harmonized"].sum().gt(0).sum()
    peak_row = d_filt.groupby("date")["count_harmonized"].sum()
    peak_val = peak_row.max() if len(peak_row) > 0 else 0
    peak_day = peak_row.idxmax().strftime("%Y-%m-%d") if peak_val > 0 else "—"

    with col_map:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Satellite Detections", f"{len(hs_filt):,}")
        k2.metric("Harmonized Sq-Days", f"{total_sq_days:,.0f}")
        k3.metric("Active Fire Days", f"{active_days:,}")
        k4.metric("Peak Single-Day", f"{peak_val:,.0f}", delta=peak_day, delta_color="off")

        m_hdr1, m_hdr2 = st.columns([1.2, 1.3])
        with m_hdr1:
            st.markdown(
                f'<div style="margin-top:6px;"><span class="fw-region-pill">📍 SELECTED REGION: <b>{selected_prov.upper()}</b></span></div>',
                unsafe_allow_html=True,
            )
        with m_hdr2:
            map_view = st.radio(
                "Map Layer",
                ["🛰️ Dark Satellite Hotspots", "🗺️ Province Intensity (Click)"],
                horizontal=True,
                label_visibility="collapsed",
            )

        if map_view == "🛰️ Dark Satellite Hotspots":
            if len(hs_filt) > 7000:
                plot_pts = hs_filt.sample(7000, random_state=42)
                sample_note = f"Displaying 7,000 sampled detections of {len(hs_filt):,} matching observations (CSV exports all)."
            else:
                plot_pts = hs_filt
                sample_note = f"Displaying all {len(hs_filt):,} matching satellite observations."

            if len(plot_pts) > 0:
                hover_cols = [c for c in ["date", "province", "frp", "satellite"] if c in plot_pts.columns]
                fig_pts = px.scatter_map(
                    plot_pts,
                    lat="lat",
                    lon="lon",
                    color="sensor",
                    color_discrete_map={
                        "VIIRS": "#ff9f0a",
                        "MODIS": "#ff3b30",
                    },
                    hover_data=hover_cols,
                    zoom=4.6 if selected_prov == "All Spain" else 7.2,
                    height=455,
                    map_style="carto-darkmatter",
                )
                fig_pts.update_traces(marker=dict(size=5, opacity=0.82))
                fig_pts.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor="#0b0f17",
                    legend=dict(
                        title="",
                        orientation="h",
                        y=0.02,
                        x=0.02,
                        bgcolor="rgba(15, 23, 42, 0.85)",
                        bordercolor="#334155",
                        borderwidth=1,
                        font=dict(color="#f8fafc", size=11),
                    ),
                )
                st.plotly_chart(fig_pts, use_container_width=True)
                st.caption(sample_note)
            else:
                st.info("No satellite detections match the current sensor/region filters.")
        else:
            prov_totals = (
                d_period.groupby("province", as_index=False)["count_harmonized"].sum()
            )
            map_gdf = provinces_gdf.merge(prov_totals, on="province", how="left").fillna(
                {"count_harmonized": 0}
            )
            fig_map = px.choropleth(
                map_gdf,
                geojson=map_gdf.__geo_interface__,
                locations="province",
                featureidkey="properties.province",
                color="count_harmonized",
                color_continuous_scale=["#111827", "#7c2d12", "#ea580c", "#facc15"],
                projection="mercator",
                labels={"count_harmonized": "Square-Days"},
            )
            fig_map.update_geos(
                fitbounds="locations",
                visible=False,
                bgcolor="rgba(0,0,0,0)",
            )
            fig_map.update_traces(marker_line_color="#334155", marker_line_width=0.6)
            fig_map.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=455,
                paper_bgcolor="#0b0f17",
                font=dict(color="#e2e8f0"),
                coloraxis_colorbar=dict(
                    orientation="h",
                    y=0.02,
                    x=0.5,
                    xanchor="center",
                    len=0.8,
                    thickness=10,
                    title="Sq-Days",
                ),
            )
            map_event = st.plotly_chart(
                fig_map, use_container_width=True, on_select="rerun", key="prov_map"
            )
            st.caption("Click any province polygon on the map to filter the entire dashboard.")
            if map_event and map_event.selection and map_event.selection.get("points"):
                clicked_prov = map_event.selection["points"][0].get("location")
                if (
                    clicked_prov
                    and clicked_prov in all_provinces
                    and clicked_prov != st.session_state.selected_province
                ):
                    st.session_state.selected_province = clicked_prov
                    st.rerun()

    # --- Right Column: Intelligence Stream & Critical Summary ---
    with col_intel:
        st.markdown('<div class="fw-panel-header">Latest Detections Stream</div>', unsafe_allow_html=True)
        if len(hs_filt) > 0:
            stream_cols = [c for c in ["date", "province", "lat", "lon", "sensor", "frp"] if c in hs_filt.columns]
            recent_df = hs_filt.sort_values("date", ascending=False)[stream_cols].head(12).copy()
            recent_df["date"] = recent_df["date"].dt.strftime("%Y-%m-%d")
            recent_df["lat"] = recent_df["lat"].round(3)
            recent_df["lon"] = recent_df["lon"].round(3)
            if "frp" in recent_df.columns:
                recent_df["frp"] = recent_df["frp"].round(1)
            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True,
                height=315,
            )
        else:
            st.caption("No detections in stream for selected filters.")

        # Dynamic Critical Alert & Intelligence Summary
        top_prov_series = d_period.groupby("province")["count_harmonized"].sum()
        top_prov_name = top_prov_series.idxmax() if len(top_prov_series) > 0 else "N/A"
        top_prov_val = top_prov_series.max() if len(top_prov_series) > 0 else 0
        max_frp = hs_filt["frp"].max() if ("frp" in hs_filt.columns and len(hs_filt) > 0) else 0.0

        st.markdown(
            f"""
            <div class="fw-alert-box">
                <div class="fw-alert-title">⚠️ Intelligence &amp; Anomaly Brief</div>
                <div>• <b>Highest Activity Province:</b> {top_prov_name} ({top_prov_val:,.0f} sq-days)</div>
                <div>• <b>Peak FRP Intensity:</b> {max_frp:,.1f} MW recorded in selection</div>
                <div>• <b>1 km Grid Harmonization:</b> Deduplicated 375 m VIIRS &amp; 1 km MODIS cells; S-NPP scaled at FRP ≥ 6 MW.</div>
                <div>• <b>Artifact Filter:</b> {"Active (30,263 La Palma volcanic & 3,908 static industrial detections excluded)." if exclude_artifacts else "Disabled (showing volcanic & industrial heat sources)."}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ==========================================================================
    # BOTTOM ANALYTICS ROW (3 ENTERPRISE CHARTS)
    # ==========================================================================
    st.markdown("<hr style='border-color:#1e293b; margin: 14px 0;'>", unsafe_allow_html=True)
    b_col1, b_col2, b_col3 = st.columns([1.25, 1.15, 0.9], gap="medium")

    with b_col1:
        st.markdown('<div class="fw-panel-header">Harmonized Series vs. Raw Sensors</div>', unsafe_allow_html=True)
        sensor_cols = [
            "count_harmonized",
            "count_terra_raw",
            "count_aqua_raw",
            "count_viirs_raw",
        ]
        ts = d_filt.set_index("date")[sensor_cols].resample("ME").sum().reset_index()

        fig_ts = go.Figure()
        fig_ts.add_trace(
            go.Scatter(
                x=ts["date"],
                y=ts["count_harmonized"],
                name="Harmonized",
                line=dict(color="#00e5ff", width=2.5),
            )
        )
        if inc_terra:
            fig_ts.add_trace(
                go.Scatter(
                    x=ts["date"],
                    y=ts["count_terra_raw"],
                    name="Terra (Raw)",
                    line=dict(color="#60a5fa", width=1.2, dash="dot"),
                )
            )
        if inc_aqua:
            fig_ts.add_trace(
                go.Scatter(
                    x=ts["date"],
                    y=ts["count_aqua_raw"],
                    name="Aqua (Raw)",
                    line=dict(color="#34d399", width=1.2, dash="dot"),
                )
            )
        if inc_viirs:
            fig_ts.add_trace(
                go.Scatter(
                    x=ts["date"],
                    y=ts["count_viirs_raw"],
                    name="VIIRS (FRP≥6)",
                    line=dict(color="#ff9f0a", width=1.3, dash="dot"),
                )
            )
        fig_ts.update_layout(
            height=290,
            margin=dict(l=0, r=0, t=24, b=0),
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#cbd5e1", size=11),
            xaxis=dict(gridcolor="#1e293b", showgrid=True),
            yaxis=dict(title="Monthly Sq-Days", gridcolor="#1e293b", showgrid=True),
            legend=dict(orientation="h", y=1.14, x=0, font=dict(size=10)),
        )
        st.plotly_chart(fig_ts, use_container_width=True)

    with b_col2:
        st.markdown('<div class="fw-panel-header">Selected Year vs. Historical Mean ("The Usual")</div>', unsafe_allow_html=True)
        avail_years = sorted(m_filt["year"].unique().tolist())
        y_c1, y_c2 = st.columns([0.9, 1.6])
        comp_year = y_c1.selectbox(
            "Year", avail_years, index=len(avail_years) - 1, key="comp_yr", label_visibility="collapsed"
        )

        by_ym = m_filt.groupby(["year", "month"], as_index=False)["count_harmonized"].sum()
        baseline = (
            by_ym[by_ym["year"] != comp_year]
            .groupby("month", as_index=False)["count_harmonized"]
            .agg(usual_mean="mean")
        )
        target = by_ym[by_ym["year"] == comp_year]

        yr_total = target["count_harmonized"].sum()
        usual_total = baseline["usual_mean"].sum()
        pct_diff = ((yr_total - usual_total) / usual_total * 100) if usual_total > 0 else 0.0
        y_c2.markdown(
            f"<div style='padding-top:6px; font-size:0.8rem; color:#94a3b8;'>"
            f"<b style='color:#f8fafc;'>{comp_year}:</b> {yr_total:,.0f} vs. Mean {usual_total:,.0f} "
            f"(<span style='color:{'#f87171' if pct_diff > 0 else '#34d399'}; font-weight:700;'>{pct_diff:+.1f}%</span>)</div>",
            unsafe_allow_html=True,
        )

        fig_comp = go.Figure()
        fig_comp.add_trace(
            go.Bar(
                x=target["month"],
                y=target["count_harmonized"],
                name=f"{comp_year}",
                marker_color="#00e5ff",
            )
        )
        fig_comp.add_trace(
            go.Scatter(
                x=baseline["month"],
                y=baseline["usual_mean"],
                name="Historical Mean",
                line=dict(color="#ff9f0a", width=2.2, dash="dash"),
            )
        )
        fig_comp.update_layout(
            height=248,
            margin=dict(l=0, r=0, t=18, b=0),
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#cbd5e1", size=11),
            xaxis=dict(dtick=1, title="Month", gridcolor="#1e293b"),
            yaxis=dict(title="Sq-Days", gridcolor="#1e293b"),
            legend=dict(orientation="h", y=1.15, x=0, font=dict(size=10)),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with b_col3:
        st.markdown('<div class="fw-panel-header">Regional Ranking &amp; Quality Audit</div>', unsafe_allow_html=True)
        rank_mode = st.radio(
            "Table View",
            ["Top Provinces", "Quality Summary"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if rank_mode == "Top Provinces":
            top_provs = (
                d_period.groupby("province", as_index=False)["count_harmonized"]
                .sum()
                .sort_values("count_harmonized", ascending=False)
                .head(12)
                .rename(columns={"province": "Province", "count_harmonized": "Sq-Days"})
            )
            top_provs["Sq-Days"] = top_provs["Sq-Days"].round(0).astype(int)
            st.dataframe(top_provs, use_container_width=True, hide_index=True, height=250)
        else:
            summary_path = resolve_path("data_quality_summary.csv")
            if os.path.exists(summary_path):
                st.dataframe(
                    pd.read_csv(summary_path),
                    use_container_width=True,
                    hide_index=True,
                    height=250,
                )

# ==============================================================================
# TAB 2: TEMPORAL HEATMAPS & ANNUAL VALIDATION
# ==============================================================================
with tab_temporal:
    st.markdown('<div class="fw-panel-header">Multi-Decade Calendar Heatmap (2000–2025)</div>', unsafe_allow_html=True)
    hm_mode = st.radio(
        "Granularity",
        ["Monthly Overview (Years × Months)", "Daily Calendar (Single Year)"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if hm_mode == "Monthly Overview (Years × Months)":
        piv = m_filt.pivot_table(
            index="year",
            columns="month",
            values="count_harmonized",
            aggfunc="sum",
            fill_value=0,
        )
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        piv.columns = [month_names[m - 1] for m in piv.columns]

        fig_heat = px.imshow(
            piv,
            color_continuous_scale=["#111827", "#7c2d12", "#ea580c", "#facc15"],
            aspect="auto",
            labels=dict(x="Month", y="Year", color="Square-Days"),
        )
        fig_heat.update_yaxes(dtick=2)
        fig_heat.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=420,
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        avail_years = sorted(m_filt["year"].unique().tolist())
        cal_year = st.selectbox(
            "Select Year", avail_years, index=len(avail_years) - 1, key="cal_yr"
        )
        yr_daily = (
            daily_df[
                (daily_df["date"].dt.year == cal_year)
                & (
                    True
                    if selected_prov == "All Spain"
                    else daily_df["province"] == selected_prov
                )
            ]
            .groupby("date", as_index=False)["count_harmonized"]
            .sum()
        )
        yr_daily["month"] = yr_daily["date"].dt.month
        yr_daily["day"] = yr_daily["date"].dt.day
        piv_d = yr_daily.pivot_table(
            index="month",
            columns="day",
            values="count_harmonized",
            aggfunc="sum",
            fill_value=0,
        )
        fig_d_heat = px.imshow(
            piv_d,
            color_continuous_scale=["#111827", "#7c2d12", "#ea580c", "#facc15"],
            aspect="auto",
            labels=dict(x="Day of Month", y="Month", color="Square-Days"),
        )
        fig_d_heat.update_yaxes(dtick=1)
        fig_d_heat.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=380,
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_d_heat, use_container_width=True)

    plot_path = resolve_path("harmonized_yearly_plot.png")
    if os.path.exists(plot_path):
        st.markdown('<div class="fw-panel-header" style="margin-top:16px;">Harmonized Spain Fire Activity (2000–2025)</div>', unsafe_allow_html=True)
        st.image(plot_path, use_container_width=True)

# ==============================================================================
# TAB 3: SATELLITE DATA & HARMONIZATION METHODOLOGY
# ==============================================================================
with tab_methodology:
    st.markdown('<div class="fw-panel-header">Scientific Architecture &amp; Harmonization Pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        """
        ### 1. Data Sources & Temporal Coverage
        - **Time Span:** **November 1, 2000 – December 31, 2025** across all 52 provinces of Spain, including the **Balearic Islands** and **Canary Islands**.
        - **Satellites & Instruments:** NASA FIRMS **MODIS Collection 6.1** (Terra & Aqua, 1 km resolution) and **VIIRS** (Suomi-NPP & NOAA-20, 375 m resolution).

        ### 2. Quality Filtering & Artifact Removal
        - **Vegetation Fire & Confidence Filter:** Retained presumed vegetation fires (`type == 0`) with MODIS confidence `≥ 30` and VIIRS confidence `nominal` or `high`.
        - **Volcanic Eruption Exclusion:** Flagged **30,263 detections** from the 2021–2022 Cumbre Vieja volcanic eruption in La Palma (Santa Cruz de Tenerife) so geological lava activity does not distort wildfire statistics.
        - **Static Heat Source Removal:** Flagged **3,908 detections** occurring in ~1 km grid cells active across `≥ 15` distinct years (persistent industrial plants, refineries, and urban heat anomalies).

        ### 3. Spatial & Cross-Sensor Harmonization
        - **1 km Grid Deduplication (`Burning Square-Days`):** Detections are snapped to a uniform ~1 km latitude/longitude grid (`0.01°` cells) and deduplicated per satellite, province, and day so higher-resolution 375 m VIIRS oversampling does not inflate counts relative to 1 km MODIS.
        - **FRP Threshold & Overlap Calibration:** S-NPP VIIRS detections are filtered at `FRP ≥ 6 MW` to align detection sensitivity with MODIS Aqua, then scaled using overlap-period ratios across three seamless eras:
          - **Nov 2000 – Jul 2002:** Scaled MODIS Terra (`Terra_scaled`)
          - **Aug 2002 – Dec 2011:** MODIS Aqua baseline (`Aqua`)
          - **Jan 2012 – Dec 2025:** Scaled VIIRS S-NPP (`VIIRS_scaled`)
        """
    )

    summary_path = resolve_path("data_quality_summary.csv")
    if os.path.exists(summary_path):
        st.markdown('<div class="fw-panel-header" style="margin-top:16px;">Data Cleaning &amp; Filtering Pipeline Summary</div>', unsafe_allow_html=True)
        st.dataframe(
            pd.read_csv(summary_path),
            use_container_width=True,
            hide_index=True,
        )

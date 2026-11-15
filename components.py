"""Reusable HTML components for the FIREWATCH UI."""
import html
import streamlit as st
from theme import COLORS


def header(status_text: str):
    st.markdown(
        '<div class="fw-head"><div style="display:flex;align-items:center">'
        '<div class="fw-title">FIREWATCH <span>INTELLIGENCE</span></div>'
        '<div class="fw-sub">NASA MODIS &amp; VIIRS Satellite Monitoring Platform</div></div>'
        f'<div class="fw-status">{html.escape(status_text)}</div></div>',
        unsafe_allow_html=True,
    )


def _spark(values, color):
    vals = [float(v) for v in values][-60:]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    pts = " ".join(f"{i * 120 / (len(vals) - 1):.1f},{34 - (v - lo) / rng * 32:.1f}" for i, v in enumerate(vals))
    return (f'<svg width="120" height="36" viewBox="0 0 120 36"><polyline fill="none" '
            f'stroke="{color}" stroke-width="1.5" points="{pts}"/></svg>')


def kpi_card(label, value, color, note="", spark=None):
    st.markdown(
        f'<div class="fw-kpi"><div><div class="fw-kpi-label">{html.escape(label)}</div>'
        f'<div class="fw-kpi-value" style="color:{color}">{html.escape(str(value))}</div>'
        f'<div class="fw-kpi-note">{html.escape(note)}</div></div>'
        f'<div>{_spark(spark, color) if spark is not None else ""}</div></div>',
        unsafe_allow_html=True,
    )


def panel_title(text):
    st.markdown(f'<div class="fw-ptitle">{html.escape(text)}</div>', unsafe_allow_html=True)


def recent_table(df):
    """df columns: date, lat, lon, sensor (most recent first)."""
    rows = "".join(
        f"<tr><td>{r.date:%Y-%m-%d}</td><td>{r.lat:.4f}</td><td>{r.lon:.4f}</td><td>{html.escape(str(r.sensor))}</td></tr>"
        for r in df.itertuples()
    )
    st.markdown(
        '<table class="fw-table"><tr><th>Date</th><th>Lat</th><th>Lon</th><th>Sensor</th></tr>'
        f"{rows}</table>",
        unsafe_allow_html=True,
    )


def alert_box(title, body):
    st.markdown(f'<div class="fw-alert"><b>{html.escape(title)}</b><br>{html.escape(body)}</div>',
                unsafe_allow_html=True)

"""FIREWATCH design system: colors, typography, CSS, Plotly styling."""
import streamlit as st

COLORS = {
    "bg": "#070b14", "surface": "#0d1422", "panel": "#111a2b",
    "border": "#1e2b42", "text": "#d7e0ee", "muted": "#7f8fa9",
    "cyan": "#22d3ee", "orange": "#ff7a2f", "red": "#ef4444", "amber": "#f5a524",
}
FONT = "'Inter', 'Segoe UI', system-ui, sans-serif"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: %(font)s; color: %(text)s; }
.stApp { background: %(bg)s; }
header[data-testid="stHeader"] { background: transparent; height: 2.2rem; z-index: 999990; }
footer, #MainMenu, [data-testid="stDecoration"], [data-testid="stToolbarActions"],
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"], .stDeployButton { display: none !important; }
/* keep the sidebar open/close buttons visible */
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapsedControl"] button,
[data-testid="stExpandSidebarButton"] button { color: %(cyan)s !important; background: %(surface)s !important; border: 1px solid %(border)s; border-radius: 4px; display: inline-flex !important; visibility: visible !important; opacity: 1 !important; }
h1,h2,h3,h4 { color: %(text)s; font-weight: 600; letter-spacing: .02em; }
hr { border-color: %(border)s; }

/* sidebar = left filter panel */
section[data-testid="stSidebar"] { background: %(surface)s; border-right: 1px solid %(border)s; }
section[data-testid="stSidebar"] h2 { font-size: .8rem; text-transform: uppercase; letter-spacing: .1em; color: %(muted)s; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { font-size: .82rem; color: %(text)s; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { background: %(bg)s !important; border-color: %(border)s !important; }

/* cards: any bordered container */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: %(panel)s; border: 1px solid %(border)s !important; border-radius: 6px;
  transition: border-color .15s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: #2d4263 !important; }

/* tabs = top navigation */
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid %(border)s; background: %(surface)s; border-radius: 6px 6px 0 0; padding: 0 .5rem; }
.stTabs [data-baseweb="tab"] { height: 40px; padding: 0 1.1rem; color: %(muted)s; font-size: .85rem; background: transparent; }
.stTabs [aria-selected="true"] { color: %(cyan)s !important; }
.stTabs [data-baseweb="tab-highlight"] { background: %(cyan)s; height: 2px; }
.stTabs [data-baseweb="tab-panel"] { padding-top: .8rem; }

/* buttons */
.stButton > button, .stDownloadButton > button {
  background: %(panel)s; color: %(text)s; border: 1px solid %(border)s; border-radius: 4px;
  font-size: .8rem; transition: all .15s ease; width: 100%%;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: %(cyan)s; color: %(cyan)s; }

/* header */
.fw-head { display:flex; justify-content:space-between; align-items:center; padding: 0 0 .7rem 0; }
.fw-title { font-size: 1.55rem; font-weight: 700; letter-spacing: .04em; color:#fff; }
.fw-title span { color: %(cyan)s; }
.fw-sub { font-size: .8rem; color: %(muted)s; margin-left: 1rem; padding-left: 1rem; border-left: 1px solid %(border)s; }
.fw-status { font-size: .72rem; color: #4ade80; border: 1px solid #14532d; background: #052e16; padding: .3rem .7rem; border-radius: 4px; letter-spacing: .05em; }

/* kpi */
.fw-kpi { background: %(panel)s; border: 1px solid %(border)s; border-radius: 6px; padding: .7rem 1rem; display:flex; justify-content:space-between; align-items:flex-end; height: 96px; }
.fw-kpi-label { font-size: .68rem; text-transform: uppercase; letter-spacing: .08em; color: %(muted)s; }
.fw-kpi-value { font-size: 1.9rem; font-weight: 600; line-height: 1.2; }
.fw-kpi-note { font-size: .72rem; color: %(muted)s; }

.fw-ptitle { font-size: .72rem; text-transform: uppercase; letter-spacing: .09em; color: %(muted)s; font-weight: 600; margin: 0 0 .4rem 0; }

/* recent detections table */
.fw-table { width:100%%; border-collapse: collapse; font-size: .72rem; font-variant-numeric: tabular-nums; }
.fw-table th { text-align:left; color: %(muted)s; font-weight:500; padding: .25rem .3rem; border-bottom: 1px solid %(border)s; }
.fw-table td { padding: .22rem .3rem; border-bottom: 1px solid #16213a; color: %(text)s; }
.fw-table tr:hover td { background: #16213a; }
.fw-alert { border:1px solid #7f1d1d; background:#2a0f12; color:#fca5a5; padding:.6rem .8rem; border-radius:6px; font-size:.78rem; margin-top:.6rem; }
.fw-alert b { color:#f87171; }
.fw-legend span { display:inline-block; margin-right:1rem; font-size:.74rem; color:%(muted)s; }
.fw-dot { display:inline-block; width:9px; height:9px; border-radius:50%%; margin-right:.35rem; }
[data-testid="stDataFrame"] { border: 1px solid %(border)s; border-radius: 6px; }
</style>
""" % {**COLORS, "font": FONT}


def apply_theme():
    st.markdown(_CSS, unsafe_allow_html=True)


def style_fig(fig, height=300, legend_top=True):
    """Apply the dark Plotly look to any figure."""
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=COLORS["text"], size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.14, bgcolor="rgba(0,0,0,0)") if legend_top else None,
        coloraxis_colorbar=dict(thickness=10, outlinewidth=0),
    )
    fig.update_xaxes(gridcolor="#18243a", zeroline=False, linecolor=COLORS["border"])
    fig.update_yaxes(gridcolor="#18243a", zeroline=False, linecolor=COLORS["border"])
    return fig

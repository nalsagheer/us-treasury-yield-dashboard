import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="US Treasury Yield Curve Dashboard",
    page_icon="📈",
    layout="wide"
)

px.defaults.template = "plotly_dark"

# -------------------------
# TICKERS
# -------------------------
MATURITY_TICKERS = {
    "US 5Y": "^FVX",
    "US 10Y": "^TNX",
    "US 30Y": "^TYX",
}

PERIODS = {
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
}

# -------------------------
# HELPERS
# -------------------------
def flatten_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Make yfinance columns consistent even when they come as MultiIndex."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    return df


def ensure_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    yfinance sometimes returns index named Date, sometimes not.
    After reset_index() the date column may be 'Date' or something else.
    This function guarantees there is a 'date' column.
    """
    df = df.reset_index()

    # lower-case all columns
    df.columns = [str(c).strip().lower() for c in df.columns]

    # common names from yfinance
    if "date" not in df.columns:
        if "datetime" in df.columns:
            df = df.rename(columns={"datetime": "date"})
        else:
            # fallback: first column from reset_index is usually the datetime index
            first_col = df.columns[0]
            df = df.rename(columns={first_col: "date"})

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.tz_localize(None)
    return df


@st.cache_data(ttl=3600)
def fetch_series(ticker: str, period: str) -> pd.DataFrame:
    df = yf.download(ticker, period=period, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()

    df = flatten_cols(df)
    df = ensure_date_column(df)

    # make sure close exists
    df.columns = [c.lower() for c in df.columns]
    if "close" not in df.columns:
        return pd.DataFrame()

    df = df.sort_values("date")[["date", "close"]].copy()

    # Yahoo treasury tickers (^TNX etc.) are scaled by 10
    df["yield"] = df["close"] / 10.0
    return df[["date", "yield"]]


# -------------------------
# SIDEBAR
# -------------------------
with st.sidebar:
    st.subheader("Controls")

    selected = st.multiselect(
        "Select Maturities",
        options=list(MATURITY_TICKERS.keys()),
        default=list(MATURITY_TICKERS.keys())
    )

    period_label = st.selectbox(
        "Select Period",
        list(PERIODS.keys()),
        index=2
    )

    rolling_window = st.slider(
        "Rolling Volatility Window (days)",
        5, 90, 30, 5
    )

period = PERIODS[period_label]

# -------------------------
# TITLE
# -------------------------
st.title("US Treasury Yield Curve Dashboard")
st.caption(
    "Interactive fixed income dashboard for US Treasury yields "
    "(level, changes, volatility, correlation). Data via Yahoo Finance."
)

if not selected:
    st.warning("Please select at least one maturity.")
    st.stop()

# -------------------------
# FETCH DATA
# -------------------------
series_map = {}
working = {}
failed = {}

with st.spinner("Loading data..."):
    for name in selected:
        ticker = MATURITY_TICKERS[name]
        df = fetch_series(ticker, period)
        if df.empty:
            failed[name] = ticker
        else:
            working[name] = ticker
            series_map[name] = df.rename(columns={"yield": name})

with st.expander("Data source status (tickers used / failed)", expanded=False):
    if working:
        st.success("Working tickers")
        st.json(working)
    if failed:
        st.error("Failed tickers")
        st.json(failed)

if not series_map:
    st.error("No data available.")
    st.stop()

# Merge all series on date (inner join)
data = None
for name, df in series_map.items():
    data = df if data is None else pd.merge(data, df, on="date", how="inner")

data = data.sort_values("date").dropna()

# -------------------------
# METRICS
# -------------------------
avg_vals = data.drop(columns=["date"]).mean()
daily_change = data.drop(columns=["date"]).diff()
vol_vals = daily_change.std()
change_vals = data.drop(columns=["date"]).iloc[-1] - data.drop(columns=["date"]).iloc[0]

global_avg = avg_vals.mean()
highest_avg = avg_vals.idxmax()
most_stable = vol_vals.idxmin()
biggest_change = change_vals.abs().idxmax()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Avg Yield (selected)", f"{global_avg:.2f}%")
k2.metric("Highest Avg Yield", highest_avg.replace("US ", ""))
k3.metric("Most Stable (Lowest Vol)", most_stable.replace("US ", ""))
k4.metric("Biggest Change", biggest_change.replace("US ", ""))

st.divider()

# -------------------------
# TABS
# -------------------------
tab_overview, tab_curve, tab_risk, tab_data = st.tabs(
    ["Overview", "Curve", "Risk", "Data"]
)

# =========================
# OVERVIEW
# =========================
with tab_overview:
    st.subheader("Yields Over Time")

    long_df = data.melt(
        id_vars="date",
        var_name="Maturity",
        value_name="Yield (%)"
    )

    fig_line = px.line(
        long_df,
        x="date",
        y="Yield (%)",
        color="Maturity",
        title="US Treasury Yields Over Time (%)"
    )
    fig_line.update_layout(height=420)
    st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("Quick Summary")
    summary = pd.DataFrame({
        "Latest Yield (%)": data.drop(columns=["date"]).iloc[-1],
        "Average Yield (%)": avg_vals,
        "Volatility (Std)": vol_vals,
        "Change (pts)": change_vals
    }).round(4)

    st.dataframe(summary, use_container_width=True)

    st.info(
        f"""
- Highest average yield: **{highest_avg.replace("US ", "")}**
- Most stable maturity: **{most_stable.replace("US ", "")}**
- Largest change: **{biggest_change.replace("US ", "")}**
"""
    )

# =========================
# CURVE
# =========================
with tab_curve:
    st.subheader("Yield Curve Snapshot (Latest)")

    latest = data.drop(columns=["date"]).iloc[-1]
    ordered = [c for c in ["US 5Y", "US 10Y", "US 30Y"] if c in latest.index]
    latest = latest[ordered]

    curve_df = pd.DataFrame({
        "Maturity": [x.replace("US ", "") for x in latest.index],
        "Yield (%)": latest.values
    })

    fig_curve = px.line(
        curve_df,
        x="Maturity",
        y="Yield (%)",
        markers=True,
        title="Latest US Yield Curve"
    )
    fig_curve.update_layout(height=420)
    st.plotly_chart(fig_curve, use_container_width=True)

    # Slope
    if "US 10Y" in data.columns and "US 5Y" in data.columns:
        st.subheader("Curve Slope (10Y - 5Y)")

        slope_df = pd.DataFrame({
            "date": data["date"],
            "Slope": data["US 10Y"] - data["US 5Y"]
        })

        fig_slope = px.line(
            slope_df,
            x="date",
            y="Slope",
            title="10Y - 5Y Slope Over Time (pp)"
        )
        fig_slope.update_traces(line=dict(width=3))
        fig_slope.update_layout(height=420, showlegend=False)

        # zero line
        fig_slope.add_hline(
            y=0,
            line_dash="dash",
            line_color="white",
            opacity=0.6
        )

        st.plotly_chart(fig_slope, use_container_width=True)
        st.caption("Positive slope = normal curve; negative slope = inverted curve.")

# =========================
# RISK
# =========================
with tab_risk:
    st.subheader(f"Rolling Volatility (window = {rolling_window} days)")

    rolling_vol = daily_change.rolling(rolling_window).std()
    rlong = rolling_vol.copy()
    rlong["date"] = data["date"]
    rlong = rlong.melt(
        id_vars="date",
        var_name="Maturity",
        value_name="Rolling Vol"
    )

    fig_rvol = px.line(
        rlong.dropna(),
        x="date",
        y="Rolling Vol",
        color="Maturity",
        title="Rolling Volatility Over Time"
    )
    fig_rvol.update_layout(height=420)
    st.plotly_chart(fig_rvol, use_container_width=True)

    st.subheader("Correlation Matrix (Daily Yield Changes)")

    if data.shape[1] > 2:
        corr = daily_change.dropna().corr().round(2)

        fig_corr = px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Blues",
            zmin=0,
            zmax=1
        )
        fig_corr.update_layout(height=420)
        st.plotly_chart(fig_corr, use_container_width=True)

        st.caption("Correlation is based on daily yield changes.")

# =========================
# DATA
# =========================
with tab_data:
    st.subheader("Raw Data Preview")
    st.dataframe(data.tail(200), use_container_width=True)
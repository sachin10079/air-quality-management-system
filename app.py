"""Air Quality Management System - Streamlit app.

Run with:   streamlit run app.py
"""
import pandas as pd
import requests
import streamlit as st

from modules import api
from modules.aqi_info import CPCB, LEVELS, SCALES, US, get_level, text_color_for
from modules.calculator import POLLUTANTS, compute_aqi
from modules.charts import gauge_chart, history_chart, subindex_chart

st.set_page_config(page_title="Air Quality Management System", page_icon="🌫️", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.8rem;}
    .aqi-card {border-radius: 18px; padding: 22px 26px; box-shadow: 0 4px 14px rgba(0,0,0,.12);}
    .aqi-card h1 {margin: 0; font-size: 4rem; line-height: 1;}
    .aqi-card h3 {margin: 6px 0 2px 0;}
    .aqi-card p {margin: 0; opacity: .92;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- caching
@st.cache_data(ttl=3600, show_spinner=False)
def cached_search(name):
    return api.search_city(name)


@st.cache_data(ttl=600, show_spinner=False)
def cached_air(lat, lon):
    return api.get_air_quality(lat, lon, past_days=10)


# ---------------------------------------------------------------- helpers
def level_card(value, level, subtitle=""):
    fg = text_color_for(level["color"])
    st.markdown(
        f"""<div class="aqi-card" style="background:{level['color']};color:{fg}">
        <p>Air Quality Index</p>
        <h1>{value:.0f}</h1>
        <h3>{level['emoji']} {level['name']}</h3>
        <p>{subtitle or level['summary']}</p></div>""",
        unsafe_allow_html=True,
    )


def advice_block(level):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 🩺 Health effects")
        for x in level["effects"]:
            st.markdown(f"- {x}")
    with c2:
        st.markdown("#### 👥 Who is at risk")
        for x in level["at_risk"]:
            st.markdown(f"- {x}")
    with c3:
        st.markdown("#### 🛡️ How to stay safe")
        for x in level["measures"]:
            st.markdown(f"- {x}")


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🌫️ AQMS")
    st.caption("Air Quality Management System")
    scale = st.radio(
        "AQI scale",
        SCALES,
        help="India CPCB AQI is computed from live pollutant data. US AQI is provided directly by the API.",
    )
    st.divider()
    st.markdown("**Data source:** [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (free, no key needed)")
    st.caption("Values are model-based estimates, not an official regulatory measurement.")

st.title("🌫️ Air Quality Management System")
tab1, tab2, tab3 = st.tabs(["🔍 City AQI & 10-Day History", "🧮 AQI Calculator", "🎚️ Pollution Level Explorer"])


# ---------------------------------------------------------------- tab 1
def city_tab():
    c1, c2 = st.columns([2, 2])
    query = c1.text_input("Search a city", value="Chandigarh", placeholder="e.g. Delhi, Mohali, Mumbai, London")
    if not query.strip():
        st.info("Type a city name to begin.")
        return
    try:
        matches = cached_search(query.strip())
    except requests.RequestException as e:
        st.error(f"Could not reach the search service. Check your internet connection.\n\n{e}")
        return
    if not matches:
        st.warning(f"No place found for '{query}'. Try another spelling.")
        return

    def label(m):
        return ", ".join(p for p in (m["name"], m["admin1"], m["country"]) if p)

    idx = c2.selectbox("Select location", range(len(matches)), format_func=lambda i: label(matches[i]))
    place = matches[idx]

    try:
        with st.spinner("Fetching live air quality..."):
            raw = cached_air(place["lat"], place["lon"])
    except requests.RequestException as e:
        st.error(f"Could not fetch air-quality data.\n\n{e}")
        return

    df = api.build_hourly(raw)
    now = api.get_now(raw, df)
    snap = api.live_snapshot(df, now)
    daily = api.daily_summary(df, now)

    try:
        cpcb_now = compute_aqi(snap)
    except ValueError:
        cpcb_now = None
    us_now = raw.get("current", {}).get("us_aqi")

    value = (cpcb_now["aqi"] if cpcb_now else None) if scale == CPCB else us_now
    if value is None:
        st.warning("Live AQI is not available for this location right now.")
        return

    level = get_level(value, scale)
    left, right = st.columns([1, 1.4])
    with left:
        sub = f"Dominant pollutant: {cpcb_now['dominant']}" if (scale == CPCB and cpcb_now) else level["summary"]
        level_card(value, level, sub)
        st.caption(f"📍 {label(place)}  •  Updated {now:%d %b %Y, %H:%M} (local time)")
    with right:
        st.markdown("##### Current pollutants")
        cols = st.columns(3)
        for i, key in enumerate(api.POLL_KEYS):
            meta = POLLUTANTS[key]
            v = snap[key]
            cols[i % 3].metric(f"{meta['name']} ({meta['avg'].split()[0]})",
                               "n/a" if pd.isna(v) else f"{v:.1f} {meta['unit']}")
        other = f"US AQI: **{us_now:.0f}**" if scale == CPCB and us_now is not None else \
            (f"India CPCB AQI: **{cpcb_now['aqi']}**" if cpcb_now else "")
        if other:
            st.caption(f"Also: {other}")

    st.plotly_chart(history_chart(daily, scale, place["name"]))

    with st.expander("📋 View the 10-day data table"):
        table = daily.copy()
        table.index = table.index.strftime("%d %b %Y")
        table.index.name = "Date"
        st.dataframe(table.round(1))

    st.subheader(f"What this means: {level['name']}")
    advice_block(level)


with tab1:
    city_tab()


# ---------------------------------------------------------------- tab 2
def calculator_tab():
    st.subheader("AQI Calculator (India CPCB method)")
    st.caption("Enter the pollutant concentrations you have. At least **3 pollutants** are needed, "
               "and one must be **PM2.5 or PM10**. Leave unknown fields empty.")
    with st.form("calc_form"):
        cols = st.columns(4)
        values = {}
        for i, (key, meta) in enumerate(POLLUTANTS.items()):
            values[key] = cols[i % 4].number_input(
                f"{meta['name']} ({meta['unit']})", min_value=0.0, value=None, step=1.0,
                help=f"{meta['avg']}", key=f"calc_{key}",
            )
        submitted = st.form_submit_button("Calculate AQI", type="primary")

    if not submitted:
        return
    try:
        res = compute_aqi(values)
    except ValueError as e:
        st.error(str(e))
        return

    level = get_level(res["aqi"], CPCB)
    c1, c2 = st.columns([1, 1])
    with c1:
        level_card(res["aqi"], level, f"Dominant pollutant: {res['dominant']}")
    with c2:
        st.plotly_chart(subindex_chart(res["sub_indices"]))
    st.plotly_chart(gauge_chart(res["aqi"], CPCB, height=280))
    st.subheader(f"What this means: {level['name']}")
    advice_block(level)


with tab2:
    calculator_tab()


# ---------------------------------------------------------------- tab 3
def slider_tab():
    st.subheader("Pollution Level Explorer")
    st.caption(f"Slide the AQI to see the pollution level, its harms and safety measures ({scale}).")
    aqi = st.slider("AQI value", 0, 500, 120, step=1)
    level = get_level(aqi, scale)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(gauge_chart(aqi, scale))
    with c2:
        level_card(aqi, level)
    advice_block(level)

    with st.expander("📊 All AQI categories"):
        st.dataframe(
            pd.DataFrame([{"AQI range": f"{l['low']} - {l['high']}", "Category": l["name"],
                           "Summary": l["summary"]} for l in LEVELS[scale]]),
            hide_index=True,
        )


with tab3:
    slider_tab()

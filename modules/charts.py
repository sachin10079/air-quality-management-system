"""Plotly charts: 10-day history line chart, AQI gauge and sub-index bars."""
import plotly.graph_objects as go

from modules.aqi_info import CPCB, LEVELS, get_level

FONT = dict(family="Inter, Segoe UI, sans-serif", size=14)


def history_chart(daily, scale, city):
    col = "CPCB AQI" if scale == CPCB else "US AQI"
    series = daily[col]
    ymax = max(float(series.max()) * 1.3, 120)

    fig = go.Figure()
    # Coloured category bands behind the line
    for lv in LEVELS[scale]:
        if lv["low"] >= ymax:
            continue
        fig.add_hrect(
            y0=lv["low"], y1=min(lv["high"] + 1, ymax),
            fillcolor=lv["color"], opacity=0.13, line_width=0, layer="below",
            annotation_text=lv["name"], annotation_position="top right",
            annotation_font=dict(size=10, color="#475569"),
        )

    colors = [get_level(v, scale)["color"] if v == v else "#94A3B8" for v in series]
    names = [get_level(v, scale)["name"] if v == v else "n/a" for v in series]
    fig.add_trace(go.Scatter(
        x=series.index, y=series.round(0),
        mode="lines+markers+text",
        text=[f"{v:.0f}" if v == v else "" for v in series],
        textposition="top center",
        textfont=dict(size=13, color="#0F172A"),
        line=dict(color="#334155", width=3.5, shape="spline", smoothing=0.7),
        marker=dict(size=14, color=colors, line=dict(color="white", width=2.5)),
        customdata=names,
        hovertemplate="<b>%{x|%a, %d %b}</b><br>AQI: %{y}<br>%{customdata}<extra></extra>",
        name="AQI",
    ))
    fig.update_layout(
        title=dict(text=f"<b>{city}</b> - AQI over the last 10 days ({scale})", font=dict(size=18)),
        template="plotly_white", font=FONT, height=460,
        margin=dict(l=20, r=20, t=70, b=30), showlegend=False,
        yaxis=dict(title="AQI", range=[0, ymax], gridcolor="#E2E8F0"),
        xaxis=dict(tickformat="%d %b", dtick=86400000, showgrid=False),
        hoverlabel=dict(font_size=14),
    )
    return fig


def gauge_chart(value, scale, height=330):
    lv = get_level(value, scale)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(font=dict(size=54, color=lv["color"])),
        title=dict(text=f"<b>{lv['name']}</b>", font=dict(size=22, color=lv["color"])),
        gauge=dict(
            axis=dict(range=[0, 500], tickwidth=1, tickcolor="#64748B"),
            bar=dict(color="#0F172A", thickness=0.22),
            bgcolor="white", borderwidth=0,
            steps=[dict(range=[l["low"], l["high"] + 1], color=l["color"]) for l in LEVELS[scale]],
            threshold=dict(line=dict(color="#0F172A", width=5), thickness=0.8, value=value),
        ),
    ))
    fig.update_layout(height=height, margin=dict(l=30, r=30, t=60, b=10), font=FONT)
    return fig


def subindex_chart(sub_indices, scale=CPCB):
    items = sorted(sub_indices.items(), key=lambda kv: kv[1])
    fig = go.Figure(go.Bar(
        x=[v for _, v in items], y=[k for k, _ in items], orientation="h",
        marker=dict(color=[get_level(v, scale)["color"] for _, v in items]),
        text=[v for _, v in items], textposition="outside",
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_layout(
        title="Sub-index of each pollutant", template="plotly_white", font=FONT,
        height=max(240, 60 * len(items) + 100),
        margin=dict(l=20, r=30, t=50, b=20),
        xaxis=dict(range=[0, max(100, max(sub_indices.values()) * 1.2)], title="Sub-index"),
    )
    return fig

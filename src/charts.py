import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .config import PHASE_ORDER, TODAY
from .analytics import split_multi_rows

CHART_CONFIG = {"displayModeBar": False}


def chart_layout(fig: go.Figure, height: int = 410) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eef5ff", "family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"},
        margin={"l": 10, "r": 10, "t": 44, "b": 10},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1,
                "font": {"color": "#f7fbff", "size": 13}, "title": {"font": {"color": "#f7fbff", "size": 13}},
                "bgcolor": "rgba(8,13,24,.72)", "bordercolor": "rgba(164,183,219,.26)", "borderwidth": 1},
        title={"font": {"color": "#ffffff", "size": 18}},
        xaxis={"gridcolor": "rgba(164,183,219,.14)", "zerolinecolor": "rgba(164,183,219,.22)", "tickfont": {"color": "#e6eefc", "size": 12}, "title": {"font": {"color": "#f4f8ff"}}},
        yaxis={"gridcolor": "rgba(164,183,219,.14)", "zerolinecolor": "rgba(164,183,219,.22)", "tickfont": {"color": "#e6eefc", "size": 12}, "title": {"font": {"color": "#f4f8ff"}}},
    )
    return fig


def active_phase_chart(active_df: pd.DataFrame) -> go.Figure:
    phase_df = active_df.groupby(["target_lane", "phase"], as_index=False).agg(trials=("nct_id", "count"), enrollment=("enrollment", "sum"))
    fig = px.bar(phase_df, x="phase", y="trials", color="target_lane", hover_data=["enrollment"], category_orders={"phase": PHASE_ORDER}, title="Active / Near-Active Trials by Phase")
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 430)


def country_charts(df: pd.DataFrame) -> tuple[go.Figure, go.Figure, pd.DataFrame]:
    country_rows = split_multi_rows(df, "countries", "country")
    country_counts = country_rows.groupby("country", as_index=False).agg(trials=("nct_id", "count"), enrollment=("enrollment", "sum"), sites=("site_count", "sum")).sort_values("trials", ascending=False).head(18)
    fig_country = px.bar(country_counts.sort_values("trials"), x="trials", y="country", orientation="h", hover_data=["enrollment", "sites"], title="Active Trials by Country")
    fig_country.update_xaxes(title="Studies")
    fig_country.update_yaxes(title="")
    geo_lane = country_rows.groupby(["target_lane", "country"], as_index=False).agg(trials=("nct_id", "count"))
    geo_pivot = geo_lane.pivot_table(index="country", columns="target_lane", values="trials", aggfunc="sum", fill_value=0) if not geo_lane.empty else pd.DataFrame()
    fig_heat = px.imshow(geo_pivot, text_auto=True, aspect="auto", title="Country × Lane Density") if not geo_pivot.empty else go.Figure()
    return chart_layout(fig_country, 470), chart_layout(fig_heat, 470), country_counts


def enrollment_charts(df: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    enroll_lane = df.groupby("target_lane", as_index=False).agg(enrollment=("enrollment", "sum"), trials=("nct_id", "count")).sort_values("enrollment", ascending=False)
    fig_lane = px.bar(enroll_lane, x="target_lane", y="enrollment", hover_data=["trials"], title="Listed Enrollment by Lane")
    fig_lane.update_xaxes(title="")
    fig_lane.update_yaxes(title="Patients")
    enroll_ind = df.groupby("indication_hint", as_index=False).agg(enrollment=("enrollment", "sum"), trials=("nct_id", "count")).sort_values("enrollment", ascending=False)
    fig_ind = px.bar(enroll_ind, x="enrollment", y="indication_hint", orientation="h", hover_data=["trials"], title="Listed Enrollment by Patient Population")
    fig_ind.update_xaxes(title="Patients")
    fig_ind.update_yaxes(title="")
    return chart_layout(fig_lane, 430), chart_layout(fig_ind, 430)


def combo_chart(df: pd.DataFrame) -> go.Figure:
    combo_df = df.groupby(["target_lane", "combo_category"], as_index=False).agg(
        trials=("nct_id", "count"), enrollment=("enrollment", "sum")
    )
    fig = px.bar(
        combo_df, x="target_lane", y="trials", color="combo_category",
        hover_data=["enrollment"], title="Combination Strategy by Lane"
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 455)


def combo_class_chart(df: pd.DataFrame) -> go.Figure:
    rows = []
    for _, r in df.iterrows():
        classes = [c.strip() for c in str(r.get("combo_classes", "")).split(",") if c.strip() and c.strip() != "No partner class detected"]
        if not classes:
            classes = ["No partner class detected"]
        for cls in classes:
            rows.append({"target_lane": r.get("target_lane"), "combo_class": cls, "nct_id": r.get("nct_id"), "enrollment": r.get("enrollment", 0)})
    d = pd.DataFrame(rows)
    combo_df = d.groupby(["combo_class", "target_lane"], as_index=False).agg(trials=("nct_id", "count"), enrollment=("enrollment", "sum")) if not d.empty else pd.DataFrame(columns=["combo_class", "target_lane", "trials", "enrollment"])
    fig = px.bar(
        combo_df, x="trials", y="combo_class", color="target_lane", orientation="h",
        hover_data=["enrollment"], title="Detected Partner Classes"
    )
    fig.update_xaxes(title="Studies")
    fig.update_yaxes(title="")
    return chart_layout(fig, 520)


def combo_confidence_chart(df: pd.DataFrame) -> go.Figure:
    conf = df.groupby(["combo_confidence", "target_lane"], as_index=False).agg(trials=("nct_id", "count"))
    fig = px.bar(conf, x="combo_confidence", y="trials", color="target_lane", title="Combination Extraction Confidence")
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Studies")
    return chart_layout(fig, 390)


def forward_start_chart(planned_start_df: pd.DataFrame) -> go.Figure:
    d = planned_start_df.copy()
    d["event_label"] = d["target_lane"] + " · " + d["sponsor"].str.slice(0, 22) + " · " + d["nct_id"]
    fig = px.scatter(d, x="start_date", y="event_label", size="enrollment", color="target_lane", hover_data=["title", "status", "phase", "indication_hint", "combo_category"], title="Forward Starts: Trials Expected to Begin")
    fig.update_yaxes(title="", autorange="reversed")
    fig.update_xaxes(title="Planned / estimated start date")
    return chart_layout(fig, max(430, min(820, 120 + len(d) * 24)))


def forward_completion_chart(expected_completion_df: pd.DataFrame) -> go.Figure:
    d = expected_completion_df.copy()
    d["event_label"] = d["target_lane"] + " · " + d["sponsor"].str.slice(0, 22) + " · " + d["nct_id"]
    fig = px.scatter(d, x="primary_completion_date", y="event_label", size="enrollment", color="phase", hover_data=["title", "status", "target_lane", "indication_hint", "combo_category"], title="Forward Completions: Primary Completion Windows")
    fig.update_yaxes(title="", autorange="reversed")
    fig.update_xaxes(title="Primary completion date")
    return chart_layout(fig, max(430, min(820, 120 + len(d) * 24)))


def sponsor_chart(df: pd.DataFrame) -> go.Figure:
    sponsor_counts = df.groupby("sponsor", as_index=False).agg(trials=("nct_id", "count"), active=("is_active", "sum"), enrollment=("enrollment", "sum"), sites=("site_count", "sum")).sort_values("trials", ascending=False).head(18)
    fig = px.bar(sponsor_counts.sort_values("trials"), x="trials", y="sponsor", orientation="h", hover_data=["active", "enrollment", "sites"], title="Top Sponsors by Trial Count")
    fig.update_yaxes(title="")
    fig.update_xaxes(title="Studies")
    return chart_layout(fig, 520)


def timeline_chart(df: pd.DataFrame) -> go.Figure:
    show_df = df.sort_values(["target_lane", "timeline_start", "sponsor"]).copy().head(55)
    show_df["label"] = show_df["target_lane"].str.slice(0, 18) + " · " + show_df["sponsor"].str.slice(0, 20) + " · " + show_df["nct_id"]
    fig = px.timeline(show_df, x_start="timeline_start", x_end="timeline_finish", y="label", color="target_lane", hover_data=["title", "sponsor", "status", "phase", "enrollment", "countries", "combo_category", "conditions", "interventions"], title="Trial Development Windows")
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="")
    return chart_layout(fig, max(520, min(980, 60 + len(show_df) * 23)))

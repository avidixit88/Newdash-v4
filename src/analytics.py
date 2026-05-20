from __future__ import annotations
import datetime as dt
import pandas as pd
from .config import PRESET_QUERIES, PRESET_PAGE_SIZE, STATUS_FOCUS, TARGET_LANES, TODAY
from .clinicaltrials_client import fetch_registry_studies


def run_clinical_analysis() -> dict:
    df = fetch_registry_studies(PRESET_QUERIES, PRESET_PAGE_SIZE)
    lane_names = list(TARGET_LANES.keys())
    df = df[df["target_lane"].isin(lane_names) | (df["target_lane"] == "Other / Unclassified")].copy()
    active_df = df[df["is_active"]].copy()
    planned_df = df[df["is_planned"]].copy()
    forward_df = df[(df["primary_completion_date"].notna()) & (df["primary_completion_date"].dt.date >= TODAY)].copy()
    planned_start_df = df[(df["start_date"].notna()) & (df["start_date"].dt.date >= TODAY)].sort_values("start_date").head(35).copy()
    expected_completion_df = forward_df.sort_values("primary_completion_date").head(35).copy()
    return {
        "df": df,
        "active_df": active_df,
        "planned_df": planned_df,
        "forward_df": forward_df,
        "planned_start_df": planned_start_df,
        "expected_completion_df": expected_completion_df,
        "lane_names": lane_names,
    }


def split_multi_rows(df: pd.DataFrame, col: str, value_name: str) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        vals = [v.strip() for v in str(r.get(col, "")).split(",") if v.strip()]
        if not vals:
            vals = ["Not listed"]
        for v in vals:
            nr = r.to_dict()
            nr[value_name] = v
            rows.append(nr)
    return pd.DataFrame(rows)


def build_signal_feed(bundle: dict) -> list[tuple[str, str]]:
    df = bundle["df"]
    active_df = bundle["active_df"]
    planned_df = bundle["planned_df"]
    forward_df = bundle["forward_df"]
    signals = []
    if len(active_df):
        signals.append(("Active footprint", f"{len(active_df)} active or near-active studies are visible across the focused lanes."))
    if not planned_df.empty:
        signals.append(("Forward-looking studies", f"{len(planned_df)} studies are listed as planned/not-yet-recruiting or have a future start date."))
    if not forward_df.empty:
        nxt = forward_df.sort_values("primary_completion_date").iloc[0]
        signals.append(("Nearest catalyst window", f"{nxt['sponsor']} lists a primary completion date of {nxt['primary_completion_date'].date()} for {nxt['nct_id']} in the {nxt['target_lane']} lane."))
    combo_n = int((df["combo_category"] != "Monotherapy / no partner agent detected").sum())
    if combo_n:
        signals.append(("Combination therapy activity", f"{combo_n} captured studies include detectable partner agents, treatment classes, or explicit combination therapy language."))
    country_rows = split_multi_rows(active_df if not active_df.empty else df, "countries", "country")
    if not country_rows.empty:
        country_counts = country_rows.groupby("country", as_index=False).agg(trials=("nct_id", "count")).sort_values("trials", ascending=False)
        signals.append(("Geographic concentration", f"{country_counts.iloc[0]['country']} is the most represented country in the current active trial footprint."))
    sponsor_counts = df.groupby("sponsor", as_index=False).agg(trials=("nct_id", "count")).sort_values("trials", ascending=False)
    if not sponsor_counts.empty:
        signals.append(("Sponsor concentration", f"{sponsor_counts.iloc[0]['sponsor']} is the most represented lead sponsor in this scan."))
    return signals[:7]

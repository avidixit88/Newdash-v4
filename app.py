import streamlit as st
from src.styles import CSS
from src.analytics import run_clinical_analysis, build_signal_feed
from src import charts
from src.ui import (
    render_sidebar, render_hero, render_idle_panel, render_snapshot,
    render_lane_cards, section, render_signal_feed, render_footer
)

st.set_page_config(page_title="NextCure Signal Room", page_icon="🧬", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)
render_sidebar()

if "scan_ran" not in st.session_state:
    st.session_state.scan_ran = False

render_hero()
run_scan = st.button("Run Analysis", key="run_analysis")
if run_scan:
    st.session_state.scan_ran = True

if not st.session_state.scan_ran:
    render_idle_panel()
    st.stop()

progress = st.progress(0)
status_box = st.empty()
status_box.caption("Initializing clinical registry scan…")
progress.progress(20)
status_box.caption("Filtering preset B7-H4, CDH6, Alzheimer’s, and bone disease lanes…")
progress.progress(45)
bundle = run_clinical_analysis()
progress.progress(75)
status_box.caption("Building charts, forward catalyst views, and evidence layer…")
progress.progress(100)
status_box.caption("Clinical intelligence layer online. Preset scan complete.")

df = bundle["df"]
active_df = bundle["active_df"]
planned_start_df = bundle["planned_start_df"]
expected_completion_df = bundle["expected_completion_df"]

section("Executive Snapshot", "A restrained top-line readout based only on structured trial registry data.")
render_snapshot(bundle)

section("Lane Cards", "The four NextCure-relevant focus areas, kept separate so Michael can see where each signal comes from.")
render_lane_cards(bundle)

section("Active Trials by Phase", "Phase mix across active and near-active studies. This shows whether each lane is early exploratory, expansion-stage, or maturing.")
if active_df.empty:
    st.info("No active phase data found for the current scan.")
else:
    st.plotly_chart(charts.active_phase_chart(active_df), use_container_width=True, config=charts.CHART_CONFIG)

section("Geographic Trial Footprint", "Country and site concentration. This helps identify where trials are actually recruiting and where expansion may be happening.")
g1, g2 = st.columns([1.05, .95])
fig_country, fig_geo_heat, _country_counts = charts.country_charts(active_df if not active_df.empty else df)
with g1:
    st.plotly_chart(fig_country, use_container_width=True, config=charts.CHART_CONFIG)
with g2:
    st.plotly_chart(fig_geo_heat, use_container_width=True, config=charts.CHART_CONFIG)

section("Patient Population & Enrollment", "Listed enrollment is not prevalence, but it is a useful proxy for trial scale, sponsor commitment, and potential near-term data density.")
e1, e2 = st.columns([1, 1])
fig_enroll_lane, fig_enroll_ind = charts.enrollment_charts(df)
with e1:
    st.plotly_chart(fig_enroll_lane, use_container_width=True, config=charts.CHART_CONFIG)
with e2:
    st.plotly_chart(fig_enroll_ind, use_container_width=True, config=charts.CHART_CONFIG)

section("Combination Therapy Intelligence", "A structured extraction of partner agents and regimen classes from intervention names, arm descriptions, summaries, and eligibility text. This separates monotherapy/no partner detected from ADC + IO, chemo/platinum/taxane, anti-VEGF, PARP/DNA damage, targeted pathway, endocrine, radiation, and multi-ADC strategies.")
cmb1, cmb2 = st.columns([1, 1])
with cmb1:
    st.plotly_chart(charts.combo_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with cmb2:
    st.plotly_chart(charts.combo_class_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
st.plotly_chart(charts.combo_confidence_chart(df), use_container_width=True, config=charts.CHART_CONFIG)
with st.expander("How combination therapy is classified", expanded=False):
    st.markdown("""
    The classifier looks across the title, conditions, intervention names, arm descriptions, brief summary, and eligibility text.

    **High confidence** means explicit combination wording plus a named partner agent or class.  
    **Medium confidence** means a partner agent/class was detected, but the protocol language may need review.  
    **Low confidence** means no named partner class was found, so the study is treated as monotherapy/no partner detected until proven otherwise.
    """)

section("Forward-Looking Catalyst Calendar", "Forward events are split into two separate views so it is clear what is starting versus what is expected to complete.")
fc1, fc2 = st.columns([1, 1])
with fc1:
    st.markdown("#### Planned Trial Starts")
    if planned_start_df.empty:
        st.info("No future start dates found in the current scan.")
    else:
        st.plotly_chart(charts.forward_start_chart(planned_start_df), use_container_width=True, config=charts.CHART_CONFIG)
with fc2:
    st.markdown("#### Expected Primary Completions")
    if expected_completion_df.empty:
        st.info("No future primary completion dates found in the current scan.")
    else:
        st.plotly_chart(charts.forward_completion_chart(expected_completion_df), use_container_width=True, config=charts.CHART_CONFIG)

section("Sponsor / Competitor Activity", "Lead sponsor concentration across the focused registry scan.")
st.plotly_chart(charts.sponsor_chart(df), use_container_width=True, config=charts.CHART_CONFIG)

section("Clinical Trial Timeline", "Lane-based view of development windows. Hover any bar for NCT ID, sponsor, phase, status, enrollment, country footprint, and combo category.")
st.plotly_chart(charts.timeline_chart(df), use_container_width=True, config=charts.CHART_CONFIG)

section("Signal Feed", "Short observations generated from the structured data layer. This is not an LLM summary, it is a rules-based executive feed.")
render_signal_feed(build_signal_feed(bundle))

section("Evidence Table", "The auditable row-level dataset behind the charts. This is the trust layer.")
cols = ["nct_id", "target_lane", "title", "sponsor", "status", "phase", "study_type", "enrollment", "enrollment_type", "start_date", "primary_completion_date", "completion_date", "countries", "site_count", "indication_hint", "combo_category", "combo_classes", "combo_agents", "combo_confidence", "combo_evidence", "conditions", "interventions", "url"]
st.dataframe(df[cols].sort_values(["target_lane", "sponsor", "phase"]).reset_index(drop=True), use_container_width=True, hide_index=True)
render_footer()

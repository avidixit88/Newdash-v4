import datetime as dt
import re
from typing import Any, Dict, List, Tuple
import pandas as pd
from .config import ACTIVE_STATUSES, PLANNED_STATUSES, TARGET_LANES, COMBO_CLASSIFIERS, COMBO_STRUCTURE_TERMS, TODAY
from .utils import safe_str, get_nested


def normalize_phase(phases: List[str]) -> str:
    """Map ClinicalTrials.gov phase codes into executive-ready labels.

    NA is not a missing phase. It means the study does not use an FDA-style
    drug phase classification. Truly absent phase data is separated so it does
    not look like a normal category.
    """
    if not phases:
        return "Phase Missing From Registry"
    phase_map = {
        "EARLY_PHASE1": "Early Phase 1",
        "PHASE1": "Phase 1",
        "PHASE2": "Phase 2",
        "PHASE3": "Phase 3",
        "PHASE4": "Phase 4",
        "NA": "Not Applicable / Non-phased Study",
    }
    clean = [phase_map.get(str(p).strip().upper(), str(p).replace("_", " ").title()) for p in phases]
    joined = "/".join([c.strip() for c in clean if c.strip()])
    return joined.replace("Phase 1/Phase 2", "Phase 1/2").replace("Phase 2/Phase 3", "Phase 2/3") or "Phase Missing From Registry"


def prettify_status(status: str | None) -> str:
    if not status:
        return "Status not listed"
    return status.replace("_", " ").title().replace("And", "and").replace("By", "by")


def parse_date_struct(module: Dict[str, Any], key: str):
    return get_nested(module, [key, "date"])


def extract_locations(protocol: Dict[str, Any]) -> Tuple[List[str], List[str], int]:
    locs = (protocol.get("contactsLocationsModule", {}) or {}).get("locations", []) or []
    countries, states = [], []
    for loc in locs:
        if isinstance(loc, dict):
            if loc.get("country"):
                countries.append(loc["country"])
            if loc.get("state"):
                states.append(loc["state"])
    return sorted(set(countries)), sorted(set(states)), len(locs)


def extract_arms_and_interventions(protocol: Dict[str, Any]) -> Tuple[List[str], List[str], str]:
    arms = protocol.get("armsInterventionsModule", {}) or {}
    arm_texts = []
    for arm in arms.get("armGroups", []) or []:
        if isinstance(arm, dict):
            arm_texts.append(" ".join([safe_str(arm.get("label")), safe_str(arm.get("description")), safe_str(arm.get("interventionNames"))]))
    names, types = [], []
    for item in arms.get("interventions", []) or []:
        if isinstance(item, dict):
            names.append(safe_str(item.get("name")))
            types.append(safe_str(item.get("type")))
    return names, types, " | ".join([t for t in arm_texts if t])


def parse_study(study: Dict[str, Any], source_query: str) -> Dict[str, Any]:
    protocol = study.get("protocolSection", {}) or {}
    ident = protocol.get("identificationModule", {}) or {}
    status = protocol.get("statusModule", {}) or {}
    sponsor = protocol.get("sponsorCollaboratorsModule", {}) or {}
    design = protocol.get("designModule", {}) or {}
    cond = protocol.get("conditionsModule", {}) or {}
    descr = protocol.get("descriptionModule", {}) or {}
    eligibility = protocol.get("eligibilityModule", {}) or {}
    intervention_names, intervention_types, arm_text = extract_arms_and_interventions(protocol)
    countries, states, site_count = extract_locations(protocol)
    conditions = cond.get("conditions", []) or []
    title = ident.get("briefTitle", "Untitled study")
    text_blob = " ".join([title, safe_str(descr.get("briefSummary", "")), safe_str(conditions), safe_str(intervention_names), arm_text, source_query, safe_str(eligibility.get("eligibilityCriteria", ""))])
    nct_id = ident.get("nctId", "")
    return {
        "nct_id": nct_id,
        "title": title,
        "sponsor": get_nested(sponsor, ["leadSponsor", "name"], "Sponsor not listed"),
        "collaborators": ", ".join([c.get("name", "") for c in sponsor.get("collaborators", []) if isinstance(c, dict)][:5]),
        "status": prettify_status(status.get("overallStatus")),
        "phase": normalize_phase(design.get("phases", []) or []),
        "study_type": design.get("studyType", "Study type not listed"),
        "enrollment": get_nested(design, ["enrollmentInfo", "count"], 0) or 0,
        "enrollment_type": get_nested(design, ["enrollmentInfo", "type"], "Enrollment type not listed") or "Enrollment type not listed",
        "start_date": parse_date_struct(status, "startDateStruct"),
        "primary_completion_date": parse_date_struct(status, "primaryCompletionDateStruct"),
        "completion_date": parse_date_struct(status, "completionDateStruct"),
        "last_update": parse_date_struct(status, "lastUpdateSubmitDateStruct"),
        "conditions": ", ".join(conditions[:8]),
        "interventions": ", ".join([n for n in intervention_names if n][:8]),
        "intervention_types": ", ".join(sorted(set([t for t in intervention_types if t]))),
        "arm_text": arm_text[:1000],
        "countries": ", ".join(countries) if countries else "Location not listed",
        "states": ", ".join(states) if states else "State not listed",
        "site_count": site_count,
        "source_query": source_query,
        "text_blob": text_blob,
        "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
    }


def extract_target_lane(row: pd.Series) -> str:
    text = safe_str(row.get("text_blob", "")).lower()
    for lane, aliases in TARGET_LANES.items():
        if any(alias.lower() in text for alias in aliases):
            return lane
    return "Other / Unclassified"


def extract_indication_hint(text: str) -> str:
    t = safe_str(text).lower()
    if any(x in t for x in ["ovarian", "fallopian", "peritoneal", "endometrial", "cervical", "gynecologic"]): return "Ovarian / Gynecologic"
    if "breast" in t: return "Breast"
    if "lung" in t or "nsclc" in t: return "Lung / NSCLC"
    if "alzheimer" in t or "dementia" in t: return "Alzheimer's"
    if "osteogenesis" in t or "bone" in t or "osteoporosis" in t: return "Bone Disease"
    if "solid" in t or "tumor" in t or "neoplasm" in t: return "Solid Tumor"
    return "Other indication"


def _combo_evidence_text(row: pd.Series) -> str:
    return " ".join([
        safe_str(row.get("title", "")),
        safe_str(row.get("conditions", "")),
        safe_str(row.get("interventions", "")),
        safe_str(row.get("intervention_types", "")),
        safe_str(row.get("arm_text", "")),
        safe_str(row.get("text_blob", "")),
    ])


def _find_combo_hits(row: pd.Series) -> Dict[str, List[str]]:
    text = _combo_evidence_text(row).lower()
    hits: Dict[str, List[str]] = {}
    for category, payload in COMBO_CLASSIFIERS.items():
        matched = []
        for agent in payload.get("agents", []):
            if re.search(r"\b" + re.escape(agent.lower()) + r"\b", text):
                matched.append(agent)
        for term in payload.get("terms", []):
            if term.lower() in text:
                matched.append(term)
        if matched:
            hits[category] = sorted(set([m.strip() for m in matched if m.strip()]))
    return hits


def extract_combo_category(row: pd.Series) -> str:
    hits = _find_combo_hits(row)
    if not hits:
        return "Monotherapy / no partner agent detected"
    if len(hits) == 1:
        return "Combo: " + next(iter(hits.keys()))
    return "Combo: multi-class regimen"


def extract_combo_agents(row: pd.Series) -> str:
    hits = _find_combo_hits(row)
    agents = []
    for category_hits in hits.values():
        for hit in category_hits:
            if len(hit) > 2 and hit not in COMBO_STRUCTURE_TERMS:
                agents.append(hit.title().replace("Pd-1", "PD-1").replace("Pd-L1", "PD-L1"))
    return ", ".join(sorted(set(agents))) if agents else "No named partner agent detected"


def extract_combo_classes(row: pd.Series) -> str:
    hits = _find_combo_hits(row)
    return ", ".join(hits.keys()) if hits else "No partner class detected"


def extract_combo_confidence(row: pd.Series) -> str:
    text = _combo_evidence_text(row).lower()
    hits = _find_combo_hits(row)
    if not hits:
        return "Low: no partner agent/class found"
    has_structure = any(term in text for term in COMBO_STRUCTURE_TERMS)
    agent_count = sum(len(v) for v in hits.values())
    if has_structure and agent_count >= 2:
        return "High: explicit combo language + partner agent/class"
    if agent_count >= 1:
        return "Medium: partner agent/class detected"
    return "Low: weak combo evidence"


def extract_combo_evidence(row: pd.Series) -> str:
    # Keep it short and auditable for the evidence table.
    text = _combo_evidence_text(row)
    hits = _find_combo_hits(row)
    if not hits:
        return "No named partner agent or combination class detected in title/interventions/arms."
    flat = []
    for category, terms in hits.items():
        flat.append(f"{category}: {', '.join(terms[:5])}")
    return " | ".join(flat)[:500]

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["start_date", "primary_completion_date", "completion_date", "last_update"]:
        if c not in df:
            df[c] = pd.NaT
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["enrollment"] = pd.to_numeric(df.get("enrollment", 0), errors="coerce").fillna(0).astype(int)
    df["site_count"] = pd.to_numeric(df.get("site_count", 0), errors="coerce").fillna(0).astype(int)
    df["text_blob"] = df.apply(lambda r: " ".join([safe_str(r.get(c, "")) for c in ["title", "conditions", "interventions", "arm_text", "source_query"]]), axis=1)
    df["target_lane"] = df.apply(extract_target_lane, axis=1)
    df["indication_hint"] = df["conditions"].fillna("Other indication").apply(extract_indication_hint)
    df["is_active"] = df["status"].isin(ACTIVE_STATUSES)
    df["is_planned"] = df["status"].isin(PLANNED_STATUSES) | ((df["start_date"].dt.date >= TODAY) & df["start_date"].notna())
    df["combo_category"] = df.apply(extract_combo_category, axis=1)
    df["combo_classes"] = df.apply(extract_combo_classes, axis=1)
    df["combo_agents"] = df.apply(extract_combo_agents, axis=1)
    df["combo_confidence"] = df.apply(extract_combo_confidence, axis=1)
    df["combo_evidence"] = df.apply(extract_combo_evidence, axis=1)
    df["quarter_start"] = df["start_date"].dt.to_period("Q").astype(str).replace("NaT", "Date not listed")
    df["primary_completion_quarter"] = df["primary_completion_date"].dt.to_period("Q").astype(str).replace("NaT", "Date not listed")
    df["timeline_start"] = df["start_date"].fillna(pd.Timestamp(TODAY - dt.timedelta(days=365)))
    df["timeline_finish"] = df["completion_date"].fillna(df["primary_completion_date"]).fillna(pd.Timestamp(TODAY + dt.timedelta(days=365)))
    return df

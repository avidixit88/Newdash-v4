import datetime as dt

APP_NAME = "NextCure Signal Room"
APP_VERSION = "v1.5 Combo Therapy Intelligence"
API_URL = "https://clinicaltrials.gov/api/v2/studies"
TODAY = dt.date.today()

TARGET_LANES = {
    "B7-H4 / VTCN1": ["B7-H4", "B7H4", "VTCN1", "B7 H4", "LNCB74", "B7-H4 ADC", "anti-B7-H4", "b7 h4"],
    "CDH6": ["CDH6", "cadherin 6", "cadherin-6", "SIM0505", "CDH6 ADC", "anti-CDH6", "raludotatug", "r-dxd", "rdxd", "CUSP06"],
    "Alzheimer's / ApoE4": ["Alzheimer", "Alzheimer's", "ApoE4", "APOE4", "APOE", "NC181"],
    "Bone / Siglec-15": ["osteogenesis imperfecta", "bone disease", "bone", "Siglec-15", "SIGLEC15", "NC605"],
}

PRESET_QUERIES = [
    "B7-H4 OR VTCN1 OR LNCB74 OR B7H4",
    "CDH6 OR cadherin 6 OR SIM0505 OR raludotatug deruxtecan OR CUSP06",
    "Alzheimer ApoE4 OR APOE4 OR NC181",
    "Siglec-15 OR osteogenesis imperfecta OR NC605 bone",
]

PRESET_PAGE_SIZE = 100
ACTIVE_STATUSES = {"Recruiting", "Not yet recruiting", "Active, not recruiting", "Enrolling by invitation"}
PLANNED_STATUSES = {"Not yet recruiting"}
STATUS_FOCUS = ["Recruiting", "Not yet recruiting", "Active, not recruiting", "Enrolling by invitation"]

PHASE_ORDER = [
    "Early Phase 1", "Phase 1", "Phase 1/2", "Phase 2", "Phase 2/3", "Phase 3", "Phase 4",
    "Not Applicable / Non-phased Study", "Phase Missing From Registry"
]

# Clinically meaningful buckets for ADC / oncology trial strategy.
COMBO_CLASSIFIERS = {
    "IO / checkpoint": {
        "agents": ["pembrolizumab", "keytruda", "nivolumab", "opdivo", "atezolizumab", "tecentriq", "durvalumab", "imfinzi", "avelumab", "cemiplimab", "dostarlimab", "balstilimab"],
        "terms": ["pd-1", "pd1", "pd-l1", "pdl1", "checkpoint", "immune checkpoint", "immunotherapy", "anti-pd", "anti pd"],
    },
    "Chemo / platinum / taxane": {
        "agents": ["carboplatin", "cisplatin", "oxaliplatin", "paclitaxel", "docetaxel", "nab-paclitaxel", "gemcitabine", "doxorubicin", "liposomal doxorubicin", "topotecan", "pemetrexed", "capecitabine", "eribulin", "irinotecan", "etoposide"],
        "terms": ["chemotherapy", "platinum", "taxane", "standard chemotherapy", "standard of care chemotherapy"],
    },
    "Anti-VEGF / angiogenesis": {
        "agents": ["bevacizumab", "avastin", "cediranib", "ramucirumab", "aflibercept"],
        "terms": ["anti-vegf", "vegf", "angiogenesis"],
    },
    "PARP / DNA damage": {
        "agents": ["olaparib", "lynparza", "niraparib", "zejula", "rucaparib", "talazoparib", "veliparib", "berzosertib", "adavosertib"],
        "terms": ["parp", "dna damage", "ddr", "atr inhibitor", "wee1 inhibitor"],
    },
    "HER2 / EGFR / targeted pathway": {
        "agents": ["trastuzumab", "herceptin", "pertuzumab", "perjeta", "tucatinib", "lapatinib", "osimertinib", "erlotinib", "gefitinib", "cetuximab", "panitumumab", "selpercatinib", "larotrectinib", "entrectinib", "alpelisib", "capivasertib"],
        "terms": ["her2", "egfr", "ret inhibitor", "ntrk", "pi3k", "akt inhibitor", "targeted therapy"],
    },
    "Endocrine / hormonal": {
        "agents": ["letrozole", "anastrozole", "exemestane", "fulvestrant", "tamoxifen", "elacestrant", "goserelin"],
        "terms": ["endocrine", "hormonal therapy", "estrogen receptor", "er-positive", "er positive"],
    },
    "Radiation / radiopharmaceutical": {
        "agents": ["lutetium", "actinium", "radium", "iodine i-131", "external beam radiation"],
        "terms": ["radiation", "radiotherapy", "radiopharmaceutical", "radioligand"],
    },
    "ADC / multi-ADC strategy": {
        "agents": ["trastuzumab deruxtecan", "enhertu", "sacituzumab govitecan", "trodelvy", "datopotamab deruxtecan", "dato-dxd", "raludotatug deruxtecan", "r-dxd", "mirvetuximab soravtansine", "elrema", "adc"],
        "terms": ["antibody-drug conjugate", "antibody drug conjugate", "adc plus", "adc in combination", "dual-payload adc", "multi-adc"],
    },
}

COMBO_STRUCTURE_TERMS = [
    "combination", "combined with", "in combination with", "plus", "added to", "with pembrolizumab", "with chemotherapy", "co-administered", "coadministered", "partner agent"
]

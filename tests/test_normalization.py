from src.normalization import extract_indication_hint, clean_df
from src.sample_data import sample_trials_raw


def test_indication_classification():
    assert extract_indication_hint("platinum resistant ovarian cancer") == "Ovarian / Gynecologic"
    assert extract_indication_hint("Alzheimer Disease") == "Alzheimer's"
    assert extract_indication_hint("osteogenesis imperfecta") == "Bone Disease"


def test_sample_data_cleans():
    df = clean_df(sample_trials_raw())
    assert "target_lane" in df.columns
    assert "combo_category" in df.columns
    assert len(df) >= 1

import pandas as pd
from typing import List, Dict


def load_services(path: str = "data/services_sample.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize language column into list
    df["languages_list"] = df["languages"].apply(
        lambda x: [l.strip() for l in str(x).split(";")]
    )
    return df


def retrieve_services(
    df: pd.DataFrame,
    needs: List[str],
    language: str,
    age_group: str,
) -> List[Dict]:
    """
    Simple tag-based retrieval:
    - category matches one of the needs
    - language matches or falls back to English
    - age_group roughly compatible (or 'all')
    """

    # Filter by category / need
    filtered = df[df["category"].isin(needs)].copy()

    # Language filter with English fallback
    def lang_ok(row):
        langs = row["languages_list"]
        return (language in langs) or ("English" in langs)

    filtered = filtered[filtered.apply(lang_ok, axis=1)]

    # Age filter (rough for MVP)
    def age_ok(row):
        if row["target_age"] == "all":
            return True
        if row["target_age"] == "18+" and age_group in ["18-29", "30-54", "55+"]:
            return True
        if row["target_age"] == age_group:
            return True
        return False

    filtered = filtered[filtered.apply(age_ok, axis=1)]

    # Limit to top N for readability
    top = filtered.head(5)

    # Convert to list of dicts for the LLM
    return top.to_dict(orient="records")

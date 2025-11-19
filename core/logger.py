import csv
import os
from datetime import datetime
from typing import Dict, List


LOG_PATH = os.path.join("data", "interaction_log.csv")


def ensure_log_file_exists():
    """
    Create the CSV file with header if it does not already exist.
    """
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "interaction_id",
                "timestamp",
                "site",
                "age_group",
                "language",
                "housing_status",
                "needs",
                "service_ids_kept",
                "service_ids_removed",
                "num_services_kept",
            ])


def log_interaction(
    visitor_context: Dict,
    kept_services: List[Dict],
    removed_ids: List,
    site: str = "NFCM",
) -> None:
    """
    Append one interaction row to the CSV log.

    visitor_context: e.g. {
        "age_group": "18-29",
        "language": "Cree",
        "housing_status": "Homeless / unstably housed",
        "needs": ["food", "housing"]
    }

    kept_services: list of service dicts (each has 'id', 'name', etc.)
    removed_ids: list of service IDs that were unchecked.
    """
    ensure_log_file_exists()

    # Build values
    timestamp = datetime.now().isoformat(timespec="seconds")
    interaction_id = f"{timestamp}_{len(kept_services)}"  # simple unique-ish id

    age_group = visitor_context.get("age_group", "")
    language = visitor_context.get("language", "")
    housing = visitor_context.get("housing_status", "")
    needs_list = visitor_context.get("needs", [])
    needs_str = ";".join(needs_list)

    kept_ids = [str(svc.get("id")) for svc in kept_services]
    kept_ids_str = ";".join(kept_ids)

    removed_ids_str = ";".join(str(rid) for rid in removed_ids)
    num_services_kept = len(kept_services)

    row = [
        interaction_id,
        timestamp,
        site,
        age_group,
        language,
        housing,
        needs_str,
        kept_ids_str,
        removed_ids_str,
        num_services_kept,
    ]

    # Append to CSV
    with open(LOG_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

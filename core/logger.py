from datetime import datetime
from typing import Dict, List
import logging

from core.google_sheets import append_interaction_row


def log_interaction(
    visitor_context: Dict,
    kept_services: List[Dict],
    removed_ids: List,
    site: str = "NFCM",
) -> None:
    """
    Log one interaction to Google Sheets (interactions worksheet).

    Columns:
    interaction_id, timestamp, site, age_group, language, housing_status,
    needs, service_ids_kept, service_ids_removed, num_services_kept
    """
    timestamp = datetime.now().isoformat(timespec="seconds")
    interaction_id = f"{timestamp}_{len(kept_services)}"

    age_group = visitor_context.get("age_group", "")
    language = visitor_context.get("language", "")
    housing = visitor_context.get("housing_status", "")
    needs_str = ";".join(visitor_context.get("needs", []))

    kept_ids_str = ";".join(str(svc.get("id")) for svc in kept_services)
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

    try:
        append_interaction_row(row)
        logging.info("Logged interaction to Google Sheets: %s", row)
    except Exception as e:
        # Don't crash the app if logging fails; just print error.
        logging.exception("Failed to log interaction to Google Sheets: %s", e)

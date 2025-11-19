import csv
from datetime import datetime
from typing import List, Dict
import os

LOG_PATH = "interaction_logs.csv"


def init_log_file():
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "age_group",
                    "language",
                    "needs",
                    "housing_status",
                    "recommended_service_ids",
                    "removed_service_ids",
                ]
            )


def log_interaction(
    visitor_context: Dict,
    recommended_services: List[Dict],
    removed_ids: List[int],
):
    init_log_file()
    with open(LOG_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                datetime.utcnow().isoformat(),
                visitor_context["age_group"],
                visitor_context["language"],
                ";".join(visitor_context["needs"]),
                visitor_context.get("housing_status", ""),
                ";".join(str(s["id"]) for s in recommended_services),
                ";".join(str(rid) for rid in removed_ids),
            ]
        )

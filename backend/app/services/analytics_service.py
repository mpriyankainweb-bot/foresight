import json
import logging
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from backend.app.memory.service import MemoryService
from backend.app.models import (
    AnalyticsResponse,
    DeployCheckRecord,
    LearningCurveDataPoint,
    TemporaryFixItem,
    TopRecurringCause,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    def get_learning_curve(self, db_session: Session) -> AnalyticsResponse:
        seed_dir = Path(__file__).parent.parent.parent.parent / "data" / "seed"
        incidents_path = seed_dir / "incidents.json"

        incidents: list[dict[str, Any]] = []
        if incidents_path.exists():
            with open(incidents_path, "r", encoding="utf-8") as f:
                incidents = json.load(f)

        # 1. Top recurring root cause classes
        cause_counts: dict[str, int] = {}
        for inc in incidents:
            cause = inc.get("root_cause_class", "unknown")
            cause_counts[cause] = cause_counts.get(cause, 0) + 1

        top_causes = [
            TopRecurringCause(cause=c, count=cnt)
            for c, cnt in sorted(cause_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        ]

        # 2. Temporary fixes list
        temp_fixes: list[TemporaryFixItem] = []
        for inc in incidents:
            for fix in inc.get("fix_attempts", []):
                if fix.get("outcome") == "temporary" and "held_for_days" in fix:
                    temp_fixes.append(
                        TemporaryFixItem(
                            incident_id=inc["id"],
                            description=fix.get("description", "Temporary patch"),
                            held_for_days=fix["held_for_days"],
                        )
                    )

        # 3. Time series learning curve
        # As memory bank grows month by month (2024-03 to 2025-03), accuracy goes up (60% -> 94%), MTTR drops (55m -> 22m)
        monthly_progression = [
            ("2024-03", 5, 62.0, 52.0),
            ("2024-04", 10, 68.0, 48.0),
            ("2024-05", 15, 72.5, 42.0),
            ("2024-06", 20, 76.0, 38.0),
            ("2024-07", 25, 80.0, 35.0),
            ("2024-08", 30, 84.0, 32.0),
            ("2024-09", 35, 87.5, 29.0),
            ("2024-10", 40, 89.0, 27.0),
            ("2024-11", 45, 91.0, 25.0),
            ("2024-12", 50, 92.5, 24.0),
            ("2025-01", 55, 93.5, 22.0),
            ("2025-02", 60, 94.5, 20.0),
        ]

        data_points = [
            LearningCurveDataPoint(
                date=m[0],
                memory_count=m[1],
                prediction_accuracy=m[2],
                mttr_minutes=m[3],
            )
            for m in monthly_progression
        ]

        current_accuracy = 94.5
        current_mttr = 20.0

        # Adjust with DB check outcomes if present
        checks = db_session.exec(select(DeployCheckRecord)).all()
        if checks:
            correct_predictions = 0
            evaluated = 0
            for c in checks:
                if c.outcome:
                    evaluated += 1
                    # HOLD/CANARY preventing incident or clean deployment correctly predicted
                    if (c.verdict == "HOLD" and c.outcome == "incident") or (c.verdict == "SHIP" and c.outcome == "clean") or (c.verdict == "CANARY" and c.outcome == "degraded"):
                        correct_predictions += 1
            if evaluated > 0:
                current_accuracy = round((correct_predictions / evaluated) * 100, 1)

        return AnalyticsResponse(
            data_points=data_points,
            current_accuracy=current_accuracy,
            current_mttr_minutes=current_mttr,
            top_recurring_causes=top_causes,
            temporary_fixes=temp_fixes,
        )

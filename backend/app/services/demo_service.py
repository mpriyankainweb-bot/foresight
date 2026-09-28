import json
import logging
from pathlib import Path
from typing import Any

from backend.app.memory.service import MemoryService
from backend.app.models.schema import (
    DemoReplayResponse,
    DemoResetResponse,
    DeployOutcomeRequest,
    DeployOutcomeResponse,
    LearningCurveDataPoint,
    LearningCurveResponse,
)

logger = logging.getLogger(__name__)

class DemoService:
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self._outcomes_history: list[dict[str, Any]] = []

    def replay_seed_data(self) -> DemoReplayResponse:
        seed_dir = Path(__file__).parent.parent.parent.parent / "data" / "seed"
        incidents_path = seed_dir / "incidents.json"
        deploys_path = seed_dir / "deploys.json"

        incidents_count = 0
        deploys_count = 0

        if incidents_path.exists():
            with open(incidents_path, "r") as f:
                incidents = json.load(f)
                for inc in incidents:
                    doc_id = f"inc-{inc['id']}"
                    content = (
                        f"INCIDENT POSTMORTEM: {inc['title']}\n"
                        f"Date: {inc['date']} | Service: {inc['service']} | Severity: {inc['severity']}\n"
                        f"Root cause class: {inc['root_cause_class']}\n"
                        f"Alert: {inc['alert_text']}\n"
                        f"Error logs:\n{inc.get('error_logs', '')}\n"
                        f"Slack War Room: {inc.get('slack_excerpt', '')}\n"
                        f"Fix attempts: {json.dumps(inc.get('fix_attempts', []))}\n"
                        f"Resolution time: {inc.get('resolution_time_minutes', 0)} mins"
                    )
                    self.memory_service.retain(
                        content=content,
                        document_id=doc_id,
                        tags=[inc["service"], inc["severity"], inc["root_cause_class"]],
                        metadata={
                            "title": inc["title"],
                            "date": inc["date"],
                            "service": inc["service"],
                            "severity": inc["severity"],
                        },
                    )
                    incidents_count += 1

        if deploys_path.exists():
            with open(deploys_path, "r") as f:
                deploys = json.load(f)
                for dep in deploys:
                    doc_id = f"dep-{dep['id']}"
                    content = (
                        f"DEPLOY RECORD: {dep['title']}\n"
                        f"Service: {dep['service']} | Author: {dep['author']} | Env: {dep['environment']}\n"
                        f"Date: {dep['date']}\n"
                        f"Config changes: {', '.join(dep.get('config_changes', []))}\n"
                        f"Outcome: {dep['outcome']}"
                    )
                    self.memory_service.retain(
                        content=content,
                        document_id=doc_id,
                        tags=[dep["service"], dep["environment"], dep["outcome"]],
                        metadata={
                            "title": dep["title"],
                            "date": dep["date"],
                            "service": dep["service"],
                            "outcome": dep["outcome"],
                        },
                    )
                    deploys_count += 1

        backend_str = "hindsight" if self.memory_service.is_live() else "mock"
        return DemoReplayResponse(
            status="success",
            incidents_retained=incidents_count,
            deploys_retained=deploys_count,
            memory_backend=backend_str,
        )

    def reset_demo(self) -> DemoResetResponse:
        self._outcomes_history.clear()
        return DemoResetResponse(
            status="success",
            message="Demo state reset successfully.",
        )

    def record_deploy_outcome(
        self, check_id: str, req: DeployOutcomeRequest
    ) -> DeployOutcomeResponse:
        doc_id = f"outcome-{check_id}"
        content = (
            f"DEPLOY CHECK VERDICT OUTCOME for {check_id}\n"
            f"Actual outcome observed: {req.outcome.value}\n"
            f"Engineer notes: {req.notes or 'None'}"
        )
        self.memory_service.retain(
            content=content,
            document_id=doc_id,
            tags=["deploy-outcome", req.outcome.value],
            metadata={"check_id": check_id, "outcome": req.outcome.value},
        )
        self._outcomes_history.append({"check_id": check_id, "outcome": req.outcome, "notes": req.notes})

        return DeployOutcomeResponse(
            check_id=check_id,
            outcome=req.outcome,
            retained=True,
            status="recorded_and_retained",
        )

    def get_learning_curve(self) -> LearningCurveResponse:
        # Pre-calculated timeline showing risk prediction accuracy up and MTTR down as memory grows
        series_data = [
            LearningCurveDataPoint(date="2024-03-01", accuracy=62.0, mttr_minutes=52.0, memories_count=5),
            LearningCurveDataPoint(date="2024-06-01", accuracy=71.5, mttr_minutes=40.0, memories_count=15),
            LearningCurveDataPoint(date="2024-09-01", accuracy=83.0, mttr_minutes=35.0, memories_count=30),
            LearningCurveDataPoint(date="2024-12-01", accuracy=89.0, mttr_minutes=25.0, memories_count=48),
            LearningCurveDataPoint(date="2025-03-01", accuracy=95.4, mttr_minutes=14.2, memories_count=60),
        ]

        total_mems = 60 + len(self._outcomes_history)
        return LearningCurveResponse(
            series=series_data,
            current_accuracy=95.4,
            current_mttr=14.2,
            total_memories=total_mems,
        )

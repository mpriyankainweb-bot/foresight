import json
import logging
from pathlib import Path
from typing import Any
from sqlmodel import Session, delete

from backend.app.models import DemoReplayResponse, DemoResetResponse, DeployCheckRecord, DeployOutcomeRecord
from backend.app.memory.service import MemoryService

logger = logging.getLogger(__name__)


class DemoService:
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service

    def replay_demo(self, db_session: Session) -> DemoReplayResponse:
        seed_dir = Path(__file__).parent.parent.parent.parent / "data" / "seed"
        incidents_path = seed_dir / "incidents.json"
        deploys_path = seed_dir / "deploys.json"

        incidents: list[dict[str, Any]] = []
        deploys: list[dict[str, Any]] = []

        if incidents_path.exists():
            with open(incidents_path, "r", encoding="utf-8") as f:
                incidents = json.load(f)

        if deploys_path.exists():
            with open(deploys_path, "r", encoding="utf-8") as f:
                deploys = json.load(f)

        # Clear memory first to ensure clean replay
        self.memory_service.reset()

        # Combine into timeline
        timeline: list[dict[str, Any]] = []

        for inc in incidents:
            timeline.append({
                "type": "incident",
                "date": inc["date"],
                "data": inc,
            })

        for dep in deploys:
            timeline.append({
                "type": "deploy",
                "date": dep["date"],
                "data": dep,
            })

        # Sort chronologically
        timeline.sort(key=lambda x: x["date"])

        incidents_count = 0
        deploys_count = 0

        for event in timeline:
            if event["type"] == "incident":
                inc = event["data"]
                content = (
                    f"Incident {inc['id']}: {inc['title']}. Root cause: {inc['root_cause_class']}. "
                    f"Service: {inc['service']}. Alert: {inc['alert_text']}. "
                    f"Error logs: {inc.get('error_logs', '')}. Slack: {inc.get('slack_excerpt', '')}. "
                    f"Fix attempts: {json.dumps(inc.get('fix_attempts', []))}"
                )
                tags = [inc["service"], inc["severity"], inc["root_cause_class"]]
                metadata = {
                    "id": inc["id"],
                    "title": inc["title"],
                    "date": inc["date"],
                    "type": "incident",
                    "service": inc["service"],
                    "severity": inc["severity"],
                    "root_cause_class": inc["root_cause_class"],
                    "fix_attempts": inc.get("fix_attempts", []),
                }
                self.memory_service.retain(
                    content=content,
                    document_id=inc["id"],
                    tags=tags,
                    metadata=metadata,
                )
                incidents_count += 1
            else:
                dep = event["data"]
                config_str = ", ".join(dep.get("config_changes", []))
                content = (
                    f"Deploy {dep['id']}: {dep['title']}. Service: {dep['service']}. "
                    f"Environment: {dep['environment']}. Config changes: [{config_str}]. "
                    f"Author: {dep.get('author', 'Unknown')}. Outcome: {dep['outcome']}."
                )
                tags = [dep["service"], dep["environment"], dep["outcome"]]
                metadata = {
                    "id": dep["id"],
                    "title": dep["title"],
                    "date": dep["date"],
                    "type": "deploy",
                    "service": dep["service"],
                    "outcome": dep["outcome"],
                }
                self.memory_service.retain(
                    content=content,
                    document_id=dep["id"],
                    tags=tags,
                    metadata=metadata,
                )
                deploys_count += 1

        total = incidents_count + deploys_count
        logger.info(f"Replayed {total} historical events into memory")

        return DemoReplayResponse(
            status="completed",
            total_retained=total,
            incidents_retained=incidents_count,
            deploys_retained=deploys_count,
            message=f"Replayed {total} historical events into Hindsight memory in chronological order.",
        )

    def reset_demo(self, db_session: Session) -> DemoResetResponse:
        # Reset memory bank
        self.memory_service.reset()

        # Reset database tables
        db_session.exec(delete(DeployOutcomeRecord))  # type: ignore
        db_session.exec(delete(DeployCheckRecord))  # type: ignore
        db_session.commit()

        logger.info("Demo state reset successfully")
        return DemoResetResponse(
            status="reset",
            message="Demo state reset successfully. Memory and check records cleared.",
        )

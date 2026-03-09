from dataclasses import dataclass
import json
from typing import Any

@dataclass
class WikipediaPageChangeRecord:
    change_id: int | None
    revision_id_old: int | None
    revision_id_new: int | None
    title: str | None
    timestamp: str | None
    user: str | None
    comment: str | None
    old_length: int | None
    new_length: int | None    
    tags: list[str]
    log_type: str | None
    log_action: str | None
    raw_json: str

    @staticmethod
    def from_dict(change: dict[str, Any]) -> "WikipediaPageChangeRecord":
        return WikipediaPageChangeRecord(
            change_id=change.get("rcid"),
            revision_id_old=change.get("old_revid"),
            revision_id_new=change.get("revid"),
            title=change.get("title"),
            timestamp=change.get("timestamp"),
            user=change.get("user"),
            comment=change.get("comment"),
            old_length=change.get("oldlen"),
            new_length=change.get("newlen"),            
            tags=change.get("tags") or [],
            log_type=change.get("logtype"),
            log_action=change.get("logaction"),
            raw_json=json.dumps(change, separators=(",", ":")),
        )



@dataclass
class GithubEvent:
    event_id: str
    event_type: str
    created_at: str
    actor_id: int
    actor_login: str
    repo_id: int
    repo_name: str
    is_public: bool
    event_json: str

    @staticmethod
    def from_dict(event: dict) -> "GithubEvent":
        actor = event.get("actor") or {}
        repo = event.get("repo") or {}
        return GithubEvent(
            event_id=str(event.get("id")),
            event_type=event.get("type"),
            created_at=event.get("created_at"),
            actor_id=actor.get("id"),
            actor_login=actor.get("login"),
            repo_id=repo.get("id"),
            repo_name=repo.get("name"),
            is_public=event.get("public"),
            event_json=json.dumps(event, separators=(",", ":")),
        )
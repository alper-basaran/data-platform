from __future__ import annotations
from datetime import datetime, timezone

from job.core.event import WikipediaPageChangeRecord
from typing import Any
from job.lib.logger import configure_logging, get_logger

_logger = get_logger(__name__)

from requests_ratelimiter import LimiterSession

PROPS = ["ids", "title", "timestamp", "user", "comment", "sizes", "flags", "loginfo", "tags"]
RESTRICT_LIST = ["anon", "bot"]

class WikipediaClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 30,        
        session: LimiterSession | None = None,
    ) -> None:
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        
        if session is None:
            raise ValueError("A LimiterSession instance must be provided.")
        
        self._session = session
        self._session.headers.update({"User-Agent": "wikipedia-elt-extractor/1.0 (https://github.com/alper-basaran/)"})

    @staticmethod
    def _to_wiki_timestamp(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_changes_page(
        self,
        interval_start: datetime,
        interval_end: datetime,
        limit: int = 100,                
        continuation_token: str | None = None,
        type: list[str] | None = None,
    ) -> tuple[list[WikipediaPageChangeRecord], str | None]:
        
        params: dict[str, Any] = {
            "action": "query",
            "list": "recentchanges",
            "rclimit": limit,
            "rcshow": "|".join(f"!{item}" for item in RESTRICT_LIST),
            "rcprop": "|".join(PROPS),
            "rcstart": self._to_wiki_timestamp(interval_start),
            "rcend": self._to_wiki_timestamp(interval_end),
            "rcdir": "newer",
            "format": "json",
        }
        if continuation_token:
            params["rccontinue"] = continuation_token
        
        if type:
            params["rctype"] = "|".join(type)

        response = self._session.get(
            self._base_url,
            params=params,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()

        payload = response.json()
        query_obj = payload.get("query")

        if not isinstance(query_obj, dict):
            raise ValueError(
                f"Expected Wikipedia API response to contain 'query' object, got {type(query_obj).__name__} instead."
            )

        changes = query_obj.get("recentchanges")
        if not isinstance(changes, list):
            raise ValueError(
                f"Expected Wikipedia 'recentchanges' to be a list, got {type(changes).__name__} instead."
            )

        next_continue: str | None = None
        continue_obj = payload.get("continue")
        if isinstance(continue_obj, dict):
            next_continue = continue_obj.get("rccontinue")

        return [WikipediaPageChangeRecord.from_dict(change) for change in changes], next_continue

    def get_changes_for_interval(
        self,
        interval_start: datetime,
        interval_end: datetime,
        page_limit: int = 100,
        max_pages: int | None = None,
        type: list[str] | None = None,
    ) -> list[WikipediaPageChangeRecord]:
        
        all_changes: list[WikipediaPageChangeRecord] = []
        continuation_token: str | None = None
        pages_fetched = 0

        while True:            
            _logger.info(
                f"Fetching page {pages_fetched + 1} of Wikipedia changes for interval "
                f"{interval_start} to {interval_end}"
            )

            changes, next_token = self.get_changes_page(
                interval_start=interval_start,
                interval_end=interval_end,
                limit=page_limit,
                continuation_token=continuation_token,
                type=type,
            )
            all_changes.extend(changes)
            pages_fetched += 1

            if not next_token:
                break
            if max_pages is not None and pages_fetched >= max_pages:
                _logger.warning(
                    f"Reached max_pages limit of {max_pages}, stopping pagination early." \
                    + f" Fetched {pages_fetched} pages and {len(all_changes)} changes so far."
                )
                break

            continuation_token = next_token

        return all_changes
    

    

if __name__== "__main__":
    configure_logging()

    client = WikipediaClient(
        base_url="https://en.wikipedia.org/w/api.php",
        session=LimiterSession(per_second=5),
    )
    
    start_time = datetime(2026, 3, 1, 13, 0, 0)
    end_time = datetime(2026, 3, 1, 14, 0, 0)
    
    all_changes = client.get_changes_for_interval(
        interval_start=start_time,
        interval_end=end_time,
        page_limit=500,
        max_pages=50,
        type=["new", "edit"]
    )
        
    for change in all_changes:
        print(change)
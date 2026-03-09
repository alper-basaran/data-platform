from sched import Event
from typing import Any
from urllib.parse import quote
import requests
from job.core.event import GithubEvent


class GitHubClient:
	def __init__(
		self,
		token: str | None = None,
		base_url: str = "https://api.github.com",
		timeout_seconds: int = 30,
	) -> None:
		
		self._base_url = base_url.rstrip("/")
		self._timeout_seconds = timeout_seconds
		self._session = requests.Session()
		self._session.headers.update(
			{
				"Accept": "application/vnd.github+json",
				"X-GitHub-Api-Version": "2022-11-28",
				"User-Agent": "github-extract-service",
			}
		)
		if token:
			self._session.headers.update({"Authorization": f"Bearer {token}"})

	def get_events(self, per_page: int = 30, page: int = 1) -> list[GithubEvent]:
		response = self._session.get(
			f"{self._base_url}/events",
			params={"per_page": per_page, "page": page},
			timeout=self._timeout_seconds,
		)
		response.raise_for_status()
		
		payload = response.json()
		if not isinstance(payload, list):
			raise ValueError(f"Expected GitHub /events response to be a list, got {type(payload).__name__} instead.")
		
		return [GithubEvent.from_dict(event) for event in payload]

if __name__ == "__main__":	
	import os
	
	token = None  # Allow unauthenticated access for testing, but note that it will be rate-limited by GitHub.
	token = os.environ.get("GITHUB_TOKEN")
	client = GitHubClient(token=token)
	
	events = client.get_events(per_page=100)	
	first_seen = set([event.created_at for event in events])
	
	events = client.get_events(per_page=100, page=2)
	second_seen = set([event.created_at for event in events])
	
	pass
	# print(f"Fetched {len(events)} events:")
	
	# for event in events:
	#     print(f"- {event.event_type} by {event.actor_login}")

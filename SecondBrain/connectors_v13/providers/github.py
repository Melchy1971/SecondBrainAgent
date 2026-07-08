class GitHubConnector:
    id = "github"

    def fetch_delta(self, cursor=None) -> list[dict]:
        return [
            {"type": "repository_event", "id": "gh-demo-1", "repo": "SecondBrain-Agent", "cursor": cursor}
        ]

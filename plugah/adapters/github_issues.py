from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx

from .base import ToolAdapter


class GitHubIssuesAdapter(ToolAdapter):
    def __init__(self) -> None:
        self._token = os.getenv("GITHUB_TOKEN", "")
        self._owner = os.getenv("GITHUB_REPO_OWNER", "")
        self._repo = os.getenv("GITHUB_REPO_NAME", "")
        self._dry = os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes"}

    def capabilities(self) -> List[str]:
        return ["create_issue", "list_issues"]

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def dry_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action")
        if action == "create_issue":
            return {
                "dry_run": True,
                "action": action,
                "owner": payload.get("owner") or self._owner,
                "repo": payload.get("repo") or self._repo,
                "title": payload.get("title"),
                "body": payload.get("body", ""),
            }
        elif action == "list_issues":
            return {
                "dry_run": True,
                "action": action,
                "owner": payload.get("owner") or self._owner,
                "repo": payload.get("repo") or self._repo,
            }
        else:
            return {"dry_run": True, "error": f"unknown action: {action}"}

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self._dry or not (self._token and self._owner and self._repo):
            return self.dry_run(payload)

        action = payload.get("action")
        owner = payload.get("owner") or self._owner
        repo = payload.get("repo") or self._repo

        try:
            if action == "create_issue":
                title = payload["title"]
                body = payload.get("body", "")
                url = f"https://api.github.com/repos/{owner}/{repo}/issues"
                resp = httpx.post(url, headers=self._headers(), json={"title": title, "body": body})
                if resp.status_code >= 400:
                    return {"error": f"github error {resp.status_code}", "detail": resp.text}
                data = resp.json()
                return {"number": data.get("number"), "html_url": data.get("html_url")}
            elif action == "list_issues":
                url = f"https://api.github.com/repos/{owner}/{repo}/issues"
                resp = httpx.get(url, headers=self._headers())
                if resp.status_code >= 400:
                    return {"error": f"github error {resp.status_code}", "detail": resp.text}
                items = resp.json()
                return {
                    "count": len(items),
                    "issues": [
                        {"number": it.get("number"), "title": it.get("title")} for it in items
                    ],
                }
            else:
                return {"error": f"unknown action: {action}"}
        except Exception as e:
            return {"error": f"exception: {e}"}


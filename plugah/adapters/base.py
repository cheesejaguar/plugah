"""
Tool adapter base interfaces and a simple registry for the MVP.
"""

from __future__ import annotations

import os
from typing import Any, Protocol


class ToolAdapter(Protocol):
    def capabilities(self) -> list[str]:
        ...

    def dry_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, ToolAdapter] = {}

    def register(self, name: str, adapter: ToolAdapter) -> None:
        self._adapters[name] = adapter

    def get(self, name: str) -> ToolAdapter | None:
        return self._adapters.get(name)

    @classmethod
    def default(cls) -> ToolRegistry:
        from .gdrive_docs import GDriveDocsAdapter
        from .github_issues import GitHubIssuesAdapter

        reg = cls()
        reg.register("github_issues", GitHubIssuesAdapter())
        reg.register("gdrive_docs", GDriveDocsAdapter())
        return reg

    @staticmethod
    def is_dry_run() -> bool:
        return os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes"}


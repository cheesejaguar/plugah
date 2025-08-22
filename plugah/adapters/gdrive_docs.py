from __future__ import annotations

import json
import os
from typing import Any

import httpx

from .base import ToolAdapter


class GDriveDocsAdapter(ToolAdapter):
    def __init__(self) -> None:
        self._dry = os.getenv("DRY_RUN", "").lower() in {"1", "true", "yes"}
        self._parent = os.getenv("GDRIVE_PARENT_FOLDER_ID", "")
        self._cred_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
        self._access_token: str | None = None
        if self._cred_path and os.path.exists(self._cred_path):
            try:
                data = json.loads(open(self._cred_path).read())
                tok = data.get("access_token") or data.get("token")
                if tok:
                    self._access_token = tok
            except Exception:
                self._access_token = None

    def capabilities(self) -> list[str]:
        return ["create_doc"]

    def dry_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "dry_run": True,
            "action": payload.get("action"),
            "parent_folder_id": payload.get("parent_folder_id") or self._parent,
            "title": payload.get("title"),
        }

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._dry or not (self._access_token and self._parent):
            return self.dry_run(payload)

        action = payload.get("action")
        if action != "create_doc":
            return {"error": f"unknown action: {action}"}

        title = payload.get("title", "Untitled")
        meta = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [payload.get("parent_folder_id") or self._parent],
        }
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        try:
            resp = httpx.post(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params={"fields": "id,name"},
                json=meta,
            )
            if resp.status_code >= 400:
                return {"error": f"gdrive error {resp.status_code}", "detail": resp.text}
            data = resp.json()
            return {"id": data.get("id"), "name": data.get("name"), "note": "metadata-only"}
        except Exception as e:
            return {"error": f"exception: {e}"}


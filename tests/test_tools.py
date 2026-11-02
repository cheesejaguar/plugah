import json

import httpx
import pytest

from plugah.adapters.base import ToolRegistry
from plugah.adapters.gdrive_docs import GDriveDocsAdapter
from plugah.adapters.github_issues import GitHubIssuesAdapter


@pytest.fixture
def clean_env(monkeypatch):
    for var in (
        "DRY_RUN",
        "GITHUB_TOKEN",
        "GITHUB_REPO_OWNER",
        "GITHUB_REPO_NAME",
        "GDRIVE_PARENT_FOLDER_ID",
        "GOOGLE_CREDENTIALS_PATH",
    ):
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


class _NoNetwork:
    def __init__(self, monkeypatch):
        def fail(*args, **kwargs):  # pragma: no cover - must not be hit
            raise AssertionError("unexpected network call")

        monkeypatch.setattr(httpx, "post", fail)
        monkeypatch.setattr(httpx, "get", fail)


def test_dry_run_behavior(clean_env):
    clean_env.setenv("DRY_RUN", "true")
    clean_env.setenv("GITHUB_TOKEN", "t")
    clean_env.setenv("GITHUB_REPO_OWNER", "acme")
    clean_env.setenv("GITHUB_REPO_NAME", "widgets")
    _NoNetwork(clean_env)

    reg = ToolRegistry.default()
    assert ToolRegistry.is_dry_run() is True
    gh = reg.get("github_issues")
    gd = reg.get("gdrive_docs")

    # DRY_RUN wins even when credentials are configured
    res_gh = gh.run({"action": "create_issue", "title": "Test", "body": "Body"})  # type: ignore[union-attr]
    assert res_gh == {
        "dry_run": True,
        "action": "create_issue",
        "owner": "acme",
        "repo": "widgets",
        "title": "Test",
        "body": "Body",
    }

    res_gd = gd.run({"action": "create_doc", "title": "Doc", "markdown_body": "# x"})  # type: ignore[union-attr]
    assert res_gd == {
        "dry_run": True,
        "action": "create_doc",
        "parent_folder_id": "",
        "title": "Doc",
    }


def test_missing_credentials_fall_back_to_dry_run(clean_env):
    _NoNetwork(clean_env)
    gh = GitHubIssuesAdapter()
    assert gh.run({"action": "list_issues", "owner": "o", "repo": "r"}) == {
        "dry_run": True,
        "action": "list_issues",
        "owner": "o",
        "repo": "r",
    }
    assert gh.run({"action": "bogus"}) == {"dry_run": True, "error": "unknown action: bogus"}

    gd = GDriveDocsAdapter()
    assert gd.run({"action": "create_doc", "title": "T"})["dry_run"] is True


class _Recorder:
    """Stands in for the GitHub / Google Drive HTTP APIs (external boundary)."""

    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def _github_env(env):
    env.setenv("GITHUB_TOKEN", "gh-test-token")
    env.setenv("GITHUB_REPO_OWNER", "acme")
    env.setenv("GITHUB_REPO_NAME", "widgets")


def test_github_create_issue_request_and_response(clean_env):
    _github_env(clean_env)
    rec = _Recorder(httpx.Response(201, json={"number": 7, "html_url": "https://gh/7", "x": 1}))
    clean_env.setattr(httpx, "post", rec)

    res = GitHubIssuesAdapter().run({"action": "create_issue", "title": "Bug", "body": "B"})

    assert res == {"number": 7, "html_url": "https://gh/7"}
    url, kwargs = rec.calls[0]
    assert url == "https://api.github.com/repos/acme/widgets/issues"
    assert kwargs["json"] == {"title": "Bug", "body": "B"}
    assert kwargs["headers"]["Authorization"] == "Bearer gh-test-token"
    assert kwargs["headers"]["Accept"] == "application/vnd.github+json"


def test_github_list_issues_and_errors(clean_env):
    _github_env(clean_env)
    rec = _Recorder(
        httpx.Response(200, json=[{"number": 1, "title": "A"}, {"number": 2, "title": "B"}])
    )
    clean_env.setattr(httpx, "get", rec)

    res = GitHubIssuesAdapter().run({"action": "list_issues", "repo": "other"})
    assert res == {
        "count": 2,
        "issues": [{"number": 1, "title": "A"}, {"number": 2, "title": "B"}],
    }
    assert rec.calls[0][0] == "https://api.github.com/repos/acme/other/issues"

    clean_env.setattr(httpx, "post", _Recorder(httpx.Response(422, text="invalid")))
    res = GitHubIssuesAdapter().run({"action": "create_issue", "title": "x"})
    assert res == {"error": "github error 422", "detail": "invalid"}

    # Missing title is reported, not raised
    res = GitHubIssuesAdapter().run({"action": "create_issue"})
    assert res["error"].startswith("exception:")


def test_gdrive_create_doc_uses_token_from_credentials_file(clean_env, tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text(json.dumps({"access_token": "drive-test-token"}))
    clean_env.setenv("GOOGLE_CREDENTIALS_PATH", str(creds))
    clean_env.setenv("GDRIVE_PARENT_FOLDER_ID", "folder-1")
    rec = _Recorder(httpx.Response(200, json={"id": "doc-9", "name": "Plan"}))
    clean_env.setattr(httpx, "post", rec)

    res = GDriveDocsAdapter().run({"action": "create_doc", "title": "Plan"})

    assert res == {"id": "doc-9", "name": "Plan", "note": "metadata-only"}
    url, kwargs = rec.calls[0]
    assert url == "https://www.googleapis.com/drive/v3/files"
    assert kwargs["headers"]["Authorization"] == "Bearer drive-test-token"
    assert kwargs["params"] == {"fields": "id,name"}
    assert kwargs["json"] == {
        "name": "Plan",
        "mimeType": "application/vnd.google-apps.document",
        "parents": ["folder-1"],
    }

    assert GDriveDocsAdapter().run({"action": "delete"}) == {"error": "unknown action: delete"}


def test_gdrive_bad_credentials_file_falls_back_to_dry_run(clean_env, tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("not json")
    clean_env.setenv("GOOGLE_CREDENTIALS_PATH", str(creds))
    clean_env.setenv("GDRIVE_PARENT_FOLDER_ID", "folder-1")
    _NoNetwork(clean_env)

    res = GDriveDocsAdapter().run({"action": "create_doc", "title": "Plan"})
    assert res == {
        "dry_run": True,
        "action": "create_doc",
        "parent_folder_id": "folder-1",
        "title": "Plan",
    }

import os

from plugah.adapters.base import ToolRegistry


def test_dry_run_behavior(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    reg = ToolRegistry.default()
    gh = reg.get("github_issues")
    gd = reg.get("gdrive_docs")

    res_gh = gh.run({"action": "create_issue", "title": "Test", "body": "Body"})  # type: ignore[arg-type]
    assert res_gh.get("dry_run") is True

    res_gd = gd.run({"action": "create_doc", "title": "Doc", "markdown_body": "# x"})  # type: ignore[arg-type]
    assert res_gd.get("dry_run") is True

    # Without credentials, still no-op but available
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    res_gh2 = gh.run({"action": "list_issues"})  # type: ignore[arg-type]
    assert res_gh2.get("dry_run") is True

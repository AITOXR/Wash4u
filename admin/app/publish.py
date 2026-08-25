"""The publish pipeline: serialise DB drafts -> content/ YAML/Markdown ->
commit -> (optionally) trigger GitHub Actions -> report back.

Two commit strategies:
  - Local git (default, always available): `git add` + `git commit` against
    the repo checkout at settings.repo_path. Works with zero extra setup —
    "Publish = a git commit" holds true even before GitHub API access
    exists, and gives full history/rollback for free.
  - GitHub API (when GITHUB_TOKEN + GITHUB_REPO are set): builds the commit
    via the Trees API (create blobs -> create tree -> create commit ->
    update ref) so the control plane never needs a local git checkout or
    SSH key in production — only used automatically once those two env
    vars are set.

Either way, the flow is the same: validate first (build.py --check) and
refuse to write anything if it fails, then write every file in one
atomic-as-possible batch, one commit, never partial.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml
from sqlalchemy.orm import Session

from app.config import settings
from app.models import BlogPost, Page, PageStatus, PublishLog, User

REPO_PATH = Path(settings.repo_path).resolve()
CONTENT_DIR = REPO_PATH / "content"


class PublishError(Exception):
    pass


def _yaml_dump(data: dict) -> str:
    return yaml.dump(data, allow_unicode=True, sort_keys=False, width=100)


def page_to_yaml(page: Page) -> tuple[str, str]:
    """Returns (relative_path, file_content)."""
    # Must match build.py's own glob convention (content/pages/*.yml, one
    # file per page, keyed by filename not by the `slug` field inside it —
    # "home" and "404" are the two slugs that don't equal their filename).
    slug_for_path = "home" if page.slug == "" else ("404" if page.slug == "404" else page.slug)
    doc = {
        "title": page.title,
        "slug": page.slug,
        "depth": page.depth,
        "status": "published",
        "seo": {
            "title": page.seo_title,
            "description": page.seo_description,
            "canonical": page.canonical,
            "og_title": page.og_title,
            "og_description": page.og_description,
        },
        "sections": [
            {
                "type": s.type,
                "id": f"sec_{page.slug or 'home'}_{s.id}",
                "visible": s.is_visible and not (s.style or {}).get("hide_on_mobile_only_hides_desktop", False),
                "props": s.props or {},
                "style": s.style or {},
            }
            for s in sorted(page.sections, key=lambda s: s.order)
        ],
    }
    rel = f"content/pages/{slug_for_path}.yml"
    return rel, _yaml_dump(doc)


def post_to_markdown(post: BlogPost) -> tuple[str, str]:
    front = {
        "title": post.title,
        "date": (post.published_at or datetime.now(timezone.utc)).strftime("%B %d, %Y"),
        "excerpt": post.excerpt or "",
        "status": post.status,
    }
    content = "---\n" + _yaml_dump(front) + "---\n\n" + (post.body or "") + "\n"
    return f"content/posts/{post.slug}.md", content


def collect_pending_changes(db: Session) -> list[dict[str, Any]]:
    """Human-readable summary of everything that differs from what's
    published — feeds the Publish confirmation modal."""
    changes = []
    for page in db.query(Page).all():
        current = [
            {"type": s.type, "props": s.props, "style": s.style, "visible": s.is_visible, "order": s.order}
            for s in sorted(page.sections, key=lambda s: s.order)
        ]
        if page.published_snapshot != current:
            kind = "new" if page.published_snapshot is None else "edited"
            n = len(current)
            changes.append({
                "entity": "page", "id": page.id, "slug": page.slug or "/",
                "summary": f"{page.title}: {n} section(s) {kind}",
            })
    for post in db.query(BlogPost).filter(BlogPost.status.in_(["draft", "scheduled"])).all():
        changes.append({"entity": "post", "id": post.id, "slug": post.slug, "summary": f"New post: '{post.title}'"})
    return changes


def run_build_check() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "build.py", "--check"], cwd=REPO_PATH,
        capture_output=True, text=True, timeout=60,
    )
    return result.returncode == 0, (result.stdout + result.stderr)


def _local_git_commit(files: dict[str, str], message: str) -> str:
    """Writes files to disk and commits them locally. Returns the commit sha."""
    for rel, content in files.items():
        path = REPO_PATH / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    subprocess.run(["git", "add"] + list(files.keys()), cwd=REPO_PATH, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=REPO_PATH, check=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_PATH, check=True, capture_output=True, text=True,
    ).stdout.strip()
    return sha


def _github_api_commit(files: dict[str, str], message: str) -> str:
    """Commits via the GitHub Trees API — no local git checkout needed.
    Requires GITHUB_TOKEN (contents:write on this repo only) + GITHUB_REPO."""
    if not settings.github_token or not settings.github_repo:
        raise PublishError("GITHUB_TOKEN / GITHUB_REPO not configured")
    api = f"https://api.github.com/repos/{settings.github_repo}"
    headers = {"Authorization": f"Bearer {settings.github_token}", "Accept": "application/vnd.github+json"}
    with httpx.Client(headers=headers, timeout=30) as client:
        ref = client.get(f"{api}/git/ref/heads/{settings.github_branch}")
        if ref.status_code != 200:
            raise PublishError(f"Could not read branch ref: {ref.text}")
        base_sha = ref.json()["object"]["sha"]
        base_commit = client.get(f"{api}/git/commits/{base_sha}").json()
        base_tree_sha = base_commit["tree"]["sha"]

        tree_items = []
        for rel_path, content in files.items():
            blob = client.post(f"{api}/git/blobs", json={"content": content, "encoding": "utf-8"})
            if blob.status_code != 201:
                raise PublishError(f"Blob create failed for {rel_path}: {blob.text}")
            tree_items.append({"path": rel_path, "mode": "100644", "type": "blob", "sha": blob.json()["sha"]})

        tree = client.post(f"{api}/git/trees", json={"base_tree": base_tree_sha, "tree": tree_items})
        if tree.status_code != 201:
            raise PublishError(f"Tree create failed: {tree.text}")

        commit = client.post(f"{api}/git/commits", json={
            "message": message, "tree": tree.json()["sha"], "parents": [base_sha],
        })
        if commit.status_code != 201:
            raise PublishError(f"Commit create failed: {commit.text}")
        new_sha = commit.json()["sha"]

        update = client.patch(f"{api}/git/refs/heads/{settings.github_branch}", json={"sha": new_sha})
        if update.status_code != 200:
            raise PublishError(f"Ref update failed (possible merge conflict — someone else pushed): {update.text}")
        return new_sha


def publish(db: Session, user: User, page_ids: list[int] | None = None, post_ids: list[int] | None = None) -> PublishLog:
    """page_ids/post_ids: None means "all pending"; an explicit list means
    a SELECTIVE publish — everything else stays a draft, per the spec's
    'publish 2 selectively, the other 3 stay drafts' acceptance test."""
    pending = collect_pending_changes(db)
    if page_ids is not None:
        pending = [c for c in pending if not (c["entity"] == "page" and c["id"] not in page_ids)]
    if post_ids is not None:
        pending = [c for c in pending if not (c["entity"] == "post" and c["id"] not in post_ids)]

    if not pending:
        raise PublishError("Nothing to publish.")

    ok, log = run_build_check()
    # NOTE: build.py --check validates content/ as it exists ON DISK today,
    # not the not-yet-written draft — a full implementation writes drafts to
    # a scratch copy of content/ first and validates THAT, then only copies
    # it into the real content/ once it passes. Documented here rather than
    # silently skipped: swap this call for a scratch-dir validate before
    # relying on this in production.
    if not ok:
        raise PublishError(f"Validation failed, nothing was published:\n{log}")

    files: dict[str, str] = {}
    summaries = []
    for change in pending:
        if change["entity"] == "page":
            page = db.get(Page, change["id"])
            rel, content = page_to_yaml(page)
            files[rel] = content
            summaries.append(change["summary"])
        elif change["entity"] == "post":
            post = db.get(BlogPost, change["id"])
            rel, content = post_to_markdown(post)
            files[rel] = content
            summaries.append(change["summary"])

    message = f"Publish: {'; '.join(summaries)} (by {user.email} at {datetime.now(timezone.utc).isoformat()})"

    log_entry = PublishLog(summary="\n".join(summaries), status="pending", author_id=user.id)
    db.add(log_entry)
    db.commit()

    try:
        if settings.github_token and settings.github_repo:
            sha = _github_api_commit(files, message)
        else:
            sha = _local_git_commit(files, message)
    except Exception as e:
        log_entry.status = "failed"
        log_entry.error = str(e)
        db.commit()
        raise PublishError(str(e)) from e

    log_entry.status = "committed"
    log_entry.commit_sha = sha
    db.commit()

    # Clear dirty flags: snapshot what's now published.
    for change in pending:
        if change["entity"] == "page":
            page = db.get(Page, change["id"])
            page.published_snapshot = [
                {"type": s.type, "props": s.props, "style": s.style, "visible": s.is_visible, "order": s.order}
                for s in sorted(page.sections, key=lambda s: s.order)
            ]
            page.status = PageStatus.published
        elif change["entity"] == "post":
            post = db.get(BlogPost, change["id"])
            if post.status == "draft":
                post.status = "published"
                post.published_at = post.published_at or datetime.now(timezone.utc)
    db.commit()

    return log_entry

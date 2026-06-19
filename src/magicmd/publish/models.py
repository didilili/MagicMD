from __future__ import annotations

from pydantic import BaseModel, Field


class GithubPublishOptions(BaseModel):
    repo: str
    target_dir: str
    branch: str = "magicmd/{slug}"
    commit_message: str = "Add article: {title}"
    create_pr: bool = False
    overwrite: bool = False


class PublishFile(BaseModel):
    source_path: str
    target_path: str
    size_bytes: int


class PublishPlan(BaseModel):
    repo: str
    target_dir: str
    branch: str
    commit_message: str
    create_pr: bool = False
    overwrite: bool = False
    title: str
    platform: str
    source_url: str
    package_dir: str
    files: list[PublishFile] = Field(default_factory=list)


class PublishResult(BaseModel):
    repo: str
    branch: str
    commit_sha: str = ""
    pr_url: str = ""
    files: list[PublishFile] = Field(default_factory=list)

from __future__ import annotations


class PublishError(RuntimeError):
    def __init__(self, message: str, stage: str = "publish"):
        self.stage = stage
        super().__init__(message)


class PublishConfigError(PublishError):
    def __init__(self, message: str):
        super().__init__(message, stage="config")


class PublishPlanError(PublishError):
    def __init__(self, message: str):
        super().__init__(message, stage="plan")


class PublishGitError(PublishError):
    def __init__(self, message: str):
        super().__init__(message, stage="git")


class PublishGitHubError(PublishError):
    def __init__(self, message: str):
        super().__init__(message, stage="github")

"""Load the optional command-line interface only when it is invoked."""


def main():
    try:
        from magicmd.cli import entrypoint
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.split(".")[0] in {"typer", "click", "rich", "httpx"}:
            raise SystemExit(
                "The CLI is optional. Install it with: pip install 'magicmd[cli]'"
            ) from exc
        raise
    entrypoint()

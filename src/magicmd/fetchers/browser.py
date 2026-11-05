from __future__ import annotations

import asyncio


def AsyncCamoufox(*args, **kwargs):
    """Keep the existing factory available without eagerly importing the browser."""
    try:
        from camoufox.async_api import AsyncCamoufox as factory
    except ImportError as exc:
        raise RuntimeError(
            "Browser support is optional. Install it with: pip install 'magicmd[browser]'"
        ) from exc
    return factory(*args, **kwargs)


async def _fetch_browser_once(url: str, wait_selector: str = "", timeout_ms: int = 15000) -> str:
    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=timeout_ms)
            except Exception:
                pass
        await asyncio.sleep(1)
        return await page.content()


async def fetch_browser_async(
    url: str,
    wait_selector: str = "",
    timeout_ms: int = 15000,
    attempts: int = 2,
) -> str:
    max_attempts = max(1, attempts)
    for attempt in range(1, max_attempts + 1):
        try:
            return await _fetch_browser_once(
                url, wait_selector=wait_selector, timeout_ms=timeout_ms
            )
        except Exception:
            if attempt >= max_attempts:
                raise
            await asyncio.sleep(min(1.0, 0.25 * attempt))
    raise RuntimeError("browser fetch retry loop exited unexpectedly")


def fetch_browser(
    url: str,
    wait_selector: str = "",
    timeout_ms: int = 15000,
    attempts: int = 2,
) -> str:
    return asyncio.run(
        fetch_browser_async(
            url,
            wait_selector=wait_selector,
            timeout_ms=timeout_ms,
            attempts=attempts,
        )
    )

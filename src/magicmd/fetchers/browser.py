from __future__ import annotations

import asyncio

from camoufox.async_api import AsyncCamoufox


async def fetch_browser_async(url: str, wait_selector: str = "", timeout_ms: int = 15000) -> str:
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


def fetch_browser(url: str, wait_selector: str = "", timeout_ms: int = 15000) -> str:
    return asyncio.run(fetch_browser_async(url, wait_selector=wait_selector, timeout_ms=timeout_ms))


import pytest

from magicmd.fetchers import browser as browser_fetcher


@pytest.mark.asyncio
async def test_fetch_browser_async_retries_browser_start_failure(monkeypatch):
    attempts = 0

    class FakePage:
        async def goto(self, url, wait_until):
            assert url == "https://example.com/article"
            assert wait_until == "domcontentloaded"

        async def wait_for_selector(self, selector, timeout):
            assert selector == "article"
            assert timeout == 15000

        async def content(self):
            return "<html>ok</html>"

    class FakeBrowser:
        async def new_page(self):
            return FakePage()

    class FakeCamoufox:
        def __init__(self, headless):
            assert headless is True

        async def __aenter__(self):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("driver closed")
            return FakeBrowser()

        async def __aexit__(self, exc_type, exc, traceback):
            return None

    async def no_sleep(seconds):
        assert seconds <= 1

    monkeypatch.setattr(browser_fetcher, "AsyncCamoufox", FakeCamoufox)
    monkeypatch.setattr(browser_fetcher.asyncio, "sleep", no_sleep)

    html = await browser_fetcher.fetch_browser_async(
        "https://example.com/article",
        wait_selector="article",
        attempts=2,
    )

    assert html == "<html>ok</html>"
    assert attempts == 2


@pytest.mark.asyncio
async def test_fetch_browser_async_raises_last_error_after_retries(monkeypatch):
    attempts = 0

    class FakeCamoufox:
        def __init__(self, headless):
            pass

        async def __aenter__(self):
            nonlocal attempts
            attempts += 1
            raise RuntimeError(f"driver closed {attempts}")

        async def __aexit__(self, exc_type, exc, traceback):
            return None

    async def no_sleep(seconds):
        return None

    monkeypatch.setattr(browser_fetcher, "AsyncCamoufox", FakeCamoufox)
    monkeypatch.setattr(browser_fetcher.asyncio, "sleep", no_sleep)

    with pytest.raises(RuntimeError, match="driver closed 3"):
        await browser_fetcher.fetch_browser_async("https://example.com/article", attempts=3)

    assert attempts == 3

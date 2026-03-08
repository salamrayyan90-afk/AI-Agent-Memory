"""Autonomous web navigation using Playwright (browser-use optional)."""
import asyncio
from typing import Optional

# Playwright is required; browser-use is optional for higher-level agent
try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None


async def run_browser_task(task_description: str) -> dict:
    """
    Run a browser task: search, compare prices, interact with sites.
    Returns {success, summary, error}.
    """
    if not async_playwright:
        return {"success": False, "summary": "", "error": "Playwright not installed. Run: pip install playwright && playwright install"}

    result = {"success": False, "summary": "", "error": None}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            # Example: open Google and run a search
            await page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)
            # Try to find search box and type task (simplified)
            selector = 'textarea[name="q"], input[name="q"]'
            try:
                await page.wait_for_selector(selector, timeout=5000)
                await page.fill(selector, task_description[:200])
                await page.press(selector, "Enter")
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                title = await page.title()
                result["summary"] = f"تم فتح البحث: {task_description[:80]}... | الصفحة: {title}"
                result["success"] = True
            except Exception as e:
                result["summary"] = "تم فتح المتصفح لكن تنفيذ المهمة لم يكتمل."
                result["error"] = str(e)
            await browser.close()
    except Exception as e:
        result["error"] = str(e)
        result["summary"] = f"خطأ في المتصفح: {e}"
    return result


def run_browser_task_sync(task_description: str) -> dict:
    """Synchronous wrapper for run_browser_task."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(run_browser_task(task_description))

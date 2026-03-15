"""
Persistent Browser Manager for Junction AI
Maintains a single browser session that can be shared between bot and human.
"""

import os
import asyncio
import threading
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext

SCREENSHOT_DIR = os.path.expanduser("~/junction-ai/")

class BrowserManager:
    """Manages a persistent browser session."""

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._lock = threading.Lock()
        self._headless = True
        self._current_url = "about:blank"
        self._barrier_detected = False

    def _ensure_browser(self, headless: bool = True):
        """Ensure browser is running. Creates if needed."""
        with self._lock:
            # If switching headless mode, restart browser
            if self._browser and self._headless != headless:
                self._close_browser()

            if not self._browser:
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(
                    headless=headless,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                self._context = self._browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 800}
                )
                self._page = self._context.new_page()
                self._headless = headless

            return self._page

    def _close_browser(self):
        """Close browser and cleanup."""
        if self._page:
            try:
                self._page.close()
            except:
                pass
            self._page = None

        if self._context:
            try:
                self._context.close()
            except:
                pass
            self._context = None

        if self._browser:
            try:
                self._browser.close()
            except:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except:
                pass
            self._playwright = None

    def navigate_and_screenshot(self, url: str, filename: str = "screenshot.png") -> dict:
        """Navigate to URL and take screenshot. Returns status dict."""
        result = {
            "success": False,
            "path": None,
            "barrier": False,
            "error": None,
            "url": url
        }

        try:
            page = self._ensure_browser(headless=True)
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)  # Let page render

            self._current_url = url

            # Check for barriers
            page_title = page.title()
            try:
                page_text = page.inner_text("body")[:2000].lower()
            except:
                page_text = ""

            barrier_keywords = ["captcha", "robot", "verify", "human", "challenge",
                              "security check", "unusual traffic", "blocked", "access denied"]

            barrier_found = any(kw in page_text or kw in page_title.lower() for kw in barrier_keywords)

            if barrier_found:
                result["barrier"] = True
                self._barrier_detected = True
                # Save barrier screenshot
                path = os.path.join(SCREENSHOT_DIR, f"barrier_{filename}")
                page.screenshot(path=path)
                result["path"] = path
            else:
                self._barrier_detected = False
                path = os.path.join(SCREENSHOT_DIR, filename)
                page.screenshot(path=path)
                result["success"] = True
                result["path"] = path

        except Exception as e:
            result["error"] = str(e)

        return result

    def open_for_manual_control(self, url: Optional[str] = None) -> dict:
        """
        Restart browser in visible (non-headless) mode for manual control.
        User can solve captcha/login, then bot resumes.
        """
        result = {
            "success": False,
            "message": "",
            "url": ""
        }

        try:
            # Use current URL if none specified
            target_url = url or self._current_url or "https://duckduckgo.com"

            # Close headless browser and open visible one
            self._close_browser()

            # Start visible browser
            page = self._ensure_browser(headless=False)
            page.goto(target_url, timeout=30000)

            self._current_url = target_url
            result["success"] = True
            result["url"] = target_url
            result["message"] = f"Browser opened to {target_url}. Solve the captcha/login, then send /resume"

        except Exception as e:
            result["message"] = f"Failed to open browser: {e}"

        return result

    def resume_headless(self) -> dict:
        """
        Switch back to headless mode after manual intervention.
        Preserves cookies/session from the visible browser.
        """
        result = {
            "success": False,
            "message": ""
        }

        try:
            # Get current URL before switching
            current_url = self._current_url

            # Get cookies from current context
            cookies = []
            if self._context:
                try:
                    cookies = self._context.cookies()
                except:
                    pass

            # Close visible browser
            self._close_browser()

            # Start headless browser
            page = self._ensure_browser(headless=True)

            # Restore cookies
            if cookies and self._context:
                try:
                    self._context.add_cookies(cookies)
                except:
                    pass

            # Navigate back to where we were
            if current_url and current_url != "about:blank":
                page.goto(current_url, timeout=30000)

            self._barrier_detected = False
            result["success"] = True
            result["message"] = "Resumed in background mode. Session preserved."

        except Exception as e:
            result["message"] = f"Resume failed: {e}"

        return result

    def get_status(self) -> dict:
        """Get current browser status."""
        return {
            "running": self._browser is not None,
            "headless": self._headless,
            "current_url": self._current_url,
            "barrier_detected": self._barrier_detected
        }

    def close(self):
        """Fully close browser."""
        self._close_browser()


# Global browser instance
_browser_manager: Optional[BrowserManager] = None

def get_browser_manager() -> BrowserManager:
    """Get or create the global browser manager."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager

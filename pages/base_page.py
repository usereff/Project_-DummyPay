from playwright.sync_api import Page
from utilities.config import BASE_URL, TIMEOUT


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page):
        self.page = page
        self.page.set_default_timeout(TIMEOUT)

    def open(self, path: str = ""):
        self.page.goto(f"{BASE_URL}{path}")

    def click(self, selector: str):
        self.page.click(selector)

    def fill(self, selector: str, value: str):
        self.page.fill(selector, value)

    def is_visible(self, selector: str) -> bool:
        return self.page.is_visible(selector)
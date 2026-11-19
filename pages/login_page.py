import re
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page Object for the Login page."""

    # Locators
    EMAIL_INPUT = "input[type='email']"
    PASSWORD_INPUT = "input[type='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    DASHBOARD_MARKER = "text=Total balance"

    def __init__(self, page: Page):
        super().__init__(page)

    def open_login(self):
        self.open("/login")

    def enter_email(self, email: str):
        self.fill(self.EMAIL_INPUT, email)

    def enter_password(self, password: str):
        self.fill(self.PASSWORD_INPUT, password)

    def click_submit(self):
        self.page.locator(self.SUBMIT_BUTTON).wait_for(state="visible")

        self.page.wait_for_function(
            """selector => document.querySelector(selector)?.disabled === false""",
            arg=self.SUBMIT_BUTTON
        )

        self.click(self.SUBMIT_BUTTON)

    def login(self, email: str, password: str):
        self.enter_email(email)
        self.enter_password(password)
        self.click_submit()

    def is_dashboard_loaded(self, timeout: int = 10000) -> bool:
        """True if the dashboard appears after login."""
        try:
            self.page.wait_for_selector(self.DASHBOARD_MARKER, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def _error_locator(self):
        # Flexible: an alert element OR text that looks like a login error.
        # TODO: replace with the exact selector/text after checking the real error message.
        return self.page.locator("[role='alert']").or_(
            self.page.get_by_text(re.compile(r"invalid|incorrect|wrong|failed|error", re.I))
        ).first

    def is_error_visible(self, timeout: int = 5000) -> bool:
        try:
            self._error_locator().wait_for(state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def get_error_text(self) -> str:
        return self._error_locator().inner_text()

    def is_on_login_page(self) -> bool:
        return "/login" in self.page.url
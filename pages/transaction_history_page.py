import re

from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage
from utilities.config import BASE_URL


class TransactionHistoryPage(BasePage):
    """Page Object for the Transaction History page."""

    TITLE = "h1:has-text('Transaction History')"
    DESCRIPTION = "All transfers you've sent and received."
    FROM_DATE = "#filter-from"
    TO_DATE = "#filter-to"
    TYPE_FILTER = "#filter-type"
    CURRENCY_FILTER = "#filter-currency"
    CLEAR_BUTTON = "button:has-text('Clear')"
    TRANSACTION_ROWS = "[data-testid='transaction-row']"
    TRANSACTION_DETAIL = "[data-testid='transaction-detail']"
    NO_RESULTS = "text=No matching transactions"
    TRANSACTION_COUNT = re.compile(r"^\d+ transactions$")
    PAGE_INDICATOR = re.compile(r"^Page \d+ of \d+$")

    def __init__(self, page: Page):
        super().__init__(page)
        self.rows = page.locator(self.TRANSACTION_ROWS)
        self.no_results = page.get_by_text("No matching transactions", exact=True)
        self.transaction_count = page.get_by_text(self.TRANSACTION_COUNT)
        self.page_indicator = page.get_by_text(self.PAGE_INDICATOR)

    def open_history(self):
        self.open("/history")
        expect(self.page.locator(self.TITLE)).to_be_visible()
        expect(self.page.get_by_text(self.DESCRIPTION, exact=True)).to_be_visible()
        self.wait_for_results()

    def wait_for_results(self):
        expect(self.rows.first.or_(self.no_results)).to_be_visible()

    def select_type(self, transaction_type: str):
        self._select_option(self.TYPE_FILTER, transaction_type)

    def select_currency(self, currency: str):
        self._select_option(self.CURRENCY_FILTER, currency)

    def _select_option(self, filter_selector: str, option: str):
        self.page.locator(filter_selector).click()
        self.page.get_by_role("option", name=option, exact=True).click()
        expect(self.page.locator(filter_selector)).to_contain_text(option)

    def set_date_range(self, start_date: str, end_date: str):
        self.page.locator(self.FROM_DATE).fill(start_date)
        self.page.locator(self.TO_DATE).fill(end_date)

    def clear_filters(self):
        self.page.get_by_role("button", name="Clear", exact=True).click()

    def open_transaction(self, index: int = 0):
        self.rows.nth(index).click()
        expect(self.page.locator(self.TRANSACTION_DETAIL)).to_be_visible()

    def detail_value(self, label: str) -> Locator:
        return self.page.locator(self.TRANSACTION_DETAIL).locator(
            "dt", has_text=label
        ).locator("xpath=following-sibling::dd")

    def close_transaction(self):
        self.page.get_by_role("dialog").get_by_role(
            "button", name="Close", exact=True
        ).click()

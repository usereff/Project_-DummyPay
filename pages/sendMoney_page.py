import re
from decimal import Decimal

from playwright.sync_api import expect

from pages.base_page import BasePage


class SendMoneyPage(BasePage):
    """Page Object for the Send Money page."""

    # Locators
    RECIPIENT_INPUT = "#recipient-email"
    FIND_RECIPIENT_BUTTON = "button:has-text('Find recipient')"
    RECIPIENT_ERROR = "text=No registered user found with this email address."
    SELF_TRANSFER_ERROR = "text=You cannot send money to yourself."
    ACTIVE_STEP = "[aria-current='step']"
    CONTINUE_BUTTON = "button:has-text('Continue')"
    AMOUNT_INPUT = "#transfer-amount"
    REVIEW_BUTTON = "button:has-text('Review transfer')"
    CONFIRM_SEND_BUTTON = "button:has-text('Confirm & send')"
    SEND_NOW_BUTTON = "button:has-text('Send now')"

    def enter_recipient_email(self, email: str):
        self.fill(self.RECIPIENT_INPUT, email)

    def click_find_recipient(self):
        self.click(self.FIND_RECIPIENT_BUTTON)

    def is_unregistered_email_error_visible(self) -> bool:
        try:
            self.page.wait_for_selector(
                self.RECIPIENT_ERROR,
                state="visible",
                timeout=5000
            )
            return True
        except Exception:
            return False

    def wait_for_step(self, step: str):
        expect(self.page.locator(self.ACTIVE_STEP)).to_have_text(
            step, timeout=15000
        )

    def click_continue(self):
        self.click(self.CONTINUE_BUTTON)

    def select_amount_mode(self, mode: str):
        self.page.get_by_role("radio", name=mode, exact=True).click()

    def enter_amount(self, amount: str):
        self.fill(self.AMOUNT_INPUT, amount)

    def click_review_transfer(self):
        self.click(self.REVIEW_BUTTON)

    def confirm_and_send(self):
        self.click(self.CONFIRM_SEND_BUTTON)

    def click_send_now(self):
        self.click(self.SEND_NOW_BUTTON)

    def get_selected_wallet_balance(self) -> tuple[str, Decimal]:
        currency = self.page.locator("select").input_value()
        option_text = self.page.locator("select option:checked").inner_text()
        balance = self._extract_amount(option_text)
        return currency, balance

    def get_recipient_currency(self) -> str:
        page_text = self.page.locator("body").inner_text()
        match = re.search(r"Receives in\s*\n\s*([A-Z]{3})\b", page_text)

        if match is None:
            raise AssertionError("Recipient currency was not shown.")

        return match.group(1)

    def get_review_summary(
        self,
    ) -> tuple[Decimal, str, Decimal, str, str, Decimal]:
        page_text = self.page.locator("body").inner_text()

        match = re.search(
            r"You send\s*\n\s*([^\n]+)\s*\n"
            r"Sending currency\s*\n\s*([A-Z]{3})\s*\n"
            r"Exchange rate\s*\n\s*1\s+([A-Z]{3})\s*=\s*([\d,.]+)\s+([A-Z]{3})\s*\n"
            r"Recipient gets\s*\n\s*([^\n]+)",
            page_text,
        )

        if match is None:
            raise AssertionError(
                "Transfer amount and exchange details were not shown."
            )

        sent_amount = self._extract_amount(match.group(1))
        sending_currency = match.group(2)
        rate = Decimal(match.group(4).replace(",", ""))
        received_amount = self._extract_amount(match.group(6))

        return (
            sent_amount,
            sending_currency,
            rate,
            match.group(3),
            match.group(5),
            received_amount,
        )

    @staticmethod
    def _extract_amount(text: str) -> Decimal:
        match = re.search(r"[\d,]+\.\d{2}", text)

        if match is None:
            raise AssertionError(
                f"Could not read a monetary amount from: {text!r}"
            )

        return Decimal(match.group(0).replace(",", ""))

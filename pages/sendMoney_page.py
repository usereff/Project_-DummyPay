import re
from decimal import Decimal, InvalidOperation

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

    def open(self, path: str = ""):
        super().open(path)
        self.page.wait_for_load_state("domcontentloaded")

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
        expect(self.page.locator(self.ACTIVE_STEP)).to_have_text(step)
        if step == "Recipient":
            expect(self.page.locator(self.RECIPIENT_INPUT)).to_be_visible()
        elif step == "Amount":
            expect(self.page.locator(self.AMOUNT_INPUT)).to_be_visible()
            expect(self.page.locator("select")).to_be_visible()
            expect(self.page.get_by_role("radio").first).to_be_visible()
            expect(self.page.locator(self.REVIEW_BUTTON)).to_be_visible()
        elif step == "Review":
            expect(
                self.page.get_by_role("button", name="Confirm & send")
            ).to_be_visible()

    def click_continue(self):
        self.click(self.CONTINUE_BUTTON)

    def select_amount_mode(self, mode: str):
        radio = self.page.get_by_role("radio", name=mode, exact=True)
        expect(radio).to_be_visible()
        radio.click()

    def enter_amount(self, amount: str):
        self.fill(self.AMOUNT_INPUT, amount)

    def click_review_transfer(self):
        self.click(self.REVIEW_BUTTON)

    def confirm_and_send(self):
        self.click(self.CONFIRM_SEND_BUTTON)

    def click_send_now(self):
        self.click(self.SEND_NOW_BUTTON)

    def get_selected_wallet_balance(self) -> tuple[str, Decimal]:
        wallet_select = self.page.locator("select")
        expect(wallet_select).to_be_visible()
        wallet_select.locator("option:checked").wait_for(state="attached")
        currency = wallet_select.input_value()
        option_text = wallet_select.locator("option:checked").inner_text()
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
        return self._parse_review_summary(page_text)

    @staticmethod
    def _parse_review_summary(
        page_text: str,
    ) -> tuple[Decimal, str, Decimal, str, str, Decimal]:
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        sent_amount_text = SendMoneyPage._value_after_label(lines, "You send")
        sending_currency = SendMoneyPage._value_after_label(
            lines, "Sending currency"
        )
        exchange_rate_text = SendMoneyPage._value_after_label(
            lines, "Exchange rate"
        )
        received_amount_text = SendMoneyPage._value_after_label(
            lines, "Recipient gets"
        )

        if not re.fullmatch(r"[A-Z]{3}", sending_currency):
            raise AssertionError(
                f"Could not read the sending currency from: {sending_currency!r}"
            )

        if re.fullmatch(r"No conversion \(same currency\)", exchange_rate_text, re.I):
            rate = Decimal("1")
            rate_source_currency = sending_currency
            rate_recipient_currency = sending_currency
        else:
            rate_match = re.search(
                r"1\s+([A-Z]{3})\s*=\s*([\d.,]+)\s+([A-Z]{3})",
                exchange_rate_text,
            )
            if rate_match is None:
                raise AssertionError(
                    f"Could not read the exchange rate from: {exchange_rate_text!r}"
                )
            rate_source_currency = rate_match.group(1)
            rate = SendMoneyPage._parse_number(rate_match.group(2), is_amount=False)
            rate_recipient_currency = rate_match.group(3)

        sent_amount = SendMoneyPage._extract_amount(sent_amount_text)
        received_amount = SendMoneyPage._extract_amount(received_amount_text)

        return (
            sent_amount,
            sending_currency,
            rate,
            rate_source_currency,
            rate_recipient_currency,
            received_amount,
        )

    @staticmethod
    def _value_after_label(lines: list[str], label: str) -> str:
        for index, line in enumerate(lines):
            if line.casefold() == label.casefold():
                if index + 1 < len(lines):
                    return lines[index + 1]
                break

            if line.casefold().startswith(f"{label.casefold()} "):
                return line[len(label):].strip().lstrip(":").strip()

            if line.casefold().startswith(f"{label.casefold()}:"):
                return line[len(label) + 1:].strip()

        raise AssertionError(f"Could not find {label!r} in the transfer review.")

    @staticmethod
    def _extract_amount(text: str) -> Decimal:
        match = re.search(r"(?<!\w)\d[\d.,]*", text)

        if match is None:
            raise AssertionError(
                f"Could not read a monetary amount from: {text!r}"
            )

        return SendMoneyPage._parse_number(match.group(0), is_amount=True)

    @staticmethod
    def _parse_number(text: str, is_amount: bool) -> Decimal:
        token = text.strip()
        separators = {separator for separator in token if separator in ".,"}
        decimal_separator = None

        if len(separators) == 2:
            decimal_separator = max(separators, key=token.rfind)
        elif len(separators) == 1:
            separator = next(iter(separators))
            fractional_digits = len(token.rsplit(separator, 1)[1])
            if not is_amount or fractional_digits == 2:
                decimal_separator = separator

        if decimal_separator is None:
            normalized = token.replace(",", "").replace(".", "")
        else:
            integer, fraction = token.rsplit(decimal_separator, 1)
            integer = integer.replace(",", "").replace(".", "")
            normalized = f"{integer}.{fraction}"

        try:
            return Decimal(normalized)
        except InvalidOperation as error:
            raise AssertionError(f"Could not parse numeric value: {text!r}") from error

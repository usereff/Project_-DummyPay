from playwright.sync_api import Locator, expect

from pages.base_page import BasePage
from utilities.config import BASE_URL


class PaymentCardsPage(BasePage):
    """Page Object for the Payment Cards page."""

    PAYMENT_CARDS_LINK = "a[href='/cards']"
    TITLE = "h1:has-text('Payment Cards')"
    ADD_CARD_BUTTON = "button:has-text('Add card')"
    EMPTY_STATE = "text=No cards yet"
    CARD_ROWS = "main li"
    CARDHOLDER_INPUT = "Cardholder name"
    CARD_NUMBER_INPUT = "Card number"
    EXPIRY_INPUT = "Expiry (MM/YY)"
    CVV_INPUT = "CVV"

    def open_from_sidebar(self):
        self.page.locator(self.PAYMENT_CARDS_LINK).click()
        expect(self.page).to_have_url(f"{BASE_URL}/cards")
        expect(self.page.locator(self.TITLE)).to_be_visible()
        self.wait_for_cards_loaded()

    def wait_for_cards_loaded(self):
        expect(
            self.page.locator(self.EMPTY_STATE).or_(
                self.page.locator(self.CARD_ROWS).first
            )
        ).to_be_visible()

    def get_card_rows(self, cardholder: str, last_four: str, expiry: str):
        return (
            self.page.locator(self.CARD_ROWS)
            .filter(has_text=cardholder)
            .filter(has_text=last_four)
            .filter(has_text=f"Exp {expiry}")
        )

    def add_card(
        self,
        cardholder: str,
        card_number: str,
        expiry: str,
        cvv: str,
    ):
        self.page.locator(self.ADD_CARD_BUTTON).click()
        dialog = self.page.get_by_role("dialog")
        dialog.get_by_label(self.CARDHOLDER_INPUT).fill(cardholder)
        dialog.get_by_label(self.CARD_NUMBER_INPUT).fill(card_number)
        dialog.get_by_label(self.EXPIRY_INPUT).fill(expiry)
        dialog.get_by_label(self.CVV_INPUT).fill(cvv)
        dialog.get_by_role("button", name="Add card", exact=True).click()

    def remove_card(self, card_row: Locator):
        card_row.locator("button[aria-label^='Remove card ending in ']").click()
        confirmation = self.page.get_by_role("alertdialog")
        expect(confirmation).to_be_visible()
        confirmation.get_by_role("button", name="Remove", exact=True).click()
        expect(confirmation).to_have_count(0)

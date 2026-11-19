from pages.base_page import BasePage

class SendMoneyPage(BasePage):
    """Page Object for the Send Money page."""

    # Locators
    RECIPIENT_INPUT = "input[type='email']"
    FIND_RECIPIENT_BUTTON = "button:has-text('Find Recipient')"
    RECIPIENT_ERROR = "text=No registered user found with this email address."

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
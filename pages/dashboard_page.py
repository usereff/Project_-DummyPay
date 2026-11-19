from pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page Object for the Dashboard page."""

    # Locators
    SEND_MONEY_BUTTON = "a:has-text('Send money'), button:has-text('Send money')"
    TOTAL_BALANCE = "text=Total balance"
    
    # View All Locators
    VIEW_ALL_BUTTON = "text=View all"
    TRANSACTION_HISTORY_TITLE = "h1:has-text('Transaction History')"

    def click_view_all(self):
        self.page.click(self.VIEW_ALL_BUTTON)

    def is_transaction_history_visible(self) -> bool:
        return self.page.is_visible(self.TRANSACTION_HISTORY_TITLE)

    def click_send_money(self):
        self.page.click(self.SEND_MONEY_BUTTON)

    def is_total_balance_visible(self) -> bool:
        return self.page.is_visible(self.TOTAL_BALANCE)
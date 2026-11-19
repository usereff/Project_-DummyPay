import pytest
from pages.dashboard_page import DashboardPage


@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.high
def test_db_001_send_money_button_redirects(logged_in_page):
    """DB-001: Verify that the Send Money button redirects to the Send Money page."""
    dashboard = DashboardPage(logged_in_page)
    # logged_in_page.pause()
    dashboard.click_send_money()

    logged_in_page.wait_for_url("https://dummypay.vercel.app/send")
    assert logged_in_page.url == "https://dummypay.vercel.app/send"


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.medium
def test_db_003_view_all_notifications_navigates(logged_in_page):
    """DB-003: Verify that "View all" in Recent notifications navigates to the Notifications page."""
    dashboard = DashboardPage(logged_in_page)

    #logged_in_page.pause()
    dashboard.click_notifications_view_all()

    #logged_in_page.pause()

    logged_in_page.wait_for_url("https://dummypay.vercel.app/notifications")
    assert logged_in_page.url == "https://dummypay.vercel.app/notifications"
    assert logged_in_page.is_visible("h1:has-text('Notifications')")
@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.high
def test_db_002_view_all_redirects_to_transaction_history(logged_in_page):

    """DB-002: Verify View All button redirects to Transaction History."""

    dashboard = DashboardPage(logged_in_page)
    # logged_in_page.pause()
    dashboard.click_view_all()

    logged_in_page.wait_for_selector(
        DashboardPage.TRANSACTION_HISTORY_TITLE
    )

    assert dashboard.is_transaction_history_visible()

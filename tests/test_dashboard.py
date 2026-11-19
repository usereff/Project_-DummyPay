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

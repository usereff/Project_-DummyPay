import pytest
from pages.dashboard_page import DashboardPage


@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.high
def test_db_001_send_money_button_redirects(logged_in_page):
    """DB-001: Verify that the Send Money button redirects to the Send Money page."""
    dashboard = DashboardPage(logged_in_page)

    dashboard.click_send_money()

    assert "send" in logged_in_page.url.lower()
import pytest
from utilities.config import EMAIL, PASSWORD


@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.high
def test_lg_001_login_with_valid_credentials(login_page):
    """LG-001: Verify that a user with valid email and password logs in and reaches the dashboard."""
    login_page.open_login()

    login_page.login(EMAIL, PASSWORD)

    assert login_page.is_dashboard_loaded(), "Dashboard did not load after valid login"


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_lg_002_login_with_wrong_password_shows_error(login_page):
    """LG-002: Verify that a wrong password shows an error message and the user stays on the login page."""
    login_page.open_login()

    login_page.login(EMAIL, "WrongPassword123!")

    assert login_page.is_error_visible(), "No error message shown for wrong password"
    assert not login_page.is_dashboard_loaded(timeout=2000), "User reached dashboard with wrong password"
    assert login_page.is_on_login_page()
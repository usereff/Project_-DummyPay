import pytest
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from utilities.config import EMAIL, PASSWORD, HEADLESS


@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            slow_mo=0 if HEADLESS else 300,
        )
        yield browser
        browser.close()


@pytest.fixture
def login_page(browser_instance):
    """Clean, NOT logged-in window. Used by the login tests."""
    context = browser_instance.new_context()
    page = context.new_page()
    yield LoginPage(page)
    context.close()


@pytest.fixture
def logged_in_page(browser_instance):
    """One window: logs in, lands on the dashboard, then the test continues in the same window."""
    context = browser_instance.new_context()
    page = context.new_page()
    login = LoginPage(page)
    login.open_login()
    login.login(EMAIL, PASSWORD)
    assert login.is_dashboard_loaded(), "Setup failed: could not log in. Check your .env credentials."
    yield page
    context.close()
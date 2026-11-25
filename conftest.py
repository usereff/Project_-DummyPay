
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

from pages.login_page import LoginPage
from utilities.config import BASE_URL, EMAIL, PASSWORD, HEADLESS


AUTH_FILE = Path(__file__).parent / ".auth" / "state.json"


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
    """Clean, NOT logged-in window. Used by login tests."""
    context = browser_instance.new_context()
    page = context.new_page()

    yield LoginPage(page)

    context.close()


@pytest.fixture(scope="session")
def auth_state(browser_instance):
    """Log in once per test session and save authentication state."""

    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    print("\n>>> Performing Login - auth_state")
    context = browser_instance.new_context()
    page = context.new_page()

    login = LoginPage(page)
    login.open_login()
    login.login(EMAIL, PASSWORD)

    assert login.is_dashboard_loaded(), (
        "Setup failed: could not log in. Check your credentials."
    )

    context.storage_state(path=str(AUTH_FILE))

    context.close()

    return str(AUTH_FILE)


@pytest.fixture
def logged_in_page(browser_instance, auth_state):
    """Create a new page using the saved authenticated state."""

    context = browser_instance.new_context(
        storage_state=auth_state
    )

    page = context.new_page()
    

    page.goto(BASE_URL)
    page.wait_for_selector("text=Total balance")
    yield page

    context.close()
    

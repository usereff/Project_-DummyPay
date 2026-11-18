import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright
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


@pytest.fixture(scope="session")
def auth_state(browser_instance):
    """Log in once per run and save the session to a file."""
    AUTH_FILE.parent.mkdir(exist_ok=True)
    context = browser_instance.new_context()
    page = context.new_page()
    page.goto(f"{BASE_URL}/login")
    page.fill("input[type='email']", EMAIL)
    page.fill("input[type='password']", PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_selector("text=Total balance")
    context.storage_state(path=str(AUTH_FILE))
    context.close()
    return str(AUTH_FILE)


@pytest.fixture
def logged_in_page(browser_instance, auth_state):
    """A fresh page that is already logged in, opened on the dashboard."""
    context = browser_instance.new_context(storage_state=auth_state)
    page = context.new_page()
    page.goto(BASE_URL)
    page.wait_for_selector("text=Total balance")
    yield page
    context.close()
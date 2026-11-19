import pytest
from pages.test_sendMoney_page import SendMoneyPage

@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_sm_001_unregistered_email_shows_error(logged_in_page):
    """SM-001: Verify that an error is displayed when entering an unregistered email."""

    send_money = SendMoneyPage(logged_in_page)
    # logged_in_page.pause()
    # Arrange
    unregistered_email = "notregistered123456@example.com"

    # Act
    send_money.open("/send")
    send_money.enter_recipient_email(unregistered_email)
    send_money.click_find_recipient()

    # Assert
    assert send_money.is_unregistered_email_error_visible(), (
        "Expected error message was not displayed for an unregistered email."
    )
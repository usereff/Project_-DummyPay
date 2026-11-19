from decimal import Decimal, ROUND_HALF_UP

import pytest
from playwright.sync_api import expect

from pages.test_sendMoney_page import SendMoneyPage
from pages.wallets_page import WalletsPage
from utilities.config import RECIPIENT_EMAIL


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_sm_002_registered_user_transfer_completes(logged_in_page):
    """SM-002: Verify that sending money to a registered user completes the full flow."""

    amount_to_send = Decimal("1.00")
    assert RECIPIENT_EMAIL, (
        "Set DUMMYPAY_RECIPIENT_EMAIL to the email of an existing recipient."
    )
    send_money = SendMoneyPage(logged_in_page)
    logged_in_page.pause()

    send_money.open("/send")
    send_money.wait_for_step("Recipient")
    send_money.enter_recipient_email(RECIPIENT_EMAIL)
    send_money.click_find_recipient()
    expect(logged_in_page.get_by_text(RECIPIENT_EMAIL, exact=True)).to_be_visible()
    recipient_currency = send_money.get_recipient_currency()
    send_money.click_continue()

    send_money.wait_for_step("Amount")
    send_money.enter_amount(str(amount_to_send))
    source_currency, balance_before = send_money.get_selected_wallet_balance()
    send_money.click_review_transfer()

    send_money.wait_for_step("Review")
    expect(logged_in_page.get_by_text(RECIPIENT_EMAIL, exact=True)).to_be_visible()
    expect(logged_in_page.get_by_role("button", name="Confirm & send")).to_be_visible()
    (
        summary_amount,
        summary_currency,
        exchange_rate,
        rate_source_currency,
        rate_recipient_currency,
        received_amount,
    ) = send_money.get_review_summary()

    assert summary_amount == amount_to_send, (
        f"Review shows {summary_amount} {summary_currency}, "
        f"but {amount_to_send} was entered."
    )
    assert summary_currency == source_currency == rate_source_currency, (
        "The source wallet currency does not match the transaction summary."
    )
    assert rate_recipient_currency == recipient_currency, (
        f"Expected conversion to {recipient_currency}, "
        f"but review shows {rate_recipient_currency}."
    )
    expected_received_amount = (summary_amount * exchange_rate).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert received_amount == expected_received_amount, (
        f"Expected recipient to receive {expected_received_amount} "
        f"{rate_recipient_currency}, got {received_amount}."
    )

    send_money.confirm_and_send()
    expect(
        logged_in_page.get_by_text("Transfers can't be reversed", exact=False)
    ).to_be_visible()
    send_money.click_send_now()

    send_money.wait_for_step("Done")
    wallets = WalletsPage(logged_in_page)
    wallets.open_from_sidebar()
    balance_after = Decimal(
        str(wallets.get_wallet_balance(source_currency))
    ).quantize(Decimal("0.01"))
    expected_balance_after = balance_before - amount_to_send
    assert abs(balance_after - expected_balance_after) <= Decimal("0.01"), (
        f"Expected {source_currency} balance to decrease from {balance_before} "
        f"to {expected_balance_after}, but it is {balance_after}."
    )


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
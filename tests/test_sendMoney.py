from decimal import Decimal, ROUND_HALF_UP

import pytest
from playwright.sync_api import expect

from pages.sendMoney_page import SendMoneyPage
from pages.wallets_page import WalletsPage
from utilities.config import EMAIL, RECIPIENT_EMAIL


def _transaction_detail_value(transaction_details, label):
    value = transaction_details.locator(
        "dt", has_text=label
    ).locator("xpath=following-sibling::dd")
    expect(value).to_be_visible()
    return value.inner_text().strip()


@pytest.mark.parametrize(
    ("review_text", "expected_summary"),
    [
        pytest.param(
            """You send
₪1.00
Sending currency
ILS
Exchange rate
No conversion (same currency)
Recipient gets
₪1.00""",
            (
                Decimal("1.00"),
                "ILS",
                Decimal("1"),
                "ILS",
                "ILS",
                Decimal("1.00"),
            ),
            id="same-currency-no-conversion",
        ),
        pytest.param(
            """You send
$1,000.00
Sending currency
USD
Exchange rate
1 USD = 0.92 EUR
Recipient gets
€920,00""",
            (
                Decimal("1000.00"),
                "USD",
                Decimal("0.92"),
                "USD",
                "EUR",
                Decimal("920.00"),
            ),
            id="cross-currency-conversion",
        ),
    ],
)
def test_review_summary_parses_conversion_details(review_text, expected_summary):
    """Verify same-currency and converted review summaries are parsed correctly."""
    assert SendMoneyPage._parse_review_summary(review_text) == expected_summary


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

    send_money.open("/history")
    previous_rows = logged_in_page.get_by_test_id("transaction-row")
    previous_transaction_id = None
    if previous_rows.count():
        previous_rows.first.click()
        previous_details = logged_in_page.get_by_test_id("transaction-detail")
        previous_transaction_id = _transaction_detail_value(
            previous_details, "Transaction ID"
        )
        logged_in_page.get_by_role("dialog").get_by_role(
            "button", name="Close"
        ).click()

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
    assert exchange_rate > 0, f"Expected a positive exchange rate, got {exchange_rate}."
    if source_currency == recipient_currency:
        assert exchange_rate == Decimal("1"), (
            "Transfers between the same currency must use a 1:1 exchange rate."
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
    assert balance_after == expected_balance_after, (
        f"Expected {source_currency} balance to decrease from {balance_before} "
        f"to {expected_balance_after}, but it is {balance_after}."
    )

    send_money.open("/history")
    expect(
        logged_in_page.get_by_role("heading", name="Transaction History")
    ).to_be_visible()
    latest_transfer = logged_in_page.get_by_test_id("transaction-row").first
    expect(latest_transfer).to_be_visible()
    latest_transfer.click()

    transaction_details = logged_in_page.get_by_test_id("transaction-detail")
    expect(transaction_details).to_be_visible()
    transaction_id = _transaction_detail_value(transaction_details, "Transaction ID")
    assert transaction_id
    assert transaction_id != previous_transaction_id, (
        "The latest transaction is unchanged; the transfer was not recorded."
    )
    assert _transaction_detail_value(transaction_details, "Status").lower() == "completed"
    assert _transaction_detail_value(
        transaction_details, "Recipient"
    ).endswith(RECIPIENT_EMAIL)
    sent_text = _transaction_detail_value(transaction_details, "Amount sent")
    assert SendMoneyPage._extract_amount(sent_text) == amount_to_send, (
        f"Expected {amount_to_send} to be recorded as sent, got {sent_text!r}."
    )
    assert _transaction_detail_value(
        transaction_details, "Sending currency"
    ) == source_currency
    received_text = _transaction_detail_value(
        transaction_details, "Amount received"
    )
    assert SendMoneyPage._extract_amount(received_text) == expected_received_amount
    assert received_text.endswith(f"({rate_recipient_currency})"), (
        f"Expected received currency {rate_recipient_currency}, "
        f"but transaction history shows {received_text!r}."
    )


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_sm_003_cannot_send_money_to_self(logged_in_page):
    """SM-003: Verify that a user cannot send money to their own email."""

    send_money = SendMoneyPage(logged_in_page)

    send_money.open("/send")
    send_money.wait_for_step("Recipient")
    send_money.enter_recipient_email(EMAIL)
    send_money.click_find_recipient()

    expect(logged_in_page.locator(send_money.SELF_TRANSFER_ERROR)).to_be_visible()
    send_money.wait_for_step("Recipient")
    expect(logged_in_page.locator(send_money.CONTINUE_BUTTON)).to_have_count(0)


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
@pytest.mark.parametrize(
    ("amount_mode", "amount_case"),
    [
        pytest.param("I send", "zero", id="i-send-zero"),
        pytest.param("I send", "over-balance", id="i-send-over-balance"),
        pytest.param("Recipient gets", "zero", id="recipient-gets-zero"),
        pytest.param("Recipient gets", "over-balance", id="recipient-gets-over-balance"),
    ],
)
def test_sm_004_invalid_amount_shows_error_and_blocks_transfer(
    logged_in_page, amount_mode, amount_case
):
    """SM-004: Verify zero and over-balance amounts are rejected in both amount modes."""

    assert RECIPIENT_EMAIL, (
        "Set DUMMYPAY_RECIPIENT_EMAIL to the email of an existing recipient."
    )
    send_money = SendMoneyPage(logged_in_page)

    send_money.open("/send")
    send_money.wait_for_step("Recipient")
    send_money.enter_recipient_email(RECIPIENT_EMAIL)
    send_money.click_find_recipient()
    expect(logged_in_page.get_by_text(RECIPIENT_EMAIL, exact=True)).to_be_visible()
    send_money.click_continue()
    send_money.wait_for_step("Amount")
    send_money.select_amount_mode(amount_mode)

    _, available_balance = send_money.get_selected_wallet_balance()

    if amount_case == "zero":
        amount = "0"
    else:
        amount = str(available_balance + Decimal("0.01"))

    send_money.enter_amount(amount)
    send_money.click_review_transfer()

    error = logged_in_page.get_by_role("alert")
    if amount_case == "zero":
        expect(error).to_have_text("Amount must be greater than zero.")
    elif amount_mode == "I send":
        expect(error).to_contain_text("You only have")
        expect(error).to_contain_text(f"{available_balance:,.2f} available.")
    else:
        expect(error).to_have_text("Insufficient funds in the selected wallet.")

    send_money.wait_for_step("Amount")
    expect(logged_in_page.get_by_role("button", name="Confirm & send")).to_have_count(0)
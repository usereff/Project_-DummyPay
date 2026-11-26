import re

import pytest
from playwright.sync_api import expect

from pages.transaction_history_page import TransactionHistoryPage


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_th_001_history_page_shows_transactions_and_pagination(logged_in_page):
    """TH-001: Verify the history page and its transaction list are displayed."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()

    expect(logged_in_page.get_by_label("From date")).to_be_visible()
    expect(logged_in_page.get_by_label("To date")).to_be_visible()
    expect(logged_in_page.get_by_text("Type", exact=True)).to_be_visible()
    expect(logged_in_page.get_by_text("Currency", exact=True)).to_be_visible()
    expect(history.rows.first).to_be_visible()
    expect(history.transaction_count).to_be_visible()
    expect(history.page_indicator).to_have_text(re.compile(r"^Page 1 of \d+$"))
    expect(logged_in_page.get_by_role("button", name="Previous")).to_be_disabled()


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
@pytest.mark.parametrize("transaction_type", ["Sent", "Received"])
def test_th_002_type_filter_shows_matching_transactions(
    logged_in_page, transaction_type
):
    """TH-002: Verify that the type filter only shows the selected transaction type."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()
    transaction_count_before = history.transaction_count.inner_text()

    history.select_type(transaction_type)
    expect(history.transaction_count).not_to_have_text(transaction_count_before)
    expect(history.rows.first).to_contain_text(f"{transaction_type} ·")

    for row in history.rows.all():
        assert f"{transaction_type} ·" in row.inner_text()


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
@pytest.mark.parametrize(
    ("transaction_type", "currency", "symbol"),
    [
        pytest.param("Sent", "EUR", "€", id="sent-eur"),
        pytest.param("Received", "ILS", "₪", id="received-ils"),
    ],
)
def test_th_003_currency_filter_shows_matching_transactions(
    logged_in_page, transaction_type, currency, symbol
):
    """TH-003: Verify type and currency filters return matching transaction rows."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()

    history.select_type(transaction_type)
    sent_or_received_count = history.transaction_count.inner_text()
    expect(history.transaction_count).not_to_have_text(sent_or_received_count)
    expect(history.rows.first).to_contain_text(f"{transaction_type} ·")
    transaction_count_before_currency = history.transaction_count.inner_text()
    history.select_currency(currency)
    expect(history.transaction_count).not_to_have_text(transaction_count_before_currency)
    expect(history.rows.first).to_contain_text(symbol)

    for row in history.rows.all():
        text = row.inner_text()
        assert f"{transaction_type} ·" in text
        assert symbol in text


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.medium
def test_th_004_valid_date_range_keeps_matching_transactions(logged_in_page):
    """TH-004: Verify a broad valid date range includes the existing transactions."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()
    transaction_count_before = history.transaction_count.inner_text()

    history.set_date_range("2000-01-01", "2099-12-31")

    expect(history.transaction_count).to_have_text(transaction_count_before)
    expect(history.rows.first).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_th_005_date_range_without_transactions_shows_empty_state(logged_in_page):
    """TH-005: Verify a date range with no matching data shows the empty state."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()

    history.set_date_range("1900-01-01", "1900-01-02")

    expect(history.no_results).to_be_visible()
    expect(history.rows).to_have_count(0)
    expect(logged_in_page.get_by_text(
        "Try changing or clearing the filters.", exact=True
    )).to_be_visible()


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.medium
def test_th_006_reversed_date_range_shows_no_transactions(logged_in_page):
    """TH-006: Verify a start date later than the end date returns no transactions."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()

    history.set_date_range("2099-12-31", "2000-01-01")

    expect(history.no_results).to_be_visible()
    expect(history.rows).to_have_count(0)


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.medium
def test_th_007_clear_resets_all_history_filters(logged_in_page):
    """TH-007: Verify Clear resets both date fields and selected filters."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()
    history.select_type("Sent")
    history.select_currency("EUR")
    history.set_date_range("2000-01-01", "2099-12-31")

    history.clear_filters()

    expect(logged_in_page.locator(history.FROM_DATE)).to_have_value("")
    expect(logged_in_page.locator(history.TO_DATE)).to_have_value("")
    expect(logged_in_page.locator(history.TYPE_FILTER)).to_contain_text("All types")
    expect(history.page.locator(history.CURRENCY_FILTER)).to_contain_text(
        "All currencies"
    )
    expect(history.rows.first).to_be_visible()


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.medium
def test_th_008_pagination_moves_forward_and_back(logged_in_page):
    """TH-008: Verify Next and Previous navigate between transaction pages."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()

    next_button = logged_in_page.get_by_role("button", name="Next", exact=True)
    if next_button.is_disabled():
        expect(history.page_indicator).to_have_text("Page 1 of 1")
        return

    first_page_first_row = history.rows.first.inner_text()
    next_button.click()
    expect(history.page_indicator).to_have_text(re.compile(r"^Page 2 of \d+$"))
    expect(history.rows.first).to_be_visible()
    expect(history.rows.first).not_to_have_text(first_page_first_row)

    logged_in_page.get_by_role("button", name="Previous", exact=True).click()
    expect(history.page_indicator).to_have_text(re.compile(r"^Page 1 of \d+$"))
    expect(history.rows.first).to_contain_text(
        first_page_first_row.splitlines()[1]
    )
    expect(history.rows.first).to_contain_text(first_page_first_row.splitlines()[2])


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_th_009_transaction_row_opens_and_closes_details(logged_in_page):
    """TH-009: Verify selecting a transaction shows its details."""
    history = TransactionHistoryPage(logged_in_page)
    history.open_history()
    history.open_transaction()

    for label in (
        "Transaction ID",
        "Date & time",
        "Type",
        "Status",
        "Sender",
        "Recipient",
        "Amount sent",
        "Sending currency",
        "Amount received",
        "Exchange rate",
    ):
        value = history.detail_value(label)
        expect(value).to_be_visible()
        assert value.inner_text().strip(), f"{label} should have a value."

    expect(history.detail_value("Status")).to_have_text("completed")
    history.close_transaction()
    expect(logged_in_page.get_by_role("dialog")).to_have_count(0)

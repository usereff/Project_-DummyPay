from uuid import uuid4

import pytest
from playwright.sync_api import expect

from pages.payment_cards_page import PaymentCardsPage


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_pc_001_add_payment_card_successfully(logged_in_page):
    """PC-001: Add the example card and verify it appears in Payment Cards."""
    cardholder = "JO"
    card_number = "4111 1111 1111 1111"
    expiry = "03/30"
    cvv = "737"

    payment_cards = PaymentCardsPage(logged_in_page)
    payment_cards.open_from_sidebar()

    card_rows = payment_cards.get_card_rows(
        cardholder,
        card_number[-4:],
        expiry,
    )
    created_by_test = card_rows.count() == 0
    if created_by_test:
        payment_cards.add_card(cardholder, card_number, expiry, cvv)

    try:
        expect(card_rows.first).to_be_visible()
        expect(card_rows.first).to_contain_text(cardholder)
        expect(card_rows.first).to_contain_text(card_number[-4:])
        expect(card_rows.first).to_contain_text(f"Exp {expiry}")
    finally:
        if created_by_test and card_rows.count():
            logged_in_page.on("dialog", lambda dialog: dialog.accept())
            payment_cards.remove_card(card_rows.first)
            expect(card_rows).to_have_count(0)
            logged_in_page.reload(wait_until="networkidle")
            expect(logged_in_page.locator(payment_cards.TITLE)).to_be_visible()
            payment_cards.wait_for_cards_loaded()
            expect(card_rows).to_have_count(0)


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_pc_002_rejects_card_with_invalid_number(logged_in_page):
    """PC-002: Reject a card number that fails the checksum validation."""
    payment_cards = PaymentCardsPage(logged_in_page)
    payment_cards.open_from_sidebar()
    payment_cards.add_card(
        cardholder="INVALID CARD",
        card_number="4111 1111 1111 1112",
        expiry="03/30",
        cvv="737",
    )

    dialog = logged_in_page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    expect(dialog).to_contain_text(
        "Card number is not valid (checksum failed)."
    )
    expect(
        payment_cards.get_card_rows("INVALID CARD", "1112", "03/30")
    ).to_have_count(0)


@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_pc_003_remove_payment_card(logged_in_page):
    """PC-003: Remove a card created by this test from the cards list."""
    suffix = uuid4().hex[:6].upper().translate(
        str.maketrans("0123456789", "ABCDEFGHIJ")
    )
    cardholder = f"DEL{suffix}"
    card_number = "4111 1111 1111 1111"
    expiry = "03/30"

    payment_cards = PaymentCardsPage(logged_in_page)
    payment_cards.open_from_sidebar()
    logged_in_page.on("dialog", lambda dialog: dialog.accept())

    card_rows = payment_cards.get_card_rows(
        cardholder,
        card_number[-4:],
        expiry,
    )
    payment_cards.add_card(
        cardholder=cardholder,
        card_number=card_number,
        expiry=expiry,
        cvv="737",
    )

    try:
        expect(card_rows).to_have_count(1)
        payment_cards.remove_card(card_rows.first)
        expect(card_rows).to_have_count(0)
        logged_in_page.reload(wait_until="networkidle")
        expect(logged_in_page.locator(payment_cards.TITLE)).to_be_visible()
        payment_cards.wait_for_cards_loaded()
        expect(card_rows).to_have_count(0)
    finally:
        if card_rows.count():
            payment_cards.remove_card(card_rows.first)
            expect(card_rows).to_have_count(0)

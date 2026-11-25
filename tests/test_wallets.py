import pytest
from pages.wallets_page import WalletsPage


@pytest.fixture
def wallets_page(logged_in_page):
    wallets = WalletsPage(logged_in_page)
    wallets.open_from_sidebar()
    wallets.reset_conversion_form()
    return wallets


# WL-001 (חיובית, Regression): הסכום המומר שווה לסכום כפול השער
@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_wl_001_conversion_preview_equals_amount_times_rate(wallets_page):
    """WL-001: Verify that the converted amount equals the entered amount multiplied by the rate."""
    amount = 200

    wallets_page.enter_amount(amount)

    _, rate, _ = wallets_page.get_conversion_rate()
    expected = round(amount * rate, 2)
    assert wallets_page.wait_for_converted_amount(expected), (
        f"Expected {expected}, got {wallets_page.get_converted_amount()}"
    )


# WL-002 (חיובית, Regression): היתרה הכוללת שווה לסכום הארנקים אחרי המרה למטבע התצוגה
@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_wl_002_total_balance_equals_sum_of_wallets(wallets_page):
    """WL-002: Verify that the total balance equals the sum of all wallets converted to the display currency."""
    expected = wallets_page.calculate_expected_total()

    actual = wallets_page.get_total_balance()

    assert abs(actual - expected) <= 0.01, f"Expected ~{expected:.2f}, got {actual}"


# WL-003 (חיובית, Regression): Swap מחליף בין מטבע המקור למטבע היעד
@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.medium
def test_wl_003_swap_reverses_currencies(wallets_page):
    """WL-003: Verify that Swap reverses the From and To currencies and the rates are inverse."""
    from_cur, rate, to_cur = wallets_page.get_conversion_rate()

    wallets_page.click_swap()

    assert wallets_page.wait_for_swapped_rate(from_cur, to_cur, rate), (
        f"After Swap expected {to_cur}->{from_cur} with inverse rate of {rate}, "
        f"got {wallets_page.get_conversion_rate()}"
    )



# WL-004 (שלילית, Regression): סכום שלילי מציג שגיאה ולא מבצע המרה
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_wl_004_negative_amount_shows_error(wallets_page):
    """WL-004: Verify that a negative amount shows a validation error and no converted amount."""
    wallets_page.enter_amount(-5)

    assert wallets_page.is_amount_error_visible(), "No error shown for negative amount"
    assert wallets_page.is_converted_amount_empty(), "A converted amount was shown for a negative amount"


# WL-005 (שלילית, Regression): אותיות בשדה הסכום מציגות שגיאה ולא מבצעות המרה
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_wl_005_letters_in_amount_show_error(wallets_page):
    """WL-005: Verify that letters in the Amount field show a validation error and no converted amount."""
    wallets_page.enter_amount("abc")

    assert wallets_page.is_amount_error_visible(), "No error shown for letters in amount"
    assert wallets_page.is_converted_amount_empty(), "A converted amount was shown for letters"


# WL-006 (שלילית, Regression): סכום אפס לא מבצע המרה (הנחה: מוצגת שגיאה)
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.medium
def test_wl_006_zero_amount_shows_error(wallets_page):
    """WL-006: Verify that an amount of zero shows a validation error and no converted amount."""
    wallets_page.enter_amount(0)

    assert wallets_page.is_amount_error_visible(), "No error shown for zero amount"
    assert wallets_page.is_converted_amount_empty(), "A converted amount was shown for zero"



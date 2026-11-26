import pytest
from playwright.sync_api import expect

from pages.bank_accounts_page import BankAccountsPage


# מתחבר (דרך logged_in_page), נכנס ל-Bank Accounts דרך התפריט, ומנקה אחרי כל בדיקה
@pytest.fixture
def bank_accounts(logged_in_page):
    logged_in_page.on("dialog", lambda dialog: dialog.accept())
    page = BankAccountsPage(logged_in_page)
    page.open_from_sidebar()
    yield page
    page.cleanup_created()


# בודק שניסיון שגוי נדחה: החלון נשאר פתוח, יש משוב ולידציה (ואם צוין, ההודעה המדויקת), ולא נוסף חשבון
def _assert_rejected(page: BankAccountsPage, expected=(), **form):
    before = page.list_size()
    page.open_add_dialog()
    page.fill_form(**form)
    page.submit()

    assert page.is_dialog_open(), "The dialog closed, the invalid account may have been accepted"
    assert page.has_validation_feedback(), "No validation feedback was shown"
    for text in expected:
        assert page.has_error_text(text), f"Expected error was not shown: {text}"
    page.cancel()
    assert page.list_size() == before, "An account was added although the input was invalid"


# ---------- בדיקות חיוביות ----------

# BA-001 (חיובית, Smoke): העמוד נטען עם הכותרת, ההודעה והכפתור
@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.high
def test_ba_001_page_loads_with_title_notice_and_add_button(bank_accounts):
    """BA-001: Verify that the Bank Accounts page loads with its title, notice and Add button."""
    expect(bank_accounts.page.locator(bank_accounts.TITLE)).to_be_visible()
    expect(bank_accounts.page.get_by_text(bank_accounts.NOTICE_TEXT)).to_be_visible()
    expect(bank_accounts.add_button).to_be_visible()


# BA-002 (חיובית, Regression): חלון ההוספה מציג את כל השדות, ו-Cancel סוגר אותו
@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.medium
def test_ba_002_add_dialog_shows_fields_and_cancel_closes_it(bank_accounts):
    """BA-002: Verify that the Add dialog shows all fields and Cancel closes it."""
    bank_accounts.open_add_dialog()
    dialog = bank_accounts.dialog

    for label in ("Account holder name", "Bank name", "Country", "Currency", "IBAN or account number"):
        expect(dialog.get_by_label(label)).to_be_visible()
    bank_accounts.cancel()


# BA-003 (חיובית, Smoke): חשבון תקין נוסף ומופיע ברשימה
@pytest.mark.smoke
@pytest.mark.positive
@pytest.mark.high
def test_ba_003_add_valid_account_appears_in_list(bank_accounts):
    """BA-003: Verify that a valid bank account is added and appears in the list."""
    holder = bank_accounts.add_account()

    expect(bank_accounts.page.get_by_text(holder).first).to_be_visible()


# BA-004 (חיובית, Regression): מספר החשבון מוצג מוסתר (רק 4 ספרות אחרונות)
@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_ba_004_account_number_is_masked_in_list(bank_accounts):
    """BA-004: Verify that the full account number is not displayed, only a masked one."""
    number = "123456789012"
    holder = bank_accounts.add_account(number=number)
    expect(bank_accounts.page.get_by_text(holder).first).to_be_visible()
    text = bank_accounts.page_text()
    assert number[-4:] in text, "The last 4 digits are not displayed"
    assert number not in text, "The full account number is displayed (should be masked)"


# BA-005 (חיובית, Regression): ערכי גבול, 4 ספרות (מינימום) ו-20 ספרות (מקסימום) מתקבלים
@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.medium
@pytest.mark.parametrize(
    "number",
    [
        pytest.param("1234", id="min-4-digits"),
        pytest.param("12345678901234567890", id="max-20-digits"),
    ],
)
def test_ba_005_boundary_account_number_lengths_are_accepted(bank_accounts, number):
    """BA-005: Verify that account numbers of 4 and 20 digits are accepted."""
    holder = bank_accounts.add_account(number=number)

    expect(bank_accounts.page.get_by_text(holder).first).to_be_visible()


# BA-006 (חיובית, Regression): הסרת חשבון מעלימה אותו, גם אחרי רענון
@pytest.mark.regression
@pytest.mark.positive
@pytest.mark.high
def test_ba_006_remove_account_deletes_it_permanently(bank_accounts):
    """BA-006: Verify that removing an account deletes it, also after a page reload."""
    holder = bank_accounts.add_account()
    expect(bank_accounts.page.get_by_text(holder).first).to_be_visible()

    bank_accounts.remove_account(holder)
    expect(bank_accounts.page.get_by_text(holder)).to_have_count(0)

    bank_accounts.page.reload(wait_until="networkidle")
    expect(bank_accounts.page.locator(bank_accounts.TITLE)).to_be_visible()
    expect(bank_accounts.page.get_by_text(holder)).to_have_count(0)


# ---------- בדיקות שליליות ----------

# BA-007 (שלילית, Regression): טופס ריק לחלוטין נדחה
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_ba_007_empty_form_is_rejected(bank_accounts):
    """BA-007: Verify that submitting a completely empty form is rejected."""
    _assert_rejected(bank_accounts, choose_country=False, choose_currency=False)


# BA-008 (שלילית, Regression): בלי שם בעל חשבון נדחה
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_ba_008_missing_account_holder_name_is_rejected(bank_accounts):
    """BA-008: Verify that an account without an account holder name is rejected."""
    _assert_rejected(bank_accounts, bank="Test Bank", number="123456789012")


# BA-009 (שלילית, Regression): מספר קצר מדי (3 ספרות, מתחת לגבול) נדחה
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_ba_009_account_number_too_short_is_rejected(bank_accounts):
    """BA-009: Verify that an account number of 3 digits (below the minimum) is rejected."""
    _assert_rejected(bank_accounts, holder="Short Number", bank="Test Bank", number="123")


# BA-010 (שלילית, Regression): מספר ארוך מדי (21 ספרות, מעל הגבול) נדחה
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.high
def test_ba_010_account_number_too_long_is_rejected(bank_accounts):
    """BA-010: Verify that an account number of 21 digits (above the maximum) is rejected."""
    _assert_rejected(bank_accounts, holder="Long Number", bank="Test Bank", number="1" * 21)


# BA-011 (שלילית, Regression): אותיות במספר החשבון נדחות עם ההודעה "IBAN format is not valid."
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.medium
def test_ba_011_letters_in_account_number_are_rejected(bank_accounts):
    """BA-011: Verify that letters in the account number are rejected."""
    _assert_rejected(
        bank_accounts,
        expected=("IBAN format is not valid.",),
        holder="Letters Number",
        bank="Test Bank",
        number="ABCD1234",
    )


# BA-012 (שלילית, Regression): בלי מדינה ומטבע נדחה עם שתי הודעות "Choose a supported ..."
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.medium
def test_ba_012_missing_country_and_currency_is_rejected(bank_accounts):
    """BA-012: Verify that an account without a country and currency is rejected."""
    _assert_rejected(
        bank_accounts,
        expected=("Choose a supported country.", "Choose a supported currency."),
        holder="No Country",
        bank="Test Bank",
        number="123456789012",
        choose_country=False,
        choose_currency=False,
    )


# BA-013 (שלילית, Regression): ספרות בשם בעל החשבון נדחות
@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.medium
def test_ba_013_digits_in_account_holder_name_are_rejected(bank_accounts):
    """BA-013: Verify that digits in the account holder name are rejected."""
    _assert_rejected(
        bank_accounts,
        expected=("Account holder name may only contain letters",),
        holder="54fvgsv",
        bank="Test Bank",
        number="123456789012",
    )
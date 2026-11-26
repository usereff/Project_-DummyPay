import re
from uuid import uuid4

from playwright.sync_api import expect

from pages.base_page import BasePage
from utilities.config import BASE_URL, TIMEOUT


class BankAccountsPage(BasePage):
    """Page Object for the Bank Accounts page."""

    # Locators
    SIDEBAR_LINK = "a[href='/bank-accounts']"
    TITLE = "h1:has-text('Bank Accounts')"
    NOTICE_TEXT = "Bank accounts in DummyPay are simulated"
    EMPTY_STATE_TEXT = "No bank accounts yet"
    REMOVE_NAME = re.compile(r"remove|delete", re.I)

    # הודעות שגיאה אפשריות (בכוונה בלי טקסט העזר הקבוע "Enter a 4-20 digit...")
    FEEDBACK = re.compile(
        r"required|invalid|must|not valid|too short|too long|at least|between"
        r"|may only|choose a supported|format",
        re.I,
    )

    # מאתחל את העמוד ויוצר רשימה של חשבונות שנוצרו בבדיקות, למחיקה בסוף
    def __init__(self, page):
        super().__init__(page)
        self.created_holders = []

    # --- כלים ---

    # יוצר שם ייחודי מאותיות בלבד (השדה לא מקבל ספרות), כדי שלא יתנגש בנתונים קיימים
    @staticmethod
    def unique_text(prefix: str) -> str:
        letters = uuid4().hex[:6].upper().translate(str.maketrans("0123456789", "ABCDEFGHIJ"))
        return f"{prefix} {letters}"

    # מחזיר את חלון ההוספה (dialog)
    @property
    def dialog(self):
        return self.page.get_by_role("dialog")

    # מחזיר את כפתור "Add bank account" שבעמוד (לא זה שבתוך החלון)
    @property
    def add_button(self):
        return self.page.get_by_role("button", name="Add bank account").first

    # --- ניווט ---

    # עובר לעמוד Bank Accounts דרך התפריט בצד (מתחילים בדשבורד) וממתין שהעמוד ייטען
    def open_from_sidebar(self):
        self.page.click(self.SIDEBAR_LINK)
        self.page.wait_for_url(f"{BASE_URL}/bank-accounts")
        self.page.wait_for_selector(self.TITLE)
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

    # --- טופס ההוספה ---

    # פותח את חלון "Add a simulated bank account" וממתין שיופיע
    def open_add_dialog(self):
        self.add_button.click()
        expect(self.dialog).to_be_visible()

    # בוחר את האפשרות הראשונה האמיתית ברשימה נפתחת (Country או Currency)
    def _choose_first_option(self, label: str):
        field = self.dialog.get_by_label(label)
        try:
            field.select_option(index=1, timeout=3000)
        except Exception:
            field.click()
            self.page.get_by_role("option").first.click()

    # ממלא את הטופס. שדה שמועבר ריק, או choose_*=False, נשאר ריק
    def fill_form(self, holder="", bank="", number="", choose_country=True, choose_currency=True):
        if holder:
            self.dialog.get_by_label("Account holder name").fill(holder)
        if bank:
            self.dialog.get_by_label("Bank name").fill(bank)
        if choose_country:
            self._choose_first_option("Country")
        if choose_currency:
            self._choose_first_option("Currency")
        if number:
            self.dialog.get_by_label("IBAN or account number").fill(number)

    # לוחץ על "Add bank account" בתוך החלון (אם הכפתור חסום, לא נתקעים)
    def submit(self):
        try:
            self.dialog.get_by_role("button", name="Add bank account").click(timeout=3000)
        except Exception:
            pass

    # לוחץ על Cancel וממתין שהחלון ייסגר
    def cancel(self):
        self.dialog.get_by_role("button", name="Cancel").click()
        expect(self.dialog).to_be_hidden()

    # מוסיף חשבון תקין, ממתין שהחלון ייסגר ומחזיר את שם בעל החשבון
    def add_account(self, holder=None, bank="Test Bank", number="123456789012"):
        holder = holder or self.unique_text("BA")
        self.created_holders.append(holder)
        self.open_add_dialog()
        self.fill_form(holder=holder, bank=bank, number=number)
        self.submit()
        expect(self.dialog).to_be_hidden(timeout=TIMEOUT)
        return holder

    # --- בדיקת מצב ---

    # בודק אם חלון ההוספה פתוח (True/False)
    def is_dialog_open(self) -> bool:
        return self.dialog.is_visible()

    # בודק שמוצג משוב ולידציה כלשהו: הודעת שגיאה, שדה לא תקין או טקסט שגיאה (מחכה עד 3 שניות)
    def has_validation_feedback(self, timeout: int = 3000) -> bool:
        try:
            expect(
                self.dialog.get_by_role("alert")
                .or_(self.dialog.locator(":invalid"))
                .or_(self.dialog.get_by_text(self.FEEDBACK))
                .first
            ).to_be_visible(timeout=timeout)
            return True
        except AssertionError:
            return False

    # בודק שהודעת שגיאה מסוימת (טקסט מדויק) מוצגת בחלון (מחכה עד 3 שניות)
    def has_error_text(self, text: str, timeout: int = 3000) -> bool:
        try:
            expect(self.dialog.get_by_text(text).first).to_be_visible(timeout=timeout)
            return True
        except AssertionError:
            return False

    # מחזיר כמה פעמים טקסט מסוים מופיע בעמוד (לבדיקת הוספה והסרה)
    def count_text(self, text: str) -> int:
        return self.page.get_by_text(text).count()

    # מחזיר את מספר החשבונות ברשימה לפי כפתורי Remove (החלון חייב להיות סגור)
    def list_size(self) -> int:
        return self.page.get_by_role("button", name=self.REMOVE_NAME).count()

    # מחזיר את כל טקסט העמוד (לבדיקת הסתרת מספר החשבון)
    def page_text(self) -> str:
        return self.page.locator("body").inner_text()

    # --- הסרה ---
    # מחזיר את האלמנט/כרטיס שמייצג את החשבון של holder ומכיל כפתור Remove
    def row(self, holder: str):
        remove_btn = self.page.get_by_role("button", name=self.REMOVE_NAME)
        return (
            self.page.locator("div, li, article, tr")
            .filter(has_text=holder)
            .filter(has=remove_btn)
            .last
        )

    # מחזיר את חלון האישור למחיקה (עובד גם אם הוא מסומן alertdialog וגם dialog)
    @property
    def confirm_dialog(self):
        return self.page.get_by_role("alertdialog").or_(self.page.get_by_role("dialog")).first

    # לוחץ על Remove בחלון האישור וממתין שהחלון ייסגר
    def _confirm_if_asked(self):
        try:
            self.confirm_dialog.wait_for(state="visible", timeout=3000)
        except Exception:
            return
        self.confirm_dialog.get_by_role("button", name="Remove", exact=True).click()
        expect(self.confirm_dialog).to_be_hidden()

    # מסיר חשבון לפי שם בעל החשבון (לוחץ Remove בשורה ומאשר בחלון)
    def remove_account(self, holder: str):
        self.row(holder).get_by_role("button", name=self.REMOVE_NAME).click()
        self._confirm_if_asked()

    # מוחק את כל החשבונות שהבדיקות יצרו (לא נכשל אם כבר נמחקו)
    def cleanup_created(self):
        for holder in self.created_holders:
            try:
                if self.count_text(holder):
                    self.remove_account(holder)
                    expect(self.page.get_by_text(holder)).to_have_count(0)
            except Exception:
                pass
import re
import time
from pages.base_page import BasePage
from utilities.config import BASE_URL, WALLETS_URL, TOLERANCE

class WalletsPage(BasePage):
    """Page Object for the Wallets page."""

    # Locators
    WALLETS_LINK = "a[href='/wallets']"
    TITLE = "h1:has-text('Wallets')"
    SWAP_BUTTON = "button:has-text('Swap')"

    # הודעות השגיאה האפשריות בשדה Amount
    ERROR_MESSAGES = [
        "Enter a valid positive number.",
        "Amount must be greater than zero.",
    ]

    # --- ניווט ---

    # עובר לעמוד Wallets דרך התפריט בצד (מתחילים בדשבורד)
    def open_from_sidebar(self):
        self.page.click(self.WALLETS_LINK)
        self.page.wait_for_url(f"{BASE_URL}/wallets")
        self.page.wait_for_selector(self.TITLE)
        self.page.wait_for_selector("text=Exchange rates")
        self.page.wait_for_selector("text=Rate:")


    # --- כלים פנימיים ---

    # מחזיר את כל הטקסט של העמוד
    def _page_text(self) -> str:
        return self.page.locator("body").inner_text()

    # ממיר טקסט כמו "3,652.71" למספר
    @staticmethod
    def _to_float(text: str) -> float:
        return float(text.replace(",", ""))

    # מחפש בעמוד ערך לפי תבנית. מנסה שוב עד 10 שניות, כי הנתונים נטענים עם עיכוב
    def _find(self, pattern: str, timeout: float = 10.0):
        end = time.time() + timeout
        while True:
            match = re.search(pattern, self._page_text(), re.S)
            if match:
                return match
            if time.time() > end:
                break
            time.sleep(0.3)
        raise AssertionError(
            f"Pattern not found on the page: {pattern}\n--- PAGE TEXT ---\n{self._page_text()}"
        )

    # מחכה עד שתנאי מתקיים (עד timeout שניות)
    @staticmethod
    def _wait_until(condition, timeout: float = 5.0) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            try:
                if condition():
                    return True
            except AssertionError:
                pass
            time.sleep(0.2)
        return False

    # --- Conversion preview ---

    # מקליד סכום בשדה Amount
    def enter_amount(self, amount):
        self.page.get_by_label("Amount").fill(str(amount))

    # מחזיר (מטבע מקור, שער, מטבע יעד) מהשורה "Rate: 1 EUR = 1.097454 USD"
    def get_conversion_rate(self):
        m = self._find(r"Rate:\s*1\s+([A-Z]{3})\s*=\s*([\d.,]+)\s+([A-Z]{3})")
        return m.group(1), self._to_float(m.group(2)), m.group(3)

    # מחזיר את הסכום המומר שמוצג תחת Converted amount
    def get_converted_amount(self) -> float:
        m = self._find(r"Converted amount\s*[^\d]*?([\d,]+\.\d{2})")
        return self._to_float(m.group(1))

    # מחכה שהסכום המומר יתעדכן לערך הצפוי (סטייה עד 0.01), מחזיר True/False
    def wait_for_converted_amount(self, expected: float) -> bool:
        return self._wait_until(lambda: abs(self.get_converted_amount() - expected) <= 0.01)

    # לוחץ על Swap
    def click_swap(self):
        self.page.click(self.SWAP_BUTTON)

    # מחכה שזוג המטבעות בשורת ה-Rate יהיה כמצופה
    # מחכה שזוג המטבעות יתחלף וגם שהשער יתעדכן להופכי של השער הקודם
    def wait_for_swapped_rate(self, from_cur: str, to_cur: str, old_rate: float) -> bool:
        def swapped():
            cur_from, cur_rate, cur_to = self.get_conversion_rate()
            return (
                cur_from == to_cur
                and cur_to == from_cur
                and abs(cur_rate * old_rate - 1) <= 0.001
            )
        return self._wait_until(swapped)

    # --- Total balance ---

    # מחזיר את היתרה הכוללת המוצגת (למשל 3652.71)
    # def get_total_balance(self) -> float:
    #     m = self._find(r"Total balance \(approximate\)\s*[^\d]*?([\d,]+\.\d{2})")
    #     return self._to_float(m.group(1))

    def get_total_balance(self):
        m = self._find(
            r"Total balance\s*[^\d]*?([\d,]+\.\d{2})"
        )
        return float(m.group(1).replace(",", ""))


    # מחזיר את מטבע התצוגה של היתרה הכוללת ("shown in EUR")
    def get_total_balance_currency(self) -> str:
        return self._find(r"shown in ([A-Z]{3})").group(1)

    # מחזיר רשימת קודי המטבעות של הארנקים, למשל ['ILS', 'EUR', 'GBP']
    def get_wallet_codes(self):
        codes = re.findall(r"\b([A-Z]{3})\s*·\s*[A-Z]", self._page_text())
        return list(dict.fromkeys(codes))

    # מחזיר את היתרה הזמינה של ארנק לפי קוד מטבע
    def get_wallet_balance(self, code: str) -> float:
        m = self._find(rf"\b{code}\s*·.*?Available balance\s*[^\d]*?([\d,]+\.\d{{2}})")
        return self._to_float(m.group(1))

    # מחזיר את השער מהמטבע הראשי למטבע אחר, מתוך Exchange rates
    def get_exchange_rate(self, base: str, code: str) -> float:
        if code == base:
            return 1.0
        m = self._find(rf"1 {base}\s*(?:→|->)\s*{code}\s*([\d.]+)")
        return float(m.group(1))

    # מחשב את היתרה הכוללת הצפויה: סכום כל הארנקים, כל אחד מחולק בשער שלו
    def calculate_expected_total(self) -> float:
        base = self.get_total_balance_currency()
        total = 0.0
        for code in self.get_wallet_codes():
            total += self.get_wallet_balance(code) / self.get_exchange_rate(base, code)
        return total


    # מוחק את תוכן שדה הסכום
    def clear_amount(self):
        self.page.get_by_label("Amount").fill("")

    # מחזיר True אם הודעת השגיאה מוצגת (מחכה עד 5 שניות)

    def is_amount_error_visible(self, timeout: int = 5000) -> bool:
        end = time.time() + (timeout / 1000.0)
        while time.time() < end:
            for msg in self.ERROR_MESSAGES:
                if self.page.locator(f"text={msg}").is_visible():
                    return True
            time.sleep(0.2)
        return False

    # מחזיר את הטקסט שמוצג בתיבת Converted amount (למשל "—")
    def get_converted_text(self) -> str:
        return self._find(r"Converted amount\s*\n?\s*([^\n]+)").group(1).strip()

    # בודק שלא מוצג סכום מומר מספרי (מוצג מקף או שום מספר)
    def is_converted_amount_empty(self) -> bool:
        return self._wait_until(lambda: not re.search(r"\d", self.get_converted_text()))

        # מחזיר את Conversion preview לברירת מחדל: סכום 100 והמטבעות המקוריים
    def reset_conversion_form(self):
        self.page.get_by_label("Amount").fill("100")
        self._wait_until(lambda: self.get_converted_amount() > 0)


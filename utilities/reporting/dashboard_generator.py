
import json
from pathlib import Path


# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTING_DIR = Path(__file__).resolve().parent

DATA_FILE = REPORTS_DIR / "test_results.json"
TEMPLATE_FILE = REPORTING_DIR / "dashboard_template.html"
CSS_FILE = REPORTING_DIR / "dashboard.css"
OUTPUT_FILE = REPORTS_DIR / "dashboard.html"


def load_report_data():
    """Load test execution results from the JSON file."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Test results file was not found: {DATA_FILE}"
        )

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def generate_dashboard():
    """Generate a standalone HTML dashboard."""

    report_data = load_report_data()

    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    css = CSS_FILE.read_text(encoding="utf-8")

    # Prevent HTML/script injection from JSON values.
    report_json = json.dumps(
        report_data,
        ensure_ascii=False,
        indent=2,
    )

    report_json = (
        report_json
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )

    html = template.replace("__DASHBOARD_CSS__", css)
    html = html.replace("__REPORT_DATA__", report_json)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(html, encoding="utf-8")

    print(f"\nDashboard generated successfully: {OUTPUT_FILE}")

    return OUTPUT_FILE


if __name__ == "__main__":
    generate_dashboard()

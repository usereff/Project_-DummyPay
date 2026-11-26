
import json
import platform
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pytest


# Markers that we want to display in the dashboard
KNOWN_MARKERS = {
    "smoke",
    "regression",
    "positive",
    "negative",
    "high",
    "medium",
    "low",
    "api",
}


def pytest_sessionstart(session):
    """Initialize dashboard data at the beginning of the test session."""

    session.config._dashboard_data = {
        "started_at": datetime.now().astimezone().isoformat(),
        "tests": defaultdict(list),
    }


def pytest_runtest_logreport(report):
    """Collect reports from setup, call and teardown phases."""

    config = report.config if hasattr(report, "config") else None

    # Pytest TestReport does not normally expose config.
    # The active plugin configuration is stored separately below.
    if config is None:
        return


def pytest_runtest_logreport(report):
    """Collect reports from all test execution phases."""

    # Access the plugin's active session data
    data = _dashboard_data

    if data is None:
        return

    data["tests"][report.nodeid].append({
        "phase": report.when,
        "outcome": report.outcome,
        "duration": report.duration,
        "error": str(report.longrepr) if report.failed else None,
        "markers": [
            marker
            for marker in KNOWN_MARKERS
            if marker in report.keywords
        ],
    })


_dashboard_data = None


def pytest_sessionstart(session):
    """Initialize dashboard data at the beginning of the test session."""

    global _dashboard_data

    _dashboard_data = {
        "started_at": datetime.now().astimezone().isoformat(),
        "tests": defaultdict(list),
    }


def _build_test_results(raw_tests):
    """Convert individual phase reports into one result per test."""

    results = []

    for nodeid, phases in raw_tests.items():
        outcomes = [phase["outcome"] for phase in phases]

        if "failed" in outcomes:
            status = "failed"
        elif "skipped" in outcomes:
            status = "skipped"
        else:
            status = "passed"

        markers = sorted({
            marker
            for phase in phases
            for marker in phase["markers"]
        })

        errors = [
            phase["error"]
            for phase in phases
            if phase["error"]
        ]

        test_file = nodeid.split("::")[0]
        test_name = nodeid.split("::")[-1]

        results.append({
            "test_id": nodeid,
            "test_name": test_name,
            "file": test_file,
            "module": Path(test_file).stem,
            "status": status,
            "duration": round(
                sum(phase["duration"] for phase in phases), 3
            ),
            "markers": markers,
            "test_type": [
                marker for marker in markers
                if marker in {"smoke", "regression", "api"}
            ],
            "category": [
                marker for marker in markers
                if marker in {"positive", "negative"}
            ],
            "priority": next(
                (
                    marker for marker in ("high", "medium", "low")
                    if marker in markers
                ),
                "unassigned",
            ),
            "error": errors[0] if errors else None,
        })

    return results


def pytest_sessionfinish(session, exitstatus):
    """Create the raw JSON report after the test session finishes."""

    if _dashboard_data is None:
        return

    tests = _build_test_results(_dashboard_data["tests"])

    passed = sum(test["status"] == "passed" for test in tests)
    failed = sum(test["status"] == "failed" for test in tests)
    skipped = sum(test["status"] == "skipped" for test in tests)

    finished_at = datetime.now().astimezone()

    report_data = {
        "project": "DummyPay",
        "started_at": _dashboard_data["started_at"],
        "finished_at": finished_at.isoformat(),
        "duration": round(
            sum(test["duration"] for test in tests), 3
        ),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pytest": pytest.__version__,
        },
        "summary": {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round(
                passed / len(tests) * 100, 2
            ) if tests else 0,
            "exit_status": int(exitstatus),
        },
        "tests": tests,
    }

    reports_dir = session.config.rootpath / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    output_file = reports_dir / "test_results.json"

    output_file.write_text(
        json.dumps(report_data, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nDashboard data generated: {output_file}")

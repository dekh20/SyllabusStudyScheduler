"""
Pytest hook that writes test_report.md after every run:
one row per test with its class, case type, description and PASS/FAIL.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

_rows = []


def pytest_runtest_logreport(report):
    if report.when != "call" and not (report.when == "setup" and report.failed):
        return
    nodeid = report.nodeid.split("::")
    cls = nodeid[1].replace("Test", "", 1) if len(nodeid) > 2 else ""
    _rows.append((cls, nodeid[-1], report.outcome.upper(), report.duration))


def pytest_collection_modifyitems(items):
    for item in items:
        doc = (item.function.__doc__ or "").strip()
        _docs[item.name] = doc


_docs = {}


def pytest_sessionfinish(session, exitstatus):
    if not _rows:
        return
    passed = sum(1 for r in _rows if r[2] == "PASSED")
    lines = [
        "# Study Assessment — Unit Test Report",
        "",
        f"Run: {datetime.now():%Y-%m-%d %H:%M}  ",
        "Framework: pytest  ",
        f"Result: **{passed} / {len(_rows)} passed**",
        "",
        "| # | Class | Test | Case | What it checks | Result |",
        "|---|-------|------|------|----------------|--------|",
    ]
    for i, (cls, name, outcome, _) in enumerate(_rows, 1):
        doc = _docs.get(name, "")
        case, _, desc = doc.partition("]")
        lines.append(
            f"| {i} | {cls} | `{name}` | {case.strip('[')} | {desc.strip()} | {outcome} |"
        )
    path = os.path.join(os.path.dirname(__file__), "test_report.md")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")

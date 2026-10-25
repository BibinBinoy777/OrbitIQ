"""Synthetic PDF extraction controls; no private PDFs or satellite inputs."""

import runpy
from pathlib import Path

import pytest

M = runpy.run_path(str(Path(__file__).parents[2] / "scripts/verify_report_pdf.py"))
READING = M["content_reading_order"]
COMPACT = M["compact"]
HEADER = "OrbitIQ / Investigation report"
WARNING = (
    "This is a current recomputation from exact archived references. "
    "Those binaries/resources are not embedded."
)


def page(number, total, body, placement="prefix"):
    footer = f"OrbitIQ · Page {number} of {total}"
    if placement == "prefix":
        return f"{HEADER}\n{footer}\n{body}\f"
    if placement == "suffix":
        return f"{body}\n{HEADER}\n{footer}\f"
    return f"{HEADER}\n{body}\n{footer}\f"


@pytest.mark.parametrize("placement", ["prefix", "suffix", "split"])
def test_cross_page_warning_keeps_every_body_word(placement):
    left, right = WARNING.split("Those ")
    raw = page(1, 2, left + "Those", placement) + page(2, 2, right, placement)
    assert COMPACT(WARNING) not in COMPACT(raw)  # Original false failure.
    assert COMPACT(WARNING) in COMPACT(READING(raw, 2))


def test_genuinely_omitted_warning_text_still_fails_the_same_content_assertion():
    raw = page(1, 2, "This is a current recomputation from exact archived references.")
    raw += page(2, 2, "Those resources are not embedded.")
    with pytest.raises(AssertionError):
        assert COMPACT(WARNING) in COMPACT(READING(raw, 2))


@pytest.mark.parametrize(
    "raw",
    [
        page(1, 2, "Body"),  # Missing raw page.
        page(1, 1, "Body").rstrip("\f"),  # Missing final page boundary.
        page(1, 1, "Body") + "Unexpected trailing content",
        page(1, 1, "Body").replace(HEADER, "Wrong header"),
        page(1, 1, "Body").replace("Page 1 of 1", "Page 2 of 1"),
        page(1, 1, "Body").replace("Page 1 of 1", "Page 1 of 2"),
        page(1, 1, "Body").replace("OrbitIQ · Page 1 of 1\n", ""),
        page(1, 1, "Body").replace(HEADER + "\n", ""),
        f"Body before\n{HEADER}\nOrbitIQ · Page 1 of 1\nBody after\f",
    ],
)
def test_missing_malformed_or_wrong_page_furniture_is_not_silently_deleted(raw):
    with pytest.raises(ValueError):
        READING(raw, 1)


def test_interior_lookalike_body_text_is_preserved():
    body = f"Body before\n{HEADER}\nOrbitIQ · Page 1 of 1\nBody after"
    assert READING(page(1, 1, body), 1) == body


def test_current_saved_or_offline_text_needs_no_special_content_exception():
    raw = page(1, 2, "Saved report identifier SYNTHETIC-ONLY-UUID")
    raw += page(2, 2, "Offline evidence warning and original source hash")
    content = READING(raw, 2)
    assert "SYNTHETIC-ONLY-UUID" in content
    assert "Offline evidence warning and original source hash" in content
    assert "Page 1 of 2" not in content and "Page 2 of 2" not in content

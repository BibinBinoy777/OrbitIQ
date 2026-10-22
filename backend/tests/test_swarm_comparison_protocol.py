"""Executable protocol controls, using synthetic metadata and mathematical points.

No original Swarm elements, ESA positions or operational alignment are exercised.
The tested documentation models cannot authorize or select a genuine input.
"""

import itertools
import runpy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
from test_swarm_pairing_assessment import sp3

ROOT = Path(__file__).resolve().parents[2]


def documented_model(filename, marker):
    text = (ROOT / "docs" / filename).read_text()
    block = text.split(f"<!-- {marker} -->", 1)[1].split("```python\n", 1)[1]
    code = block.split("```", 1)[0]
    namespace = {}
    exec(compile(code, filename, "exec"), namespace)
    return namespace


PROTOCOL = documented_model("phase-11.3.1-comparison-protocol.md", "protocol-model")
FRAME = documented_model(
    "phase-11.3.1-frame-alignment-investigation.md", "frame-control"
)
TIME = documented_model("phase-11.3.1-frame-alignment-investigation.md", "time-control")
ANCHOR = datetime(2014, 1, 1, tzinfo=UTC)  # Synthetic control, not an actual selection.
EPOCHS = [ANCHOR + timedelta(hours=h) for h in (1, 2)]


def candidate(name, epoch, **changes):
    return {
        "id": name,
        "epoch": epoch,
        "catalog_id": 39452,
        "designator": "2013-067B",
        "static_valid": True,
        **changes,
    }


def plan(records, *, epochs=None, gates=None):
    return PROTOCOL["planned_order"](
        records,
        ANCHOR,
        ANCHOR + timedelta(days=1),
        EPOCHS if epochs is None else epochs,
        dict.fromkeys(PROTOCOL["REQUIRED_GATES"], True) if gates is None else gates,
    )


def test_plan_is_order_invariant_and_never_scientific_authorization():
    records = [
        candidate("synthetic-old", ANCHOR - timedelta(days=2)),
        candidate("synthetic-new", ANCHOR - timedelta(days=1)),
        candidate("synthetic-future", ANCHOR + timedelta(minutes=1)),
    ]
    for order in itertools.permutations(records):
        result = plan(order)
        assert result == {
            "status": "PLAN_ONLY",
            "candidate_order": ["synthetic-new", "synthetic-old"],
            "selected_source_index": None,
            "comparison_ready": False,
        }


@pytest.mark.parametrize("gate", PROTOCOL["REQUIRED_GATES"])
def test_each_missing_gate_blocks_before_candidates_are_examined(gate):
    class ForbiddenRecords:
        def __iter__(self):
            raise AssertionError("Blocked protocol must not rank source records")

    gates = dict.fromkeys(PROTOCOL["REQUIRED_GATES"], True)
    del gates[gate]
    assert plan(ForbiddenRecords(), gates=gates)["status"] == "BLOCKED"


@pytest.mark.parametrize("claim", [None, False, 1, "true"])
def test_gate_claims_are_not_coerced_into_approval(claim):
    gates = dict.fromkeys(PROTOCOL["REQUIRED_GATES"], True)
    gates["frame_alignment"] = claim
    assert plan([], gates=gates)["status"] == "BLOCKED"


@pytest.mark.parametrize("same_identity", [False, True])
def test_ambiguity_never_falls_back_to_an_older_record(same_identity):
    records = [
        candidate("old", ANCHOR - timedelta(days=2)),
        candidate("new", ANCHOR - timedelta(days=1)),
        candidate("new" if same_identity else "competing", ANCHOR - timedelta(days=1)),
    ]
    assert plan(records)["status"] == "BLOCKED"
    assert plan(records)["candidate_order"] == []


def test_every_reference_epoch_obeys_inclusive_seven_day_constraint():
    at_boundary = candidate("boundary", EPOCHS[-1] - timedelta(days=7))
    assert plan([at_boundary])["candidate_order"] == ["boundary"]
    too_old = {**at_boundary, "epoch": at_boundary["epoch"] - timedelta(microseconds=1)}
    assert plan([too_old])["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "changes",
    [{"catalog_id": 25544}, {"designator": "different"}, {"static_valid": False}],
)
def test_target_and_static_failures_cannot_enter_plan(changes):
    assert plan([candidate("bad", ANCHOR, **changes)])["status"] == "BLOCKED"


@pytest.mark.parametrize(
    "epochs",
    [
        [],
        [ANCHOR, ANCHOR],
        [ANCHOR - timedelta(microseconds=1)],
        [ANCHOR.replace(tzinfo=None)],
    ],
)
def test_empty_duplicate_outside_and_naive_reference_times_block(epochs):
    assert plan([candidate("valid", ANCHOR)], epochs=epochs)["status"] == "BLOCKED"


def test_unqualified_frame_cannot_be_promoted_by_generic_label():
    qualifier = runpy.run_path(str(ROOT / "scripts/qualify_swarm_inputs.py"))
    igb08 = qualifier["frame_qualification"]("IGb08")
    generic = qualifier["frame_qualification"]("ITRS")
    assert igb08["status"] == "BLOCKED" and generic["status"] == "REJECTED"
    assert not igb08["identity_transform_assumed"]
    assert not igb08["helmert_transform_implemented"]


def test_header_diagnostic_matches_exact_rational_format_controls():
    assessor = runpy.run_path(str(ROOT / "scripts/assess_swarm_pairing.py"))
    actual = assessor["redundant_header_time"](sp3())  # Artificial P/EP fixture.
    control = TIME["time_control"]()
    assert Fraction(actual["mjd_minus_first_epoch_seconds"]) == control["mjd_delta_s"]
    assert control["mjd_delta_s"] == Fraction(3712, 10**11)
    assert control["quantum_s"] == Fraction(864, 10**11)
    assert control["nearest_delta_s"] == Fraction(256, 10**11)
    assert control["mjd_delta_s"] > control["quantum_s"] / 2
    assert Fraction(actual["week_seconds_minus_first_epoch_seconds"]) == -120
    assert control["week_delta_s"] == -120
    assert actual["status"] == "PARTIAL"
    assert not actual["mjd_fraction_used_for_conversion"]


@pytest.mark.parametrize(
    "years,expected",
    [
        ("0", ["7000000.00146", "0.0019", "0.0024"]),
        ("4", ["7000000.0023", "0.0019", "0.0020"]),
    ],
)
def test_published_itrf_row_against_literal_synthetic_controls(years, expected):
    # IERS chapter-4 update 2019, Table 4.1; not OrbitIQ-ITRS -> IGb08.
    result = FRAME["published_frame_control"](
        years, [Decimal("7000000"), Decimal(0), Decimal(0)]
    )
    assert result == [Decimal(v) for v in expected]


def test_full_moving_point_derivative_retains_terms_dropped_for_stations():
    # Independent exact central difference of a quadratic coordinate model.
    # Hypothetical coefficients/rates in SI; no spacecraft/reference data.
    def transformed(t):
        x, y = Fraction(7000000), Fraction(7500) * t
        scale = Fraction("1e-10") + Fraction("2e-18") * t
        rz = Fraction("3e-10") + Fraction("4e-18") * t
        return [
            x + Fraction("1e-6") * t + scale * x - rz * y,
            y + Fraction("2e-6") * t + scale * y + rz * x,
            Fraction("3e-6") * t,
        ]

    h = Fraction(1, 2)
    derivative = [
        (a - b) / (2 * h) for a, b in zip(transformed(h), transformed(-h), strict=True)
    ]
    assert derivative == [
        Fraction("-0.000001249986"),
        Fraction("7500.000002750028"),
        Fraction("0.000003"),
    ]
    station_simplified = [
        Fraction("0.000001000014"),
        Fraction("7500.000002000028"),
        Fraction("0.000003"),
    ]
    assert [a - b for a, b in zip(derivative, station_simplified, strict=True)] == [
        Fraction("-0.00000225"),
        Fraction("0.00000075"),
        Fraction(0),
    ]

"""Tests for price list parsing against a recorded slice of the us-east-1 price list."""

from pathlib import Path

import pytest

from cloudfit_provider_aws import parse_price_list

FIXTURE = Path(__file__).parent / "fixtures" / "us-east-1-sample.csv"


@pytest.fixture(scope="module")
def by_id():
    with FIXTURE.open(newline="") as f:
        return {m.id: m for m in parse_price_list(f, "us-east-1")}


def test_keeps_linux_instance_types(by_id):
    assert set(by_id) == {
        "c5d.large", "d3.xlarge", "g5.xlarge", "m1.small", "m5.large",
        "m7i-flex.large", "m7i.2xlarge", "p4d.24xlarge", "p5en.48xlarge", "t3.micro",
    }


def test_drops_non_gpu_accelerators_and_fractional_gpus(by_id):
    assert "inf2.xlarge" not in by_id   # Inferentia, listed as a GPU in the price list
    assert "g6f.large" not in by_id     # half an L4


def test_on_demand_price_ignores_windows_dedicated_and_3yr_rows(by_id):
    m5 = by_id["m5.large"]
    assert m5.price_hr == pytest.approx(0.096)
    assert m5.cud_1yr_price_hr == pytest.approx(0.06)   # 1yr standard No Upfront
    assert m5.provider == "aws"
    assert m5.region == "us-east-1"


def test_missing_reserved_price_leaves_cud_unset(by_id):
    assert by_id["p5en.48xlarge"].cud_1yr_price_hr is None


def test_spot_price_is_not_set(by_id):
    assert all(m.spot_price_hr is None for m in by_id.values())


def test_no_header_raises():
    with pytest.raises(ValueError, match="no header"):
        parse_price_list(['"FormatVersion","v1.0"\n'], "us-east-1")

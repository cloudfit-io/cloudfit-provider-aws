"""Tests for AWSProvider, with the price list download replaced by the fixture."""

from pathlib import Path

import pytest
from cloudfit import WorkloadProfile, rank
from cloudfit.providers.base import Provider

from cloudfit_provider_aws import AWSProvider, provider as provider_module

FIXTURE = Path(__file__).parent / "fixtures" / "us-east-1-sample.csv"


@pytest.fixture
def downloads(monkeypatch):
    """Serve the fixture for us-east-1, fail other regions, and record requests."""
    requested = []

    def fake_open(region, timeout):
        requested.append(region)
        if region != "us-east-1":
            raise OSError(f"HTTP Error 404 for {region}")
        return FIXTURE.read_text().splitlines(keepends=True)

    monkeypatch.setattr(provider_module, "open_price_list", fake_open)
    return requested


def test_implements_the_provider_contract():
    assert isinstance(AWSProvider(), Provider)


def test_fetch_instances_downloads_once_per_region(downloads):
    provider = AWSProvider()
    first = provider.fetch_instances("us-east-1")
    second = provider.fetch_instances("us-east-1")
    assert first is second
    assert downloads == ["us-east-1"]
    assert len(first) == 10


def test_get_pricing(downloads):
    provider = AWSProvider()
    assert provider.get_pricing("m5.large", "us-east-1") == pytest.approx(0.096)
    assert provider.get_pricing("no.such-type", "us-east-1") == 0.0


def test_all_regions_skips_a_failed_region(downloads):
    instances = AWSProvider().fetch_instances_all_regions(["us-east-1", "xx-nowhere-1"])
    assert len(instances) == 10
    assert downloads == ["us-east-1", "xx-nowhere-1"]


def test_results_rank_with_cloudfit_core(downloads):
    candidates = AWSProvider().fetch_instances("us-east-1")
    profile = WorkloadProfile(vcpu=8, ram_gb=32, optimize_for="balanced")
    best = rank(profile, candidates)[0]
    assert best.instance.provider == "aws"
    assert not best.disqualified

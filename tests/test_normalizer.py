"""Tests for normalize_offer: price list attributes to MachineType."""

import pytest
from cloudfit import perf_factor_for

from cloudfit_provider_aws.normalizer import normalize_offer


def attrs(instance_type, **extra):
    base = {
        "Instance Type": instance_type,
        "vCPU": "8",
        "Memory": "32 GiB",
        "Storage": "EBS only",
        "GPU": "",
        "GPU Memory": "NA",
        "Current Generation": "Yes",
    }
    base.update(extra)
    return base


def normalize(instance_type, **extra):
    return normalize_offer(attrs(instance_type, **extra), region="us-east-1", price_hr=1.0)


def test_basic_fields_and_perf_factor():
    m = normalize("m7i.2xlarge")
    assert (m.vcpu, m.ram_gb, m.gpu_count, m.local_ssd_tb) == (8, 32.0, 0, 0.0)
    assert m.perf_factor == perf_factor_for("m7i.2xlarge") == 1.2
    assert m.status == "active"


def test_memory_with_thousands_separator():
    assert normalize("u-6tb1.56xlarge", Memory="6,144 GiB").ram_gb == 6144.0


def test_previous_generation_is_deprecated():
    assert normalize("m1.small", **{"Current Generation": "No"}).status == "deprecated"


@pytest.mark.parametrize("storage, tb", [
    ("EBS only", 0.0),
    ("1 x 50 NVMe SSD", 0.05),
    ("2 x 1900 NVMe SSD", 3.8),
    ("900 GB NVMe SSD", 0.9),
    ("4 X 940 GB NVMe SSD", 3.76),
    ("3 x 2000 HDD", 0.0),
])
def test_local_ssd(storage, tb):
    assert normalize("c5d.large", Storage=storage).local_ssd_tb == tb


def test_gpu_vram_is_per_gpu_not_the_column_total():
    m = normalize("p4d.24xlarge", GPU="8", **{"GPU Memory": "320 GB HBM2"})
    assert (m.gpu_count, m.gpu_vram_gb, m.gpu_type) == (8, 40, "nvidia-a100")


def test_gpu_vram_is_right_when_the_column_is_per_gpu():
    m = normalize("p5en.48xlarge", GPU="8", **{"GPU Memory": "141 GB HBM3e"})
    assert (m.gpu_count, m.gpu_vram_gb, m.gpu_type) == (8, 141, "nvidia-h200")


def test_unknown_gpu_family_splits_column_total_and_has_no_model():
    m = normalize("g9.xlarge", GPU="2", **{"GPU Memory": "96 GB"})
    assert (m.gpu_count, m.gpu_vram_gb, m.gpu_type) == (2, 48, None)


@pytest.mark.parametrize("instance_type", [
    "inf2.xlarge", "trn1.2xlarge", "dl1.24xlarge", "f1.2xlarge", "vt1.3xlarge", "mac2.metal",
])
def test_unmodeled_families_are_skipped(instance_type):
    assert normalize(instance_type, GPU="1", **{"GPU Memory": "32 GB"}) is None


def test_fractional_gpu_is_skipped():
    assert normalize("g6f.large", GPU="0.5", **{"GPU Memory": "12 GB"}) is None

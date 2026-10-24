"""Normalizes AWS EC2 price list attributes into cloudfit MachineType objects."""

from __future__ import annotations

import re

from cloudfit.models import MachineType
from cloudfit.scorer import perf_factor_for

# Families whose accelerators are not GPUs (Inferentia, Trainium, Gaudi, FPGA,
# video transcode) or that do not run Linux (Mac). cloudfit does not model them,
# and the price list reports some of them as GPUs.
_EXCLUDED_KINDS = frozenset({"inf", "trn", "dl", "f", "vt", "mac"})

# Per-family accelerator model and VRAM per GPU. The price list has no GPU model
# column, and its "GPU Memory" column mixes per-GPU and total values across
# families, so known families use this table instead.
_GPU_FAMILIES: dict[str, tuple[str, int]] = {
    "p2":      ("nvidia-k80",          12),
    "g2":      ("nvidia-grid-k520",     4),
    "g3":      ("nvidia-tesla-m60",     8),
    "g3s":     ("nvidia-tesla-m60",     8),
    "g4dn":    ("nvidia-t4",           16),
    "g4ad":    ("amd-radeon-pro-v520",  8),
    "g5":      ("nvidia-a10g",         24),
    "g5g":     ("nvidia-t4g",          16),
    "g6":      ("nvidia-l4",           24),
    "gr6":     ("nvidia-l4",           24),
    "g6e":     ("nvidia-l40s",         48),
    "p3":      ("nvidia-v100",         16),
    "p3dn":    ("nvidia-v100",         32),
    "p4d":     ("nvidia-a100",         40),
    "p4de":    ("nvidia-a100-80gb",    80),
    "p5":      ("nvidia-h100",         80),
    "p5e":     ("nvidia-h200",        141),
    "p5en":    ("nvidia-h200",        141),
    "p6-b200": ("nvidia-b200",        179),
}

_KIND = re.compile(r"^[a-z]+")
_STORAGE = re.compile(r"^(?:(\d+)\s*x\s*)?([\d,.]+)\b.*\bSSD\b", re.IGNORECASE)


def normalize_offer(
    attrs: dict[str, str],
    region: str,
    price_hr: float,
    cud_1yr_price_hr: float | None = None,
) -> MachineType | None:
    """Convert one price list product's attributes into a MachineType.

    Returns None for a family cloudfit does not model (non-GPU accelerators,
    Mac) or a fractional-GPU instance, whose share of a GPU the schema cannot
    express.
    """
    instance_type = attrs["Instance Type"]
    family = instance_type.split(".")[0]
    kind_match = _KIND.match(family)
    if kind_match is None or kind_match.group(0) in _EXCLUDED_KINDS:
        return None

    gpu = _gpu(family, attrs.get("GPU", ""), attrs.get("GPU Memory", ""))
    if gpu is None:
        return None
    gpu_count, gpu_vram_gb, gpu_type = gpu

    return MachineType(
        id=instance_type,
        provider="aws",
        vcpu=int(attrs["vCPU"]),
        ram_gb=_number(attrs.get("Memory", "")),
        price_hr=price_hr,
        cud_1yr_price_hr=cud_1yr_price_hr,
        local_ssd_tb=_local_ssd_tb(attrs.get("Storage", "")),
        gpu_count=gpu_count,
        gpu_vram_gb=gpu_vram_gb,
        gpu_type=gpu_type,
        region=region,
        status="active" if attrs.get("Current Generation") != "No" else "deprecated",
        perf_factor=perf_factor_for(instance_type),
    )


def _gpu(
    family: str, count_text: str, memory_text: str
) -> tuple[int, int | None, str | None] | None:
    """Return (gpu_count, vram_gb per GPU, gpu_type), or None for a fractional GPU."""
    if count_text in ("", "NA", "0"):
        return 0, None, None
    count = float(count_text)
    if count < 1 or not count.is_integer():
        return None
    known = _GPU_FAMILIES.get(family)
    if known is not None:
        return int(count), known[1], known[0]
    # Unknown GPU family: no model, and VRAM read as the column's total split
    # across the GPUs (the more common of the column's two conventions).
    total = _number(memory_text)
    return int(count), int(total / count) or None, None


def _local_ssd_tb(storage: str) -> float:
    """Local SSD capacity in TB from e.g. "2 x 1900 NVMe SSD"; HDD and EBS-only are 0."""
    match = _STORAGE.match(storage.strip())
    if match is None:
        return 0.0
    disks = int(match.group(1) or 1)
    size_gb = float(match.group(2).replace(",", ""))
    return round(disks * size_gb / 1000, 2)


def _number(text: str) -> float:
    """Leading number of e.g. "1,952 GiB"; 0.0 when absent."""
    match = re.match(r"\s*([\d,.]+)", text)
    return float(match.group(1).replace(",", "")) if match else 0.0

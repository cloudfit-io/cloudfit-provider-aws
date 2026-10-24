"""Reads the public AWS EC2 bulk price list into cloudfit MachineType objects.

AWS publishes the full EC2 offer for each region as a public CSV, with no
credentials or account needed. Each row is one price term for one product, and
also carries the product's attributes (vCPU, memory, GPU, storage, generation),
so one file gives both the catalog and its prices.

The files are large (about 300 MB for us-east-1), so they are streamed row by
row and never held in memory whole.
"""

from __future__ import annotations

import csv
import io
import logging
import urllib.error
import urllib.request
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from cloudfit.models import MachineType

from .normalizer import normalize_offer

logger = logging.getLogger(__name__)

PRICE_LIST_URL = (
    "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/{region}/index.csv"
)

# The rows cloudfit scores: a plain Linux instance on shared tenancy, billed per
# hour with no preinstalled software or license, and not a capacity reservation.
_LINUX_ON_DEMAND: dict[str, str] = {
    "Tenancy":           "Shared",
    "Operating System":  "Linux",
    "Pre Installed S/W": "NA",
    "License Model":     "No License required",
    "CapacityStatus":    "Used",
    "operation":         "RunInstances",
    "MarketOption":      "OnDemand",
    "Unit":              "Hrs",
}
_COMPUTE_FAMILIES = ("Compute Instance", "Compute Instance (bare metal)")


@dataclass
class _Offer:
    """Attributes and prices gathered for one instance type."""

    attrs: dict[str, str]
    on_demand: float = 0.0
    reserved_1yr: float = 0.0


def open_price_list(region: str, timeout: float = 120.0) -> Iterator[str]:
    """Stream the price list CSV for a region, line by line.

    Raises:
        ValueError: if AWS publishes no price list for ``region`` (usually a
            mistyped region code).
    """
    url = PRICE_LIST_URL.format(region=region)
    try:
        response = urllib.request.urlopen(url, timeout=timeout)
    except urllib.error.HTTPError as exc:
        exc.close()  # an HTTPError holds the open error response
        if exc.code in (403, 404):
            raise ValueError(
                f"No public EC2 price list for region {region!r} (HTTP {exc.code}). "
                "Check the region code; AWS_REGIONS lists the supported ones."
            ) from exc
        raise
    with response:
        yield from io.TextIOWrapper(response, encoding="utf-8", newline="")


def parse_price_list(lines: Iterable[str], region: str) -> list[MachineType]:
    """Parse price list CSV lines into MachineType objects for one region.

    Keeps Linux on-demand and 1-year standard No Upfront reserved prices (the
    reserved rate fills ``cud_1yr_price_hr``, cloudfit's 1-year commitment
    mode). Instance types without an on-demand price, and families cloudfit does
    not model (see normalizer.normalize_offer), are skipped.
    """
    offers: dict[str, _Offer] = {}
    for row in _rows(lines):
        if row.get("Product Family") not in _COMPUTE_FAMILIES:
            continue
        if any(row.get(column) != value for column, value in _LINUX_ON_DEMAND.items()):
            continue
        instance_type = row.get("Instance Type", "")
        if not instance_type:
            continue
        offer = offers.setdefault(instance_type, _Offer(attrs=row))
        price = _price(row.get("PricePerUnit", ""))
        if row.get("TermType") == "OnDemand":
            offer.on_demand = price
        elif (
            row.get("TermType") == "Reserved"
            and row.get("LeaseContractLength") == "1yr"
            and row.get("PurchaseOption") == "No Upfront"
            and row.get("OfferingClass") == "standard"
        ):
            offer.reserved_1yr = price

    instances: list[MachineType] = []
    for instance_type, offer in offers.items():
        if offer.on_demand <= 0:
            logger.debug("Skipped %s: no on-demand price", instance_type)
            continue
        machine = normalize_offer(
            offer.attrs,
            region=region,
            price_hr=offer.on_demand,
            cud_1yr_price_hr=offer.reserved_1yr or None,
        )
        if machine is not None:
            instances.append(machine)
    return instances


def _rows(lines: Iterable[str]) -> Iterator[dict[str, str]]:
    """Yield CSV rows as dicts, skipping the metadata lines before the header."""
    iterator = iter(lines)
    for line in iterator:
        if line.startswith('"SKU"'):
            header = next(csv.reader([line]))
            break
    else:
        raise ValueError("price list has no header row (expected a line starting with \"SKU\")")
    for values in csv.reader(iterator):
        yield dict(zip(header, values))


def _price(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0

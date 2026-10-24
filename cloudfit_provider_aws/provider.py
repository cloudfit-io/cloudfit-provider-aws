"""AWS EC2 provider for cloudfit-core."""

from __future__ import annotations

import logging

from cloudfit.models import MachineType
from cloudfit.providers.base import Provider

from .pricelist import open_price_list, parse_price_list
from .regions import AWS_REGIONS

logger = logging.getLogger(__name__)


class AWSProvider(Provider):
    """Fetches AWS EC2 instance types and prices and normalizes them for cloudfit-core.

    Reads AWS's public EC2 price list, so no AWS account or credentials are
    needed. Each region's list is a large download (about 300 MB for
    us-east-1), so fetch on a schedule, never on a request path. A fetched
    region is cached on the provider instance.

    Each instance carries its on-demand price, the 1-year standard No Upfront
    reserved price as ``cud_1yr_price_hr``, a ``perf_factor`` from cloudfit-core's
    AWS table, and the GPU model and per-GPU VRAM for GPU families. Spot prices
    are not included: they vary by availability zone and hour and are not in
    the public price list.

    Args:
        timeout: Network timeout in seconds for each price list download.

    Example:
        provider = AWSProvider()
        instances = provider.fetch_instances(region="us-east-1")
        print(instances[0])
    """

    def __init__(self, timeout: float = 120.0) -> None:
        self.timeout = timeout
        self._cache: dict[str, list[MachineType]] = {}

    # ── Provider interface ────────────────────────────────────────────────

    def fetch_instances(self, region: str) -> list[MachineType]:
        """Fetch all Linux EC2 instance types with prices for an AWS region.

        Args:
            region: AWS region code (e.g. "us-east-1")

        Returns:
            List of normalized MachineType objects.
        """
        if region not in self._cache:
            instances = parse_price_list(open_price_list(region, self.timeout), region)
            logger.info("Fetched %d instance types for region %s", len(instances), region)
            self._cache[region] = instances
        return self._cache[region]

    def fetch_instances_all_regions(
        self,
        regions: list[str] | None = None,
    ) -> list[MachineType]:
        """Fetch instance types across all (or the given) AWS regions.

        Downloads one price list per region, so all regions is roughly 30
        downloads of tens to hundreds of MB each; pass ``regions`` to limit it.
        A region that fails is logged and skipped.
        """
        target_regions = regions or AWS_REGIONS
        all_instances: list[MachineType] = []
        for region in target_regions:
            try:
                all_instances.extend(self.fetch_instances(region))
            except Exception as exc:
                logger.warning("Failed to fetch region %s: %s", region, exc)
        logger.info(
            "Total: %d instance types across %d regions",
            len(all_instances), len(target_regions),
        )
        return all_instances

    def get_pricing(self, instance_id: str, region: str) -> float:
        """Return the on-demand price/hr for an instance type, or 0.0 if not offered."""
        for instance in self.fetch_instances(region):
            if instance.id == instance_id:
                return instance.price_hr
        return 0.0

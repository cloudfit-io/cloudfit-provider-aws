"""AWS region list for cloudfit-provider-aws."""

from __future__ import annotations

# Commercial regions with a public EC2 price list (from the price list's
# region_index.json, read 2026-10-23; Local Zones, Wavelength, and GovCloud are
# left out). Opt-in regions are included; their price lists are public whether or
# not an account has enabled them.
AWS_REGIONS: list[str] = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ca-central-1", "ca-west-1",
    "sa-east-1", "mx-central-1",
    "eu-west-1", "eu-west-2", "eu-west-3",
    "eu-central-1", "eu-central-2",
    "eu-north-1", "eu-south-1", "eu-south-2",
    "ap-south-1", "ap-south-2",
    "ap-southeast-1", "ap-southeast-2", "ap-southeast-3",
    "ap-southeast-4", "ap-southeast-5", "ap-southeast-6", "ap-southeast-7",
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
    "ap-east-1", "ap-east-2",
    "me-south-1", "me-central-1",
    "il-central-1", "af-south-1",
]

# The five regions carried by the bundled snapshots, one per major geography,
# matching the spread of cloudfit-provider-gcp's snapshot regions.
SNAPSHOT_REGIONS: list[str] = [
    "us-east-1",
    "us-east-2",
    "us-west-2",
    "eu-west-1",
    "ap-southeast-1",
]

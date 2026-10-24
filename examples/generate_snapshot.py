"""Generate a machine-type snapshot from AWS's public EC2 price list.

Writes a list of cloudfit MachineType records (with perf_factor, gpu_type, and
1-year reserved prices) for the given regions, in the same format as
cloudfit-provider-gcp's snapshots. No AWS account or credentials are needed.

Run
---
    python examples/generate_snapshot.py --output aws_snapshot.json

    # custom regions (default: the five snapshot regions)
    python examples/generate_snapshot.py --regions us-east-1 eu-west-1

Notes
-----
- Each region's price list is a large download (about 300 MB for us-east-1),
  streamed and never held in memory whole. Expect a few minutes for five regions.
- The run fails, writing nothing, if any region returns no instance types, so a
  scheduled refresh cannot silently publish an empty or partial snapshot.
"""

from __future__ import annotations

import argparse
import json
import sys

from cloudfit_provider_aws import SNAPSHOT_REGIONS, AWSProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an AWS EC2 machine-type snapshot.")
    parser.add_argument(
        "--regions",
        nargs="+",
        default=SNAPSHOT_REGIONS,
        help="Regions to fetch (default: the five snapshot regions).",
    )
    parser.add_argument(
        "--output",
        default="aws_snapshot.json",
        help="Output JSON path (default: aws_snapshot.json).",
    )
    args = parser.parse_args()

    provider = AWSProvider()
    instances = []
    for region in args.regions:
        print(f"Fetching {region} ...", flush=True)
        try:
            fetched = provider.fetch_instances(region)
        except Exception as exc:
            sys.exit(f"error: fetching {region} failed ({exc}); nothing written.")
        if not fetched:
            sys.exit(f"error: no instance types for {region}; nothing written.")
        print(f"  {len(fetched)} instance types")
        instances.extend(fetched)

    # Stable order (the price list's row order shifts), so a refresh diff shows only real changes.
    instances.sort(key=lambda m: (m.region, m.id))
    rows = [m.model_dump(exclude_none=True) for m in instances]
    with open(args.output, "w") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")

    reserved = sum(1 for m in instances if m.cud_1yr_price_hr)
    gpus = sum(1 for m in instances if m.gpu_count)
    print(f"Wrote {len(rows)} rows to {args.output} ({reserved} with a 1-year price, {gpus} GPU)")


if __name__ == "__main__":
    main()

"""Fetch live EC2 instance types for a region and rank them for a workload.

No AWS account or credentials are needed: prices come from AWS's public price
list (a large download, about 300 MB for us-east-1).

    python examples/recommend.py            # us-east-1
    python examples/recommend.py eu-west-1
"""

from __future__ import annotations

import sys

from cloudfit import WorkloadProfile, rank

from cloudfit_provider_aws import AWSProvider


def main() -> None:
    region = sys.argv[1] if len(sys.argv) > 1 else "us-east-1"
    candidates = AWSProvider().fetch_instances(region)

    profile = WorkloadProfile(
        vcpu=32,
        ram_gb=128,
        archetype="cpu",
        optimize_for="balanced",
        region=region,
    )
    for result in rank(profile, candidates)[:5]:
        m = result.instance
        print(f"{m.id:<20} score={result.score:.3f}  ${m.price_hr:.4f}/hr  {result.reason}")


if __name__ == "__main__":
    main()
